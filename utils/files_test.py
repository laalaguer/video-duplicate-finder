'''Tests for files.py module - pytest version'''
import os
import platform
import pytest
from pathlib import Path
from unittest.mock import patch

from utils.files import scan, VIDEO_FILE_SUFFIXES

@pytest.fixture
def test_dir(tmp_path):
    """Create test directory structure with sample files"""
    # Create test files
    (tmp_path / 'video1.mp4').touch()
    (tmp_path / 'video2.mkv').touch()
    (tmp_path / 'text.txt').touch()
    
    # Create subdirectory
    subdir = tmp_path / 'subdir'
    subdir.mkdir()
    (subdir / 'video3.avi').touch()
    (subdir / '.hidden_video.mp4').touch()
    
    return tmp_path

@pytest.fixture
def readonly_dir_fixture(tmp_path):
    """Fixture with readonly subdirectory"""
    # Create main dir with video
    (tmp_path / 'video1.mp4').touch()
    
    # Create readonly subdir
    subdir = tmp_path / 'readonly_subdir'
    subdir.mkdir()
    (subdir / 'video2.mp4').touch()
    
    # Set readonly permissions
    if platform.system() == 'Windows':
        os.chmod(subdir, 0o555)  # Readonly on Windows
    else:
        os.chmod(subdir, 0o400)  # Readonly on Unix
    
    return tmp_path

def test_scan_basic(test_dir):
    '''Test basic file scanning'''
    result = scan(test_dir)
    expected = {
        test_dir / 'video1.mp4',
        test_dir / 'video2.mkv',
        test_dir / 'subdir' / 'video3.avi'
    }
    assert result == expected

def test_scan_ignore_hidden(test_dir):
    '''Test hidden file handling'''
    result = scan(test_dir, ignore_hidden=True)
    assert (test_dir / 'subdir' / '.hidden_video.mp4') not in result
    
    result = scan(test_dir, ignore_hidden=False)
    assert (test_dir / 'subdir' / '.hidden_video.mp4') in result

def test_scan_non_recursive(test_dir):
    '''Test non-recursive scanning'''
    result = scan(test_dir, recursive=False)
    expected = {
        test_dir / 'video1.mp4',
        test_dir / 'video2.mkv'
    }
    assert result == expected

def test_scan_all_video_formats(test_dir):
    '''Test all supported video formats'''
    for ext in VIDEO_FILE_SUFFIXES:
        test_file = test_dir / f'test{ext}'
        test_file.touch()
        result = scan(test_dir)
        assert test_file in result
        test_file.unlink()

def test_scan_ignore_readonly_folder(readonly_dir_fixture):
    '''Test scanning with ignore_readonly_folder=True'''
    result = scan(readonly_dir_fixture, ignore_readonly_folder=True)
    assert (readonly_dir_fixture / 'video1.mp4') in result
    assert (readonly_dir_fixture / 'readonly_subdir' / 'video2.mp4') not in result

def test_scan_include_readonly_folder(readonly_dir_fixture):
    '''Test scanning with ignore_readonly_folder=False'''
    result = scan(readonly_dir_fixture, ignore_readonly_folder=False)
    assert (readonly_dir_fixture / 'video1.mp4') in result
    
    # Platform-specific assertion
    if platform.system() == 'Windows':
        assert (readonly_dir_fixture / 'readonly_subdir' / 'video2.mp4') in result
    else:
        assert (readonly_dir_fixture / 'readonly_subdir' / 'video2.mp4') not in result