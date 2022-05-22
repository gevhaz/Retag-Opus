# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2022-05-22

### Added

- Changelog
- Suggest splitting genre and artist tags when appropriate.
- Parse featuring artist from original title tag.
- Ability to remove tag data when a tag conflict is found.
- Let the user choose to print youtube description data at each conflict
  resolution stage.
- Add 'version' tag based on data about whether the song in a remix or
  is a live version.
- Add 'instrumental' as genre when data indicates song is instrumental.
- Allow setting album manually with --album flag.
- Add 'terminal menu' whenever user should select something. This is
  provided by a separate package. It is more interactive and user
  friendly than entering a number and pressing enter.
- Add ability to interactively choose the album artist from all known
  artists for song.
- Add data to version tag about whether the song is remastered.
- Display already handled/resolved tags as green when printing tags
  before each conflict resolution scenario.
- Allow deleting parts of tag from conflict resolution selection menu.
- Allow choosing tags from the known ones when manually setting a tag.

### Changed

- Refine regex to capture more formats for artist data.
- Prune title from original tags, not just from youtube tags.
- Ask before copying first parsed artist to 'albumartist' tag.
- Get youtube description from 'synopsis' tag as well as 'description'
  tag.
- Refine regex for finding live versions.
- Prune surrounding whitespace when cleaning up title tag.
- Combine view for showing original tags and youtube tags. They are now
  shown in one single list with the source indicated with color.
- List all known tags for the various tag sources regardless of whether
  they contain data.
- Allow exiting the program whenever.
- When setting the 'album' key manually, allow saving any parsed album
  title as 'discsubtitle'.
- Skip songs with no new data to add.

### Fixed

- Makeup artist and finishing artists are no longer added to the
  'artist' tag.
- Fix bug where choices weren't reshown when invalid choice was
  provided.
- Fix bug with pruning unnecessary tags.
- Missing colon before the "Not set" indicating a key has no value set
  when printing tags.
- Fix album data not being found in description.
- Fix original tags not being split.

### Removed

- Verbose flag.
