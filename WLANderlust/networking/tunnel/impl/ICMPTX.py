import os, signal, subprocess, threading, re, time, netifaces, logging, bottle
from datetime import datetime

from WLANderlust.networking.tunnel import Tunnel
from WLANderlust import config, CredentialsStore

logger = logging.getLogger(__name__)

class ICMPTX(Tunnel):
  name = "ICMPTX"
  description = "IP over ICMP tunnel"
  executable = '/usr/sbin/icmptx'

  server = None
  process = None

  timeout = 3

  def install(self):
    if not os.path.isfile(self.executable):
      self.logger.info("Installing %s" % self.name)
      subprocess.call(['/usr/bin/apt-get', 'install', '-y', 'icmptx'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

  def isConfigured(self):
    if not os.path.isfile(self.executable) or not os.access(self.executable, os.X_OK):
      self.logger.error("%s is not installed" % self.name)
      return False

    if not self.credentials:
      self.logger.error("Icmptx is not configured")
      return False

    if 'server' not in self.credentials or not self.credentials['server']:
      self.logger.error("No Server configured")
      return False

    if 'ipaddress' not in self.credentials or not self.credentials['ipaddress']:
      self.logger.error("No IP address configured")
      return False

    if 'netmask' not in self.credentials or not self.credentials['netmask']:
      self.logger.error("No netmask configured")
      return False

    if 'gateway' not in self.credentials or not self.credentials['gateway']:
      self.logger.error("No gateway configured")
      return False

    return True

  def start(self):
    status = {}

    if not self.isConfigured():
      self.logger.error("IP over ICMP is not configured")
      return False

    if self.process:
      self.logger.error("Icmptx process is already active")
      return False

    interfaces = netifaces.interfaces()

    self.server = self.credentials['server']
    self.process = subprocess.Popen([self.executable, '-c', self.server], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    status['server'] = self.server

    time.sleep(1)

    interfaces = [ i for i in netifaces.interfaces() if i not in interfaces]

    if len(interfaces) != 1:
      self.logger.error("Failed to get IP over ICMP tunnel interface")
      self.stop()
      return False
    self.interface = interfaces[0]
    self.logger.debug("Interface: %s" % self.interface)

    #self.logger.debug(subprocess.run(['/sbin/ifconfig', self.interface, 'mtu', '65535', 'up', self.credentials['ipaddress'], 'netmask', self.credentials['netmask']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    if subprocess.run(['/sbin/ifconfig', self.interface, 'up', self.credentials['ipaddress'], 'netmask', self.credentials['netmask']]).returncode != 0:
      self.logger.error("Failed to set IP of IP over ICMP tunnel interface")
      self.stop()
      return false

    status['interface'] = self.interface
    status['ipaddress'] = self.credentials['ipaddress']
    status['netmask'] = self.credentials['netmask']
    status['gateway'] = self.credentials['gateway']
    self.status = {**self.status, **status}

    subprocess.run(['/sbin/ip', 'route', 'add', self.server, 'via', self.parentInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

    # Remove route
    subprocess.run(['/sbin/ip', 'route', 'del', self.server, 'via', self.parentInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    #for nameserver in self.parentInterface.status['nameservers']:
    #  #ToDo check if nameserver is outside of the netmask of the parent interface
    #  if nameserver != self.parentInterface.status['gateway']:
    #    subprocess.run(['/sbin/ip', 'route', 'del', nameserver, 'via', self.parentInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Stop Icmptx
    if self.process:
      self.logger.info("Stopping IP over ICMP tunnel")
      self.process.terminate()
      self.process = None

      self.server = None
      self.status['server'] = None
      self.interface = None
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

@bottle.post('/Networking/tunnel/ICMPTX/add')
def configAdd():
  id = bottle.request.forms.get('id', None)
  name = bottle.request.forms.get('name', None)
  server = bottle.request.forms.get('server')
  ipaddress = bottle.request.forms.get('ipaddress')
  netmask = bottle.request.forms.get('netmask')
  gateway = bottle.request.forms.get('gateway')
  logger.debug("Server:", server)

  if server and ipaddress and netmask and gateway:
    if id:
      credentials = config['Networking']['Tunnels'][id]
    else:
      credentials = {}
    credentials['type'] = 'ICMPTX'
    credentials['name'] = name
    credentials['server'] = server
    credentials['ipaddress'] = ipaddress
    credentials['netmask'] = netmask
    credentials['gateway'] = gateway
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
