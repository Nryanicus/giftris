from multiprocessing import Process
import os, ctypes

from Gif import Gif 

def avail():
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    
        def __init__(self):
            # have to initialize this to the size of MEMORYSTATUSEX
            self.dwLength = ctypes.sizeof(self)
            super(MEMORYSTATUSEX, self).__init__()
    
    stat = MEMORYSTATUSEX()
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
    return stat.ullAvailVirtual


class GifLoader(Process):
    
    def __init__(self, rect_in, gif_out, CONSTS):
        Process.__init__(self)
        self._daemonic = True
        self.CONSTS = CONSTS
        self.rect_in = rect_in # Queue
        self.gif_out = gif_out # Queue
        
    def run(self):
        while True:
            # blocking is fine here
            rect = self.rect_in.get()
            
            # rough estimate of RAM needed to store this gif
            filesize = os.path.getsize(rect.filename)
            pyobject_size_estimate = filesize*1.1
            while pyobject_size_estimate > avail():
                # if it's not available, spin until it is
                pass
            
            gif = Gif(rect, self.CONSTS)
            self.gif_out.put(gif)