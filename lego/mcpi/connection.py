import socket
import select
import sys
import atexit
import os
import platform
from util import flatten_parameters_to_string
from threading import Lock

""" @author: Aron Nieminen, Mojang AB"""

class RequestError(Exception):
   pass

class Connection:
   """Connection to a Minecraft Pi game"""
   RequestFailed = "Fail"

   def __init__(self, address=None, port=None):
      if address==None:
         try:
             address = os.environ['MINECRAFT_API_HOST']
         except KeyError:
             address = "localhost"
      if port==None:
         try:
             port = int(os.environ['MINECRAFT_API_PORT'])
         except KeyError:
             port = 4711
      if int(sys.version[0]) >= 3:
         self.send = self.send_python3
         self.send_flat = self.send_flat_python3
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.connect((address, port))
      self.readFile = self.socket.makefile("r")
      self.lastSent = ""
      self.lock = Lock()
      if platform.system() == "Windows":
         atexit.register(self.close)

   def __del__(self):
      if platform.system() == "Windows":
         self.close()
         try:
            atexit.unregister(self.close)
         except:
            pass

   def close(self):
      try:
         self.readFile.close()
      except:
         pass
      try:
         self.socket.close()
      except:
         pass

   def drain(self, locked = False):
      """Drains the socket of incoming data"""
      try:
         if not locked:
            self.lock.acquire()
         while True:
            readable, _, _ = select.select([self.socket], [], [], 0.0)
            if not readable:
               break
            data = self.socket.recv(1500)
            if not data:
               self.socket.close()
               raise ValueError('Socket got closed')
            e =  "Drained Data: <%s> [%d]\n"%(data.strip(),len(data))
            e += "Last Message: <%s>\n"%self.lastSent.strip()
            sys.stderr.write(e)
      except:
         raise
      finally:
         if not locked:
            self.lock.release()

   def send(self, f, *data, **kwargs):
      """Sends data. Note that a trailing newline '\n' is added here"""
      locked = kwargs.get('locked',False)
      try:
         if not locked:
            self.lock.acquire()
         s = "%s(%s)\n"%(f, flatten_parameters_to_string(data))
         #print "f,data:",f,data
         self.drain(locked=True)
         self.lastSent = s
         self.socket.sendall(s)
      except:
         raise
      finally:
         if not locked:
            self.lock.release()

   def send_python3(self, f, *data, **kwargs):
      """Sends data. Note that a trailing newline '\n' is added here"""
      locked = kwargs.get('locked',False)
      try:
         if not locked:
            self.lock.acquire()
         s = "%s(%s)\n"%(f, flatten_parameters_to_string(data))
         #print "f,data:",f,data
         self.drain(locked=True)
         self.lastSent = s
         self.socket.sendall(s.encode("utf-8"))
      except:
         raise
      finally:
         if not locked:
            self.lock.release()

   def send_flat(self, f, data, locked = False):
      """Sends data. Note that a trailing newline '\n' is added here"""
#      print "f,data:",f,list(data)
      try:
         if not locked:
            self.lock.acquire()
         s = "%s(%s)\n"%(f, ",".join(data))
         self.drain(locked=True)
         self.lastSent = s
         self.socket.sendall(s)
      except:
         raise
      finally:
         if not locked:
            self.lock.release()

   def send_flat_python3(self, f, data, locked = False):
      """Sends data. Note that a trailing newline '\n' is added here"""
#      print "f,data:",f,list(data)
      try:
         if not locked:
            self.lock.acquire()
         s = "%s(%s)\n"%(f, ",".join(data))
         self.drain(locked=True)
         self.lastSent = s
         self.socket.sendall(s.encode("utf-8"))
      except:
         raise
      finally:
         if not locked:
            self.lock.release()

   def receive(self, locked = False):
      """Receives data. Note that the trailing newline '\n' is trimmed"""
      try:
         if not locked:
            self.lock.acquire()
         s = self.readFile.readline().rstrip("\n")
         if s == Connection.RequestFailed:
            raise RequestError("%s failed"%self.lastSent.strip())
      except:
         raise
      finally:
         if not locked:
            self.lock.release()
      return s

   def sendReceive(self, *data, **kwargs):
      """Sends and receive data"""
      locked = kwargs.get('locked',False)
      try:
         if not locked:
            self.lock.acquire()
         self.send(*data, locked=True)
         r = self.receive(locked=True)
      except:
         raise
      finally:
         if not locked:
            self.lock.release()
      return r

   def sendReceive_flat(self, f, data, locked = False):
      """Sends and receive data"""
      try:
         if not locked:
            self.lock.acquire()
         self.send_flat(f, data, locked=True)
         r = self.receive(locked=True)
      except:
         raise
      finally:
         if not locked:
            self.lock.release()
      return r
