''' file system related functions (Windows, Mac, Linux) '''

import os
import re
from pathlib import Path
from typing import Set, Union, List

try:
    from send2trash import send2trash
    TRASH_SUPPORTED = True
except ImportError:
    TRASH_SUPPORTED = False

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

def atoi(text: str):
    ''' convert text to int, if failed then return text itself '''
    return int(text) if text.isdigit() else text


def natural_keys(text: str):
    ''' Given a string, chop it into a list.
        All the numbers will be turned to int.
        Text remains text。
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]

def sort_path_naturally(paths: List[Path]) -> List[Path]:
    ''' Return the paths with natural sorting by whole path, section by section, excluding suffix '''
    aparted_paths = []
    for p in paths:
        # Chop path into sections by OS separator
        sections = list(Path(p).parts)
        if sections:
            # For the last section (filename), remove suffix
            filename = sections[-1]
            stem = Path(filename).stem
            sections[-1] = stem
        # For each section, generate natural_keys()
        keys = []
        for section in sections:
            keys.extend(natural_keys(section))
        aparted_paths.append(keys)
    to_be_sorted = list(zip(aparted_paths, paths))
    sorted_list = sorted(to_be_sorted, key=lambda x: x[0])
    return [x[1] for x in sorted_list]

def silent_remove(path: Union[Path, str]) -> None:
    '''Remove a file silently without raising errors for permissions, not found, etc.
    
    Args:
        path: Path to file to remove (Path object or string)
        
    Returns:
        None in all cases
    '''
    try:
        path = Path(path) if not isinstance(path, Path) else path
        path.unlink()
    except (FileNotFoundError, PermissionError, OSError, IsADirectoryError):
        pass


def safe_remove(path: Union[Path, str], use_trash: bool = True) -> None:
    '''Remove a file, optionally using trash if available
    
    Args:
        path: Path to file to remove (Path object or string)
        use_trash: Whether to attempt using trash (default: True)
        
    Returns:
        None in all cases
    '''
    try:
        if use_trash and TRASH_SUPPORTED:
            send2trash(str(path))
        else:
            silent_remove(path)
    except Exception:
        silent_remove(path)


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

def scan(folder_path: Union[str, Path], ignore_hidden: bool = True, ignore_readonly_folder:bool = True, recursive: bool = True) -> Set[Path]:
    '''
    Scan for video files in the specified folder.
    
    Args:
        folder_path: Path to scan
        ignore_hidden: Whether to ignore hidden files/folders
        ignore_readonly_folder: Whether to ignore immediate child videos of read-only folders (since we cannot delete them)
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

                # If current_folder is set to 'readonly',
                # On Unix/Linux systems:
                # if no execute permission (no x) on dir, child_file.is_file() will FAIL with PermissionError
                # because: it needs execute permission on dir to access child file's metadata.
                # (in other words, it needs execute perssion to access dir's contents)
                # On Windows:
                # child_file.is_file() will succeed.
                if item.is_file() and item.suffix.lower() in VIDEO_FILE_SUFFIXES:
                    if ignore_readonly_folder and _is_readonly_folder(item.parent):
                        continue
                    video_files.add(item)
                
                if item.is_dir() and recursive:
                    _scan(item)
        except (PermissionError, OSError):
            pass
            
    _scan(folder)
    return video_files