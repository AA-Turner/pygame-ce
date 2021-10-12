import numpy
import cv2
import time

import pygame

def list_cameras():
    return [0]

def list_cameras_darwin():
    import subprocess
    import xml.etree.ElementTree as ElementTree

    flout, _ = subprocess.Popen("system_profiler -xml SPCameraDataType", shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    last_text = None
    cameras = []

    for node in ElementTree.fromstring(flout).iterfind('./array/dict/array/dict/*'):
        if last_text == "_name":
            cameras.append(node.text)
        last_text = node.text

    return cameras

class Camera(object):
    def __init__(self, device=0, size=(640, 480), mode="RGB"):
        if isinstance(device, int):
            self._device_index = device
        if isinstance(device, str):
            self._device_index = list_cameras_darwin().index(device)
        self._size = size
        
        if mode == "RGB":
            self._fmt = cv2.COLOR_BGR2RGB
        elif mode == "YUV":
            self._fmt = cv2.COLOR_BGR2YUV
        elif mode == "HSV":
            self._fmt = cv2.COLOR_BGR2HSV
        else:
            raise ValueError("Not a supported mode")

        self._open = False

    # all of this could have been done in the constructor, but creating
    # the VideoCapture is very time consuming, so it makes more sense in the
    # actual start() method
    def start(self):
        if self._open:
            return
        
        self._cam = cv2.VideoCapture(self._device_index)

        if not self._cam.isOpened():
            raise ValueError("Could not open camera.")

        self._cam.set(cv2.CAP_PROP_FRAME_WIDTH, self._size[0])
        self._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self._size[1])

        w = self._cam.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self._cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self._size = (int(w), int(h))

        self._flipx = False
        self._flipy = False
        self._brightness = 1

        self._frametime = 1 / self._cam.get(cv2.CAP_PROP_FPS)
        self._last_frame_time = 0

        self._open = True

    def stop(self):
        if self._open:
            self._cam.release()
            self._cam = None
            self._open = False

    def get_size(self):
        if not self._open:
            raise pygame.error("Camera needs to be started first")
        
        return self._size

    def set_controls(self, hflip = None, vflip = None, brightness = None):
        if not self._open:
            raise pygame.error("Camera needs to be started first")
        
        if hflip is not None:
            self._flipx = bool(hflip)
        if vflip is not None:
            self._flipy = bool(vflip)
        if brightness is not None:
            self._cam.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
            
        return self.get_controls()
        
    def get_controls(self):
        if not self._open:
            raise pygame.error("Camera needs to be started first")
        
        return (self._flipx, self._flipy, self._cam.get(cv2.CAP_PROP_BRIGHTNESS))

    def query_image(self):
        if not self._open:
            raise pygame.error("Camera needs to be started to read data")
        
        current_time = time.time()
        if current_time - self._last_frame_time > self._frametime:
            return True
        return False

    def get_image(self, dest_surf=None):
        if not self._open:
            raise pygame.error("Camera needs to be started to read data")
        
        self._last_frame_time = time.time()
        
        _, image = self._cam.read()
        
        image = cv2.cvtColor(image, self._fmt) 

        flip_code = None
        if self._flipx:
            if self._flipy:
                flip_code = -1
            else:
                flip_code = 1
        elif self._flipy:
            flip_code = 0

        if flip_code is not None:
            image = cv2.flip(image, flip_code)
        
        image = numpy.fliplr(image)
        image = numpy.rot90(image)

        surf = pygame.surfarray.make_surface(image)

        if dest_surf:
            dest_surf.blit(surf, (0,0))
            return dest_surf
            
        return surf

    def get_raw(self):
        if not self._open:
            raise pygame.error("Camera needs to be started to read data")

        self._last_frame_time = time.time()

        _, image = self._cam.read()

        return image.tobytes()

