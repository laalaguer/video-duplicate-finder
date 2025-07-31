#!/usr/bin/env python3
'''Command line tool to compare two images and output their hashes and distance'''

import argparse
from pathlib import Path
from utils.images import HashComputer, HashableImage

def main():
    parser = argparse.ArgumentParser(description='Compare two images and output their hashes and distance')
    parser.add_argument('image1', type=str, help='Path to first image')
    parser.add_argument('image2', type=str, help='Path to second image')
    parser.add_argument('--hash-mode', choices=['ahash', 'phash'], default='ahash',
                       help='Hash algorithm to use (default: ahash)')
    
    args = parser.parse_args()
    
    # Validate image paths
    img1_path = Path(args.image1)
    img2_path = Path(args.image2)
    
    if not img1_path.exists():
        print(f"Error: Image not found - {img1_path}")
        return
    if not img2_path.exists():
        print(f"Error: Image not found - {img2_path}")
        return
    
    # Compute hashes
    computer = HashComputer(args.hash_mode)
    try:
        hashable1 = HashableImage(img1_path, computer)
        hashable2 = HashableImage(img2_path, computer)
    except Exception as e:
        print(f"Error processing images: {e}")
        return
    
    # Output results
    print(f"Image 1 ({img1_path}): {hashable1.get_hash()}")
    print(f"Image 2 ({img2_path}): {hashable2.get_hash()}")
    print(f"Distance between images: {abs(hashable1.get_hash() - hashable2.get_hash())}")

if __name__ == '__main__':
    main()