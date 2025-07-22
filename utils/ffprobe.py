''' ffprobe related functions '''
import os
import subprocess
import json
from typing import Tuple, List

def _process_fps(data_str) -> int:
    ''' Process the fps number into int '''
    parts = data_str.split('/')
    if len(parts) != 2:
        return 0
    else:
        if parts[1] == '0':
            return 0
        else:
            return round(float(parts[0]) / float(parts[1]))

def get_video_info(file_path) -> Tuple[int, int, float, int, int, str]:
    ''' Return width, height, duration (seconds) , file size (bytes) , fps, encoder codec name'''
    try:
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-show_entries', 'format=size',
            '-show_entries', 'stream=width,height,avg_frame_rate,codec_name',
            '-select_streams', 'v:0',
            '-of', 'json',
            file_path
        ]
        output = subprocess.check_output(command).decode('utf-8').strip()

        data = json.loads(output)
        width = data['streams'][0]['width']
        height = data['streams'][0]['height']
        avg_frame_rate = _process_fps(data['streams'][0]['avg_frame_rate'])
        duration = float(data['format']['duration'])
        file_size = os.path.getsize(file_path)
        codec_name = str(data['streams'][0]['codec_name']) # hevc, h264

        return width, height, duration, file_size, avg_frame_rate, codec_name
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error processing video file: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise Exception(f"Error parsing ffprobe output: {e}")
