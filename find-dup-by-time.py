'''Command line interface for video file scanning sorted by duration'''

import argparse
import sys
import platform
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from collections import defaultdict
from utils.files import scan, sort_path_naturally, safe_remove
from utils.ffprobe import get_video_info
from utils.ffmpeg import screenshot
from utils.helpers import seconds_to_str, size_to_str
from utils.images import read_thumb
from utils.video_object import VideoObject
from PIL import ImageTk
import tkinter as tk

class VideoDisplayComponent(tk.Frame):
    def __init__(self, parent, video_object, images):
        super().__init__(parent, borderwidth=2, relief="groove", padx=10, pady=10)
        
        # Configure grid layout
        self.columnconfigure(0, weight=1)  # Images column
        self.columnconfigure(1, weight=1)  # Path column
        self.columnconfigure(2, weight=1)  # Info column
        self.columnconfigure(3, weight=1)  # Button column
        
        # First column - images
        img_frame = tk.Frame(self)
        img_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        
        # Display up to 3 images side by side
        for i, img in enumerate(images[:3]):
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(img_frame, image=photo)
            label.image = photo  # Keep reference
            label.pack(side=tk.LEFT, padx=5)
        
        # Second column - file path (with wrapping)
        path_frame = tk.Frame(self)
        path_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        def open_file_location():
            file_path = video_object.file_path
            parent = str(file_path.parent)
            if platform.system() == "Windows":
                import os
                os.startfile(parent)
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", str(file_path)])
            else:  # Linux
                subprocess.run(["xdg-open", parent])

        path_label = tk.Label(
            path_frame,
            text=str(video_object.file_path),
            wraplength=200,
            justify="left",
            fg="blue",
            cursor="hand2"
        )
        path_label.pack(fill="both", expand=True)
        path_label.bind("<Button-1>", lambda e: open_file_location())
        
        # Third column - video info
        info_frame = tk.Frame(self)
        info_frame.grid(row=0, column=2, sticky="nsew", padx=5)
        
        info_labels = [
            f"{video_object.width}x{video_object.height}",
            f"Duration: {seconds_to_str(video_object.duration)}",
            f"Size: {size_to_str(video_object.size)}",
            f"Codec: {video_object.codec}",
            f"FPS: {video_object.fps}"
        ]
        
        for text in info_labels:
            label = tk.Label(info_frame, text=text)
            label.pack(anchor="w")
        
        # Fourth column - delete button
        button_frame = tk.Frame(self)
        button_frame.grid(row=0, column=3, sticky="nsew", padx=5)
        
        def delete_and_close():
            safe_remove(video_object.file_path)
            delete_btn.config(state=tk.DISABLED, relief=tk.SUNKEN)
        
        delete_btn = tk.Button(
            button_frame,
            text="Delete",
            command=delete_and_close
        )
        delete_btn.pack()

def show_all_videos_window(video_paths, video_objects, video_thumbs):
    """Show a scrollable window with all videos sorted by duration"""
    window = tk.Toplevel()
    window.title("All Videos (Sorted by Duration)")
    window.minsize(850, 800)
    
    # Create canvas with scrollbar
    canvas = tk.Canvas(window)
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Enable middle-click drag scrolling
    def start_scroll(event):
        canvas.scan_mark(event.x, event.y)
    
    def move_scroll(event):
        canvas.scan_dragto(event.x, event.y, gain=1)
    
    scrollable_frame.bind("<ButtonPress-2>", start_scroll)
    scrollable_frame.bind("<B2-Motion>", move_scroll)
    
    def _on_mousewheel(event):
        """Handle mouse wheel events for scrolling"""
        if event.num == 5 or event.delta == -120:  # Scroll down
            canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:  # Scroll up
            canvas.yview_scroll(-1, "units")
    
    # Bind mouse wheel for all platforms
    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Button-4>", _on_mousewheel)  # Linux scroll up
    canvas.bind("<Button-5>", _on_mousewheel)  # Linux scroll down
    scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
    scrollable_frame.bind("<Button-4>", _on_mousewheel)
    scrollable_frame.bind("<Button-5>", _on_mousewheel)
    
    # Clean up bindings when window closes
    def _on_close():
        canvas.unbind("<MouseWheel>")
        canvas.unbind("<Button-4>")
        canvas.unbind("<Button-5>")
        scrollable_frame.unbind("<MouseWheel>")
        scrollable_frame.unbind("<Button-4>")
        scrollable_frame.unbind("<Button-5>")
        window.destroy()
    
    window.protocol("WM_DELETE_WINDOW", _on_close)
    
    # Pack widgets
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Add video components
    for video_path in video_paths:
        if video_path in video_thumbs and video_thumbs[video_path]:
            component = VideoDisplayComponent(
                scrollable_frame,
                video_objects[video_path],
                video_thumbs[video_path]
            )
            component.pack(fill="x", padx=10, pady=5)
    
    return window

def main():
    parser = argparse.ArgumentParser(description='Scan for video files sorted by duration')
    parser.add_argument('folder_path', type=str, help='Path to scan for video files')
    parser.add_argument('--no-ignore-hidden', action='store_false', dest='ignore_hidden',
                       help='Include hidden files/folders in scan')
    parser.add_argument('--no-ignore-readonly', action='store_false', dest='ignore_readonly_folder',
                       help='Include videos in read-only folders')
    parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                       help='Disable recursive directory scanning')
    parser.add_argument('--interactive', action='store_true',
                       help='Show one group at a time with thumbnails')

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

    if args.interactive:
        # Create root window (will be hidden but needed for mainloop)
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        # Set window icon
        icon = ImageTk.PhotoImage(file="logo.png")
        root.iconphoto(True, icon)

    # Create a temp dir to host screenshots of videos
    temp_dir = TemporaryDirectory()

    # Create video objects map
    video_objects = {}
    
    # Create map of video_path and screenshots
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
            timestamps = [10, 60, 120]
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

    # Sort all videos by duration (longest first)
    sorted_videos = sorted(
        video_objects.values(),
        key=lambda x: x.duration,
        reverse=True
    )

    # Print all video results
    if not args.interactive:
        print("\nAll Videos (Sorted by Duration):")
        for video_obj in sorted_videos:
            print(f"{seconds_to_str(int(video_obj.duration))} {video_obj.width}x{video_obj.height} {video_obj.fps} {video_obj.codec} {video_obj.file_path}")
    else:
        # Show all videos in single scrollable window
        window = show_all_videos_window(
            [v.file_path for v in sorted_videos],
            video_objects,
            video_thumbs
        )
        
        # When main window closes, exit program
        def on_close():
            root.quit()
            root.destroy()
        
        window.protocol("WM_DELETE_WINDOW", on_close)
        root.mainloop()

if __name__ == '__main__':
    main()