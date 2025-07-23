'''Tests for files.py module'''
import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.files import scan, VIDEO_FILE_SUFFIXES

class TestFileScanning(unittest.TestCase):
    def setUp(self):
        # Create temp directory in current test directory
        self.test_dir = Path(__file__).parent / 'test_temp'
        self.test_dir.mkdir(exist_ok=True)
        
        # Create some test files
        (self.test_dir / 'video1.mp4').touch()
        (self.test_dir / 'video2.mkv').touch()
        (self.test_dir / 'text.txt').touch()
        
        # Create a subdirectory
        subdir = self.test_dir / 'subdir'
        subdir.mkdir()
        (subdir / 'video3.avi').touch()
        (subdir / '.hidden_video.mp4').touch()
    
    def tearDown(self):
        # Clean up test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_scan_basic(self):
        '''Test basic file scanning'''
        result = scan(self.test_dir)
        expected = {
            self.test_dir / 'video1.mp4',
            self.test_dir / 'video2.mkv',
            self.test_dir / 'subdir' / 'video3.avi'
        }
        self.assertEqual(result, expected)
    
    def test_scan_ignore_hidden(self):
        '''Test hidden file handling'''
        result = scan(self.test_dir, ignore_hidden=True)
        self.assertNotIn(self.test_dir / 'subdir' / '.hidden_video.mp4', result)
        
        result = scan(self.test_dir, ignore_hidden=False)
        self.assertIn(self.test_dir / 'subdir' / '.hidden_video.mp4', result)
    
    def test_scan_non_recursive(self):
        '''Test non-recursive scanning'''
        result = scan(self.test_dir, recursive=False)
        expected = {
            self.test_dir / 'video1.mp4',
            self.test_dir / 'video2.mkv'
        }
        self.assertEqual(result, expected)
    
    def test_scan_all_video_formats(self):
        '''Test all supported video formats'''
        for ext in VIDEO_FILE_SUFFIXES:
            test_file = self.test_dir / f'test{ext}'
            test_file.touch()
            result = scan(self.test_dir)
            self.assertIn(test_file, result)
            test_file.unlink()


if __name__ == '__main__':
    unittest.main()