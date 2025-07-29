# About

<img src="./logo.png" width="192">

**Video & Image Duplicate Finder** is an open source Python tool that identifies duplicate videos and images by analyzing visual similarity. It uses image comparison algorithms to detect duplicates even when file formats or resolutions differ.

Key Features:
- Visual comparison of duplicate videos and images
- Side-by-side preview of media thumbnails
- One-click delete functionality
- Detailed metadata display

# Example

<img src="./screenshot.png" width="800">

# Requirements

1) Python 3 (>=3.10 preferred)
2) `ffmpeg` and `ffprobe` binaries for video processing

# Install

```bash
# Create virtual environment and install dependencies
python3 -m venv .env
source .env/bin/activate && pip3 install -r requirements.txt
```

or

```bash
# Using Makefile
make dep
```

# Use

## Video Duplicates

### Command Line
```bash
python3 find-dup-vid.py /path/to/videos
```

### GUI
```bash
python3 find-dup-vid-wxpython.py /path/to/videos
```

## Image Duplicates

### Command Line
```bash
python3 find-dup-img.py /path/to/images
```

### GUI
```bash
python3 find-dup-img-wxpython.py /path/to/images
```

# License

Open source - feel free to use, modify and distribute.
