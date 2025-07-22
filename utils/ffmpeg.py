''' ffmpeg command related functions '''
from typing import Union, List, Tuple
from pathlib import Path
import subprocess
import os


def screenshot(v_file, output_jpg_path, timestamp="01:00"):
    ''' Take one screenshot at specific timestamp as jpg'''
    command = [
        "ffmpeg",
        "-ss", timestamp,
        "-i", v_file,
        "-vf", "scale=iw*sar:ih",  # Preserve aspect ratio
        "-vframes", "1",
        "-q:v", "3",
        output_jpg_path
    ]
    subprocess.run(command, check=True)


def fix_timestamp(video_file: Union[Path, str], output_file: Union[Path, str, None] = None):
    ''' Fix incorrect timestamp and artifacts before/after the video '''
    if output_file is None:
        file_name, file_extension = os.path.splitext(video_file)
        output_file = f"{file_name}_fix{file_extension}"
    
    command = [
        "ffmpeg",
        '-v', 'error',
        "-ss", "00:00",  # starting point, no end point (till the end)
        "-i", video_file,
        "-c", "copy",  # copy all streams
        "-reset_timestamps", "1",  # reset the timeline for newly created chunk of video
        str(output_file)  # Convert Path to string if needed
    ]
    subprocess.run(command, check=True)
