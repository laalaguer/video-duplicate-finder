'''Command line interface for video file scanning'''

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from utils.files import scan, sort_path_naturally
from utils.ffprobe import get_video_info
from utils.ffmpeg import screenshot
from utils.helpers import seconds_to_str
from utils.images import HashableImage, HashComputer
from utils.video_compare import VideoComparisonObject, mark_groups, sort_videos
from utils.safe_counter import SafeCounter

def main():
    parser = argparse.ArgumentParser(description='Scan for video files')
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

    # Create <video objects> map
    # key: video_path, value: VideoObject
    video_objects = {}
    
    # Create <video comparison objects> map
    # key: video_path, value: VideoComparisonObject
    video_comparison_objects = {}

    # Image Hash related
    _computer = HashComputer('ahash')
    
    try:
        for video_path in video_files:
            # Get video info
            width, height, duration, size, fps, codec = get_video_info(str(video_path))
            duration = int(duration)
            
            # Create VideoObject (assuming it's a dict for now)
            video_obj = {
                'path': video_path,
                'width': width,
                'height': height,
                'duration': duration,
                'size': size,
                'fps': fps,
                'codec': codec,
                'screenshots': []
            }
            
            # Take screenshots at key timestamps
            timestamps = [10, 60, 120]
            for sec in timestamps:
                if sec <= duration:  # Only if video is long enough
                    timestamp_str = seconds_to_str(sec)
                    screenshot_path = Path(temp_dir.name) / f"{video_path.stem}_{sec}s.jpg"
                    screenshot(str(video_path), str(screenshot_path), timestamp_str)
                    video_obj['screenshots'].append(str(screenshot_path))
            
            video_objects[video_path] = video_obj
            
            # Create VideoComparisonObject with hashed screenshots
            hashed_imgs = []
            for screenshot_path in video_obj['screenshots']:
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

    # Print grouped video results in ascending order
    print("\nDuplicate Video Groups:")
    for group_num in sorted(grouped_videos.keys()):
        print(f"\nGroup {group_num}:")
        for video_path in grouped_videos[group_num]:
            video_obj = video_objects[video_path]
            duration_str = seconds_to_str(video_obj['duration'])
            print(f"  - {video_path} [{video_obj['width']}x{video_obj['height']}, {video_obj['fps']} fps, {video_obj['codec']}, {duration_str}]")

if __name__ == '__main__':
    main()