'''Command line interface for video file scanning'''

import argparse
import sys
from pathlib import Path
from utils.files import scan

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

    # Call scan function with arguments
    results = scan(
        folder_path=args.folder_path,
        ignore_hidden=args.ignore_hidden,
        ignore_readonly_folder=args.ignore_readonly_folder,
        recursive=args.recursive
    )

    # Print results line by line
    print(f"Found {len(results)} video files:")
    for file in sorted(results):
        print(file)

if __name__ == '__main__':
    main()