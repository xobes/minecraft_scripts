#!/usr/bin/env python

from mcpi.vec3 import Vec3
from sign import Sign

# import mcpi.block
# # get a list of all blocks which can be simply defined (replaced and restored completely)
# basic_blocks = [getattr(mcpi.block, x) for x in dir(mcpi.block)
#                 if (not x.startswith('_') and x != 'Block' and (x == x.upper()))]

def angleToMenuDirection(angle):
   # print angle
   direction = int(round((angle+360-45) % 360) / 90)
   # print direction
   if direction == 0:
      v = Vec3(-1, 0, 0)
   elif direction == 1:
      v = Vec3(0, 0, -1)
   elif direction == 2:
      v = Vec3(1, 0, 0)
   elif direction == 3:
      v = Vec3(0, 0, 1)
   return v # .cross(Vec3(0,1,0))

import time
import threading
class Menu(threading.Thread):
   def __init__(self,
                choices,
                pos,
                click_handler,
                title = None,
                mc=None):
      '''
      choices will be a dictionary of key:value pairs
      The values will be displayed to the user on signs, when the sign is hit,
      the key will be returned and the menu destroyed.
      '''
      threading.Thread.__init__(self)
      self.daemon = True

      self.mc = mc
      # if position is None:
      #    position = self.mc.player.getTilePos() + Vec3(0, 0, -1)
      #    # player_dir = mc.player.getDirection()  # not used yet... do vector stuff (vector)
      #    # mc.player.getRotation() # degrees of rotation
      # # end if
      #
      # self.position = position
      self.pos = pos
      self.click_handler = click_handler
      self.choices = choices
      self.signs = {}
      self.title = title
      self.displayed = False

   def run(self):
      while self.displayed:
         # for s in self.signs:
         #    if not self.displayed: break
         #    sign = self.signs[s]
         #    with sign.lock:
         #       sign.face_player()
         #       sign.update()
         time.sleep(0.1)

   def Register_Sign(self, key, s, cb):
      self.signs.update({key: s})
      def acknowledge_response(hitBlock):
         s.spin_once() # by definition, hitBlock is this sign...
         self.cleanup()
         return cb(key, hitBlock)
      # end while
      self.click_handler.Register(s.position, acknowledge_response)

   def build_menu(self):
      '''
      build a menu
       by default, right in front of the player
      '''

      forward_vec = angleToMenuDirection(self.mc.player.getRotation() )# Vec3(*[round(x) for x in self.mc.player.getDirection()])
      forward_vec.y = 0 # same height as player
      up_vec = Vec3(0,1,0)
      menu_vec = forward_vec.cross(up_vec)

      max_rows =  3
      ideal_cols = 3
      c = len(self.choices)
      rows = 1
      cols = min(ideal_cols, len(self.choices))
      while ((cols * rows) < c):
         if rows < max_rows:
            rows += 1
         else:
            cols += 1

      p0 = self.pos + menu_vec * -int(cols/2)

      if self.title: self.mc.postToChat("%s"%(self.title))
      i = 0 # cols
      j = 0 # rows
      for key in self.choices:
         value = self.choices[key]
         name = value['name']
         callback = value['callback']
         # print key, value
         # self.mc.postToChat("%s"%(name))
         v = p0 + menu_vec * i + (up_vec * j)
         s = Sign(v, name, mc = self.mc)
         self.Register_Sign(key, s, callback)

         # -------------------------------
         i += 1
         if (i >= cols):
            j += 1
            i = 0
      # end for
      self.displayed = True
      self.start() # start thread to keep signs facing player
   # end def

   def cleanup(self):
      if self.displayed: # don't do this twice, makes blocks...
         self.displayed = False
         for key in self.signs:
            sign = self.signs[key]
            self.click_handler.Remove(sign.position) # Note, this includes portions of the brick
            sign.destroy()
         print "all signs gone"


# class BlockChooser():
#    def __init__(self,
#                 flash_block = GLOWSTONE_BLOCK,
#                 mc=None):
#       '''
#       '''
#       self.mc = mc
#       self.flash_block = flash_block
#       self.last_position = None
#       self.last_block = None
#       self.block_was_special = False
#
#    def _clear_hit_queue(self):
#       for hitBlock in self.mc.events.pollBlockHits():
#          pass
#
#    def get_hit_position(self):
#       self._clear_hit_queue()
#       position = None
#       while position is None:
#          for hitBlock in self.mc.events.pollBlockHits():
#             position = hitBlock.pos.clone()
#          # end for
#          time.sleep(default_delay)
#       # end while
#       self.last_position = position
#
#       self.last_block = self.mc.getBlockWithData(
#                               position.x,
#                               position.y,
#                               position.z)
#
#       self._flash_block()
#
#       return self.last_position
#
#    def _flash_block(self):
#       position = self.last_position
#       if self.last_block in basic_blocks:
#          self.mc.setBlock(position,
#                           self.flash_block)
#          time.sleep(0.1)
#          self.mc.setBlock(position,
#                           self.last_block) # back to original
#          self.block_was_special = False
#       else:
#          self.mc.postToChat("selected special block: %s"%(str(self.last_block)))
#          self.block_was_special = True
#       # end if //
#
#    def get_block(self):
#       self.get_hit_position()
#       return self.last_block
