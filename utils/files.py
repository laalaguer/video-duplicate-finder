''' file system related functions (Windows, Mac, Linux) '''

import os
from pathlib import Path
from typing import Set, Union

VIDEO_FILE_SUFFIXES = [
    '.asf',
    '.avi',
    '.flv',
    '.hevc',
    '.m4v',
    '.mkv',
    '.mov',
    '.mp4',
    '.mpeg',
    '.mpg',
    '.rm',
    '.rmvb',
    '.ts',
    '.vob',
    '.webm',
    '.wmv'
]

def _is_hidden(path: Path) -> bool:
    '''Check if a file/folder is hidden (works on Windows, Linux, Mac)'''
    if os.name == 'nt':  # Windows
        try:
            return bool(os.stat(path).st_file_attributes & 2)  # FILE_ATTRIBUTE_HIDDEN
        except:
            return False
    else:  # Unix-like
        return path.name.startswith('.')

def _is_readonly_folder(path: Path) -> bool:
    '''Check if a folder is read-only'''
    try:
        test_file = path / '.temp_test_file'
        test_file.touch()
        test_file.unlink()
        return False
    except (OSError, PermissionError):
        return True

def scan(folder_path: Union[str, Path], ignore_hidden: bool = True, ignore_readonly_folder: bool = True, recursive: bool = True) -> Set[Path]:
    '''
    Scan for video files in the specified folder.
    
    Args:
        folder_path: Path to scan
        ignore_hidden: Whether to ignore hidden files/folders
        ignore_readonly_folder: Whether to ignore read-only folders
        recursive: Whether to scan recursively
        
    Returns:
        Set of Path objects for found video files
    '''
    folder = Path(folder_path).resolve()
    video_files = set()
    
    def _scan(current_folder: Path):
        try:
            for item in current_folder.iterdir():
                if ignore_hidden and _is_hidden(item):
                    continue
                    
                if item.is_file():
                    if item.suffix.lower() in VIDEO_FILE_SUFFIXES:
                        video_files.add(item)
                elif item.is_dir() and recursive:
                    if ignore_readonly_folder and _is_readonly_folder(item):
                        # Only skip files directly in this folder, but still scan subfolders
                        _scan(item)
                    else:
                        _scan(item)
        
        except (PermissionError, OSError):
            pass
            
    _scan(folder)
    return video_files