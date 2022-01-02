# Retag Opus

Say you have a music file in opus format, with a tag called
`description` that holds data about the music in the format used by
Youtube's ContentID. This script will help you parse that tag and put
the relevant data into the tags where it actually belongs, such as
`title`, `artist`, and `album`.

# Usage

Run the script like so:

```
python3 main.py --directory /path/to/directory/with/your/opus/files.opus
```

There is also a help (`-h`) flag:

```
$ ./main.py -h
usage: main.py [-h] [-d DIR] [-v] [-V]

options:
  -h, --help            show this help message and exit
  -d DIR, --directory DIR
                        directory in which the files to be retagged are located
  -v, --verbose         show verbose output
  -V, --version         show program's version number and exit
```

# Project status

The project is still under development. The most common tags can be
parsed but there are many more which will just be ignored. Work needs to
be done in usability.
