from multiprocessing import Process

from RectPacker import RectPacker

class RectPackerManager(Process):
    
    def __init__(self, pack_in, remove_in, pack_out, remove_out, rect_library, initial_rects, CONSTS):
        '''Active thread object which wraps the RectPacker. Expects two input
        and two output pipe connections'''
        Process.__init__(self)
        self._daemonic = True
        # input streams
        self.pack_in = pack_in     # Queue of Rects
        self.remove_in = remove_in # Queue of rect names
        # output streams
        self.pack_out = pack_out     # Queue of Rects
        self.remove_out = remove_out # Queue of rect names
        
        self.packer = RectPacker(rect_library, initial_rects, CONSTS)

    def empty(self):
        return bool(self.packer.rects_to_place)
        
    def run(self):
        removed = []
        packed = []
        while True:
            to_remove = []
            to_pack = []
            # get input from Queues
            while not self.remove_in.empty():
                to_remove.append(self.remove_in.get_nowait())
            while not self.pack_in.empty():
                to_pack.append(self.pack_in.get_nowait())
            
            # remove rects
            for rect in self.packer.removeRects(to_remove):
                removed.append(rect)
            # place rects
            self.packer.rects_to_place.extend(to_pack)
            for rect in self.packer.placeRects():
                packed.append(rect)
                
            # send output along Queues
            while removed:
                if not self.remove_out.full():
                    self.remove_out.put_nowait(removed.pop())
                else:
                    break
            
            while packed:
                if not self.pack_out.full():
                    r = packed.pop()
                    self.pack_out.put_nowait(r)
                else:
                    break
