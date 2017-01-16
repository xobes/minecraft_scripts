#!/usr/bin/env python
'''

import os, sys; os.chdir(r'C:\Users\Andy\AppData\Roaming\.minecraft2\mcpipy\lego'); sys.path.insert(0,'.'); import test

'''


from mcpi.minecraft import Minecraft

import time
default_delay = 0.1 # don't hog cpu

mc = Minecraft.create()

'''
mc.player.setPos(0,3,4)
print "hello"
mc.setBlock(0,0,0,3,0)
print mc.getBlock(0,0,0)
pos = mc.player.getPos()
pos.x = pos.x - 10
print mc.player.getPitch()
print mc.player.getRotation()
print mc.player.getDirection()
'''

import sign
reload(sign)
import menu
reload(menu)
import lego_grid
reload(lego_grid)
import lego_brick
reload(lego_brick)
import lego
reload(lego)

g = lego.Game(mc = mc)
try:
   g.start()
except:
   import traceback
   print traceback.format_exc()

if __name__ == '__main__':
   while 1:
      time.sleep(0.1)