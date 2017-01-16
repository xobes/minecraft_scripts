#!/usr/bin/env python

from mcpi.minecraft import Minecraft
from mcpi.block import * # Block and all constant block definitions
from mcpi.vec3 import Vec3

import server
import math
import text # from mcpipy scripts distribution
from sign import Sign
from menu import Menu, BlockChooser
from lego_brick import LegoBrick, LegoGrid, angleToBrickDirection
from collections import OrderedDict
import time
from threading import Lock

from click_handler import *

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

class Game():
   def __init__(self,
                quit_block = TNT,
                mc = None):
      self.mc = mc
      self.quit_block = quit_block
      self.my_bricks = set()
      self.my_grid = None
      self.my_lock = Lock()
      self.last_brick = None

      self.done = False
      self.mqtt_data = {}

      self.myClickHandler = ClickHandler(mc = mc)

      self.my_mqtt_client = None
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

   def remove_brick(self,brick):
      self.my_bricks.discard(brick)

   def set_active_brick(self, brick):
      print "set_active_brick not implemented"
      # for brick in self.my_bricks:
      #    if position in brick.active_blocks:
      #       self.last_brick = brick
      #       brick.pop_menu()
      #       handled = True
      #       break
      #       # end if
      # # end if

   def click_to_quit_or_place_new(self, hitBlock):
      pb = PosBlock(hitBlock.pos, mc = self.mc)
      if pb.block == self.quit_block:
         self.done = True
      elif (pb.block in BASIC_BLOCKS): # pass the buck
         self.mc.postToChat("%s"%(pb.block))

         if self.my_grid is None:
            self.my_grid = LegoGrid(pb.pos)
         # end if

         kwargs = {}
         if self.last_brick:
            kwargs.update({
               'block': self.last_brick.block,
               'length': min(8,self.last_brick.length),
               'width':  min(2, self.last_brick.width),
               'height':  self.last_brick.height,
            })
         else:
            kwargs.update({
               'block': pb.block,
            })
         # end if
         kwargs.update(dict(
            mc=self.mc,
            grid=self.my_grid,
            click_handler = self.myClickHandler,
            on_destroy=self.remove_brick,
         ))

         # print kwargs

         brick = LegoBrick(pb.pos,
                           **kwargs
                           )

         self.last_brick = brick
         self.my_bricks.add(brick)
      else:
         self.mc.postToChat("Ignored %s" % (pb.block))
      # end if
   # end if

   def run(self):
      # Cannot do this here!  myClickHandler uses the mainloop below...
      #########################################################
      def Wait_For_Hit(mc):
         def Make_Hit_Waiter():
            Waiter = {}
            def Call_On_Hit(Hit):
               Waiter['hit'] = Hit
            return Waiter, Call_On_Hit
         w, c = Make_Hit_Waiter()
         self.myClickHandler.Register_Default_Handler(c)
         while not w.has_key('hit'):
            time.sleep(0.05)
            self.myClickHandler.Parse_Clicks()
         self.myClickHandler.Reset_Default_Handler()
         return w['hit']
      # end def Wait_For_Hit
      self.mc.postToChat("testing Wait_For_Hit")
      pos_block = Wait_For_Hit(self.mc)
      print "hit detected", pos_block
      #########################################################

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

print "lego"