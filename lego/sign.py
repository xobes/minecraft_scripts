from mcpi.block import * # Block and all constant block definitions
from mcpi.vec3 import Vec3
import time
import threading

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
      self.lock = threading.Lock()
      try:
         self.original_block = mc.getBlockWithData(self.position)
      except:
         self.original_block = AIR
      self.deleted = False

      self.update(message)

   def destroy(self):
      self.deleted = True
      self.mc.setBlock(Vec3(*tuple(self.position)),
                       Block(*tuple(self.original_block)))

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
      try:
         r = self.mc.player.getRotation()
         x = 360/16
         self.rotation = int(round((r + 180) % 360) / x)
      except ValueError:
         pass
      # end try

   def spin_once(self):
      with self.lock:
         for i in range(16):
            self.rotate()
            time.sleep(0.02)

   def update(self, message = None):
      if not self.deleted:
         self.rotation = self.rotation % 16 # keep in bounds
         message_changed = False
         if message is not None:
            self.message = message
            message_changed = True
         # end if

         extra_data = "{id:\"Sign\""
         lines = self.message.splitlines()

         # top of signs is hidden often, shift down if we have the room
         if len(lines) < 4: lines.insert(0,'')

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


