#!/usr/bin/env python

from mcpi.minecraft import Minecraft
from mcpi.block import * # Block and all constant block definitions
from mcpi.vec3 import Vec3

from collections import OrderedDict
import time
from threading import Lock

import mcpi.block
BASIC_BLOCKS = [getattr(mcpi.block, x) for x in dir(mcpi.block)
                if (not x.startswith('_') and \
                     x != 'Block' and \
                     (x == x.upper()) and \
                     'DOOR' not in x.upper() and \
                     'GATE' not in x.upper()
                   )]

def Flash_Block(mc, pos, flash_block):
   block = mc.getBlockWithData(pos)
   if block in BASIC_BLOCKS:
      mc.setBlock(pos, flash_block)
      time.sleep(0.1)
      mc.setBlock(pos, block)  # back to original
   else:
      mc.postToChat("selected special block: %s" % (str(block)))
   # end if
# end def

def PositionHandlerDecorator(pos_handler):
   def inner(hitBlock):
      return pos_handler(hitBlock.pos)
   return inner
# end def

def BlockHandlerDecorator(mc):
   def decor(block_handler):
      def inner(hitBlock):
         return block_handler(PosBlock(hitBlock.pos, mc = mc))
      return inner
   return decor
# end def

class PosBlock():
   def __init__(self, vec, block = None, mc = None):
      print locals()
      self.pos = None
      self.block = None
      # print vec, isinstance(vec, Vec3), type(vec)
      # print block, isinstance(block, Block), type(block)
      if isinstance(vec, Vec3):
         if (block is None) and (mc is not None):
            block = mc.getBlockWithData(vec)
         if isinstance(block, Block):
            self.block = block
            self.pos = vec.clone()
      if (self.pos is None or self.block is None):
         print self.pos, self.block
         raise Exception("PosBlock needs a Vec3 and either a Block or mc...")

class ClickHandler():
   def __init__(self,
                mc = None):
      self.mc = mc
      self._lookup = {}
      self.default_handler = None
      self.default_handlers = []
      self.Reset_Default_Handler()
      self._clear_hit_queue()
      self.next_click_handler = None

   def _hash(self, vec):
      t = 0
      v = repr(vec)
      for c in range(len(v), 0, -1):
         t += ord(v[c - 1]) * 10 ** c
      # end for
      return t

   def _print_events(self, event, *args, **kwargs):
      print event, args, kwargs

   def Register_Default_Handler(self, defaultClickHandler):
      self.default_handlers.append(self.default_handler)
      self.default_handler = defaultClickHandler

   def Reset_Default_Handler(self):
      try:
         self.default_handler = self.default_handlers.pop()
      except:
         self.default_handler = self._print_events

   def Register(self, vec, clickHandler):
      if isinstance(vec, Vec3) and callable(clickHandler):
         # self.blocks.append((vec, clickHandler))
         self._lookup.update( { self._hash(vec) : clickHandler } )

   def Remove(self, vec):
      try:
         self._lookup.pop(self._hash(vec))
      except: pass

   def Register_Next_Click_Handler(self, nextClickHandler):
      self.next_click_handler = nextClickHandler

   def Remove_Next_Click_Handler(self):
      self.next_click_handler = None

   def _clear_hit_queue(self):
      for hitBlock in self.mc.events.pollBlockHits():
         pass

   def Parse_Clicks(self):
      for hitBlock in self.mc.events.pollBlockHits():
         position = hitBlock.pos
         h = self._hash(position)
         handled = False
         if self.next_click_handler:
            try:
               self.next_click_handler(hitBlock)
            finally:
               self.Remove_Next_Click_Handler()
               handled = True
         if not handled:
            if h in self._lookup:
               f = self._lookup[h]
               try:
                  f(hitBlock)
               except:
                  import traceback
                  print traceback.format_exc()
               finally:
                  handled = True
               # end try
            # end if

         if not handled:
            self.default_handler(hitBlock)
         # end if
      # end for
   # end def
# end class
