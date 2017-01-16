#!/usr/bin/env python

from mcpi.minecraft import Minecraft
from mcpi.block import * # Block and all constant block definitions
from mcpi.vec3 import Vec3

import server
import math
import text # from mcpipy scripts distribution
from sign import Sign
import time
default_delay = 0.1 # don't hog cpu

# get a list of all blocks which can be simply defined (replaced and restored completely)
import mcpi.block
basic_blocks = [getattr(mcpi.block, x) for x in dir(mcpi.block)
                if (not x.startswith('_') and x != 'Block' and (x == x.upper()))]

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
   return v.cross(Vec3(0,1,0))

class Menu():
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

   def Register_Sign(self, key, s, cb):
      self.signs.update({key: s})
      def acknowledge_response(hitBlock):
         s.spin_once() # by definition, hitBlock is this sign...
         self.cleanup()
         print cb
         return cb(key, hitBlock)
      # end while
      self.click_handler.Register(s.position, acknowledge_response)

   def build_menu(self):
      '''
      build a menu
       by default, right in front of the player
      '''

      forward_vec = Vec3(*[round(x) for x in self.mc.player.getDirection()])
      forward_vec.y = 0
      up_vec = Vec3(0,1,0)
      menu_vec = forward_vec.cross(up_vec)

      # p0 = self.mc.player.getTilePos() + \
      #       up_vec * 2 +\
      #       forward_vec * 3 + \
      p0 = self.pos + menu_vec * -int(len(self.choices)/2)
      # print p0

      if self.title: self.mc.postToChat("%s"%(self.title))
      i = 0
      for key in self.choices:
         value = self.choices[key]
         name = value['name']
         callback = value['callback']
         # print key, value
         # self.mc.postToChat("%s"%(name))
         v = p0 + menu_vec * i
         s = Sign(v, name, mc = self.mc)
         self.Register_Sign(key, s, callback)
         i += 1
      # end for
   # end def

   def cleanup(self):
      for key in self.signs:
         sign = self.signs[key]
         self.click_handler.Remove(sign.position)
         sign.destroy()


class BlockChooser():
   def __init__(self,
                flash_block = GLOWSTONE_BLOCK,
                mc=None):
      '''
      '''
      self.mc = mc
      self.flash_block = flash_block
      self.last_position = None
      self.last_block = None
      self.block_was_special = False

   def _clear_hit_queue(self):
      for hitBlock in self.mc.events.pollBlockHits():
         pass

   def get_hit_position(self):
      self._clear_hit_queue()
      position = None
      while position is None:
         for hitBlock in self.mc.events.pollBlockHits():
            position = hitBlock.pos.clone()
         # end for
         time.sleep(default_delay)
      # end while
      self.last_position = position

      self.last_block = self.mc.getBlockWithData(
                              position.x,
                              position.y,
                              position.z)

      self._flash_block()

      return self.last_position

   def _flash_block(self):
      position = self.last_position
      if self.last_block in basic_blocks:
         self.mc.setBlock(position,
                          self.flash_block)
         time.sleep(0.1)
         self.mc.setBlock(position,
                          self.last_block) # back to original
         self.block_was_special = False
      else:
         self.mc.postToChat("selected special block: %s"%(str(self.last_block)))
         self.block_was_special = True
      # end if //

   def get_block(self):
      self.get_hit_position()
      return self.last_block
