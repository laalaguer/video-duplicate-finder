'''
    Main logic for video comparison based on screenshots of video.
    If screenshots of video is similar to another video, it is considered same video.
    The judgement of 'similar' is based on the image hash of images.
    Logic placed here can be used in upper-level program. (GUI, cmd)
'''
from typing import List
from pathlib import Path
from .images import HashableImage, is_identical_img, is_similar_img
from .safe_counter import SafeCounter


class VideoComparisonObject:
    ''' Represents a Video Comparison Object,

        Unique key is its file_path.
    '''
    def __init__(self, file_path: Path, hashed_imgs: List[HashableImage]):
        self.file_path = file_path
        self.hashed_imgs = hashed_imgs
        self.group_number = 0


def visual_compare_video(a: VideoComparisonObject, b: VideoComparisonObject) -> bool:
    ''' visually compare videos (based on screenshots) '''
    if len(a.hashed_imgs) == 0 or len(b.hashed_imgs) == 0:
        return False

    same_flags = []
    for x, y in zip(a.hashed_imgs, b.hashed_imgs):
        same_flags.append(is_similar_img(x, y))
    
    return all(same_flags)


def mark_groups(a: List[VideoComparisonObject], counter: SafeCounter) -> List[VideoComparisonObject]:
    ''' Run through the list.
        Find the identical videos and mark the group number on the video (>0).
    '''
    for idx, item in enumerate(a):
        if idx == len(a) - 1:
            break

        if item.group_number > 0: # skip already grouped video
            continue

        for idx2, item2 in enumerate(a[idx+1:]):
            if item2.group_number > 0: # skip already grouped video
                continue

            if visual_compare_video(item, item2):
                if item.group_number == 0:
                    group_number = counter.get_int()
                    item.group_number = group_number
                    item2.group_number = group_number
                else:
                    item2.group_number = item.group_number
    
    return a


def sort_videos(a: List[VideoComparisonObject]) -> List[VideoComparisonObject]:
    ''' sort the input videos based on group number property (ascending) '''
    return sorted(a, key=lambda x: x.group_number)