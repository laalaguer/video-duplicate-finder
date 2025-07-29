'''
    Main logic for image comparison based on screenshot of image.
    If screenshot of image is similar to another image, it is considered same image.
    The judgement of 'similar' is based on the image hash.
    Logic placed here can be used in upper-level program. (GUI, cmd)
'''
from typing import Optional, List
from pathlib import Path
from .images import HashableImage, is_similar_img
from .safe_counter import SafeCounter


class ImageComparisonObject:
    ''' Represents an Image Comparison Object,
    
        Unique key is its file_path.
    '''
    def __init__(self, file_path: Path, hashed_img: Optional[HashableImage] = None):
        self.file_path = file_path
        self.hashed_img = hashed_img
        self.group_number = 0


def visual_compare_image(a: ImageComparisonObject, b: ImageComparisonObject) -> bool:
    ''' visually compare images (based on single screenshot) '''
    if a.hashed_img is None or b.hashed_img is None:
        return False
    return is_similar_img(a.hashed_img, b.hashed_img)


def mark_groups(a: List[ImageComparisonObject], counter: SafeCounter) -> List[ImageComparisonObject]:
    ''' Run through the list.
        Find the identical images and mark the group number on the image (>0).
    '''
    for idx, item in enumerate(a):
        if idx == len(a) - 1:
            break

        if item.group_number > 0: # skip already grouped image
            continue

        for idx2, item2 in enumerate(a[idx+1:]):
            if item2.group_number > 0: # skip already grouped image
                continue

            if visual_compare_image(item, item2):
                if item.group_number == 0:
                    group_number = counter.get_int()
                    item.group_number = group_number
                    item2.group_number = group_number
                else:
                    item2.group_number = item.group_number
    
    return a


def sort_images(a: List[ImageComparisonObject]) -> List[ImageComparisonObject]:
    ''' sort the input images based on group number property (ascending) '''
    return sorted(a, key=lambda x: x.group_number)