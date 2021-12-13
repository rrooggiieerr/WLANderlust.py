import os, signal, subprocess, threading, re, time, netifaces, logging, bottle
from datetime import datetime

from WLANderlust.networking import Proxy
from WLANderlust import config, CredentialsStore

logger = logging.getLogger(__name__)

class Ptunnel(Proxy):
  interface = 'lo'
  name = "Ptunnel"
  description = "TCP over ICMP tunnel"
  executable = '/usr/sbin/ptunnel'

  credentials = None

  server = None
  process = None

  timeout = 3

  def __init__(self, parentInterface, credentials):
    super().__init__(parentInterface)

    self.credentials = credentials

  def install(self):
    if not os.path.isfile(self.executable):
      self.logger.info("Installing %s" % self.name)
      subprocess.call(['/usr/bin/apt', 'install', '-y', 'ptunnel'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

  def isConfigured(self):
    if not os.path.isfile(self.executable) or not os.access(self.executable, os.X_OK):
      self.logger.error("%s is not installed" % self.name)
      return False

    if not self.credentials:
      self.logger.error("No credentials")
      return False

    if 'server' not in self.credentials or not self.credentials['server']:
      self.logger.error("No Server configured")
      return False

    if 'listenport' not in self.credentials or not self.credentials['listenport']:
      self.logger.error("No Listen Port configured")
      return False

    if 'destinationaddress' not in self.credentials or not self.credentials['destinationaddress']:
      self.logger.error("No Destination Address configured")
      return False

    if 'destinationport' not in self.credentials or not self.credentials['destinationport']:
      self.logger.error("No Destination Port configured")
      return False

    return True

  def start(self):
    status = {}

    if not self.isConfigured():
      self.logger.error("TCP over ICMP is not configured")
      return False

    if self.process:
      self.logger.error("%s process is already active" % self.name)
      return False

    self.server = self.credentials['server']
    command = [self.executable, '-p', self.server, '-lp', self.credentials['listenport'], '-da', self.credentials['destinationaddress'], '-dp', self.credentials['destinationport'], '-c', self.parentInterface.interface]
    if 'password' in self.credentials and self.credentials['password']:
      command.extend(['-x', self.credentials['password']])
    self.process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    status['server'] = self.server

    status['interface'] = self.interface
    status['ipaddress'] = '127.0.0.1'
    status['netmask'] = '255.0.0.0'
    status['cidr'] = 8
    status['gateway'] = '127.0.0.1'
    self.status = {**self.status, **status}

    time.sleep(1)

    if not self.isOnline():
      self.stop()
      return False

    status['status'] = 'online'
    status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    self.online = True
    self.onlineSince = time.time()
    status['onlineSince'] = int(time.time() - self.onlineSince)
    self.status = status

    return super().start()

  def stop(self):
    super().stop()

    # Stop Ptunnel
    if self.process:
      self.logger.info("Stopping TCP over ICMP tunnel")
      self.process.terminate()
      self.process = None

      self.server = None
      self.status['server'] = None
      self.status['interface'] = None
      self.status['ipaddress'] = None
      self.status['netmask'] = None
      self.status['gateway'] = None
      self.logger.info("Stopped IP over ICMP tunnel")

    self.online = False
    self.onlineSince = None
    self.status['status'] = 'offline'
    self.status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    return True

  def isProcessRunning(self):
    if self.process.poll() == None:
      self.logger.debug("%s process is running" % self.name)
      return True

    self.logger.error("%s process is not running" % self.name)
    return False

  def getNetworkInterfaceStatus(self):
    # Check if the process is still running
    if not self.isProcessRunning():
      status = {'status': 'noprocess'}
      self.status = {**self.status, **status}
      return status

    return super().getNetworkInterfaceStatus()

  def isStillOnline(self):
    # Check if the process is still running
    if not self.isProcessRunning():
      return False

    return super().isStillOnline()

@bottle.post('/Networking/tunnel/Ptunnel/add')
def configAdd():
  id = bottle.request.forms.get('id', None)
  name = bottle.request.forms.get('name', None)
  server = bottle.request.forms.get('server')
  logger.debug("Server:", server)

  if server and ipaddress and netmask and gateway:
    if id:
      credentials = config['Networking']['Tunnels'][id]
    else:
      credentials = {}
    credentials['type'] = 'Ptunnel'
    credentials['name'] = name
    credentials['server'] = server
    logger.debug("Credentials: %s" % credentials)

    if 'Networking' not in config:
      config['Networking'] = {}
    if 'Tunnels' not in config['Networking']:
      config['Networking']['Tunnels'] = []

    if id:
      config['Networking']['Tunnels'][id] = credentials
    else:
      config['Networking']['Tunnels'].append(credentials)
    config.save()

    bottle.response.status = 200
    return

  bottle.response.status = 500
