#!/usr/bin/python
from mcpi.minecraft import Minecraft
from mcpi.block import *
from mcpi.vec3 import Vec3
from mcpi.util import *

import pyfiglet

mc = None

def main(text,
         block_id,
         offset_x = 0,
         offset_y = 0,
         offset_z = 0,
         direction = "xy",
         font = 'xhelv',
        ):
   offset_x = int(offset_x)
   offset_y = int(offset_y)
   offset_z = int(offset_z)
   if isinstance(block_id, str):
      block_id = int(block_id)
   
   global mc
   if mc is None:
      mc = Minecraft.create()

   pf = pyfiglet.Figlet(font)
   
   p = mc.player.getTilePos()
   x = p.x
   y = p.y
   z = p.z
   x += offset_x
   y += offset_y
   z += offset_z

   figlet = pf.renderText(text)
   ta = []
   for row in figlet.splitlines():
      ta.append([])
      for c in row:
         if c == " ":
            this_block = None
         else:
            this_block = block_id
         ta[-1].append(this_block)
      # end for
   # end for

   layer = ta
   
   # rows in layers are representing x
   k = 0
   rows = len(layer)
   for i in xrange(0, rows, 1):
      row = layer[i]
      cols = len(row)
      for j in xrange(0, cols, 1):
         block = row[j]
         if block is not None:
            mc.setBlock(x+j, y-i, z+k, block);
      # end for
   # end for
# def

if __name__ == "__main__":
   import sys
   main(*sys.argv[1:])
