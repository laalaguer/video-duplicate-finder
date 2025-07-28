# About

<img src="./logo.png" width="192">


**Video Duplicate Finder** is an open source tool developed in Python 3, designed to identify duplicated video files by analyzing visual similarity. Unlike conventional duplicate detection methods that rely on file hashes or metadata, this software employs image-based comparison algorithms to detect duplicates even when the framerate, resolution parameters differ. Leveraging Python’s platform-independent architecture, the software is fully compatible with Windows, Linux, and macOS.

# GUI

<img src="./screenshot.png" width="800">

# System-wide Dependency

1) Python 3 (>=3.10 preferred)
2) `ffmpeg` and `ffprobe` binaries shall be present on your system. (extract video meta info and do screenshots)

# Library Dependency

Use Python virtual env to install the dependencies in isolation.

```bash
# Install
cd video-duplicate-finder/
python3 -m venv .env
source .env/bin/activate && pip3 install -r requirements.txt
```

or

```
# Install
make dep
```

# Use

## Command Line Interface (find-dup.py)

```bash
# Basic scan (just preview duplicates)
python3 find-dup.py /path/to/your/video/folder
```

## GUI (find-dup-wxpython.py)

```bash
# Launch the wxPython GUI
python3 find-dup-wxpython.py /path/to/your/video/folder
```

The wxPython GUI provides:
- Visual comparison of duplicate videos
- Side-by-side preview of video thumbnails
- One-click delete functionality
- Detailed video metadata display
 
# Methodology

Similar videos share some similar properties:
1) Resolution
2) Duration
3) Visually similar screenshots on specific time points.

This tool will capture screenshots and group similar videos, order them by resolution (desc).


# Buy Me a Coffee

No, I am kidding. With AI's help for the GUI interface, it took me only 1.5 days to finish the initial release version.

Feel free to use, update and fork the software.
