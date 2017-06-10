import time
import subprocess
import socket
import psutil
import sys

sys.setrecursionlimit(10000) #Maybe too many zeros? :P This is to prevent the Recurring Depth error.
REMOTE_SERVER = "www.google.com" #Cause it's the fastest site. 

def is_connected():
   try:
      host = socket.gethostbyname(REMOTE_SERVER)   #DNSLookup
      s = socket.create_connection((host, 80), 10) #Connect Succesfully
      return True
   except:
      pass
   return False

def inloop(check):
   print('Entered inloop().')
   time.sleep(20)
   while not check:
      check = is_connected()
      print(check)
      inloop(check)
   print('Got Connection Back!')
   try:
      for proc in psutil.process_iter():  #made this with windows in mind, but easier replacable.
         if proc.name() == "cmd.exe" and proc.username()=="<insert username of host>":
            proc.terminate()
            print("Successfully killed previous session.")
         try:
            if proc.name() == "conhost.exe" and proc.username()=="<insert username of host>":
            proc.terminate()
            print("Successfully killed previous session.")
         except:
            pass
      for proc2 in psutil.process_iter():
         if proc2.name() == "cmd.exe" and proc2.username()=="<insert username of host>":
            proc2.terminate()
            print("Successfully killed previous session.")
         try:
            if proc2.name() == "conhost.exe" and proc2.username()=="<insert username of host>":
            proc2.terminate()
            print("Successfully killed previous session.")
         except:
            pass  
      subprocess.Popen(['C:\\Users\\username\\path\YourBot-master\\runbot.bat'])
      print("Successfully launched Bot.")
      looper()
   except Exception as e:
      print(str(e)) 
      time.sleep(50)
      subprocess.Popen(['C:\\Users\\username\\path\YourBot-master\\runbot.bat'])
      looper()
   else:
      inloop(check)
          
def looper():
   nbool = is_connected()    
   while nbool:
      nbool = is_connected()
      print('Connected')
      time.sleep(5)
      looper()
   print('Lost connection. Retrying....')
   check2 = False
   inloop(check2)

looper()
