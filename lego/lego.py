#!/usr/bin/env python

from click_handler import *
import json
import threading
from lego_grid import LegoGrid
from lego_brick import LegoBrick, angleToBrickDirection

mqtt_broker = '192.168.1.33'

try:
   import paho.mqtt.client as mqtt
except:
   mqtt = None
   print "paho.mqtt.client was unavailable"
if mqtt:
   class MqttClient():
      def __init__(self,
                   host,
                   port = 1883,
                   on_connect = None,
                   on_message = None,
                   ):
         self.host = host
         self.port = port

         client = mqtt.Client()
         client.on_connect = on_connect
         client.on_message = on_message
         self.client = client
         self.connect()

      def subscribe(self, label):
         self.client.subscribe(label)

      def connect(self):
         print "connecting to mqtt server %s" % (self.host)
         self.client.connect(self.host, self.port, 60)
         self.client.loop_start()

      def disconnect(self):
         # Blocking call that processes network traffic, dispatches callbacks and
         # handles reconnecting.
         # Other loop*() functions are available that give a threaded interface and a
         # manual interface.
         self.client.loop_stop()


def grid_to_dict(grid):
   d = {
      'brick_width' : getattr(grid,'brick_width', 3),
      'brick_height' : getattr(grid,'brick_height', 3),
      # 'plate_height' : getattr(grid,'plate_height', 1),
      'origin' : tuple(getattr(grid,'origin', (0,0,0))),
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
         'length_vec' : tuple(getattr(brick,'length_vec', (1,0,0))),
         'up_vec' : tuple(getattr(brick,'up_vec', (0,1,0))),
         'origin' : tuple(getattr(brick,'origin', (0,0,0))),
         }
      return d

def game_to_dict(game):
   d = {
      'grid' : grid_to_dict(game.my_grid),
      'bricks': [brick_to_dict(b) for b in list(game.my_bricks)]
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
      self.mqtt_data = {}

      self.myClickHandler = ClickHandler(mc = mc)

      self.my_bricks = []
      self.my_grid = None

      self.next_brick = {
         'length': 1,
         'width' : 1,
         'height': 3, # brick not plate
         'block' : Block(1,0), # stone
      }
      self.active_brick = None

      if load_from_file:
         self.load(load_from_file)

      self.my_mqtt_client = None
      self._init_mqtt()

   def load(self, input_file):
      with open(input_file, 'r') as fp:
         o = json.load(fp)
         grid = o['grid']
         self.my_grid = LegoGrid(origin =       Vec3(*grid['origin']),
                                 brick_width =  int(grid['brick_width']),
                                 brick_height = int(grid['brick_height']),
                                )
         for b in o['bricks']:
            if b is not None:
               self.add_brick(pos =                 Vec3(*b['origin']),
                              length =              int(b['length']),
                              width =               int(b['width']),
                              height =              int(b['height']),
                              block =               Block(*b['block']),
                              length_vec =          Vec3(*b['length_vec']),
                              up_vec =              Vec3(*b['up_vec']),
                             )

   def save(self, output_file):
      with open(output_file, 'w') as fp:
         json.dump(game_to_dict(self), fp)

   def _init_mqtt(self):
      if mqtt:

         # The callback for when the client receives a CONNACK response from the server.
         def on_connect(client, userdata, flags, rc):
            print("Connected with result code " + str(rc))

            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            client.subscribe("minecraft/lego/#")
         # end def

         # The callback for when a PUBLISH message is received from the server.
         def on_message(client, userdata, msg):
            print(msg.topic + " " + str(msg.payload))
            # print parts

            parts = msg.topic.split('/')

            if parts[2] == 'last_brick':
               if self.last_brick is not None:
                  if parts[-1] == 'length':
                     self.last_brick.length = int(msg.payload)
                  if parts[-1] == 'width':
                     self.last_brick.width = int(msg.payload)
                  if parts[-1] == 'action':
                     action = msg.payload
                     if action == 'rotate':
                        self.last_brick.length_vec = angleToBrickDirection(self.mc.player.getRotation())
                     elif action == 'move':
                        self.last_brick.ask_position()
                  self.last_brick.draw()
            if parts[2] == 'command':
               if parts[3] == 'save':
                  import pickle

                  import pdb; pdb.set_trace()
               if parts[3] == 'sandwall':
                  from mcpi import block, vec3
                  mc = self.mc
                  p = mc.player.getTilePos();
                  try:
                     if ' ' in msg.payload:
                        l, h = [int(x) for x in msg.payload.split(' ')]
                     else:
                        raise Exception()
                  except:
                     l, h = self.mqtt_data.get('l',1), self.mqtt_data.get('h',1)
                  self.mqtt_data['l'], self.mqtt_data['h'] = l, h
                  d = mc.player.getDirection()
                  if abs(d.x) > abs(d.z):
                     di = Vec3(d.x/abs(d.x),0,0)
                  else:
                     di = Vec3(0,0,d.z/abs(d.z))
                  mc.setBlocks(p + di + vec3.Vec3(0, 3, 0),
                               p + (di * l) + vec3.Vec3(0, h, 0),
                               block.SAND)
         # end def

         self.my_mqtt_client = MqttClient(mqtt_broker,
                                          on_connect=on_connect,
                                          on_message=on_message)
      # end if // else there will be no mqtt sync

   def set_active_brick(self, brick):
      self.active_brick = brick
      # for brick in self.my_bricks:
      #    if position in brick.active_blocks:
      #       self.last_brick = brick
      #       brick.pop_menu()
      #       handled = True
      #       break
      #       # end if
      # # end if

   def add_brick(self, pos, length, width, height, block,
                 length_vec = None,
                 up_vec = None,
                ):
      brick = LegoBrick(pos,
                        block  = Block(*tuple(block)),
                        length = length,
                        width  = width,
                        height = height,
                        length_vec = length_vec,
                        up_vec     = up_vec,
                        mc=self.mc,
                        grid=self.my_grid,
                        click_handler=self.myClickHandler,
                        on_destroy=self.remove_brick,
                        )

      self.set_active_brick(brick)
      self.my_bricks.append(brick)

   def remove_brick(self, brick):
      try:
         self.my_bricks.remove(brick)
      except:
         pass

   def click_to_quit_or_place_new(self, hitBlock):
      pb = PosBlock(hitBlock.pos, mc = self.mc)
      if pb.block == self.quit_block:
         self.done = True
      else:
         self.mc.postToChat("%s"%(pb.block))

         if self.my_grid is None:
            self.my_grid = LegoGrid(pb.pos)
         # end if

         self.add_brick(pos =    pb.pos,
                        length = self.next_brick['length'],
                        width =  self.next_brick['width'],
                        height = self.next_brick['height'],
                        block =  Block(*tuple(self.next_brick['block'])),
                       )

      # end if
   # end if

   def redraw_all(self):
      for b in self.my_bricks:
         b.redraw()

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
      while not self.done:
         time.sleep(0.05)
         self.myClickHandler.Parse_Clicks()
      # end while // not done

      if self.my_mqtt_client:
         self.my_mqtt_client.disconnect()
      # end if

      self.mc.postToChat("All Done, hope you had fun!")
   # end def // run
# end class


r'''
with open(r'c:\temp\paris.json','w') as fp: json.dump(game_to_dict(test.g), fp)
with open(r'c:\temp\paris.json','r') as fp: o = json.load(fp); print o
'''