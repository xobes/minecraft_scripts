#!/usr/bin/env python

from mcpi.minecraft import Minecraft
from mcpi.block import * # Block and all constant block definitions
from mcpi.vec3 import Vec3

import server
import math
import text # from mcpipy scripts distribution
from sign import Sign
from menu import Menu, BlockChooser
from collections import OrderedDict
import time
default_delay = 0.1 # don't hog cpu
import threading
Lock = threading.Lock

LEGO_WIDTH = 3
LEGO_HEIGHT = 3

from click_handler import *

def angleToBrickDirection(angle):
   # print angle
   direction = int(round((angle+360-45) % 360) / 90)
   # print direction
   if direction == 0:
      return Vec3(-1, 0, 0)
   elif direction == 1:
      return Vec3(0, 0, -1)
   elif direction == 2:
      return Vec3(1, 0, 0)
   elif direction == 3:
      return Vec3(0, 0, 1)

class LegoGrid():
   def __init__(self,
                origin,
                brick_width = LEGO_WIDTH,
                brick_height = LEGO_HEIGHT,
                mc = None,
               ):
      # if origin is None:
      #    origin = Menu.BlockChooser().get_hit_position()
      # # end if
      self.origin = origin.clone()
      self.brick_width = brick_width
      self.brick_height = brick_height
      self.plate_height = max(1, int(self.brick_height/3))
      print "Lego Grid Created at origin %d,%d,%d"%(self.origin.x,
                                                    self.origin.y,
                                                    self.origin.z,
                                                    )
   def align_to_grid(self, position):
      print "align_to_grid not implemented"
      return position

class LegoBrick():
   def __init__(self,
                position,
                length=1,
                width=1,
                rounded_corners=False,
                height=LEGO_HEIGHT,  # brick vs plate
                block=None,
                grid=None,
                up_vec = None,
                length_vec = None,
                mc=None,
                click_handler = None,
                on_destroy = None
               ):
      '''
      '''
      self.mc = mc
      self.origin = position.clone() # TODO: check against a LegoGrid
      self.active_blocks = set() # used to activate control menu
      self.my_blocks = set() # keep track of all our parts

      self.length = length
      self.width = width
      self.height = height
      self.deleted = False

      if grid is None:
         grid = LegoGrid(position)
      self.grid = grid
      self.click_handler = click_handler

      if up_vec is None:
         up_vec = Vec3(0, 1, 0);

      if length_vec is None:
         length_vec = angleToBrickDirection(self.mc.player.getRotation())

      self.up_vec = up_vec
      self.length_vec = length_vec

      if block is None:
         self.ask_block() # what material to use?
      else:
         self.block = block
      # end if

      self.menu = None

      self.draw()
   # end def __init__

   def setMenu(self, new_menu):
      if self.menu: # have a menu already
         self.menu.cleanup() # get rid of that menu
         self.draw()
      self.menu = new_menu
      if self.menu is not None:
         self.menu.build_menu()
      else:
         self.draw()

   def cancel_menu(self, *args):
      self.setMenu(None)

   def pop_menu(self, hitBlock):
      self.setMenu( Menu(choices = OrderedDict([
               ('move' ,   {'name': 'Move Brick',      'callback': self.ask_position            }),
               ('length',  {'name': 'Change Length',   'callback': self.ask_dim('length')       }),
               ('width',   {'name': 'Change Width',    'callback': self.ask_dim('width')        }),
               ('height',  {'name': 'Change Height',   'callback': self.ask_dim('height',[1,3]) }),
               # ('corners', {'name': 'Toggle Corners',  'callback': self._not_impl_menu          }),
               ('block',   {'name': 'Change Material', 'callback': self.ask_block               }),
               ('rotate' , {'name': 'Rotate Brick',    'callback': self.ask_direction           }),
               ('delete' , {'name': 'Delete Brick',    'callback': self.ask_destroy             }),
               ('cancel' , {'name': 'Cancel',          'callback': self.cancel_menu             }),
            ]),
            title = 'Brick Menu - Choose what to change',
            pos = hitBlock.pos,
            mc = self.mc,
            click_handler = self.click_handler,
         ))
   # end def

   def ask_destroy(self, value, hitBlock):
      self.destroy()
      self.setMenu(None)

   def ask_position(self, value, hitBlock):
      self.setMenu(None)

      @PositionHandlerDecorator
      def get_pos(vec):
         self.origin = vec.clone()
         self.draw()

      self.mc.postToChat("Choose a new stud")
      self.click_handler.Register_Next_Click_Handler(get_pos)

      self.hide()
   # end def

   def ask_block(self, value, hitBlock):
      self.setMenu(None)

      @BlockHandlerDecorator(self.mc)
      def get_block(pb):
         if pb.block in BASIC_BLOCKS:
            self.block = pb.block
         self.draw()

      self.mc.postToChat("Choose a block type to use")
      self.click_handler.Register_Next_Click_Handler(get_block)

      self.hide()
   # end def

   def ask_direction(self, value, hitBlock):
      self.setMenu(None)

      def set_rotation(hitBlock):
         self.length_vec = angleToBrickDirection(self.mc.player.getRotation())
         self.draw()

      self.mc.postToChat("Face a new direction and hit something")
      self.click_handler.Register_Next_Click_Handler(set_rotation)

      self.hide()
   # end def

   def ask_dim(self, attr, opts=None):
      if opts is None:
         opts=[1,2,4,6,8,10,12,16]
      def selected_dim(value, hitBlock):
         self.setMenu(None)
         print "Select the new length"
         def set_dim(x):
            def inner(value, hitBlock):
               setattr(self, attr, x)
               self.draw()
            return inner
         self.setMenu( Menu(choices=OrderedDict(
               [(i,  {'name': str(i), 'callback': set_dim(i) }) for i in
                  opts
                ]
            ),
            title = 'Choose New %s'%(attr),
            pos = hitBlock.pos,
            mc = self.mc,
            click_handler = self.click_handler,
         ))
      # end def
      return selected_dim
   # end def

   def draw(self):
      '''
      we don't know what's different this time around, but we may have grown or shrunk
      '''
      if self.deleted: return
      current_geometry = [x for x in self.my_blocks]
      self.my_blocks = set()

      # self.origin
      block_length = self.length * self.grid.brick_width
      block_width = self.width * self.grid.brick_width
      block_height = self.height * self.grid.brick_height/3 # TODO: use grid constant... self.height is not used...
      # print block_length, block_width, block_height

      # a brick at origin has self.origin which is stud-aligned position
      # the extents of the block (seen from above):
      '''
            X = oorigin

            +----+    ---> length_vec
            |X  o|  w
            +----+
               l

            (l) block_length = length * grid.brick_width
            (w) block_width  = width * grid.brick_width

      '''

      length_vec = self.length_vec
      up_vec = self.up_vec
      width_vec = length_vec.cross(up_vec)

      half_block_width = int(self.grid.brick_width / 2)
      p0 = self.origin + \
           (length_vec * -half_block_width) + \
           (width_vec * -half_block_width)

      exclude_volume = set()
      wall_thickness = 1
      for dl in range(wall_thickness,block_length-wall_thickness):
         for dw in range(wall_thickness,block_width-wall_thickness):
            for dh in range(block_height-wall_thickness):
               pixel_pos = p0 + (length_vec * dl) + \
                           (up_vec * dh) + \
                           (width_vec * dw)
               exclude_volume.add(pixel_pos)
            # end for // h
         # end for // w
      # end for // l

      for dl in range(block_length):
         for dw in range(block_width):
            for dh in range(block_height):
               pixel_pos = p0 + (length_vec * dl) + \
                           (up_vec * dh) + \
                           (width_vec * dw)
               if pixel_pos not in exclude_volume:
                  self.my_blocks.add(pixel_pos)
                  self._Register_Active_Block(pixel_pos)
               # end if
            # end for // h
         # end for // w
      # end for // l

      # draw studs
      # stud_radius =
      stud_height = 1
      s1= self.origin + \
           (up_vec * block_height)
      s0 = self.origin
      for l in range(self.length):
         dl = l * self.grid.brick_width
         for w in range(self.width):
            dw = w * self.grid.brick_width
            # add studs
            for dh in range(stud_height):
               pixel_pos = s1 + (length_vec * dl) + \
                                (up_vec * dh) + \
                                (width_vec * dw)
               self.my_blocks.add(pixel_pos)
            # end for // h

            dh = 0
            # make bottom stud holes
            pixel_pos = s0 + (length_vec * dl) + \
                             (up_vec * dh) + \
                             (width_vec * dw)
            self.my_blocks.discard(pixel_pos)
         # end for // w
      # end for // l

      erase = set(current_geometry).difference(self.my_blocks)
      for e in erase:
         # print 'erasing %s'%(e)
         self.mc.setBlock(e, AIR)
         self._Remove_Active_Block(e)
      for p in self.my_blocks:
         # print 'drawing %s' % (p)
         self.mc.setBlock(p, self.block)

   def _Remove_Active_Block(self, vec):
      self.click_handler.Remove(vec)
      self.active_blocks.discard(vec)

   def _Register_Active_Block(self, vec):
      self.click_handler.Register(vec, self.pop_menu)
      self.active_blocks.add(vec) # all but the studs

   def hide(self):
      done = False
      print self.my_blocks
      while not done:
         try:
            b = self.my_blocks.pop()
            try:
               self.mc.setBlock(b, AIR)
               self._Remove_Active_Block(b)
            except: pass
         except:
            done = True

   def destroy(self):
      self.hide()
      self.deleted = True
      try:
         self.on_destroy(self)
      except:
         pass
      # end try
   # end def

