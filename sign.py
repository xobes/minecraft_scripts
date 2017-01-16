from mcpi.block import * # Block and all constant block definitions
import time
from mcpi.vec3 import Vec3

class Sign():
   def __init__(self,
                position,
                message,
                mc,
                rotation = 0,
               ):
      self.mc = mc
      self.position = Vec3(*[int(x) for x in tuple(position)])
      self.rotation = rotation
      self.face_player()
      self.update(message)

   def destroy(self):
      self.mc.setBlock(self.position, AIR)

   def rotate(self, rotation = 'CW'):
      if rotation == 'CCW':
         self.rotation -= 1
      elif rotation == 'CW':
         self.rotation += 1
      else:
         self.rotation = rotation
      # end if
      if self.rotation < 0:
         self.rotation = 15 # max
      if self.rotation > 15:
         self.rotation = 0 # min
      self.update()

   def face_player(self):
      x = 360/16
      self.rotation = int(round((self.mc.player.getRotation() + 180) % 360) / x)

   def spin_once(self):
      for i in range(16):
         self.rotate()
         time.sleep(0.02)

   def update(self, message = None):
      self.rotation = self.rotation % 16 # keep in bounds
      message_changed = False
      if message is not None:
         self.message = message
         message_changed = True
      # end if

      extra_data = "{id:\"Sign\""
      lines = self.message.splitlines()
      for i in range(min(4,len(lines))):
         line = lines[i]
         # print line
         extra_data += ",Text%d:\"%s\"" % (i+1, line)
      # end for
      extra_data += "}"

      if message_changed:
         r = self.rotation
         self.rotate() # stimulate a redraw
         self.rotation = r
      # end if
      self.mc.conn.send("world.setBlock",
                        self.position.x, self.position.y, self.position.z,
                        63, self.rotation,
                        extra_data
                       )

if __name__ == '__main__':
   from mc import *
   mc = Minecraft()

   # mc.conn.send("world.setBlocks",0,0,0,5,5,5,63,1,"{id:\"Sign\",Text1:\"My signs 5\"}")
   # mc.conn.send("world.setBlocks",0,0,0,1,1,1,63,1,"{id:\"Sign\",Text1:\"My sign 1\"}")
   # mc.conn.send("world.setBlock",0,0,0,63,1,"{id:\"Sign\",Text1:\"My single sign\"}")

   # place a sign
   s = Sign(0,0,0, 'ANDY WAS HERE!', mc =  mc)


