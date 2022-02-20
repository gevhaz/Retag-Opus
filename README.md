# Retag Opus

Say you have a music file in opus format, with a tag called
`description` that holds data about the music in the format used by
Youtube's ContentID. This script will help you parse that tag and put
the relevant data into the tags where it actually belongs, such as
`title`, `artist`, and `album`.

# Dependencies

Retag requires
[simple-term-menu](https://github.com/IngoMeyer441/simple-term-menu) to
be installed.

# Usage

Run the script like so:

```
python3 retag --directory /path/to/directory/with/your/opus/files.opus
```

There is also a help (`-h`) flag:

```
$ retag -h
usage: main.py [-h] [-d DIR] [-v] [-V]

options:
-h, --help            show this help message and exit
-s {bash,zsh,tcsh}, --print-completion {bash,zsh,tcsh}
                      print shell completion script
-a, --all             Even if there is no YouTube description, suggest improving existing tags
-d DIR, --directory DIR
                      directory in which the files to be retagged are located
-V, --version         show program's version number and exit
```

# Project status

The project is still under development. The most common tags can be
parsed but there are many more which will just be ignored. Work needs to
be done in usability.
