import logging
import logging.handlers
import docker
import docker.transport
import time
import thread
import threading
import os
import inspect
import traceback
import _socket

format_hdlr = "%(asctime)s %(levelname)s:%(lineno)-3s - %(funcName)-20s %(message)-40s "
hdlr = logging.handlers.RotatingFileHandler('docker_prepare_db2.log',maxBytes=1000000, backupCount = 2)
hdlr1 =  logging.StreamHandler()
log_formatter = logging.Formatter(format_hdlr)
hdlr.setFormatter(log_formatter)
hdlr1.setFormatter(log_formatter)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(hdlr)
log.addHandler(hdlr1)


def print_docker_errors_APIError(e):
   if isinstance(e,docker.errors.APIError):
      log.error("docker.errors.APIError  %s" % e)
      log.error( "explanation:           %s" % e.explanation)
      log.error( "is_server_error        %s" % e.is_server_error())
      log.error( "is_client_error        %s" % e.is_client_error())
      log.error( "e.response.status_code %d" % e.response.status_code)
      log.error( "e.response.reason      %s" % e.response.reason)
      log.error( "e.status_code          %d" % e.status_code)
      
   traceback.print_stack()  

def print_running_status( threadName, delay, exec_id,APIclient,thread_event):
   count = 0
   
   while count < 50:
      time.sleep(delay)
      count += 1
      try:
         inspect = APIclient.exec_inspect(exec_id)
         if inspect['Running'] == False:
            break
      except docker.errors.APIError as e: 
         print_docker_errors_APIError(e)
         break
  
   thread_event.set() 
class PlayingWithDocker:
   container  = None
   APIclient  = None
   def __init__(self):
      log.info (inspect.stack()[0][3])
      self.client = docker.from_env()
      self.client.images.pull("angoca/db2-instance:latest")
      if os.name != "nt":
         self.APIclient = docker.APIClient(base_url='unix:///var/run/docker.sock')
      else:
         self.APIclient = docker.APIClient(base_url='npipe:////./pipe/docker_engine')
   
   def execute_command(self, container_id,cmd, user,detach, trace_time):
      log.info (inspect.stack()[0][3])
      try:   
         if cmd is None:
            cmd = ['bash','-c','ls']
     
         if user is None:
            user = 'root' 
         self.exec_id =  self.APIclient.exec_create(container_id,
                                                    cmd=cmd, 
                                                    user=user)
         self.event = threading.Event()
         thread.start_new_thread( print_running_status, ("thread to monitor command", 
                                                         trace_time,
                                                         self.exec_id,
                                                         self.APIclient,
                                                         self.event ) )
         command_output = None
         command_output = self.APIclient.exec_start(self.exec_id, 
                                                        detach=False, 
                                                        tty=False, 
                                                        stream=True, 
                                                        socket=True)
         event_is_set = False
         if isinstance(command_output,_socket.socket) == True:
            command_output.settimeout(500.0)# I need this as default is 60.0, and db2sampl takes a lot of time
               
         elif isinstance(command_output,docker.transport.npipesocket.NpipeSocket) == True:
            command_output.settimeout(0)
         
         while not event_is_set:
            time.sleep(20)
            event_is_set = self.event.isSet() 
            
            exec_log = command_output.recv(1024)
            log.info("exec_log '%s'" %(exec_log))
            if exec_log.find("'db2sampl' processing complete.") != -1:
               event_is_set = True
               time.sleep(15)# give time for the thread to exit as inspect['Running'] will be 'False'
              
         command_output.close() 
   
      except docker.errors.APIError as e:
         print_docker_errors_APIError(e)
         log.error("APIError %s",e,exc_info=True)  
         
  

        
   def containerlist(self):
      for c in self.client.containers.list(all = True):
         if c.name == "db2inst1":
            self.container = c  
                
   def run_db2(self):
      commands = ['/bin/bash']
      self.container = self.client.containers.run(image      = "angoca/db2-instance:latest",
                                                  command    = commands,
                                                  detach     = True,
                                                  name       = "db2inst1",
                                                  volumes    = {},
                                                  tty        = True,
                                                  stdin_open = False,
                                                  privileged = True,
                                                  ports      = {'50000/tcp': 50001})
      self.container.reload()                                
   def run_container(self):
      log.info (inspect.stack()[0][3])
    
      self.containerlist()
      try:
         if self.container is not None:
            self.container.remove(v=True,force=True)
            self.container = None
         if self.container is None :
            self.run_db2()
            if self.container.status == 'created':
               self.container.start()
               
            if self.container.status == 'running':
               self.execute_command(self.container.id,cmd=['ls'],
                                    user=None,
                                    detach =True,trace_time = 1) 
               
               self.execute_command(self.container.id,
                                    cmd=['./createInstance', 'db2inst1'],
                                    user=None,
                                    detach = True,
                                    trace_time = 3)  
            
               self.execute_command(self.container.id,
                                    cmd=['/opt/ibm/db2/V11.1/bin/db2sampl'],
                                    user= "db2inst1",
                                    detach = True,
                                    trace_time = 20)
               
               self.execute_command(self.container.id,
                                    cmd=['/home/db2inst1/sqllib/adm/db2start'],
                                    user= "db2inst1",
                                    detach = True,
                                    trace_time = 2)
                        
      except docker.errors.APIError as e:
         print_docker_errors_APIError(e)
         log.error("APIError %s" % e, exc_info=True)
      if self.container == None:
         log.error("container is None")
         return      

def mymain():
   mydocker = PlayingWithDocker()
   mydocker.run_container()
if __name__ == "__main__":
   mymain()


