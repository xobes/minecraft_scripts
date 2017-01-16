#!/usr/bin/python
from mcpi.minecraft import Minecraft
from mcpi.block import *
from mcpi.vec3 import Vec3
from mcpi.util import *

import skyscraper_design

mc = None

def Build_From_Layers(layers,
                      x = None,
                      y = None,
                      z = None,
                      dx = 0,
                      dy = 0,
                      dz = 0,
                     ):
   global mc
   if mc is None:
      mc = Minecraft.create()
   '''
   Example:
      layers = [
         # 0 +z ---->
         [[1,1,1,1], # 0  ^  +y
          [1,0,0,1], #    !   |
          [1,0,0,1], #    !   |
          [1,1,0,1]],#   +x  v
         [[1,1,1,1],
          [1,0,0,1],
          [1,0,0,1],
          [1,1,0,1]],
         [[1,1,1,1],
          [1,1,1,1],
          [1,1,1,1],
          [1,1,1,1]],
          
      ]
   '''
   p = mc.player.getTilePos()
   if x is None: x = p.x
   if y is None: y = p.y
   if z is None: z = p.z

   j = 0;
   for layer in layers:
      # rows in layers are representing x
      rows = len(layer)
      for i in xrange(0, rows, 1):
         #print "%s/%s"%(dx,rows)
         row = layer[i]
         cols = len(row)
         for k in xrange(0, cols, 1):
            #print "   %s/%s"%(dz,cols)
            block_id = row[k]
            #print "(%s, %s, %s, %s)"%(x+dx+i, y+dy+j, z+dz+k, block_id)
            if block_id is not None:
               mc.setBlock(x+dx-i, y+dy+j, z+dz+k, block_id);
         # end for
      # end for
      j += 1
   # end for
# def

def Build_Skyscraper(num_floors = 5,
                     building_material = 42,
                     flooring_material = 1,
                     num_windows = 4,
                    ):
   global mc
   if mc is None:
      mc = Minecraft.create()
   if isinstance(building_material, str):
      building_material = int(building_material)
   if isinstance(flooring_material, str):
      flooring_material = int(flooring_material)
   if isinstance(num_windows, str):
      num_windows = int(num_windows)
   building = skyscraper_design.define_building(
      num_floors = int(num_floors),
      building_material = building_material,
      flooring_material = flooring_material,
      num_windows = num_windows,
   )
   size = skyscraper_design.max_size_x(building[0])
   Build_From_Layers(building,
                     dx=+size, # standing in doorway
                     dy=-1,
                     dz=-int(size/2))

if __name__ == "__main__":
   import sys
   Build_Skyscraper(*sys.argv[1:])
