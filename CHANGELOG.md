# Changelog

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
