import time

import pygame # for optimising image data structures
from PIL import ImageSequence, Image

from Rect import Rect

class Gif(Rect, pygame.sprite.Sprite):
    
    def __init__(self, path=None, CONSTS=None):
        pygame.sprite.Sprite.__init__(self)
        
        self.filename = path.filename
        
        self.frames = []
        # duration of each frame, in milliseconds
        image = Image.open(path.filename)
        self.durations = []
        for frame_string, duration in extractFrames(image):
            self.frames.append(frame_string)
            self.durations.append(duration)
        
        self.totalDuration = 0
        self.currentDuration = 0
        
        self.SCREEN_HEIGHT = CONSTS['HEIGHT']
        
        self.LOADING_ITERATIONS = CONSTS['LOADING_ITERATIONS']

        self.height = path.height
        self.width  = path.width
        self.x      = path.x
        self.y      = 0 - path.height - path.y
        
        self.numFrames = len(self.frames)
        self.currentFrame = 0
        self.loops = 0
        self.complete = False
        self.MAX_LOOPS = int(CONSTS["LOOPS"])
        self.LOOP_TIME = int(CONSTS["LOOP_TIME"])*1000
        self.FALL_RATE = float(CONSTS["FALL_RATE"])/1000
        
    def ready(self):
        frames = []
        size= (self.width,self.height)
        time_elapsed = 0
        i = 0
        i_max = self.LOADING_ITERATIONS
        for frame_string in self.frames:
            t = time.time()
            frames.append(pygame.image.frombuffer(frame_string, size, 'RGBA').convert())
            time_elapsed += time.time() - t
            i += 1
            if i == 5:
                i = 0
                yield False
            #else:
            #    yield True
        self.frames = frames
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
            
    def update(self, gifs, dt, complete):
        self.currentDuration += dt
        self.totalDuration += dt
        if self.currentDuration >= self.durations[self.currentFrame]:
            self.currentDuration -= self.durations[self.currentFrame]
            self.currentFrame = (self.currentFrame + 1)%self.numFrames
        # move down, if not on bottom of screen
        if self.y + self.height < self.SCREEN_HEIGHT:
            self.y += int(self.FALL_RATE*dt)
            # if collision, move up again
            while self.collision(gifs) or self.y + self.height > self.SCREEN_HEIGHT:
                self.y -= 1
        # update images
        if self.currentFrame == self.numFrames-1:
            self.loops += 1
            if self.LOOP_TIME and self.totalDuration >= self.LOOP_TIME and not self.complete:
                self.complete = True
                complete.append(self.filename)
                
        if not self.LOOP_TIME and self.loops > self.MAX_LOOPS and not self.complete:
            self.complete = True
            complete.append(self.filename)
        self.image = self.frames[self.currentFrame]
        
        self.rect.x = self.x
        self.rect.y = self.y
        
    def collision(self, rects):
        '''test if this Gif collides with any others'''
        left = self.x; bottom = self.y; right = left+self.width; top = bottom+self.height
        for rect in rects:
            if rect == self: continue
            left2 = rect.x; bottom2 = rect.y; right2 = left2+rect.width; top2 = bottom2+rect.height
            col_test = not(left >= right2 or right <= left2 or top <= bottom2 or bottom >= top2)
            if col_test:
                return True
        return False

def gifIterator(img):
    """
    Handle gifs with transparency in non-changed pixels.
    
    Modified from:
    http://stackoverflow.com/questions/14550055/loss-of-data-when-extracting-frames-from-gif-to-png/14550885#14550885
    """
    pal = img.getpalette()
    prev = img.convert('RGBA')
    prev_dispose = True
    for i, frame in enumerate(ImageSequence.Iterator(img)):
        dispose = frame.dispose
    
        if frame.tile:
            x0, y0, x1, y1 = frame.tile[0][1]
            if not frame.palette.dirty:
                frame.putpalette(pal)
            frame = frame.crop((x0, y0, x1, y1))
            bbox = (x0, y0, x1, y1)
        else:
            bbox = None
    
        if dispose is None:
            prev.paste(frame, bbox, frame.convert('RGBA'))
            yield prev
            prev_dispose = False
        else:
            if prev_dispose:
                prev = Image.new('RGBA', img.size, (0, 0, 0, 0))
            out = prev.copy()
            out.paste(frame, bbox, frame.convert('RGBA'))
            yield out

def extractFrames(gif):
    """
    Extracts pygame.Surfaces from a source gif's frames.
    
    Modified from https://gist.github.com/revolunet/848913
    """
    size = gif.size
    frames = []
    for frame in gifIterator(gif):
        try:
            duration = frame.info['duration']
            if not duration: duration = 60
        except KeyError:
            duration = 60
        frame_string = frame.tostring()
        frames.append((frame_string,duration))
    return frames