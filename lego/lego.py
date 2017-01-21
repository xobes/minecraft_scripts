#!/usr/bin/env python

from click_handler import *
import json
import threading
from lego_grid import LegoGrid
from lego_brick import LegoBrick, angleToBrickDirection

mqtt_broker = '192.168.1.33'
mqtt_port = 1883

try:
   import paho.mqtt.client as mqtt
except:
   mqtt = None
   print "paho.mqtt.client was unavailable"

def grid_to_dict(grid):
   d = {
      'brick_width' : getattr(grid,'brick_width', 3),
      'brick_height' : getattr(grid,'brick_height', 3),
      # 'plate_height' : getattr(grid,'plate_height', 1),
      'origin' : tuple(getattr(grid,'origin', (0,0,0))),
      'bricks': [brick_to_dict(b) for b in list(grid.my_bricks)]
      }
   return d

def brick_to_dict(brick):
   deleted = getattr(brick, 'deleted', False)
   if not deleted:
      d = {
         # 'my_blocks' : [tuple(v) for v in getattr(brick,'my_blocks', [])],
         # 'active_blocks' : [tuple(v) for v in getattr(brick,'active_blocks', [])],
         'length' : getattr(brick,'length', 1),
         'width' : getattr(brick,'width', 1),
         'height' : getattr(brick,'height', 1),
         'block' : tuple(getattr(brick,'block', (1,0))),
         'has_studs': 1 * (getattr(brick, 'has_studs', 1)),
         'length_vec' : tuple(getattr(brick,'length_vec', (1,0,0))),
         'up_vec' : tuple(getattr(brick,'up_vec', (0,1,0))),
         'origin' : tuple(getattr(brick,'origin', (0,0,0))),
         }
      if brick.has_custom_shape:
         d.update(dict(
            shape = [tuple(x) for x  in getattr(brick,'shape',[])],
            shape_studs = [tuple(x) for x  in getattr(brick,'shape_studs',[])],
         ))
      return d

def game_to_dict(game):
   d = {
      'grid' : grid_to_dict(game.my_grid),
   }
   return d

class Game(threading.Thread):
   def __init__(self,
                quit_block = TNT,
                load_from_file = None,
                mc = None):
      threading.Thread.__init__(self)
      self.daemon = True

      self.mc = mc
      self.quit_block = quit_block
      self.last_brick = None

      self.done = False
      # self.mqtt_data = {}

      self.myClickHandler = ClickHandler(mc = mc)

      self.my_grid = None

      self.next_brick = {
         'length': 1,
         'width' : 1,
         'height': 3, # brick not plate
         'has_studs': 1,
         'block' : Block(1,0), # stone
      }

      if load_from_file:
         self.load(load_from_file)

      self.mqtt_client = None
      self._init_mqtt()

   def load(self, input_file):
      with open(input_file, 'r') as fp:
         o = json.load(fp)
         grid = o['grid']
         self.my_grid = LegoGrid(origin =       Vec3(*grid['origin']),
                                 brick_width =  int(grid['brick_width']),
                                 brick_height = int(grid['brick_height']),
                                )
         for b in grid['bricks']:
            if b is not None:
               self._add_brick(
                              pos =                 Vec3(*b['origin']),
                              length =              int(b['length']),
                              width =               int(b['width']),
                              height =              int(b['height']),
                              block =               Block(*b['block']),
                              has_studs =           int(b.get('has_studs',1)),
                              length_vec =          Vec3(*b['length_vec']),
                              up_vec =              Vec3(*b['up_vec']),
                              shape =               b.get('shape',None),
                              shape_studs =         b.get('shape_studs', None),
                             )

   def save(self, output_file):
      with open(output_file, 'w') as fp:
         json.dump(game_to_dict(self), fp)

   def _init_mqtt(self):
      if mqtt:
         self.mqtt_client = mqtt.Client()

         # The callback for when the client receives a CONNACK response from the server.
         def on_connect(client, userdata, flags, rc):
            print("Connected with result code " + str(rc))

            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.subscribe("minecraft/lego/input/#")
            client.subscribe("minecraft/lego/input/#")
         # end def

         # TODO: consider using mqtt_client.message_callback_add:
         # mqtt_client.message_callback_add(topic, callback)

         # The callback for when a PUBLISH message is received from the server.
         def on_message(client, userdata, msg):
            print(msg.topic + " " + str(msg.payload))
            # print parts

            parts = msg.topic.split('/')

            if parts[3] == 'next_brick': # .../input/next_brick/...
               k = parts[4]
               try: # try plain number
                  self.next_brick[k] = int(msg.payload)
               except: # try tuple of integers
                  try:
                     if k == 'block':
                        self.next_brick[k] = Block(*[int(x) for x in str(msg.payload).split(',')])
                     else:
                        raise
                  except:
                     import traceback
                     print traceback.format_exc()
                  # end try
               # end try
            elif parts[3] == 'active_brick':
               k = parts[4]
               if k == 'action':
                  if parts[5] == 'rotate':
                     self.my_grid.active_brick.length_vec = angleToBrickDirection(self.mc.player.getRotation())
                     self.my_grid.active_brick.draw()
                  elif parts[5] == 'move':
                     self.my_grid.active_brick.ask_position()
               elif k == 'block':
                  v = Block(*[int(x) for x in str(msg.payload).split(',')])
                  self.my_grid.active_brick.block = v
                  self.my_grid.active_brick.draw()
               elif k in ['width','length','height','has_studs'] and \
                     not self.my_grid.active_brick.has_custom_shape:
                  # presume it's an attribute and attempt to set it
                  v = int(msg.payload)
                  try:
                     setattr(self.my_grid.active_brick,k,v)
                     self.my_grid.active_brick.rebuild_shape()
                     self.my_grid.active_brick.draw()
                  except:
                     import traceback
                     print traceback.format_exc()
                  # end try
               else:
                  print "received data for %s and ignored it"%(k)
               # end try
            elif parts[3] == 'command':
               c = parts[4]
               if c == 'redraw':
                  self.redraw_all()
               elif c == 'save':
                  self.save(r'C:\temp\%s'%(str(msg.payload)) )
               elif c == 'load':
                  self.load(r'C:\temp\%s'%(str(msg.payload)))
               # end if
            # end if
         # end def

         self.mqtt_client.on_connect = on_connect
         self.mqtt_client.on_message = on_message

         self.mqtt_client.connect(mqtt_broker, mqtt_port, 60)
         self.mqtt_client.loop_start()
      # end if // else there will be no mqtt sync

   def _add_brick(self, pos, length, width, height, block,
                 has_studs = True,
                 length_vec = None,
                 up_vec = None,
                 shape=None, shape_studs=None,
                ):
      brick = LegoBrick(pos,
                        block  = Block(*tuple(block)),
                        length = length,
                        width  = width,
                        height = height,
                        has_studs = has_studs,
                        length_vec = length_vec,
                        up_vec     = up_vec,
                        shape=shape,
                        shape_studs=shape_studs,
                        mc=self.mc,
                        grid=self.my_grid,
                        click_handler=self.myClickHandler,
                        # on_destroy=self.remove_brick,
                        )
      self.my_grid.add_brick(brick)

   def click_to_quit_or_place_new(self, hitBlock):
      pb = PosBlock(hitBlock.pos, mc = self.mc)
      if pb.block == self.quit_block:
         self.done = True
      else:
         self.mc.postToChat("%s"%(pb.block))

         if self.my_grid is None:
            self.my_grid = LegoGrid(pb.pos)
         # end if

         self._add_brick(pos =    pb.pos,
                        length = self.next_brick['length'],
                        width =  self.next_brick['width'],
                        height = self.next_brick['height'],
                        has_studs = self.next_brick['has_studs'],
                        block =  Block(*tuple(self.next_brick['block'])),
                       )

      # end if
   # end if

   def redraw_all(self):
      self.my_grid.redraw_all()

   def update_mqtt(self, mqtt_data):
      last_next_brick_data = mqtt_data.get('next_brick',{})
      last_active_brick_data = mqtt_data.get('active_brick',{})
      try:
         if self.mqtt_client:
            if self.next_brick:
               changed = False
               if last_next_brick_data:
                  for k in self.next_brick:
                     if self.next_brick[k] != last_next_brick_data.get(k):
                        changed = True
               else:
                  changed = True

               if changed:
                  last_next_brick_data = {}
                  for k in self.next_brick:
                     v = self.next_brick[k]
                     last_next_brick_data[k] = v
                     try:
                        v = int(v)
                     except:
                        v = tuple(v)
                     # end try
                     self.mqtt_client.publish('minecraft/lego/output/next_brick/%s' % (k), str(v))
                  # end for each k in the next_brick dictionary
               # end if changed
            # end if
            ######################################################################################
            if self.my_grid and self.my_grid.active_brick:
               changed = False
               if last_active_brick_data:
                  for k in self.next_brick: # active_brick has same attrs we care about
                     if getattr(self.my_grid.active_brick,k) != last_active_brick_data.get(k):
                        changed = True
               else:
                  changed = True

               if changed:
                  last_active_brick_data = {}
                  for k in self.next_brick: # active_brick has same attrs we care about
                     v = getattr(self.my_grid.active_brick,k)
                     last_active_brick_data[k] = v
                     try:
                        v = int(v)
                     except:
                        v = tuple(v)
                     # end try
                     self.mqtt_client.publish('minecraft/lego/output/active_brick/%s' % (k), str(v))
                  # end for each k in the active_brick dictionary
               # end if changed
            # end if
         # end if
      except:
         import traceback
         print traceback.format_exc()

      mqtt_data['next_brick'] = last_next_brick_data
      mqtt_data['active_brick'] = last_active_brick_data

      return mqtt_data
   # end def update_mqtt

   def run(self):
      # #########################################################
      # def Wait_For_Hit(mc):
      #    def Make_Hit_Waiter():
      #       Waiter = {}
      #       def Call_On_Hit(Hit):
      #          Waiter['hit'] = Hit
      #       return Waiter, Call_On_Hit
      #    w, c = Make_Hit_Waiter()
      #    self.myClickHandler.Register_Default_Handler(c)
      #    while not w.has_key('hit'):
      #       time.sleep(0.05)
      #       self.myClickHandler.Parse_Clicks()
      #    self.myClickHandler.Reset_Default_Handler()
      #    return w['hit']
      # # end def Wait_For_Hit
      # self.mc.postToChat("testing Wait_For_Hit")
      # pos_block = Wait_For_Hit(self.mc)
      # print "hit detected", pos_block
      # #########################################################
      # TODO: setup workbench for special menu activation...

      self.mc.postToChat("Pick TNT to quit, any other block to make LEGO bricks")
      self.myClickHandler.Register_Default_Handler(self.click_to_quit_or_place_new)

      self.done = False
      mqtt_data = {}
      while not self.done:
         time.sleep(0.01)
         self.myClickHandler.Parse_Clicks()

         mqtt_data = self.update_mqtt(mqtt_data)
      # end while // not done

      if self.mqtt_client:
         self.mqtt_client.loop_stop()
      # end if

      self.mc.postToChat("All Done, hope you had fun!")
   # end def // run
# end class


r'''
with open(r'c:\temp\paris.json','w') as fp: json.dump(game_to_dict(test.g), fp)
with open(r'c:\temp\paris.json','r') as fp: o = json.load(fp); print o
'''
