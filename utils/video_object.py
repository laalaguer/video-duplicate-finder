from typing import List
from pathlib import Path


class VideoObject:
    '''Represents a video file with metadata and screenshots'''
    
    def __init__(
        self,
        file_path: Path,
        screenshots: List[Path],
        width: int = 0,
        height: int = 0,
        duration: int = 0,
        size: int = 0,
        fps: int = 0,
        codec: str = ""
    ):
        self.file_path = file_path
        self.screenshots = screenshots or []
        self.width = width
        self.height = height
        self.duration = duration
        self.size = size
        self.fps = fps
        self.codec = codec