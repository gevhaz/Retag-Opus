# Code style

- Use very descriptive variable names, even if they're long.
- Don't cram logic into one line. Prefer a plain loop or a named
  variable over a dense comprehension or a long expression.
- Follow PEP 8 and PEP 257 and write idiomatic Python, e.g. plain
  functions in a module rather than a class of static methods. Where
  the rules here differ from them, the rules here win.

# Docstrings

- Write for the caller: give enough to call the function without
  reading its code. Say what it returns, or what it does if it's
  called for its effect, and the special cases and constraints that
  its name and signature don't show.
- Don't restate the signature, e.g. `:param title: The title.` Leave
  out the parameter and return sections when a sentence covers them.
- Use a single line when the name and signature say the rest. An
  example often says more than another sentence would.
- Explain how the function works in comments in its body, so that the
  docstring stays true when the implementation changes. Leave out
  background that the caller doesn't need.
- Whatever a docstring repeats from the code has to be kept in sync by
  hand, and no check notices when it isn't. Prefer saying less to
  saying something that can go stale.
- Shorter doesn't mean fewer: public functions and functions with
  non-obvious behavior still get a docstring.

# Platforms

- Only Linux is supported, so e.g. `readline` can be used without a
  fallback for Windows.

# Tests

- The coverage threshold, `fail_under` in `pyproject.toml`, is only
  there to make a drop in coverage visible. It's completely fine to
  lower it when that makes sense, e.g. after removing tested code.

# Spellcheck

- Keep the words in `.github/data/project-dictionary.txt` sorted
  alphabetically, with uppercase before lowercase.

# Writing

- Write pull request descriptions and commit messages for a reader who
  reads them first, to get oriented, and only then looks at the code.
  Don't assume they already have a specific part of the code in mind.

# Commits

- Write the subject in the imperative mood, capitalized, without a full
  stop and without prefixes like `feat:`, e.g. "Fix parsing of guitar".
  Keep it short, ideally under 50 characters.
- In the body, explain what's wrong without the change and why the
  change fixes it. The diff shows how.
- Keep commit messages as long as the change needs, and only a little
  longer than in code written without AI. A small change gets a subject
  line and at most a few lines of body.
- Make one commit per logical change, e.g. a refactoring, a bug fix and
  a new feature are separate commits. One change across many files is
  still one commit. Each commit should pass the tests on its own.
- Until a branch is merged, fold review fixes into the commits they fix.

# Pull requests

- Follow the rules in @CONTRIBUTING.md.

# Standards

- When choosing between conventions, e.g. for tag names, prefer them in
  this order: the Vorbis comment specification, Quod Libet, MusicBrainz
  Picard, DDEX.
