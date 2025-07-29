'''wxPython GUI for finding duplicate images'''

import argparse
import sys
import platform
import subprocess
import wx.lib.newevent
from pathlib import Path
import wx
import wx.lib.scrolledpanel as scrolled

from utils.files import scan, sort_path_naturally, safe_remove, IMAGE_FILE_SUFFIXES
from utils.images import HashableImage, HashComputer, create_thumb, get_image_info
from utils.image_compare import ImageComparisonObject, mark_groups, sort_images
from utils.image_object import ImageObject
from utils.safe_counter import SafeCounter

# Custom event for image deletion
ImageDeleteEvent, IMAGE_EVT_DELETE = wx.lib.newevent.NewEvent()

class ImageDisplayPanel(wx.Panel):
    ''' Entry / item for displaying the image and details '''
    def __init__(self, parent, image_object, image, property_diffs=None):
        wx.Panel.__init__(self, parent, style=wx.BORDER_THEME)
        
        self.image_object = image_object
        self.image = image
        
        # Main sizer
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Image section (left)
        bitmap = wx.Bitmap.FromBuffer(image.width, image.height, image.tobytes())
        static_bitmap = wx.StaticBitmap(self, wx.ID_ANY, bitmap)
        static_bitmap.SetMinSize((200, -1))  # Fixed width of 200px
        sizer.Add(static_bitmap, 0, wx.ALL, 5)
        
        # Path section (middle) - constrained width
        path_panel = wx.Panel(self)
        path_panel.SetMinSize((190, -1))  # Fixed width
        path_sizer = wx.BoxSizer(wx.VERTICAL)
        path_text = wx.StaticText(path_panel, label=str(image_object.file_path))
        path_text.SetForegroundColour(wx.Colour(0, 0, 255))  # Blue color
        path_text.SetFont(path_text.GetFont().Underlined())  # Underlined
        path_text.Wrap(180)  # Wrap slightly less than panel width
        path_text.Bind(wx.EVT_LEFT_DOWN, lambda event: self.open_file_location(image_object.file_path))
        path_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        path_sizer.Add(path_text, 1, wx.EXPAND|wx.ALL, 5)
        path_panel.SetSizer(path_sizer)
        sizer.Add(path_panel, 1, wx.EXPAND|wx.ALL, 5)
        
        # Info section (right)
        info_sizer = wx.BoxSizer(wx.VERTICAL)
        info_labels = [
            (f"{image_object.width}x{image_object.height}", 'resolution'),
            (f"Size: {image_object.size}", 'size')
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
        safe_remove(self.image_object.file_path)
        event.GetEventObject().Disable()
        self.Hide()
        
        # Send delete event up to parent window
        delete_event = ImageDeleteEvent()
        wx.PostEvent(self.GetParent().GetParent(), delete_event)
        
        # Force layout update
        self.GetParent().Layout()

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
    ''' A window wrapper for a group of related images '''
    def __init__(self, group_num, image_paths, image_objects, image_thumbs, total_groups=None, fast_mode=False):
        # Analyze property differences in the group
        self.property_diffs = self._analyze_property_differences(image_paths, image_objects)
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
        
        # Middle scrolled panel for image content
        scroll_panel = scrolled.ScrolledPanel(self)
        scroll_panel.SetupScrolling()
        scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add image panels
        for image_path in image_paths:
            if image_path in image_thumbs and image_thumbs[image_path]:
                image_panel = ImageDisplayPanel(
                    scroll_panel,
                    image_objects[image_path],
                    image_thumbs[image_path][0],  # Only one thumbnail per image
                    self.property_diffs
                )
                scroll_sizer.Add(image_panel, 0, wx.EXPAND|wx.ALL, 5)
        
        scroll_panel.SetSizer(scroll_sizer)
        main_sizer.Add(scroll_panel, 1, wx.EXPAND)
        
        # Bottom panel with group info
        bottom_panel = wx.Panel(self)
        bottom_panel.SetBackgroundColour(wx.WHITE)
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        bottom_sizer.AddStretchSpacer()
        group_info = wx.StaticText(bottom_panel,
            label=f"Group {group_num} of {total_groups or len(image_objects)}")
        bottom_sizer.Add(group_info, 0, wx.ALL|wx.ALIGN_CENTER, 5)
        bottom_sizer.AddStretchSpacer()
        bottom_panel.SetSizer(bottom_sizer)
        main_sizer.Add(bottom_panel, 0, wx.EXPAND)
        
        # Track fast mode and deletion counts
        self.fast_mode = fast_mode
        self.total_images = len(image_paths)
        self.deleted_count = 0
        
        # Bind delete event handler
        self.Bind(IMAGE_EVT_DELETE, self.on_image_deleted)
        
        self.SetSizer(main_sizer)
        self.Show()
        self.Raise()  # Bring window to front
        self.SetFocus()  # Force focus
        self.RequestUserAttention()  # Ensure window gets attention
    
    def _analyze_property_differences(self, image_paths, image_objects):
        """Analyze image properties to find differences within the group"""
        properties = {
            'resolution': set(),
            'size': set()
        }
        
        for path in image_paths:
            if path in image_objects:
                image = image_objects[path]
                properties['resolution'].add(f"{image.width}x{image.height}")
                properties['size'].add(image.size)
        
        # Return which properties have differences
        return {
            'resolution': len(properties['resolution']) > 1,
            'size': len(properties['size']) > 1
        }

    def on_image_deleted(self, event):
        """Handle image deletion events"""
        self.deleted_count += 1
        if self.fast_mode and abs(self.total_images - self.deleted_count) <= 1:
            self.Close()

def main():
    parser = argparse.ArgumentParser(description='Scan for image files')
    parser.add_argument('folder_path', type=str, help='Path to scan for image files')
    parser.add_argument('--no-ignore-hidden', action='store_false', dest='ignore_hidden',
                       help='Include hidden files/folders in scan')
    parser.add_argument('--no-ignore-readonly', action='store_false', dest='ignore_readonly_folder',
                       help='Include images in read-only folders')
    parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                       help='Disable recursive directory scanning')
    parser.add_argument('--fast-mode', action='store_true',
                       help='Auto-close group window when all but one images are marked for deletion')
    parser.add_argument('--ignore-partial-names', type=str, default='',
                       help='Comma-separated list of partial names to ignore in file paths')

    args = parser.parse_args()

    # Verify user provided path exists
    path = Path(args.folder_path)
    if not path.exists():
        print(f"Error: Path does not exist: {args.folder_path}")
        sys.exit(1)

    # Look for images
    # Convert comma-separated ignore names to list
    ignore_names = [name.strip() for name in args.ignore_partial_names.split(',')] if args.ignore_partial_names else []
    
    image_files = scan(
        folder_path=args.folder_path,
        ignore_hidden=args.ignore_hidden,
        ignore_readonly_folder=args.ignore_readonly_folder,
        recursive=args.recursive,
        ignore_partial_names=ignore_names,
        target_suffixes=IMAGE_FILE_SUFFIXES
    )

    print(f"image files found: {len(image_files)}")

    # Create image objects map
    image_objects = {}
    image_comparison_objects = {}
    image_thumbs = {}

    # Image Hash related
    _computer = HashComputer('ahash')
    
    for image_path in image_files:

        _info = get_image_info(image_path)

        if not _info:
            print(f"Error reading image: {image_path}")
            continue
        
        # Create ImageObject
        image_obj = ImageObject(
            file_path=image_path,
            width=_info['width'],
            height=_info['height'],
            size=_info['file_size']
        )
        image_objects[image_path] = image_obj
        
        # Create thumbnail
        _img_thumb = create_thumb(image_path)
        if _img_thumb:
            image_thumbs[image_path] = [_img_thumb]
        else:
            print(f"Error generate thumb for image {image_path}")
            continue
        
        # Create ImageComparisonObject with hashed image
        hashed_img = None
        try:
            hashed_img = HashableImage.from_pil_image(image_path, _img_thumb, _computer)
        except Exception as e:
            print(f"Error hashing image {image_path}: {e}")
            continue
        
        image_comparison_objects[image_path] = ImageComparisonObject(
            file_path=image_path,
            hashed_img=hashed_img
        )

    # Process image comparisons
    counter = SafeCounter()
    image_comparison_list = list(image_comparison_objects.values())
    grouped_images = mark_groups(image_comparison_list, counter)

    print(f"Groups: {counter.peek_int()}")
    
    # Filter out ungrouped images (group_number = 0)
    filtered_images = [v for v in grouped_images if v.group_number > 0]
    
    # Sort the filtered images
    sorted_images = sort_images(filtered_images)

    # Group images by group_number
    grouped_images = {}
    for image in sorted_images:
        if image.group_number not in grouped_images:
            grouped_images[image.group_number] = []
        grouped_images[image.group_number].append(image.file_path)

    print(f"\nTotal Groups: {len(grouped_images.keys())}")

    # Sort each group's images naturally
    for group in grouped_images:
        grouped_images[group] = sort_path_naturally(grouped_images[group])

    # Create wxPython app
    app = wx.App(False)
    # Show each group in wxPython window
    total_groups = len(grouped_images.keys())
    for group_num in sorted(grouped_images.keys()):
        if grouped_images[group_num]:
            GroupWindow(
                group_num,
                grouped_images[group_num],
                image_objects,
                image_thumbs,
                total_groups,
                args.fast_mode
            )
            app.MainLoop()  # Process events until window closes

if __name__ == '__main__':
    main()