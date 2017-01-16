#!/usr/bin/env python

LEGO_WIDTH = 3
LEGO_HEIGHT = 3

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