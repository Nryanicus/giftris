import os, ctypes, sys
from random import shuffle, randint
from copy import copy
from multiprocessing import Queue, Manager, freeze_support
from Queue import Full, Empty

import pygame

from Gif import Gif
from Rect import Rect
from RectPackerManager import RectPackerManager
from GifLoader import GifLoader

def main():
    #### Initialisation ####
    
    ## get config data
    WIDTH = ctypes.windll.user32.GetSystemMetrics(0)
    HEIGHT = ctypes.windll.user32.GetSystemMetrics(1)
    CONSTS = {"WIDTH":WIDTH,"HEIGHT":HEIGHT}
    with open("config.txt","r") as config:
        for line in config:
            if line[0] == "#" or line == "\n": continue
            key,value = line.split(" ")
            value = value.strip()
            CONSTS[key] = value
            
    ## get gif library
    gif_path = CONSTS['SOURCE_DIRC']
    assert os.path.exists(gif_path), gif_path+" is not an valid directory"
    all_files = os.listdir(gif_path)
    gif_files = []
    for file in all_files:
        if file[-4:] == ".gif":
            gif_files.append(gif_path+"\\"+file)
            
    ## Packer process Setup
    rect_library = {}
    for filename in gif_files:
        rect_library[filename] = Rect(filename)
    
    # Queues
    pack_in = Queue()    # Queue of rects names
    remove_in = Queue()  # Queue of rect names
    pack_out = Queue()   # Queue of Rects
    remove_out = Queue() # Queue of rects names
    
    rect_in = Queue()    # Queue of rects
    gif_out = Queue()    # Queue of gifs
    
    initial_rects = rect_library.keys()
    shuffle(initial_rects)
    packer = RectPackerManager(pack_in, remove_in, pack_out, remove_out, rect_library, initial_rects, CONSTS)
    packer.start()
    
    ## GifLoader process Setup
    loader = GifLoader(rect_in, gif_out, CONSTS)
    loader.start()
    
    ## pygame bootstrappery
    pygame.init()
    # move display window to top left of screen
    os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
    screen = pygame.display.set_mode((WIDTH, HEIGHT),pygame.NOFRAME)
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    # pleasant dark grey
    background.fill((20, 20, 20))
    pygame.display.set_caption('Giftris')
    clock = pygame.time.Clock()
    
    active_sprites = pygame.sprite.Group()
    active_gifs = {}
    
    #### Application Loop ####
    dt = 0
    rects_to_add = [] # rects which need to be added to the packer
    added_rects = initial_rects  # rects which have been added, and must not be again
    completed_gifs = [] # gifs whose animation is done and must be removed from the packer
    packed_rects = [] # rects who have been packed and must have their animation created
    loading_gif = None
    loading_func = None
    j = 0
    while True:
        ## Packer Communication
        
        # if packer is empty, refill it
        if packer.empty():
            rects_to_add = rect_library.keys()
            # don't add rects which are still onscreen to the packer, as this 
            # would cause filenames to be ambiguous ids. And be boring
            for rect_name in added_rects:
                if rect_name in rects_to_add:
                    rects_to_add.remove(rect_name)
            shuffle(rects_to_add)
        # if there are any rects have not been sent, send them    
        i = 0
        for rect_name in rects_to_add:
            if not pack_in.full():
                assert not rect_name in added_rects
                pack_in.put_nowait(rect_name)
                added_rects.append(rect_name)
                i += 1
            else: # keep whatever gifs weren't queued for next iteration 
                rects_to_add = rects_to_add[i:]
                break
        else: # all completed gifs got queued, so empty list
            rects_to_add = []
        
        # send completed gif ids to packer 
        i = 0
        for filename in completed_gifs:
            if not remove_in.full():
                remove_in.put_nowait(filename)
                i += 1
            else:
                completed_gifs = completed_gifs[i:]
                break
        else:
            completed_gifs = []
            
        # get removed rects and kill sprites
        removed_rects = []
        while not remove_out.empty():
            rect_name = remove_out.get_nowait()
            removed_rects.append(rect_name)
            added_rects.remove(rect_name)
        for rect_name in removed_rects:
            gif = active_gifs.pop(rect_name)
            gif.kill()
            active_sprites.remove(gif)
        
        ## add new sprites
        # get packed rects from packer
        while not pack_out.empty():
            rect = pack_out.get_nowait()
            packed_rects.append(rect)
            assert not rect.filename in active_gifs, rect.filename
            assert not loading_gif or not rect.filename == loading_gif.filename, rect.filename
        
        # send rects to have it's animation loaded
        i = 0
        for rect in packed_rects:
            if not rect_in.full():
                assert not rect.filename in active_gifs
                rect_in.put_nowait(rect)
                #print "putting into loader",rect.filename
                i += 1
            else:
                packed_rects = packed_rects[i:]
                break
        else:
            packed_rects = []
        
        # receive loaded animations and add them to rendering pipeline
        if not loading_gif and not gif_out.empty():
            loading_gif = gif_out.get_nowait()
            #print "getting from loader",loading_gif.filename
            loading_func = loading_gif.ready()
        # continue loading gifs
        if loading_gif:
            complete = False
            try:
                while loading_func.next():
                    j += 1
                    pass
            except StopIteration:
                complete = True
            if complete:
                j = 0
                assert not loading_gif.filename in active_gifs, loading_gif.filename
                active_gifs[loading_gif.filename] = loading_gif
                active_sprites.add(loading_gif)
                loading_gif = None
                loading_func = None
                complete = False
        
        ## Render
        screen.blit(background, (0,0))
        
        active_sprites.draw(screen)
        pygame.display.update()
        active_sprites.update(active_sprites, dt, completed_gifs)
        
        ## Framerate
        dt = clock.tick(30)
        ## IO
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                '''if event.key == pygame.K_SPACE:
                    import code
                    code.interact(local=locals())'''
                    
        # DEBUG:
        if not packer.is_alive():
            return
    
if __name__ == '__main__':
    freeze_support()
    main()