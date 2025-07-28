'''wxPython GUI for finding duplicate videos by duration only'''

import argparse
import sys
import platform
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import wx
import wx.lib.scrolledpanel as scrolled

from utils.files import scan, sort_path_naturally, safe_remove
from utils.ffprobe import get_video_info
from utils.ffmpeg import screenshot
from utils.helpers import seconds_to_str, size_to_str
from utils.images import read_thumb
from utils.video_object import VideoObject

class VideoDisplayPanel(wx.Panel):
    def __init__(self, parent, video_object, images):
        wx.Panel.__init__(self, parent, style=wx.BORDER_THEME)
        
        self.video_object = video_object
        self.images = images
        
        # Main sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Images section (left)
        img_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for img in images[:3]:
            bitmap = wx.Bitmap.FromBuffer(img.width, img.height, img.tobytes())
            static_bitmap = wx.StaticBitmap(self, wx.ID_ANY, bitmap)
            static_bitmap.SetMinSize((100, -1))  # Fixed width of 100px
            img_sizer.Add(static_bitmap, 0, wx.ALL, 5)
        sizer.Add(img_sizer, 0, wx.ALL, 5)
        
        # Path section (middle) - constrained width
        path_panel = wx.Panel(self)
        path_panel.SetMinSize((190, -1))  # Fixed width
        path_sizer = wx.BoxSizer(wx.VERTICAL)
        path_text = wx.StaticText(path_panel, label=str(video_object.file_path))
        path_text.SetForegroundColour(wx.Colour(0, 0, 255))  # Blue color
        path_text.SetFont(path_text.GetFont().Underlined())  # Underlined
        path_text.Wrap(180)  # Wrap slightly less than panel width
        path_text.Bind(wx.EVT_LEFT_DOWN, lambda event: self.open_file_location(video_object.file_path))
        path_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        path_sizer.Add(path_text, 1, wx.EXPAND|wx.ALL, 5)
        path_panel.SetSizer(path_sizer)
        sizer.Add(path_panel, 1, wx.EXPAND|wx.ALL, 5)
        
        # Info section (right)
        info_sizer = wx.BoxSizer(wx.VERTICAL)
        info_labels = [
            f"{video_object.width}x{video_object.height}",
            f"Duration: {seconds_to_str(video_object.duration)}",
            f"Size: {size_to_str(video_object.size)}",
            f"FPS: {video_object.fps}",
            f"Codec: {video_object.codec}"
        ]
        for text in info_labels:
            label = wx.StaticText(self, label=text)
            info_sizer.Add(label, 0, wx.ALL, 2)
        sizer.Add(info_sizer, 0, wx.ALL, 5)
        
        # Delete button (far right)
        delete_btn = wx.Button(self, label="Delete")
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        sizer.Add(delete_btn, 0, wx.ALL, 5)
        
        self.SetSizer(sizer)
    
    def on_delete(self, event):
        safe_remove(self.video_object.file_path)
        event.GetEventObject().Disable()

    def open_file_location(self, file_path):
        """Open file location in system file explorer and focus on file"""
        file_path = Path(file_path)
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', '-R', str(file_path)])
            elif platform.system() == 'Windows':
                subprocess.run(['explorer', '/select,', str(file_path)])
            else:  # Linux and others
                subprocess.run(['xdg-open', str(file_path.parent)])
        except Exception as e:
            print(f"Error opening file location: {e}")

class GroupWindow(wx.Frame):
    def __init__(self, group_num, video_paths, video_objects, video_thumbs, total_groups=None):
        wx.Frame.__init__(self, None, title=f"Group {group_num}",
                         size=(850, 800))
        
        # Main sizer for entire window
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Top panel with close button
        top_panel = wx.Panel(self)
        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.AddStretchSpacer()
        close_btn = wx.Button(top_panel, label="Close group")
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        top_sizer.Add(close_btn, 0, wx.ALL|wx.TOP|wx.BOTTOM, 10)
        top_sizer.AddStretchSpacer()
        top_panel.SetSizer(top_sizer)
        main_sizer.Add(top_panel, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 10)
        
        # Middle scrolled panel for video content
        scroll_panel = scrolled.ScrolledPanel(self)
        scroll_panel.SetupScrolling()
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add video panels
        for video_path in video_paths:
            if video_path in video_thumbs and video_thumbs[video_path]:
                video_panel = VideoDisplayPanel(
                    scroll_panel,
                    video_objects[video_path],
                    video_thumbs[video_path]
                )
                scroll_sizer.Add(video_panel, 0, wx.EXPAND|wx.ALL, 5)
        
        scroll_panel.SetSizer(scroll_sizer)
        main_sizer.Add(scroll_panel, 1, wx.EXPAND)
        
        # Bottom panel with group info
        bottom_panel = wx.Panel(self)
        bottom_panel.SetBackgroundColour(wx.WHITE)
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        bottom_sizer.AddStretchSpacer()
        group_info = wx.StaticText(bottom_panel,
            label=f"Group {group_num} of {total_groups or len(video_objects)}")
        bottom_sizer.Add(group_info, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        bottom_sizer.AddStretchSpacer()
        bottom_panel.SetSizer(bottom_sizer)
        main_sizer.Add(bottom_panel, 0, wx.EXPAND)
        
        self.SetSizer(main_sizer)
        self.Show()
        self.Raise()  # Bring window to front
        self.SetFocus()  # Force focus
        self.RequestUserAttention()  # Ensure window gets attention

def group_videos_by_duration(video_objects):
    """Group videos by duration, return dict of {duration: [video_paths]}"""
    duration_groups = {}
    
    # Sort videos by duration (longest first)
    sorted_videos = sorted(
        video_objects.items(),
        key=lambda x: x[1].duration,
        reverse=True
    )
    
    for video_path, video_obj in sorted_videos:
        duration = video_obj.duration
        if duration not in duration_groups:
            duration_groups[duration] = []
        duration_groups[duration].append(video_path)
    
    # Filter out groups with only one video
    filtered_groups = {
        duration: paths 
        for duration, paths in duration_groups.items() 
        if len(paths) > 1
    }
    
    # Convert to group_number: paths format to match original structure
    return {
        i+1: sort_path_naturally(paths)
        for i, (duration, paths) in enumerate(filtered_groups.items())
    }

def main():
    parser = argparse.ArgumentParser(description='Scan for video files by duration')
    parser.add_argument('folder_path', type=str, help='Path to scan for video files')
    parser.add_argument('--no-ignore-hidden', action='store_false', dest='ignore_hidden',
                       help='Include hidden files/folders in scan')
    parser.add_argument('--no-ignore-readonly', action='store_false', dest='ignore_readonly_folder',
                       help='Include videos in read-only folders')
    parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                       help='Disable recursive directory scanning')

    args = parser.parse_args()

    # Verify user provided path exists
    path = Path(args.folder_path)
    if not path.exists():
        print(f"Error: Path does not exist: {args.folder_path}")
        sys.exit(1)

    # Look for videos
    video_files = scan(
        folder_path=args.folder_path,
        ignore_hidden=args.ignore_hidden,
        ignore_readonly_folder=args.ignore_readonly_folder,
        recursive=args.recursive
    )

    # Create a temp dir to host screenshots of videos
    temp_dir = TemporaryDirectory()

    # Create video objects map
    video_objects = {}
    video_thumbs = {}

    try:
        for video_path in video_files:
            # Get video info
            width, height, duration, size, fps, codec = get_video_info(str(video_path))
            duration = int(duration)
            
            # Create VideoObject
            video_obj = VideoObject(
                file_path=video_path,
                screenshots=[],
                width=width,
                height=height,
                duration=duration,
                size=size,
                fps=fps,
                codec=codec
            )
            
            # Take screenshots at key timestamps
            timestamps = [5, 60, 120]
            for sec in timestamps:
                if sec <= duration:  # Only if video is long enough
                    timestamp_str = seconds_to_str(sec)
                    screenshot_path = Path(temp_dir.name) / f"{video_path.stem}_{sec}s.jpg"
                    screenshot(str(video_path), str(screenshot_path), timestamp_str)
                    
                    _img_obj = read_thumb(screenshot_path)
                    if not video_thumbs.get(video_path, None):
                        video_thumbs[video_path] = []
                    if _img_obj:
                        video_thumbs[video_path].append(_img_obj)

                    video_obj.screenshots.append(screenshot_path)
            
            video_objects[video_path] = video_obj

    finally:
        temp_dir.cleanup()

    # Group videos by duration
    grouped_videos = group_videos_by_duration(video_objects)

    print(f"\nTotal Groups: {len(grouped_videos.keys())}")

    # Create wxPython app
    app = wx.App(False)
    # Show each group in wxPython window
    total_groups = len(grouped_videos.keys())
    for group_num in sorted(grouped_videos.keys()):
        if grouped_videos[group_num]:
            GroupWindow(
                group_num,
                grouped_videos[group_num],
                video_objects,
                video_thumbs,
                total_groups
            )
            app.MainLoop()  # Process events until window closes

if __name__ == '__main__':
    main()