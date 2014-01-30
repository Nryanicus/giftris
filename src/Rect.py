from PIL import Image

class Rect(object):
    
    def __init__(self, path):
        self.filename = path
        image = Image.open(path)
        self.width,self.height = image.size
        self.x = 0
        self.y = 0
        
    def collision(self, rects):
        '''test if this Rect collides with any others'''
        left = self.x; bottom = self.y; right = left+self.width; top = bottom+self.height
        for rect in rects:
            if rect == self: continue
            left2 = rect.x; bottom2 = rect.y; right2 = left2+rect.width; top2 = bottom2+rect.height
            col_test = not(left >= right2 or right <= left2 or top <= bottom2 or bottom >= top2)
            if col_test:
                return True
        return False
    
    def contains(self, point):
        '''test if the given point is in this rect'''
        x, y = point
        return self.x <= x <= self.x+self.width and self.y <= y <= self.y+self.height
    
class PhoneyRect(Rect):
    
    def __init__(self, x, y, w, h):
        '''filled-in LAG used by RectPacker'''
        self.filename = "Phoney"+str(hash(self))
        self.x = x
        self.y = y
        self.width  = w
        self.height = h
        