from Rect import PhoneyRect

class RectPacker(object):
    
    def __init__(self, rect_library, initial_rects, CONSTS):
        '''
        Container which attempts to pack as many path as possible into a given
        space.
        '''
        self.width = CONSTS['WIDTH']
        self.height = CONSTS['HEIGHT']
        
        self.heights = self.width*[0]
        # Lowest Available Gap - (x coord, width)
        self.LAG = [0, self.width]
        
        self.rect_library = rect_library # {path name: Rect}
        self.placed_rects = {}
        self.rects_to_place = initial_rects # [path names]
        # where to place rects in the LAG. Alternate between left and right
        self.leftmost = True

        # how far above the screen rects can be placed legally
        self.HEIGHT_EXCEEDANCE_THRESHOLD = int(1.1*self.height)
        # maximum number of rects to attempt to fit before giving up (and recalcing LAG)
        self.MAX_PLACES = int(CONSTS['MAX_PLACES'])
        # maximum number of new LAGs to calculate before giving up (and terminating)
        self.MAX_RECALCS = int(CONSTS['MAX_RECALCS'])
        
        self.priority = 0
        
    def placeRects(self):
        '''
        attempts to place as many rects as possible.
        '''
        place_tries = 0
        recalcs = 0
        i = 0
        i_max = len(self.rects_to_place)
        time_elapsed = 0
        while self.rects_to_place:
            if recalcs > self.MAX_RECALCS:
                #print "placeRects aborting due to recalc limit"
                return
            if place_tries > self.MAX_PLACES:
                full_lag = self.__fillLAG()
                if full_lag:
                    #print "placeRects aborting due to LAG taking up whole width"
                    return
                place_tries = 0
                recalcs += 1
            i = i%i_max
            rect = self.rect_library[self.rects_to_place[i]]
            if self.__canPlace(rect):
                self.__placeRect(rect)
                place_tries = 0
                recalcs = 0
                i_max -= 1
                rect.priortity = self.priority
                self.priority += 1
                yield rect
            else:
                i += 1
                place_tries += 1
        #print "placeRects complete due to exhausted rects"

    def removeRects(self, rect_names):
        '''remove the named rects and drop other rects into the space left'''
        for rect_name in rect_names:
            assert rect_name in self.placed_rects
            '''if not rect_name in self.placed_rects:
                print "remove request", rect_name, "not in packer"
                print "rects in packer"
                for name in self.placed_rects.keys():
                    print name
                print
                continue'''
            self.placed_rects.pop(rect_name)
            yield rect_name
        self.__removePhonies()
    
    def __removePhonies(self):
        for rect in self.placed_rects.values():
            if type(rect) == PhoneyRect:
                self.placed_rects.pop(rect.filename)
        self.__dropRects()
        self.__recalc()
                
    def __dropRects(self):
        '''drop all rects into any available space'''
        movement = True
        while movement:
            movement = False
            for rect in self.placed_rects.values():
                rect.y -= 1
                if rect.collision(self.placed_rects.values()) or rect.y < 0:
                    rect.y += 1
                    continue
                while not (rect.collision(self.placed_rects.values())) and rect.y >= 0:
                    rect.y -= 1
                movement = True
                rect.y += 1
        self.__recalc()

    def __fillLAG(self):
        '''put a phoney rect in the LAG space'''
        left = self.LAG[0]
        right = sum(self.LAG)-1
        #print "heights",self.heights
        #print "lag",self.LAG
        #print "l,r",left,right
        #print "h: l,r",self.heights[left],self.heights[right]
        #print "h: l,r",self.heights[left-1],self.heights[right+1]
        #print
        if left == 0 and right == self.width-1:
            return True
        if left == 0:
            h = self.heights[right+1] - self.heights[right]
        elif right == self.width-1:
            h = self.heights[left-1] - self.heights[left]
        else:
            h = min(self.heights[right+1] - self.heights[right], self.heights[left-1] - self.heights[left])
        x = self.LAG[0]
        y = self.heights[x]
        w = self.LAG[1]
        rect = PhoneyRect(x,y,w,h)
        self.placed_rects[rect.filename] = rect
        
        # update heights
        for x in range(rect.x, rect.x+rect.width):
            self.heights[x] += rect.height
            
        # recalc LAG
        self.__recalcLAG()
        
    def __recalc(self):
        '''recalculate heights and LAG'''
        self.__recalcHeights()
        self.__recalcLAG()
    
    def __recalcHeights(self):
        self.heights = self.width*[0]
        for rect in self.placed_rects.values():
            h = rect.y+rect.height
            for x in range(rect.x, rect.x+rect.width):
                if h > self.heights[x]:
                    self.heights[x] = h
                    
    def __recalcLAG(self):
        self.LAG = [0,0]
        h = 2*self.height
        continueous = True
        for x in range(0,self.width):
            if self.heights[x] < h:
                h = self.heights[x]
                self.LAG[0] = x
                self.LAG[1] = 1
                continueous = True
            elif self.heights[x] == h and continueous:
                self.LAG[1] += 1
            else:
                continueous = False
    
    def __canPlace(self, rect):
        '''check if a rect can fit in the LAG'''
        return rect.width <= self.LAG[1] and rect.height+self.heights[self.LAG[0]] < self.HEIGHT_EXCEEDANCE_THRESHOLD
        
    def __placeRect(self, rect):
        '''place a rect in the LAG'''
        if self.leftmost:
            x = self.LAG[0]
        else:
            x = sum(self.LAG) - rect.width
        rect.x = x
        rect.y = self.heights[x]

        self.placed_rects[rect.filename] = rect
        self.rects_to_place.remove(rect.filename)
        
        # update heights
        for x in range(rect.x, rect.x+rect.width):
            self.heights[x] += rect.height
        
        # update LAG
        if self.leftmost:
            self.LAG[0] += rect.width
            self.LAG[1] -= rect.width
        else:
            self.LAG[1] -= rect.width
            
        if self.LAG[1] == 0:
            self.__recalcLAG()
            
        assert self.LAG[0] >= 0
        assert self.LAG[0] < self.width
        assert self.LAG[1] > 0
        
        self.leftmost = not self.leftmost