''' ffmpeg command related functions '''
import subprocess

def screenshot(v_file:str, output_jpg_path:str, timestamp="01:00"):
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
