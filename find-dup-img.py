'''Command line tool for finding duplicate images'''

import argparse
import sys
import json
from pathlib import Path
from utils.files import scan, sort_path_naturally, IMAGE_FILE_SUFFIXES
from utils.images import HashableImage, HashComputer, create_thumb, get_image_info
from utils.image_compare import ImageComparisonObject, mark_groups, sort_images
from utils.image_object import ImageObject
from utils.safe_counter import SafeCounter

def format_size(size):
    '''Format file size with comma as thousand separator'''
    return f"{size:,}"

def main():
    parser = argparse.ArgumentParser(description='Scan for duplicate image files')
    parser.add_argument('folder_path', type=str, help='Path to scan for image files')
    parser.add_argument('--no-ignore-hidden', action='store_false', dest='ignore_hidden',
                       help='Include hidden files/folders in scan')
    parser.add_argument('--no-ignore-readonly', action='store_false', dest='ignore_readonly_folder',
                       help='Include images in read-only folders')
    parser.add_argument('--no-recursive', action='store_false', dest='recursive',
                       help='Disable recursive directory scanning')
    parser.add_argument('--ignore-partial-names', type=str, default='',
                       help='Comma-separated list of partial names to ignore in file paths')
    parser.add_argument('--json', type=str, default=None,
                       help='Path to JSON file to save grouped duplicates information')

    args = parser.parse_args()

    # Verify user provided path exists
    path = Path(args.folder_path)
    if not path.exists():
        print(f"Error: Path does not exist: {args.folder_path}")
        sys.exit(1)

    # Look for images
    ignore_names = [name.strip() for name in args.ignore_partial_names.split(',')] if args.ignore_partial_names else []
    
    image_files = scan(
        folder_path=args.folder_path,
        ignore_hidden=args.ignore_hidden,
        ignore_readonly_folder=args.ignore_readonly_folder,
        recursive=args.recursive,
        ignore_partial_names=ignore_names,
        target_suffixes=IMAGE_FILE_SUFFIXES
    )

    print(f"Image files found: {len(image_files)}")

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

    # Clean up thumbnails after processing
    del image_thumbs

    # Process image comparisons
    counter = SafeCounter()
    image_comparison_list = list(image_comparison_objects.values())
    grouped_images = mark_groups(image_comparison_list, counter)

    print(f"Potential duplicate groups found: {counter.peek_int()}")
    
    # Filter out ungrouped images (group_number = 0)
    filtered_images = [v for v in grouped_images if v.group_number > 0]
    
    # Sort the filtered images
    sorted_images = sort_images(filtered_images)

    # Group images by group_number
    grouped_images_dict = {}
    for image in sorted_images:
        if image.group_number not in grouped_images_dict:
            grouped_images_dict[image.group_number] = []
        grouped_images_dict[image.group_number].append(image.file_path)

    # Sort each group's images naturally
    for group in grouped_images_dict:
        grouped_images_dict[group] = sort_path_naturally(grouped_images_dict[group])

    # Prepare JSON output if requested
    json_output = {}
    
    print("\nDuplicate Groups:")
    for group_num in sorted(grouped_images_dict.keys()):
        group_files = grouped_images_dict[group_num]
        if group_files:
            print(f"\nGroup {group_num}:")
            
            # Prepare group entry for JSON
            json_group = []
            
            for file_path in group_files:
                img_obj = image_objects[file_path]
                resolution = f"{img_obj.width}x{img_obj.height}"
                size = format_size(img_obj.size)
                print(f"  {file_path} ({resolution}, {size} bytes)")
                json_group.append(str(file_path))
            
            json_output[group_num] = json_group

    # Save to JSON file if requested
    if args.json:
        try:
            with open(args.json, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, indent=2, ensure_ascii=False)
            print(f"\nGroup information saved to: {args.json}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")

if __name__ == '__main__':
    main()