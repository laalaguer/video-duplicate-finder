'''wxPython GUI for finding duplicate videos'''

import argparse
import sys
import platform
import subprocess
import wx.lib.newevent
from pathlib import Path
from tempfile import TemporaryDirectory
import wx
import wx.lib.scrolledpanel as scrolled

from utils.files import scan, sort_path_naturally, safe_remove
from utils.ffprobe import get_video_info
from utils.ffmpeg import screenshot
from utils.helpers import seconds_to_str, size_to_str, generate_random_string
from utils.images import HashableImage, HashComputer, create_thumb
from utils.video_compare import VideoComparisonObject, mark_groups, sort_videos
from utils.video_object import VideoObject
from utils.safe_counter import SafeCounter

# Custom event for video deletion
VideoDeleteEvent, VIDEO_EVT_DELETE = wx.lib.newevent.NewEvent()

class VideoDisplayPanel(wx.Panel):
    ''' Entry / item for displaying the video images and details '''
    def __init__(self, parent, video_object, images, property_diffs=None):
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
            (f"{video_object.width}x{video_object.height}", 'resolution'),
            (f"Duration: {seconds_to_str(video_object.duration)}", 'duration'),
            (f"Size: {size_to_str(video_object.size)}", 'size'),
            (f"FPS: {video_object.fps}", 'fps'),
            (f"Codec: {video_object.codec}", 'codec')
        ]
        
        for text, prop in info_labels:
            label = wx.StaticText(self, label=text)
            # Highlight in red if this property differs in the group
            if property_diffs and property_diffs.get(prop, False):
                label.SetForegroundColour(wx.Colour(255, 0, 0))  # Red
            info_sizer.Add(label, 0, wx.ALL, 2)
        sizer.Add(info_sizer, 0, wx.ALL, 5)
        
        # Delete button (far right)
        delete_btn = wx.Button(self, label="Delete")
        delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        sizer.Add(delete_btn, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        
        self.SetSizer(sizer)
    
    def on_delete(self, event):
        safe_remove(self.video_object.file_path)
        event.GetEventObject().Disable()
        
        # Send delete event up to parent window
        delete_event = VideoDeleteEvent()
        wx.PostEvent(self.GetParent().GetParent(), delete_event)

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
    ''' A window wrapper for a group of related videos '''
    def __init__(self, group_num, video_paths, video_objects, video_thumbs, total_groups=None, fast_mode=False):
        # Analyze property differences in the group
        self.property_diffs = self._analyze_property_differences(video_paths, video_objects)
        title = f"Group {group_num}"
        if fast_mode:
            title += " (fast mode)"
        wx.Frame.__init__(self, None, title=title, size=(850, 800))
        
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
                    video_thumbs[video_path],
                    self.property_diffs
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
        
        # Track fast mode and deletion counts
        self.fast_mode = fast_mode
        self.total_videos = len(video_paths)
        self.deleted_count = 0
        
        # Bind delete event handler
        self.Bind(VIDEO_EVT_DELETE, self.on_video_deleted)
        
        self.SetSizer(main_sizer)
        self.Show()
        self.Raise()  # Bring window to front
        self.SetFocus()  # Force focus
        self.RequestUserAttention()  # Ensure window gets attention
    
    def _analyze_property_differences(self, video_paths, video_objects):
        """Analyze video properties to find differences within the group"""
        properties = {
            'resolution': set(),
            'duration': set(),
            'size': set(),
            'fps': set(),
            'codec': set()
        }
        
        for path in video_paths:
            if path in video_objects:
                video = video_objects[path]
                properties['resolution'].add(f"{video.width}x{video.height}")
                properties['duration'].add(video.duration)
                properties['size'].add(video.size)
                properties['fps'].add(video.fps)
                properties['codec'].add(video.codec)
        
        # Return which properties have differences
        return {
            'resolution': len(properties['resolution']) > 1,
            'duration': len(properties['duration']) > 1,
            'size': len(properties['size']) > 1,
            'fps': len(properties['fps']) > 1,
            'codec': len(properties['codec']) > 1
        }

    def on_video_deleted(self, event):
        """Handle video deletion events"""
        self.deleted_count += 1
        if self.fast_mode and abs(self.total_videos - self.deleted_count) <= 1:
            self.Close()

def main():
    parser = argparse.ArgumentParser(description='Scan for video files')
    parser.add_argument('folder_path', type=str, help='Path to scan for video files')
    parser.add_argument('--no-ignore-hidden', action='store_false', dest='ignore_hidden',
                       help='Include hidden files/folders in scan')
    parser.add_argument('--no-ignore-readonly', action='store_false', dest='ignore_readonly_folder',
                       help='Include videos in read-only folders')
    parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                       help='Disable recursive directory scanning')
    parser.add_argument('--fast-mode', action='store_true',
                       help='Auto-close group window when all but one videos are marked for deletion')
    parser.add_argument('--ignore-partial-names', type=str, default='',
                       help='Comma-separated list of partial names to ignore in file paths')

    args = parser.parse_args()

    # Verify user provided path exists
    path = Path(args.folder_path)
    if not path.exists():
        print(f"Error: Path does not exist: {args.folder_path}")
        sys.exit(1)

    # Look for videos
    # Convert comma-separated ignore names to list
    ignore_names = [name.strip() for name in args.ignore_partial_names.split(',')] if args.ignore_partial_names else []
    
    video_files = scan(
        folder_path=args.folder_path,
        ignore_hidden=args.ignore_hidden,
        ignore_readonly_folder=args.ignore_readonly_folder,
        recursive=args.recursive,
        ignore_partial_names=ignore_names
    )

    # Create a temp dir to host screenshots of videos
    temp_dir = TemporaryDirectory()

    # Create video objects map
    video_objects = {}
    video_comparison_objects = {}
    video_thumbs = {}

    # Image Hash related
    _computer = HashComputer('ahash')
    try:
        for video_path in video_files:
            # Generate unique random string for this video
            rand_str = generate_random_string()
            
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
                    screenshot_path = Path(temp_dir.name) / f"{video_path.stem}_{rand_str}_{sec}s.jpg"
                    screenshot(str(video_path), str(screenshot_path), timestamp_str)
                    
                    _img_obj = create_thumb(screenshot_path)
                    if not video_thumbs.get(video_path, None):
                        video_thumbs[video_path] = []
                    if _img_obj:
                        video_thumbs[video_path].append(_img_obj)

                    video_obj.screenshots.append(screenshot_path)
            
            video_objects[video_path] = video_obj
            
            # Create VideoComparisonObject with hashed screenshots
            hashed_imgs = []
            for screenshot_path in video_obj.screenshots:
                try:
                    hashed_img = HashableImage(Path(screenshot_path), _computer)
                    hashed_imgs.append(hashed_img)
                except Exception as e:
                    print(f"Error processing screenshot {screenshot_path}: {e}")
            
            video_comparison_objects[video_path] = VideoComparisonObject(
                file_path=video_path,
                hashed_imgs=hashed_imgs
            )

    finally:
        temp_dir.cleanup()

    # Process video comparisons
    counter = SafeCounter()
    video_comparison_list = list(video_comparison_objects.values())
    grouped_videos = mark_groups(video_comparison_list, counter)
    
    # Filter out ungrouped videos (group_number = 0)
    filtered_videos = [v for v in grouped_videos if v.group_number > 0]
    
    # Sort the filtered videos
    sorted_videos = sort_videos(filtered_videos)

    # Group videos by group_number
    grouped_videos = {}
    for video in sorted_videos:
        if video.group_number not in grouped_videos:
            grouped_videos[video.group_number] = []
        grouped_videos[video.group_number].append(video.file_path)

    print(f"\nTotal Groups: {len(grouped_videos.keys())}")

    # Sort each group's videos naturally
    for group in grouped_videos:
        grouped_videos[group] = sort_path_naturally(grouped_videos[group])

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
                total_groups,
                args.fast_mode
            )
            app.MainLoop()  # Process events until window closes

if __name__ == '__main__':
    main()