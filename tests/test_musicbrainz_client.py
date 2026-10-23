"""Tests for musicbrainz_client.py."""

import io
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import pytest

from retag_opus.musicbrainz_client import USER_AGENT, MusicBrainzClient, MusicBrainzError, exact_title_and_artist_query


class FakeOpener:
    """Stand-in for urlopen that returns or raises prepared results."""

    def __init__(self, *results: Any) -> None:
        """Store the results to return, in order."""
        self.results = list(results)
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> Any:
        """Record the request and return or raise the next result."""
        self.requests.append(request)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return io.BytesIO(json.dumps(result).encode())

    def query(self, index: int = -1) -> dict[str, list[str]]:
        """Get the query parameters of a recorded request."""
        return urllib.parse.parse_qs(urllib.parse.urlparse(self.requests[index].full_url).query)


class FakeTime:
    """Clock that only advances when sleeping."""

    def __init__(self) -> None:
        """Start the clock at an arbitrary time."""
        self.now = 100.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        """Get the current fake time."""
        return self.now

    def sleep(self, seconds: float) -> None:
        """Advance the fake time."""
        self.sleeps.append(seconds)
        self.now += seconds


def http_error(code: int) -> urllib.error.HTTPError:
    """Create an HTTP error with the given status code."""
    return urllib.error.HTTPError("https://musicbrainz.org", code, "error", None, None)  # type: ignore


def make_client(*results: Any) -> tuple[MusicBrainzClient, FakeOpener, FakeTime]:
    """Create a client with a fake opener and clock."""
    opener = FakeOpener(*results)
    fake_time = FakeTime()
    return MusicBrainzClient(opener, fake_time.clock, fake_time.sleep), opener, fake_time


def test_get_sends_user_agent_and_json_format() -> None:
    """Requests identify the app and ask for JSON."""
    client, opener, _ = make_client({"id": "abc"})
    assert client.get("recording/abc", {"inc": "artist-credits"}) == {"id": "abc"}
    assert opener.requests[0].get_header("User-agent") == USER_AGENT
    assert opener.query() == {"inc": ["artist-credits"], "fmt": ["json"]}


def test_get_is_cached() -> None:
    """Asking for the same resource twice only sends one request."""
    client, opener, _ = make_client({"id": "abc"})
    client.get("recording/abc", {})
    assert client.get("recording/abc", {}) == {"id": "abc"}
    assert len(opener.requests) == 1


def test_get_is_rate_limited() -> None:
    """Requests are spaced at least one second apart."""
    client, _, fake_time = make_client({}, {})
    client.get("recording/a", {})
    fake_time.now += 0.25
    client.get("recording/b", {})
    assert fake_time.sleeps == [0.75]


def test_get_not_found_returns_none() -> None:
    """A missing resource is not an error."""
    client, _, _ = make_client(http_error(404))
    assert client.get("recording/missing", {}) is None


def test_get_retries_when_busy(capsys: pytest.CaptureFixture[str]) -> None:
    """Busy responses are retried with doubling delays."""
    client, opener, fake_time = make_client(http_error(503), http_error(503), {"id": "abc"})
    assert client.get("recording/abc", {}) == {"id": "abc"}
    assert len(opener.requests) == 3
    assert fake_time.sleeps == [2.0, 4.0]
    assert "MusicBrainz is busy. Trying again in 4 seconds." in capsys.readouterr().out


def test_get_raises_when_busy_too_long() -> None:
    """Give up after three retries."""
    client, opener, _ = make_client(*[http_error(503)] * 4)
    with pytest.raises(MusicBrainzError, match="HTTP 503"):
        client.get("recording/abc", {})
    assert len(opener.requests) == 4


def test_get_raises_when_unreachable() -> None:
    """Network errors become MusicBrainzError."""
    client, _, _ = make_client(urllib.error.URLError("no network"))
    with pytest.raises(MusicBrainzError, match="no network"):
        client.get("recording/abc", {})


def test_exact_title_and_artist_query() -> None:
    """Search terms are quoted and escaped as phrases."""
    assert exact_title_and_artist_query('Say "Hi"', "Artist") == 'recording:"Say \\"Hi\\"" AND artist:"Artist"'


def test_search_recordings_with_fields() -> None:
    """Send a query that names fields as written."""
    client, opener, _ = make_client({"recordings": [{"id": "abc", "score": 100}]})
    assert client.search_recordings('recording:"Hi" AND artist:"Artist"') == [{"id": "abc", "score": 100}]
    assert opener.query()["query"] == ['recording:"Hi" AND artist:"Artist"']
    assert "dismax" not in opener.query()


def test_search_recordings_by_words() -> None:
    """Search for words only, leaving out other characters."""
    client, opener, _ = make_client({"recordings": [{"id": "abc"}]})
    assert client.search_recordings('Song: "Hi" | (Official) M.S. Artist') == [{"id": "abc"}]
    assert opener.query()["query"] == ["Song Hi Official M S Artist"]
    assert opener.query()["dismax"] == ["true"]


def test_search_not_found() -> None:
    """Searches that find nothing give no results."""
    client, _, _ = make_client(http_error(404))
    assert client.search_recordings("Title") == []


def test_search_releases() -> None:
    """Releases are searched by title and artist."""
    client, opener, _ = make_client({"releases": [{"id": "rel"}]}, {"releases": []})
    assert client.search_releases("Album", "Artist") == [{"id": "rel"}]
    assert opener.query()["query"] == ['release:"Album" AND artist:"Artist"']
    assert client.search_releases("Album", None) == []
    assert opener.query()["query"] == ['release:"Album"']


def test_lookup_recording() -> None:
    """A recording is looked up with its releases."""
    client, opener, _ = make_client({"id": "rec"})
    assert client.lookup_recording("rec") == {"id": "rec"}
    assert urllib.parse.urlparse(opener.requests[0].full_url).path == "/ws/2/recording/rec"
    assert opener.query()["inc"] == ["releases"]


def test_lookup_release() -> None:
    """A release is looked up with tracks and relationships."""
    client, opener, _ = make_client({"id": "rel"})
    assert client.lookup_release("rel") == {"id": "rel"}
    assert urllib.parse.urlparse(opener.requests[0].full_url).path == "/ws/2/release/rel"
    assert "recording-level-rels" in opener.query()["inc"][0]
