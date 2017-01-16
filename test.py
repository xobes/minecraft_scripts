#!/usr/bin/env python

from mcpi.minecraft import Minecraft
from mcpi.block import * # Block and all constant block definitions
from mcpi.vec3 import Vec3

import server
import math
import text # from mcpipy scripts distribution
from sign import Sign
from menu import Menu, BlockChooser
import time
default_delay = 0.1 # don't hog cpu

mc = Minecraft.create(server.address)

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
import menu
reload(sign)
reload(menu)

import lego
reload(lego)
g = lego.Game(mc = mc)
g.run()