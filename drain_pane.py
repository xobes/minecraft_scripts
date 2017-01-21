#
# Code under the MIT license by Alexander Pruss
#


from mc import *
import time
import os

mc = Minecraft()

bridge = []

done = False
r = 50
n = 100
SPONGE = Block(19,0)

pos = mc.player.getTilePos()

while not done:
   pos.y -= 1
   print "draining... %s"%(pos.y)
   found = 0
   for i in range(-r,r+1): # radius
      for j in range(-r,r+1):
         p = Vec3(i, 0, j) + pos
         belowBlock = mc.getBlock(p)
         if not( abs(j) == r or abs(i) == r): # edges
            if belowBlock in [SPONGE.id,
                              GLASS.id,
                             ]:
               mc.setBlock(p, AIR) # erase smaller grids within...
         if belowBlock in [WATER_FLOWING.id,
                           WATER_STATIONARY.id,
                           AIR.id,
                          ]:
            found += 1

            if abs(j) == r or abs(i) == r:
               mc.setBlock(p, GLASS)
            else:
               if belowBlock != AIR.id:
                  bridge.append(p)
                  mc.setBlock(p, SPONGE)

            if len(bridge) > n:
               firstPos = bridge.pop(0)
               if not firstPos in bridge:
                  mc.setBlock(firstPos, AIR)
      time.sleep(0.05)

   while len(bridge):
      firstPos = bridge.pop(0)
      if not firstPos in bridge:
         mc.setBlock(firstPos, AIR)

   done = (found == 0)
   time.sleep(0.05)
print "done"
