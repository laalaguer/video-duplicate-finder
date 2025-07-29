from typing import Optional
from pathlib import Path


class ImageObject:
    '''Represents an image file with metadata and single screenshot'''
    
    def __init__(
        self,
        file_path: Path,
        width: int = 0,
        height: int = 0,
        size: int = 0
    ):
        self.file_path = file_path
        self.width = width
        self.height = height
        self.size = size