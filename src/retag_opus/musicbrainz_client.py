"""Module for talking to the MusicBrainz web service.

Only read access is used, which requires no account or API key. The
MusicBrainz API rules require a User-Agent identifying the application
and no more than one request per second on average.
"""

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any, Final

from retag_opus import __version__, messages

JsonDict = dict[str, Any]

API_ROOT: Final[str] = "https://musicbrainz.org/ws/2/"
USER_AGENT: Final[str] = f"retag-opus/{__version__} ( https://github.com/gevhaz/Retag-Opus )"
MIN_REQUEST_INTERVAL_SECONDS: Final[float] = 1.0
# The service is often busy, so busy responses are retried with
# doubling delays: 2, 4, and 8 seconds.
RETRY_DELAYS: Final[list[float]] = [2.0, 4.0, 8.0]
REQUEST_TIMEOUT_SECONDS: Final[float] = 15.0


def quote_as_phrase(text: str) -> str:
    """Quote text as a phrase in a search query.

    MusicBrainz searches are written in the query language of the
    Lucene search engine, e.g. 'recording:"Title" AND artist:"Name"',
    where quotes make a phrase that has to match as a whole.
    """
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def exact_title_and_artist_query(title: str, artist: str) -> str:
    """Get a query for recordings with exactly the given title and artist.

    E.g. 'recording:"Title" AND artist:"Name"'.
    """
    return f"recording:{quote_as_phrase(title)} AND artist:{quote_as_phrase(artist)}"


class MusicBrainzError(Exception):
    """Raised when the MusicBrainz web service can't be used."""


class MusicBrainzClient:
    """Rate limited and cached client for the MusicBrainz web service."""

    def __init__(
        self,
        opener: Callable[..., Any] = urllib.request.urlopen,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a client with an empty cache.

        :param opener: Function opening a URL request, like urlopen.
        :param clock: Monotonic clock used for rate limiting.
        :param sleep: Function used to wait between requests.
        """
        self._opener = opener
        self._clock = clock
        self._sleep = sleep
        self._last_request_time: float | None = None
        self._cache: dict[str, JsonDict | None] = {}

    def _wait_for_rate_limit(self) -> None:
        """Sleep until enough time has passed since the last request."""
        if self._last_request_time is not None:
            elapsed = self._clock() - self._last_request_time
            if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
                self._sleep(MIN_REQUEST_INTERVAL_SECONDS - elapsed)
        self._last_request_time = self._clock()

    def get(self, path: str, params: dict[str, str]) -> JsonDict | None:
        """Get a resource from the web service as JSON.

        Responses are cached for the lifetime of the client, so asking
        for the same resource twice only results in one request.

        :param path: Path below the API root, e.g. "recording/<mbid>".
        :param params: Query parameters to send.

        :raises MusicBrainzError: If the service can't be reached or
            returns an error other than "not found".

        :return: The parsed JSON response, or None if the resource
            doesn't exist.
        """
        query = urllib.parse.urlencode({**params, "fmt": "json"})
        url = f"{API_ROOT}{path}?{query}"
        if url in self._cache:
            return self._cache[url]

        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        result: JsonDict | None = None
        retry_delays = iter(RETRY_DELAYS)
        while True:
            self._wait_for_rate_limit()
            try:
                with self._opener(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                    result = json.load(response)
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break
                # When busy, wait for the next delay, unless all delays are used up
                retry_delay = next(retry_delays, None)
                if e.code == 503 and retry_delay is not None:
                    messages.warning(f"MusicBrainz is busy. Trying again in {retry_delay:g} seconds.")
                    self._sleep(retry_delay)
                    continue
                raise MusicBrainzError(f"MusicBrainz returned HTTP {e.code} for {url}") from e
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                raise MusicBrainzError(f"Could not get data from MusicBrainz: {e}") from e

        self._cache[url] = result
        return result

    def search_recordings(self, query: str) -> list[JsonDict]:
        """Search for recordings.

        A query with field names, like 'recording:"Title" AND
        artist:"Name"', is sent as written. Any other query is words in
        any order, which may be in the title, artist, or release of the
        recording. That suits text that mixes them, like a YouTube video
        title. Characters other than letters and digits are left out of
        the words, since the service rejects some of them.

        :return: Recordings with the releases they're on, best match
            first.
        """
        query_has_field_names = re.search(r"\b[a-z]+:", query) is not None
        if query_has_field_names:
            return self._search("recording", {"query": query})
        words = " ".join(re.findall(r"\w+", query))
        return self._search("recording", {"query": words, "dismax": "true"})

    def search_releases(self, title: str, artist: str | None) -> list[JsonDict]:
        """Search for releases by title and optionally artist.

        :return: Releases, best match first. Each release has a "score"
            between 0 and 100 and a "track-count".
        """
        query = f"release:{quote_as_phrase(title)}"
        if artist:
            query += f" AND artist:{quote_as_phrase(artist)}"
        return self._search("release", {"query": query})

    def lookup_recording(self, mbid: str) -> JsonDict | None:
        """Get a recording with the releases it's on."""
        return self.get(f"recording/{mbid}", {"inc": "releases"})

    def lookup_release(self, mbid: str) -> JsonDict | None:
        """Get a release with its tracks and everything needed to tag them.

        The relationships of the recordings and of their works, such as
        performers and composers, are included, so one request is
        enough for all songs on the release.
        """
        inc = [
            "recordings",
            "artist-credits",
            "release-groups",
            "artist-rels",
            "work-rels",
            "recording-level-rels",
            "work-level-rels",
        ]
        return self.get(f"release/{mbid}", {"inc": "+".join(inc)})

    def _search(self, entity: str, params: dict[str, str]) -> list[JsonDict]:
        """Search for entities, e.g. recordings."""
        result = self.get(entity, {"limit": "25", **params})
        if result is None:
            return []
        found: list[JsonDict] = result.get(f"{entity}s", [])
        return found
