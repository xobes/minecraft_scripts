#!/usr/bin/env python

from click_handler import *
from menu import Menu
from lego_grid import LegoGrid
from collections import OrderedDict

EDIT_BLOCK_TYPE = GLOWSTONE_BLOCK

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

class LegoBrick():
   def __init__(self,
                position,
                length=1,
                width=1,
                rounded_corners=False,
                has_studs = True,
                height=3,  # brick (3) vs plate (1)
                shape = None,
                shape_studs = None,
                block=None,
                grid=None,
                up_vec = None,
                length_vec = None,
                mc=None,
                click_handler = None,
                # on_destroy = None
               ):
      '''
      '''
      self.mc = mc
      # self.on_destroy = on_destroy
      self.origin = position.clone() # TODO: check against a LegoGrid
      self.active_blocks = set() # used to activate control menu
      self.my_blocks = set() # keep track of all our parts

      self.length = length
      self.width = width
      self.height = height
      self.deleted = False

      self.radius = 0 # rounded_corners should be radius... 1x round vs 2x round, etc.
      self.has_studs = has_studs
      self.shape = set()
      self.shape_studs = set()
      self.has_custom_shape = False

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
         self.block = Block(*tuple(block))
      # end if

      self.menu = None

      self.edit_mode = False
      self._original_block = Block(*tuple(block)) # copy, not reference
      print self.block, self._original_block

      if shape is None and shape_studs is None:
         self.rebuild_shape()
      else:
         # reconstitute a saved shape
         self.has_custom_shape = 1
         self.shape = set([Vec3(*x) for x in shape])
         self.shape_studs = set([Vec3(*x) for x in shape_studs])
      self.draw()
   # end def __init__

   def clone(self, position = None):
      if position is None:
         position = self.origin
      # end if
      if self.has_custom_shape:
         shape = self.shape
         shape_studs = self.shape_studs
      else:
         shape, shape_studs = None, None
      b = LegoBrick(
                position,
                length=self.length,
                width=self.width,
                # rounded_corners=self.rounded_corners,
                has_studs = self.has_studs,
                height=self.height,
                shape= shape,
                shape_studs = shape_studs,
                block=self.block,
                grid=self.grid,
                up_vec = self.up_vec,
                length_vec = self.length_vec,
                mc=self.mc,
                click_handler = self.click_handler,
                # on_destroy = self.on_destroy,
      )
      self.grid.add_brick(b)
      return b

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

   def pop_edit_menu(self, key, hitBlock):
      '''
      add blocks
      remove blocks
      save
      cancel

      reset shape
      '''
      self.setMenu(None) # same as all other sub menus, destroy main object menu

      def change_shape(hitBlock):
         vec = hitBlock.pos
         if self.edit_mode == 'add':
            # every block hit becomes part of the shape
            # whole block brick becomes glowstone
            self.add_block_to_shape(vec)
         elif self.edit_mode == 'remove':
            # when a block is selected with the remove tool/mode, make into air and remove from shape
            self.remove_block_from_shape(vec)
         # end if
         self.draw()

      @PositionHandlerDecorator
      def place_menu(vec):
         # store original shape in case we cancel
         self._original_shape = set([x for x in self.shape])
         self._original_shape_studs = set([x for x in self.shape_studs])
         # while in edit mode, the main menu is disabled, must deal with this menu until it is cancelled

         for b in [x for x in self.active_blocks]:
            self._Remove_Active_Block(b)

         # every block hit turns to glowstone (redraw after each block hit)
         self._original_block = Block(*tuple(self.block))
         self.block = Block(*tuple(EDIT_BLOCK_TYPE))
         print self.block, self._original_block

         def close_edit_menu(key, hitBlock):
            print "close edit menu"
            self.click_handler.Reset_Default_Handler()
            self.block = Block(*tuple(self._original_block))
            print self.block, self._original_block
            if key == 'save':
               pass # keep shape as-is
            elif key == 'cancel':
               self.shape = set([x for x in self._original_shape])
               self.shape_studs = set([x for x in self._original_shape_studs])

            self.edit_mode = False
            self.draw()
            self.setMenu(None)

         def set_hit_mode(key, hitBlock):
            if key == 'add':
               print "Every block hit will be ADDED to the shape."
               self.edit_mode = 'add'
            elif key == 'remove':
               print "Every block hit will be REMOVED from the shape."
               self.edit_mode = 'remove'

         # self.edit_mode = True (glowstone, store original block type)
         # set hit mode to add blocks
         set_hit_mode('add',None)
         self.click_handler.Register_Default_Handler(change_shape)

         self.draw() # redisplay the brick

         choices = OrderedDict([
            ('add' ,   {'name': 'Add Bricks\nto Shape',      'callback': set_hit_mode    }),
            ('remove', {'name': 'Remove Bricks\nfrom Shape', 'callback': set_hit_mode    }),
            ('save',   {'name': 'Save',                      'callback': close_edit_menu }),
            ('cancel', {'name': 'Cancel',                    'callback': close_edit_menu }),
         ])
         self.setMenu( Menu(choices = choices,
               title = 'Brick Menu - Choose what to change',
               pos = vec, # TODO: given player pos, direction, and hit pos... given hit face... sign...
               mc = self.mc,
               persistent = True,
               click_handler = self.click_handler,
            ))
      # TODO:
      # print "register next click handler to place the menu at that time..."
      # print "menu can be anywhere, should *not* be in the block area..."
      # print "if blocks selected with the add block are part of something else, like this menu... or another brick..."
      self.mc.postToChat("Choose where to place your Shape Edit menu.")
      self.click_handler.Register_Next_Click_Handler(place_menu)

   def pop_menu(self, hitBlock):
      if self.edit_mode == False:
         choices = OrderedDict([
            ('move' ,   {'name': 'Move Brick',      'callback': self.ask_position            }),
            ('rotate' , {'name': 'Rotate Brick',    'callback': self.ask_direction           }),
            ('block',   {'name': 'Change Material', 'callback': self.ask_block               }),
            ('shape',   {'name': 'Edit Shape',      'callback': self.pop_edit_menu           }),
            ('studs',   {'name': 'Toggle Studs',    'callback': self.toggle_studs            }),
            ('length',  {'name': 'Change Length',   'callback': self.ask_dim('length')       }),
            ('width',   {'name': 'Change Width',    'callback': self.ask_dim('width')        }),
            ('height',  {'name': 'Change Height',   'callback': self.ask_dim('height',[1,3]) }),
            ('delete' , {'name': 'Delete Brick',    'callback': self.ask_destroy             }),
            ('cancel' , {'name': 'Cancel',          'callback': self.cancel_menu             }),
            ('clone',   {'name': 'Clone Brick',     'callback': self.place_clone             }),
            # copy
            # paste (if copied)
         ])
         if self.has_custom_shape:
            # TODO: perhaps a shape edit menu (edit shape) is warranted?
            for key in ['length','width','height','studs']:
               choices[key]['name'] += '\nDISABLED\nCustom Shape'
               choices[key]['callback'] = self.cancel_menu
         # end if
         self.setMenu( Menu(choices = choices,
               title = 'Brick Menu - Choose what to change',
               pos = hitBlock.pos,
               mc = self.mc,
               click_handler = self.click_handler,
            ))
      else:
         print "Unable to pop main object menu while Edit Shape menu is in use."
      # end if
   # end def

   def toggle_studs(self, *args):
      self.has_studs = not self.has_studs
      self.rebuild_shape()
      self.draw()

   def ask_destroy(self, *args):
      self.destroy()
      self.setMenu(None)
      print "Brick destroyed"

   def ask_position(self, *args, **kwargs):
      self.setMenu(None)

      set_rotation = kwargs.get('set_rotation')

      @PositionHandlerDecorator
      def get_pos(vec):
         self.origin = vec.clone()
         if set_rotation:
            self.length_vec = angleToBrickDirection(self.mc.player.getRotation())
         self.draw()

      self.mc.postToChat("Choose a new stud")
      self.click_handler.Register_Next_Click_Handler(get_pos)

      self.hide()
   # end def

   def place(self):
      self.ask_position(set_rotation = True)

   def place_clone(self, *args):
      c = self.clone().place() # add c to parent LegoGame block array # TODO
      self.draw()

   def ask_block(self, *args):
      self.setMenu(None)

      @BlockHandlerDecorator(self.mc)
      def get_block(pb):
         # if pb.block in BASIC_BLOCKS:
         self.block = pb.block
         print "Set block to %s"%(str(tuple(self.block)))
         self.draw()

      self.mc.postToChat("Choose a block type to use")
      self.click_handler.Register_Next_Click_Handler(get_block)

      self.hide()
   # end def

   def ask_direction(self, *args):
      self.setMenu(None)

      def set_rotation(hitBlock):
         self.length_vec = angleToBrickDirection(self.mc.player.getRotation())
         print "Brick aligned with %s"%(str(tuple(self.length_vec)))
         self.draw()

      self.mc.postToChat("Face a new direction and hit something")
      self.click_handler.Register_Next_Click_Handler(set_rotation)

      self.hide()
   # end def

   def ask_dim(self, attr, opts=None):
      if opts is None:
         opts=[1,2,3,4,6,8,10,12,16]
      def selected_dim(value, hitBlock):
         self.setMenu(None)
         print "Select the new length"
         def set_dim(x):
            def inner(value, hitBlock):
               setattr(self, attr, x)
               self.rebuild_shape()
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

   def rebuild_shape(self):
      '''
      build the shape from length/width/height, etc. (reset to standard block)
      '''
      if self.deleted: return
      self.shape = set()
      self.shape_studs = set()
      self.has_custom_shape = False # we just destroyed it

      block_length = self.length * self.grid.brick_width
      block_width = self.width * self.grid.brick_width
      block_height = self.height * self.grid.brick_height/3

      # a brick at origin has self.origin which is stud-aligned position
      # the extents of the block (seen from above):
      '''
            X = origin

            +----+    ---> length_vec
            |X  o|  w
            +----+
               l

            (l) block_length = length * grid.brick_width
            (w) block_width  = width * grid.brick_width

      '''

      length_vec = Vec3(1,0,0)
      up_vec = Vec3(0,1,0)
      width_vec = length_vec.cross(up_vec)

      half_block_width = int(self.grid.brick_width / 2)
      p0 = Vec3(0,0,0) + \
           (length_vec * -half_block_width) + \
           (width_vec * -half_block_width)

      exclude_volume = set() # center void
      wall_thickness = 1
      for dl in range(wall_thickness,block_length-wall_thickness):
         for dw in range(wall_thickness,block_width-wall_thickness):
            for dh in range(block_height-wall_thickness):
               pixel_pos = p0 + Vec3(dl, dh, dw)
               exclude_volume.add(pixel_pos)
            # end for // h
         # end for // w
      # end for // l

      for dl in range(block_length):
         for dw in range(block_width):
            for dh in range(block_height):
               pixel_pos = p0 + Vec3(dl, dh, dw)
               if pixel_pos not in exclude_volume:
                  self.shape.add(pixel_pos)
               # end if
            # end for // h
         # end for // w
      # end for // l

      # draw studs
      stud_height = 1
      s0 = Vec3(0,0,0)
      s1 = s0 + up_vec * block_height # first stud
      if not self.has_studs:
         # adjust s1 to be one block lower, to fill the void on a plate
         s1 = s1 + Vec3(0,-1,0)
         stud_height = 1 # regardless of previous setting
      # end if

      for l in range(self.length): # num studs long
         dl = l * self.grid.brick_width
         for w in range(self.width): # num studs wide
            dw = w * self.grid.brick_width

            dh = 0
            # make bottom stud holes (required first in case of tiles)
            pixel_pos = s0 + Vec3(dl, dh, dw)
            self.shape.discard(pixel_pos)

            # add studs to top (see above for special tile rule)
            for dh in range(stud_height):
               pixel_pos = s1 + Vec3(dl, dh, dw)
               self.shape_studs.add(pixel_pos)
            # end for // h
         # end for // w
      # end for // l
   # end def // rebuild_shape

   def _global_to_shape(self, vec):
      v = vec - self.origin
      # now rotate it...
      width_vec =  self.length_vec.cross(self.up_vec)

      a,b,c = self.length_vec
      d,e,f,= self.up_vec
      g,h,i = width_vec
      shape_vec = (Vec3(*[i,h,g]) * v.x) + \
                  (Vec3(*[f,e,d]) * v.y) + \
                  (Vec3(*[c,b,a]) * v.z)
      return shape_vec

   def add_block_to_shape(self, vec): # globally scoped vector
      self.has_custom_shape = True
      self.shape.add(self._global_to_shape(vec))

   def remove_block_from_shape(self, vec): # globally scoped vector
      self.has_custom_shape = True
      self.shape.discard(self._global_to_shape(vec))
      self.shape_studs.discard(self._global_to_shape(vec))

   def draw(self):
      '''
      we don't know what's different this time around, but we may have grown or shrunk
      '''
      if self.deleted: return
      current_geometry = [x for x in self.my_blocks]
      self.my_blocks = set()

      length_vec = self.length_vec
      up_vec =     self.up_vec
      width_vec =  length_vec.cross(up_vec)

      p0 = self.origin
      # for the non-studs (all of which are 'active' and will pop the menu -- owned by us)
      for dl,dh,dw in self.shape:
         pixel_pos = p0 + (length_vec * dl) + \
                          (up_vec * dh) + \
                          (width_vec * dw)
         self.my_blocks.add(pixel_pos)
         if not self.edit_mode:
            self._Register_Active_Block(pixel_pos)
      # end for each pixel in our shape

      # for the studs (which are not 'active' and instead are used to place blocks, owned by our parent)
      for dl, dh, dw in self.shape_studs:
         pixel_pos = p0 + (length_vec * dl) + \
                          (up_vec * dh) + \
                          (width_vec * dw)
         self.my_blocks.add(pixel_pos)
      # end for each stud pixel in our shape

      erase = set(current_geometry).difference(self.my_blocks)
      for e in erase:
         self.mc.setBlock(e, AIR)
         self._Remove_Active_Block(e)
      for p in self.my_blocks:
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
         self.grid.remove_brick(self)
      except:
         pass
      # end try
   # end def

