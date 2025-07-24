''' image load/manipulation/compare functions '''
from pathlib import Path
from PIL import Image as PILImage
import imagehash

# HASH_SIZE = 64
# IDENTICAL_THRESHOLD = 6 # nearly identical in 64 bits
# SIMILAR_THRESHOLD = 12 # visually similar in 64 bits

HASH_SIZE = 8
IDENTICAL_THRESHOLD = 1 # nearly identical in 8 bits
SIMILAR_THRESHOLD = 2 # visually similar in 8 bits

def _func_factory():
    ''' Function factory for imagehash '''
    def _ahash(img: PILImage.Image) -> imagehash.ImageHash:
        return imagehash.average_hash(img, hash_size=HASH_SIZE)
    
    def _phash(img: PILImage.Image) -> imagehash.ImageHash:
        return imagehash.phash(img, hash_size=HASH_SIZE)
    
    # def _dhash(img: PILImage.Image) -> imagehash.ImageHash:
    #     return imagehash.dhash(img, hash_size=64)
    
    # def _color(img: PILImage.Image) -> imagehash.ImageHash:
    #     return imagehash.colorhash(img, binbits=9)
    
    return {
        'ahash': _ahash,
        'phash': _phash,
        # 'dhash': _dhash,
        # 'color': _color,
    }

class HashComputer:
    ''' Image Hash Computer
        Recommend: 
        
        ahash & phash (for similarity and works pretty fast)
        dhash (not good)
        color (sensitive to color)
    '''
    MODE = _func_factory()
    
    def __init__(self, mode: str):
        _mode_name = mode.lower()
        if _mode_name in HashComputer.MODE:
            self.mode = HashComputer.MODE[_mode_name]
        else:
            self.mode = HashComputer.MODE['ahash'] # default mode is ahash

    def compute(self, img: PILImage.Image) -> imagehash.ImageHash:
        ''' compute the given img's image hash '''
        return self.mode(img)


class HashableImage:
    ''' Container of {Path, ImageHash} '''
    def __init__(self, path: Path, computer: HashComputer):
        self.path = path
        self.img = PILImage.open(path)
        self.computer = computer
        try:
            self.img_hash = computer.compute(self.img)
        except Exception as e:
            raise Exception(f'Error in hashing image: {str(path)}')

    def get_hash(self):
        return self.img_hash
    
    def get_path(self) -> Path:
        return self.path


def is_similar_img(a: HashableImage, b: HashableImage) -> bool:
    ''' Decide if images are similar '''
    return abs(a.get_hash() - b.get_hash()) < SIMILAR_THRESHOLD

def is_identical_img(a: HashableImage, b: HashableImage) -> bool:
    ''' Decide if images are identical '''
    return abs(a.get_hash() - b.get_hash()) < IDENTICAL_THRESHOLD