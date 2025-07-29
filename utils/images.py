''' image load/manipulation/compare functions '''
from typing import Union
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
        self.computer = computer
        try:
            with PILImage.open(path) as img: # optimize, make the image short lived.
                self.img_hash = computer.compute(img)
        except Exception as e:
            raise Exception(f'Error in hashing image: {str(path)}')

    @classmethod
    def from_pil_image(cls, path: Path, img: PILImage.Image, computer: HashComputer):
        '''Create HashableImage from existing PIL Image
        
        Args:
            path: path to the image file
            img: PIL Image to be hashed
            computer: HashComputer instance
        '''
        instance = cls.__new__(cls)
        instance.path = path
        instance.computer = computer
        instance.img_hash = computer.compute(img)
        return instance

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

def create_thumb(p: Path, dimension: int = 100) -> Union[None, PILImage.Image]:
    '''Read and resize an image to thumbnail with specified width.
    
    Args:
        p: Path to image file
        dimension: Maximum width of thumbnail (height scales proportionally)
        
    Returns:
        PIL.Image or None if error opening/processing file
    '''
    try:
        img = PILImage.open(p)
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")
        
        width, height = img.size
        
        if width > dimension:
            # Calculate new height preserving aspect ratio
            ratio = dimension / width
            new_height = int(height * ratio)
            img = img.resize((dimension, new_height))
        
        return img
    except Exception:
        return None

def get_image_info(p: Path) -> Union[dict[str, int], None]:
    '''Get detailed information about an image file
    
    Args:
        p: Path to the image file
        
    Returns:
        Dictionary containing:
        - width: Image width in pixels
        - height: Image height in pixels
        - file_size: File size in bytes
        Or None if the file cannot be read
    '''
    try:
        with PILImage.open(p) as img:
            width, height = img.size
        file_size = p.stat().st_size
        return {
            'width': width,
            'height': height,
            'file_size': file_size
        }
    except Exception:
        return None