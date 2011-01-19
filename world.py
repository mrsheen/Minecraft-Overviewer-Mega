#    This file is part of the Minecraft Overviewer.
#
#    Minecraft Overviewer is free software: you can redistribute it and/or
#    modify it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or (at
#    your option) any later version.
#
#    Minecraft Overviewer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
#    Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with the Overviewer.  If not, see <http://www.gnu.org/licenses/>.

import functools
import os
import os.path
import multiprocessing
import Queue
import sys
import logging
import cPickle

import collections
import datetime
import time

import numpy

import chunk
import nbt

"""
This module has routines related to generating all the chunks for a world
and for extracting information about available worlds

"""

base36decode = functools.partial(int, base=36)
Chunk = collections.namedtuple('Chunk', 'col row timestamp path')

def get_chunk_renderset(chunkfiles):
    """Returns a set of (col, row) chunks that should be rendered. Returns
    None if all chunks should be rendered"""
    
    if not chunkfiles:
        return None
    
    
    # Get a list of the (chunks, chunky, filename) from the passed in list
    # of filenames
    chunklist = []
    for path in chunkfiles:
        if path.endswith("\n"):
            path = path[:-1]
        f = os.path.basename(path)
        if f and f.startswith("c.") and f.endswith(".dat"):
            p = f.split(".")
            chunklist.append(Chunk(base36decode(p[1]), base36decode(p[2]), 0,path))
            #chunklist.append((base36decode(p[1]), base36decode(p[2]), path))

    # No chunks found
    if len(chunklist) == 0:
        return None;
    
    # Translate to col, row coordinates
    _, _, _, _, chunklist = _convert_coords(chunklist)

    # Build a set from the col, row pairs
    inclusion_set = set()
    for col, row, timestamp, filename in chunklist:
        inclusion_set.add((col, row))
        

    return inclusion_set


def _convert_coords(chunks):
    """Takes the list of (chunkx, chunky, chunkfile) where chunkx and chunky
    are in the chunk coordinate system, and figures out the row and column in
    the image each one should be.

    returns mincol, maxcol, minrow, maxrow, chunks_translated
    chunks_translated is a list of (col, row, filename)
    """
    chunks_translated = []
    # columns are determined by the sum of the chunk coords, rows are the
    # difference
    item = chunks[0]
    mincol = maxcol = item.col + item.row
    minrow = maxrow = item.row - item.col
    for c in chunks:
        col = c.col + c.row
        mincol = min(mincol, col)
        maxcol = max(maxcol, col)
        row = c.row - c.col
        minrow = min(minrow, row)
        maxrow = max(maxrow, row)
        chunks_translated.append(Chunk(col, row, c.timestamp, c.path))

    return mincol, maxcol, minrow, maxrow, chunks_translated


def base36encode(number, alphabet='0123456789abcdefghijklmnopqrstuvwxyz'):
    '''
    Convert an integer to a base36 string.
    '''
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')
    
    newn = abs(number)
    
    # Special case for zero
    if number == 0:
        return '0'
    
    base36 = ''
    while newn != 0:
        newn, i = divmod(newn, len(alphabet))
        base36 = alphabet[i] + base36
    
    if number < 0:
        return "-" + base36
    return base36

class WorldRenderer(object):
    """Renders a world's worth of chunks.
    worlddir is the path to the minecraft world
    cachedir is the path to a directory that should hold the resulting images.
    It may be the same as worlddir (which used to be the default).
    
    If chunklist is given, it is assumed to be an iterator over paths to chunk
    files to update. If it includes a trailing newline, it is stripped, so you
    can pass in file handles just fine.
    """

    def __init__(self, worlddir, cachedir, allbranches=False):
        self.worlddir = worlddir
        self.allbranches = allbranches
        if not os.path.exists(cachedir):
            os.mkdir(cachedir)
        self.cachedir = os.path.join(cachedir, "unlit") #!TODO!Replace with logic for allbranches
        self.chunkset = None #!TODO!remove references to this
        
        self.lighting = False

        #  stores Points Of Interest to be mapped with markers
        #  a list of dictionaries, see below for an example
        self.POI = []

        
        
        # Load the full world queue from disk, or generate if its the first time
        self.pickleFile = os.path.join(self.cachedir,"worldqueue.dat")
        if os.path.exists(self.pickleFile):
            with open(self.pickleFile,"rb") as p:
                self.worldqueue = cPickle.load(p)
        else:
            # some defaults
            self.worldqueue = self._find_chunkfiles()
        
        
        # Translate chunks to our diagonal coordinate system
        mincol, maxcol, minrow, maxrow, self.worldqueue = _convert_coords(self.worldqueue)
        
        self.mincol = mincol
        self.maxcol = maxcol
        self.minrow = minrow
        self.maxrow = maxrow
        
        #Sort worldqueue by timestamp
        self.worldqueue = sorted(self.worldqueue, key=lambda chunk: chunk.timestamp)
        #print "worldqueue size: " + str(len(self.worldqueue))
        
        
        # if it exists, open overviewer.dat, and read in the data structure
        # info self.persistentData.  This dictionary can hold any information
        # that may be needed between runs.
        # Currently only holds into about POIs (more more details, see quadtree)
        self.pickleFile = os.path.join(self.cachedir,"overviewer.dat")
        if os.path.exists(self.pickleFile):
            with open(self.pickleFile,"rb") as p:
                self.persistentData = cPickle.load(p)
        else:
            # some defaults
            self.persistentData = dict(POI=[])

        
                
    def get_chunk_path(self, chunkX, chunkY):
        """Returns the path to the chunk file at (chunkX, chunkY), if
        it exists."""
        
        chunkFile = "%s/%s/c.%s.%s.dat" % (base36encode(chunkX % 64),
                                           base36encode(chunkY % 64),
                                           base36encode(chunkX),
                                           base36encode(chunkY))
        
        return os.path.join(self.worlddir, chunkFile)
    
    def findTrueSpawn(self):
        """Adds the true spawn location to self.POI.  The spawn Y coordinate
        is almost always the default of 64.  Find the first air block above
        that point for the true spawn location"""

        ## read spawn info from level.dat
        data = nbt.load(os.path.join(self.worlddir, "level.dat"))[1]
        spawnX = data['Data']['SpawnX']
        spawnY = data['Data']['SpawnY']
        spawnZ = data['Data']['SpawnZ']
   
        ## The chunk that holds the spawn location 
        chunkX = spawnX/16
        chunkY = spawnZ/16

        ## The filename of this chunk
        chunkFile = self.get_chunk_path(chunkX, chunkY)

        data=nbt.load(chunkFile)[1]
        level = data['Level']
        blockArray = numpy.frombuffer(level['Blocks'], dtype=numpy.uint8).reshape((16,16,128))

        ## The block for spawn *within* the chunk
        inChunkX = spawnX - (chunkX*16)
        inChunkZ = spawnZ - (chunkY*16)

        ## find the first air block
        while (blockArray[inChunkX, inChunkZ, spawnY] != 0):
            spawnY += 1


        self.POI.append( dict(x=spawnX, y=spawnY, z=spawnZ, 
                msg="Spawn", type="spawn", chunk=(inChunkX,inChunkZ)))

    def renderChunkset(self, procs, initial=False, chunkset=None):
        """Starts the initial render. This returns when it is finished"""
        self.chunkset = chunkset
            
        # Make the destination dir
        if not os.path.exists(self.cachedir):
            os.mkdir(self.cachedir)
        
        if initial:
            chunk.saveUnderConstructionImage(self.cachedir)

        self.chunkmap = self._render_chunks_async(self.worldqueue, procs, initial, True)
        

    def getQueueTop(self, number=1000):
        #!TODO!update timestamps here? use a deque?
        
        # Build a set from the col, row pairs
        inclusion_set = set()
        for i in range(number):
            chunk = self.worldqueue.pop(0)
            inclusion_set.add((chunk.col, chunk.row))
            #print "worldqueue length: " + str(len(self.worldqueue))
            self.worldqueue.append(Chunk(chunk.col,chunk.row, time.time(), chunk.path))
            #print "worldqueue length: " + str(len(self.worldqueue))
            #print "chunk time difference: " + str(datetime.timedelta(seconds=(int(time.time()) - chunk.timestamp))) + " " + str(chunk.col) + "," + str(chunk.row) + " " + chunk.path
            del chunk
            
        return inclusion_set

    def _find_chunkfiles(self):
        """Returns a deque(list) of all the chunk file locations, and the file they
        correspond to.
        
        Returns a list of (chunkx, chunky, filename) where chunkx and chunky are
        given in chunk coordinates. Use convert_coords() to turn the resulting list
        into an oblique coordinate system."""
        
        all_chunks = []

        for dirpath, dirnames, filenames in os.walk(self.worlddir):
            if not dirnames and filenames and "DIM-1" not in dirpath:
                for f in filenames:
                    if f.startswith("c.") and f.endswith(".dat"):
                        p = f.split(".")
                        all_chunks.append(Chunk(base36decode(p[1]), base36decode(p[2]), int(os.path.getmtime(os.path.join(dirpath, f))),os.path.join(dirpath, f)))

        if not all_chunks:
            logging.error("Error: No chunks found!")
            sys.exit(1)
        return all_chunks
           

    def _render_chunks_async(self, chunks, processes, initial=False, force=False):
        """Starts up a process pool and renders all the chunks asynchronously.

        chunks is a list of (col, row, chunkfile)

        Returns a dictionary mapping (col, row) to the file where that
        chunk is rendered as an image
        """
        # The set of chunks to render, or None for all of them. The logic is
        # slightly more compliated than it should seem, since we still need to
        # build the results dict out of all chunks, even if they're not being
        # rendered.
        
        if self.chunkset:
            logging.info("Inclusion set found, rendering only a subset of map")
            logging.info("Total chunks to render: {0}".format(len(self.chunkset)))

        
        
        results = {}
        manager = multiprocessing.Manager()
        q = manager.Queue()

        if processes == 1:
            # Skip the multiprocessing stuff
            logging.debug("Rendering chunks synchronously since you requested 1 process")
            for i, (col, row, timestamp, chunkfile) in enumerate(chunks):
                if self.chunkset and (col, row) not in self.chunkset:
                    # Skip rendering, just find where the existing image is
                    _, imgpath = chunk.ChunkRenderer(chunkfile,
                            self.cachedir, self, q).find_oldimage()
                    if imgpath:
                        results[(col, row)] = imgpath
                        continue
                
                if initial:
                    # Skip rendering, just find where the existing image is
                    _, imgpath = chunk.ChunkRenderer(chunkfile,
                            self.cachedir, self, q).find_oldimage()
                    if imgpath:
                        results[(col, row)] = imgpath
                        continue

                result = chunk.render_and_save(chunkfile, self.cachedir, self, initial=initial, queue=q, force=force)
                results[(col, row)] = result
                if i > 0:
                    try:
                        item = q.get(block=False)
                        if item[0] == "newpoi":
                            self.POI.append(item[1])
                        elif item[0] == "removePOI":
                            self.persistentData['POI'] = filter(lambda x: x['chunk'] != item[1], self.persistentData['POI'])
                    except Queue.Empty:
                        pass
                    if 1000 % i == 0 or i % 1000 == 0:
                        logging.info("{0}/{1} chunks rendered".format(i, len(chunks)))
        else:
            logging.debug("Rendering chunks in {0} processes".format(processes))
            pool = multiprocessing.Pool(processes=processes)
            asyncresults = []
            for col, row, timestamp, chunkfile in chunks:
                if self.chunkset and (col, row) not in self.chunkset:
                    # Skip rendering, just find where the existing image is
                    _, imgpath = chunk.ChunkRenderer(chunkfile,
                            self.cachedir, self, q).find_oldimage()
                    if imgpath:
                        results[(col, row)] = imgpath
                        continue
                
                if initial:
                    # Skip rendering, just find where the existing image is
                    _, imgpath = chunk.ChunkRenderer(chunkfile,
                            self.cachedir, self, q).find_oldimage()
                    if imgpath:
                        results[(col, row)] = imgpath
                        continue

                result = pool.apply_async(chunk.render_and_save,
                        args=(chunkfile,self.cachedir,self),
                        kwds=dict(initial=initial, queue=q))
                asyncresults.append((col, row, result))

            pool.close()

            for i, (col, row, result) in enumerate(asyncresults):
                results[(col, row)] = result.get()
                try:
                    item = q.get(block=False)
                    if item[0] == "newpoi":
                        self.POI.append(item[1])
                    elif item[0] == "removePOI":
                        self.persistentData['POI'] = filter(lambda x: x['chunk'] != item[1], self.persistentData['POI'])

                except Queue.Empty:
                    pass
                if i > 0:
                    if 1000 % i == 0 or i % 1000 == 0:
                        logging.info("{0}/{1} chunks rendered".format(i, len(asyncresults)))

            pool.join()
        logging.info("Done!")

        return results

        
def get_save_dir():
    """Returns the path to the local saves directory
      * On Windows, at %APPDATA%/.minecraft/saves/
      * On Darwin, at $HOME/Library/Application Support/minecraft/saves/
      * at $HOME/.minecraft/saves/

    """
    
    savepaths = []
    if "APPDATA" in os.environ:
        savepaths += [os.path.join(os.environ['APPDATA'], ".minecraft", "saves")]
    if "HOME" in os.environ:
        savepaths += [os.path.join(os.environ['HOME'], "Library",
                "Application Support", "minecraft", "saves")]
        savepaths += [os.path.join(os.environ['HOME'], ".minecraft", "saves")]

    for path in savepaths:
        if os.path.exists(path):
            return path

def get_worlds():
    "Returns {world # : level.dat information}"
    ret = {}
    save_dir = get_save_dir()

    # No dirs found - most likely not running from inside minecraft-dir
    if save_dir is None:
        return None

    for dir in os.listdir(save_dir):
        if dir.startswith("World") and len(dir) == 6:
            world_n = int(dir[-1])
            info = nbt.load(os.path.join(save_dir, dir, "level.dat"))[1]
            info['Data']['path'] = os.path.join(save_dir, dir)
            ret[world_n] = info['Data']

    return ret
