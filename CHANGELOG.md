# Changelog

## [Unreleased]

### Added

- For songs from the same album, the album artist, date, genre and album only
  have to be chosen once.
- Look up songs on MusicBrainz, enabled with the `--musicbrainz` flag or
  `musicbrainz = true` in the configuration file. MusicBrainz is used as one
  more source of tags, including track numbers, credits and MusicBrainz IDs.
  Songs from the same album are looked up together.
- Video titles like "Artist - Title" are split into the artist and the title,
  when one side is the existing artist, which `yt-dlp` sets to the YouTube
  channel.
- Mixers and engineers are put in the `mixer` and `engineer` tags, from YouTube
  descriptions and from MusicBrainz, as in Picard.

### Changed

- Credits are put in tags named as on MusicBrainz: "Vocals" in YouTube
  descriptions goes in `performer:lead vocals` instead of `performer:vocals`,
  "Drums" in `performer:drums (drum set)` instead of `performer:drums`, and
  "Writer" or "Written by" in `writer` instead of `lyricist`. Tags with the old
  names are left as they are.
- All `performer:` tags are shown as performers, not only the ones parsed from
  YouTube descriptions.
- Programmers are no longer put in `performer:programming`. Programming isn't
  an instrument, and neither Quod Libet nor Picard has a tag for it.
- Credits in YouTube descriptions are read as a role and a name, instead of
  with one pattern per role. Roles are recognized when written in other ways,
  e.g. "Backing Vocals" or "Rhythm Guitar", and any role after "Associated
  Performer" in auto-generated descriptions is a performer's role, e.g.
  "Associated Performer, Theremin". A role has to be a known one, so e.g.
  "Makeup Artist" is no longer read as an artist.
- The result shown before saving only lists performers that have a value or
  were removed, instead of every performer that can be parsed from YouTube
  descriptions.
- Notes about the YouTube video, like "(Official Video)" or "[Lyric Video]",
  and hashtags at the end are removed from titles.
- A song found on MusicBrainz by the words of a video title is only used
  without asking if one of its artists is among the words or is the YouTube
  channel.
- Notes about the video, like "(Official Video)", are left out when searching
  MusicBrainz.
- The auto-generated part of a YouTube description is read by its layout, also
  when it's pasted among other text, and only there are the organization,
  copyright and release date read. Copies whose layout was changed, e.g. with
  all lines joined into one, no longer give a title or organization made of
  several lines run together. Conflicts are asked about with the title first.
- The values of a tag are listed in the same order everywhere: the YouTube
  description, tags parsed from the original tags, tags parsed from the YouTube
  tags, MusicBrainz, and last the existing metadata.
- Python 3.13 or newer is now required.
- `--album` (`-b`) is replaced by `--grouping` (`-g`), which puts songs in a mix
  of your own by setting the `grouping` tag. The album stays the one the song is
  from, instead of becoming the disc subtitle, and its tags from MusicBrainz,
  like track numbers, are used.
- Unset tags are shown in gray instead of black, so they are readable on dark
  terminal backgrounds.
- Colors are turned off when the `NO_COLOR` environment variable is set, and
  can be forced on with `FORCE_COLOR`.

### Removed

- The `-a`/`--all` option. It never did anything: existing tags are parsed for
  all songs, whether or not they have a YouTube description.
- The dependency on colorama.

### Fixed

- "Guitar" in YouTube descriptions is read. "Electric Guitar" is put in
  `performer:electric guitar`, the name of that instrument on MusicBrainz.
- Manually entered genres are split on commas and semicolons, and all manually
  entered tags on ` | `, like when modifying tags.
- Tags deleted because of the configuration are no longer restored when the
  YouTube description or parsed tags have the same value.
- Look for the configuration file in `XDG_CONFIG_HOME`, as documented, instead
  of `XDG_CONFIG_DIR`.

### Internal

- Run CI and deployment on Python 3.13.
- Drop the `pydub` test dependency, which doesn't work on Python 3.13, and
  generate the test audio file with `ffmpeg` directly instead.
- Update `flake8`, `coverage` and `pytest-cov` to versions that work on Python 3.12+.
- Lower the required test coverage from 95.73% to 95%.

## [0.4.1] - 2024-01-28

### Internal

- Update deploy workflow to use Trusted Publisher technology. This doesn't
  affect users.

## [0.4.0] - 2024-01-28

### Added

- Information about whether the song is an "Album version" or not is now parsed
  from the title of analyzed songs.
- Add a section to the printed tags for tags that are not tracked by Retag
  Opus. This gives the user the opportunity to manually modify or delete any tag
  in the audio file.
- Show values from original metadata of tags that will be deleted.
- Add configuration file.
- Add ability to configure tags that should always be deleted, or tag content,
  the presence of which, should lead to the deletion of that tag.

### Changed

- Show metadata that was extracted from the original metadata above metadata
  extracted from YouTube and above the original metadata. This metadata tends to
  be the most accurate if it exists.
- Make metadata that was extracted from the original metadata accepted by
  default if the tag where it will be added to is empty.
- Make regular expressions for extracting data from original metadata case
  insensitive.

### Fixed

- Add comment tag about source of song only if the source has been verified.
- Make sure tags that have been marked for deletion are actually deleted in the
  audio file.
- Do not add source metadata comment tag if it already exists.
- When setting a manual album – so that any old or extracted album goes in the
  `discsubtitle` tag instead – make sure that both are printed with the right
  tag name in the tags printed during operation of the program.
- Improve ability to extract artist and title from file name. This is only used
  to show which song is being re-tagged, not to actually add tags to the file.
- Fix and improve extraction of "featuring" artist.
- Strip white space from beginning and end of tags when they are split.
- Strip white space without treating it as a new tag for the users to approve.
- Fix extraction of "remastered" versions.
- Remove duplicate values in tags if there are any.

## [0.3.0] - 2022-05-30

### Modified

- Restructure project to use Poetry.
- Deploy this and future versions to PyPI through GitHub Actions.

## [0.2.0] - 2022-05-22

### Added

- Changelog
- Suggest splitting `genre` and `artist` tags when appropriate.
- Parse featuring artist from original `title` tag.
- Ability to remove tag data when a tag conflict is found.
- Let the user choose to print YouTube description data at each conflict
  resolution stage.
- Add `version` tag based on data about whether the song in a remix or
  is a live version.
- Add `instrumental` as genre when data indicates song is instrumental.
- Allow setting album manually with `--album` flag.
- Add 'terminal menu' whenever user should select something. This is
  provided by a separate package. It is more interactive and user
  friendly than entering a number and pressing enter.
- Add ability to interactively choose the album artist from all known
  artists for song.
- Add data to `version` tag about whether the song is remastered.
- Display already handled/resolved tags as green when printing tags
  before each conflict resolution scenario.
- Allow deleting parts of tag from conflict resolution selection menu.
- Allow choosing tags from the known ones when manually setting a tag.

### Changed

- Refine regex to capture more formats for artist data.
- Prune title from original tags, not just from YouTube tags.
- Ask before copying first parsed artist to `albumartist` tag.
- Get YouTube description from `synopsis` tag as well as `description`
  tag.
- Refine regex for finding live versions.
- Prune surrounding white space when cleaning up `title` tag.
- Combine view for showing original tags and YouTube tags. They are now
  shown in one single list with the source indicated with color.
- List all known tags for the various tag sources regardless of whether
  they contain data.
- Allow exiting the program whenever.
- When setting the `album` key manually, allow saving any parsed album
  title as `discsubtitle`.
- Skip songs with no new data to add.

### Fixed

- Makeup artist and finishing artists are no longer added to the
  `artist` tag.
- Fix bug where choices weren't reshown when invalid choice was
  provided.
- Fix bug with pruning unnecessary tags.
- Missing colon before the "Not set" indicating a key has no value set
  when printing tags.
- Fix album data not being found in description.
- Fix original tags not being split.

### Removed

- Verbose flag.
