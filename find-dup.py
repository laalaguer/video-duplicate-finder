'''Command line interface for video file scanning'''

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from utils.files import scan, sort_path_naturally
from utils.ffprobe import get_video_info
from utils.ffmpeg import screenshot
from utils.helpers import seconds_to_str, size_to_str
from utils.images import HashableImage, HashComputer, read_thumb
from utils.video_compare import VideoComparisonObject, mark_groups, sort_videos
from utils.video_object import VideoObject
from utils.safe_counter import SafeCounter
from PIL import ImageTk
import tkinter as tk

def open_img_window(video_object, images):
    # Create window
    window = tk.Toplevel()
    window.title(video_object.file_path.name)
    
    # First row - images
    img_frame = tk.Frame(window)
    img_frame.pack(pady=10)
    
    # Display up to 3 images side by side
    for i, img in enumerate(images[:3]):
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(img_frame, image=photo)
        label.image = photo  # Keep reference
        label.pack(side=tk.LEFT, padx=10)
    
    # Second row - video info
    info_frame = tk.Frame(window)
    info_frame.pack(pady=10)
    
    # Stacked video info labels
    info_labels = [
        f"{video_object.width}x{video_object.height}",
        f"Duration: {seconds_to_str(video_object.duration)}",
        f"Size: {size_to_str(video_object.size)}",
        f"Codec: {video_object.codec}",
        f"FPS: {video_object.fps}"
    ]
    
    for text in info_labels:
        label = tk.Label(info_frame, text=text)
        label.pack()
    
    # Third row - delete button
    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)
    
    def delete_and_close():
        from utils.files import silent_remove
        silent_remove(video_object.file_path)
        window.after(1000, window.destroy)  # Close after 1 second
    
    delete_btn = tk.Button(
        button_frame,
        text="Delete",
        command=delete_and_close
    )
    delete_btn.pack()
    
    return window

def main():
    parser = argparse.ArgumentParser(description='Scan for video files')
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
        # Create root window first (hidden)
        root = tk.Tk()
        root.withdraw()

    # Create a temp dir to host screenshots of videos
    temp_dir = TemporaryDirectory()

    # Create <video objects> map
    # key: video_path, value: VideoObject
    video_objects = {}
    
    # Create <video comparison objects> map
    # key: video_path, value: VideoComparisonObject
    video_comparison_objects = {}

    # Create a map of video_path and screenshots
    # key: video_path, value: List[PIL_Image]
    video_thumbs = {}

    # Image Hash related
    _computer = HashComputer('ahash')
    
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

    # Sort each group's videos naturally
    for group in grouped_videos:
        grouped_videos[group] = sort_path_naturally(grouped_videos[group])

    # Print grouped video results
    print("\nDuplicate Video Groups:")
    for group_num in sorted(grouped_videos.keys()):
        print(f"\nGroup {group_num}:")
        for video_path in grouped_videos[group_num]:
            video_obj = video_objects[video_path]
            duration_str = seconds_to_str(video_obj.duration)
            print(f"  - {video_path} [{video_obj.width}x{video_obj.height}, {video_obj.fps} fps, {video_obj.codec}, {duration_str}]")
        
        if args.interactive:
            # Show thumbnails for first video in group
            for video_path_2 in grouped_videos[group_num]:
                if video_path_2 in video_thumbs and video_thumbs[video_path_2]:
                    open_img_window(video_objects[video_path_2], video_thumbs[video_path_2])
            
        # Wait for user input before next group
        input("\nPress Enter to continue to next group...")

if __name__ == '__main__':
    main()