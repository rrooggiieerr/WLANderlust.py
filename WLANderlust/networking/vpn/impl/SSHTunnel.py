import os, subprocess, threading, socket, netifaces, socket, re, time, logging, bottle
from datetime import datetime

from WLANderlust.networking.vpn import VPN
from WLANderlust import config

logger = logging.getLogger(__name__)

class SSHTunnel(VPN):
  name = 'SSH Tunnel'
  id = 'sshtunnel'
  description = ''

  ctrlPath = None

  privatekey = '/etc/WLANderlust/sshtunnel.id_rsa'
  knownhosts = '/etc/WLANderlust/sshtunnel.known_hosts'

  def __init__(self, parentInterface, credentials):
    super().__init__(parentInterface, credentials)

    self.ctrlPath = '/var/run/sshtunnel.%s.socket' % self.parentInterface.interface

  def isConfigured(self):
    if not os.path.isfile('/usr/bin/ssh') or not os.access('/usr/bin/ssh', os.X_OK):
      self.logger.error("SSH is not installed")
      return False

    if not os.path.isfile(self.privatekey):
      self.logger.error("No SSH public/private key combo")
      return False

    if not self.credentials:
      self.logger.error("No credentials")
      return False

    if 'hostname' not in self.credentials or not self.credentials['hostname']:
      self.logger.error("No hostname configured")
      return False

    if 'username' not in self.credentials or not self.credentials['username']:
      self.logger.error("No username configured")
      return False
    self.credentials['username'] = 'vpn'

    if 'port' not in self.credentials or not self.credentials['port']:
      self.logger.error("No port configured")
      return False

    if 'ipaddress' not in self.credentials:
      self.credentials['ipaddress'] = '192.168.244.2'

    if 'netmask' not in self.credentials:
      self.credentials['netmask'] = '255.255.255.0'

    if 'gateway' not in self.credentials:
      self.credentials['gateway'] = '192.168.244.1'

    return True

  def start(self):
    status = {}

    if not self.isConfigured():
      return False

    for server in socket.gethostbyname_ex(self.credentials['hostname'])[2]:
      _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      _socket.bind((self.parentInterface.status['ipaddress'], 0))
      _socket.settimeout(1)
      if _socket.connect_ex((server, self.credentials['port'])) == 0:
        _socket.close()
        break
      _socket.close()
      self.logger.warning("Unable to connect to port %s on SSH server IP address %s" % (self.credentials['port'], server))
      server = None

    if not server:
      self.logger.error("SSH Server hostname %s could not be resolved" % self.credentials['hostname'])
      return False
    self.logger.debug("SSH Server IP address: %s" % server)

    index = [x for x in netifaces.interfaces() if re.compile("^tun[0-9]+$").match(x)]
    index = len(index)
    _interface = 'tun%s' % int(index)

    # Check if TUN interface already exists, this is just paranoia
    if _interface in netifaces.interfaces():
      self.logger.error("TUN interface %s already exists" % _interface)
      return False

    # Add server to known hosts file
    knownHostsFile = open(self.knownhosts, 'w')
    subprocess.run(['/usr/bin/ssh-keyscan', server], stdout=knownHostsFile, stderr=subprocess.DEVNULL)
    knownHostsFile.close()

    self.server = server
    status['server'] = self.server
    command = ['/usr/bin/ssh', '-p', str(self.credentials['port']), '-f',
      '-i', self.privatekey,
      '-M', '-S', self.ctrlPath,
      '-o', 'UserKnownHostsFile=' + self.knownhosts,
      '-o', 'PermitLocalCommand=yes',
      '-o', 'LocalCommand=ifconfig %s %s pointopoint %s netmask %s' % (_interface, self.credentials['ipaddress'], self.credentials['gateway'], self.credentials['netmask']),
      '-o', 'ServerAliveInterval=5',
      '-o', 'ConnectTimeout=3',
      '-o', 'ExitOnForwardFailure=yes',
      '-b', self.parentInterface.status['ipaddress'],
      '-w', '0:0', '%s@%s' % (self.credentials['username'], self.server),
      'sudo ifconfig %s %s pointopoint %s netmask %s' % ('tun0', self.credentials['gateway'], self.credentials['ipaddress'], self.credentials['netmask'])]
    if subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
      self.logger.error("Failed to create %s" % self.name)
      self.stop()
      return False
    self.logger.info("Created %s" % self.name)

    while not os.path.exists(self.ctrlPath):
      time.sleep(0.1)

    time.sleep(1)

    if _interface not in netifaces.interfaces():
      self.logger.error("Failed to create TUN interface %s" % _interface)
      self.stop()
      return False
    self.logger.info("Created TUN interface %s" % _interface)
    self.interface = _interface
    status['interface'] = self.interface

    if subprocess.call(['/usr/bin/ssh', '-S', self.ctrlPath, '-O', 'check', '%s@%s' % (self.credentials['username'], self.server)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
      self.logger.error("Failed to create %s" % self.name)
      self.stop()
      return False

    self.logger.info("Created %s" % self.name)

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

    if self.ctrlPath:
      if os.path.exists(self.ctrlPath):
        self.logger.info("Stopping %s" % self.name)
        if subprocess.call(['/usr/bin/ssh', '-S', self.ctrlPath, '-O', 'exit', '%s@%s' % (self.credentials['username'], self.server)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
          self.logger.error("Failed to stop %s" % self.name)
          self.status['status'] = 'failure'
          return False
        self.logger.info("Stopped %s" % self.name)

      self.ctrlPath = None
      self.server = None
      self.status['server'] = None

      if self.interface in netifaces.interfaces():
        self.logger.error("Failed to remove TUN interface %s" % self.interface)
        self.status['status'] = 'failure'
        return False
      self.logger.info("Removed TUN interface %s" % self.interface)

      self.interface = None
      self.status['interface'] = None
      self.status['ipaddress'] = None
      self.status['netmask'] = None
      self.status['gateway'] = None

    self.online = False
    self.onlineSince = None
    self.status['status'] = 'offline'
    self.status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    return True

  def isProcessRunning(self):
    if subprocess.call(['/usr/bin/ssh', '-S', self.ctrlPath, '-O', 'check', '%s@%s' % (self.credentials['username'], self.server)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
      self.logger.error("%s process is not running" % self.name)
      return False

    self.logger.debug("%s process is running" % self.name)
    return True

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

@bottle.get('/Networking/vpn/SSHTunnel/publickey')
def publicKey():
  if not os.path.isfile(SSHTunnel.privatekey):
    # Generate SSH public/private key
    logger.info("Generating SSH public/private key combo")
    subprocess.run(['/usr/bin/ssh-keygen', '-b', '2048', '-t', 'rsa', '-f', SSHTunnel.privatekey, '-q', '-N', ''], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  return bottle.static_file(SSHTunnel.privatekey + '.pub', root = '/')

@bottle.post('/Networking/vpn/SSHTunnel/add')
def configAdd():
  id = bottle.request.forms.get('id', None)
  name = bottle.request.forms.get('name')
  username = bottle.request.forms.get('username')
  hostname = bottle.request.forms.get('hostname')
  port = int(bottle.request.forms.get('port'))
  ipaddress = bottle.request.forms.get('ipaddress')
  netmask = bottle.request.forms.get('netmask')
  gateway = bottle.request.forms.get('gateway')

  logger.debug("username: %s" % username)
  logger.debug("hostname: %s" % hostname)
  logger.debug("port    : %s" % port)

  if username and hostname:
    if id:
      credentials = config['Networking']['VPNs'][id]
    else:
      credentials = {}

    credentials['type'] = 'SSHTunnel'
    credentials['name'] = name
    credentials['username'] = username
    credentials['hostname'] = hostname
    credentials['port'] = port
    credentials['ipaddress'] = ipaddress
    credentials['netmask'] = netmask
    credentials['gateway'] = gateway
    logger.debug("Credentials: %s" % credentials)

    if 'Networking' not in config:
      config['Networking'] = {}
    if 'VPNs' not in config['Networking']:
      config['Networking']['VPNs'] = []

    if id:
      config['Networking']['VPNs'][id] = credentials
    else:
      config['Networking']['VPNs'].append(credentials)
    config.save()

    bottle.response.status = 200
    return

  bottle.response.status = 500
