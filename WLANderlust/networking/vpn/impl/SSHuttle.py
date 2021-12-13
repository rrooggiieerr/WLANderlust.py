import os, signal, subprocess, threading, socket, time, re, logging, bottle
from datetime import datetime

from WLANderlust.networking.Networking import Networking
from WLANderlust.networking.Proxy import Proxy
from WLANderlust import config

logger = logging.getLogger(__name__)

class SSHuttle(Proxy):
  interface = 'lo'
  name = "SSHuttle"
  description = ""
  executable = '/usr/bin/sshuttle'

  credentials = None

  pidFile = None
  pid = None
  server = None

  #privatekey = '/etc/WLANderlust/sshuttle.id_rsa'
  privatekey = '/etc/WLANderlust/sshtunnel.id_rsa'
  #knownhosts = '/etc/WLANderlust/sshuttle.known_hosts'
  knownhosts = '/etc/WLANderlust/sshtunnel.known_hosts'

  def __init__(self, parentInterface, credentials):
    super().__init__(parentInterface)

    self.credentials = credentials
    self.pidFile = '/var/run/sshuttle.%s.pid' % self.parentInterface.interface

  def install(self):
    if not os.path.isfile(self.executable):
      self.logger.info("Installing %s" % self.name)
      subprocess.call(['/usr/bin/apt', 'install', '-y', 'sshuttle'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

  def isConfigured(self):
    if not os.path.isfile(self.executable) or not os.access(self.executable, os.X_OK):
      self.logger.error("%s is not installed" % self.name)
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

    if 'port' not in self.credentials or not self.credentials['port']:
      self.logger.error("No port configured")
      return False

    return True

  def start(self):
    status = {}

    if not self.isConfigured():
      return False

    if os.path.exists(self.pidFile):
      # Check if the process is running
      with open(self.pidFile, 'r') as pidFile:
        pid = int(pidFile.read().strip())
        if self.isProcessRunning(pid):
          self.logger.error("%s process is already active" % self.name)
          return False
      self.logger.info("%s process is not running" % self.name)
      os.remove(self.pidFile)

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

    # Add server to known hosts file
    knownHostsFile = open(self.knownhosts, 'w')
    subprocess.run(['/usr/bin/ssh-keyscan', server], stdout=knownHostsFile, stderr=subprocess.DEVNULL)
    knownHostsFile.close()

    self.server = server
    status['server'] = self.server
    command = [self.executable, '--pidfile=' + self.pidFile, '-D', '-e', 'ssh -p %s -i %s -o UserKnownHostsFile=%s -b %s' % (self.credentials['port'], self.privatekey, self.knownhosts, self.parentInterface.status['ipaddress']), '-r', '%s@%s' % (self.credentials['username'], self.server), '0/0', '-x', self.server, '-l', '0.0.0.0:0']
    for networkInterface in Networking.getInstance().inwardNetworkInterfaces:
      if networkInterface.status.get('ipaddress', None):
        command.extend(['-x', networkInterface.status['ipaddress'] + '/' + str(networkInterface.status['cidr'])])
        #command.extend(['-l', networkInterface.status['ipaddress'] + ":0"])
    for networkInterface in Networking.getInstance().outwardNetworkInterfaces:
      if networkInterface.status.get('ipaddress', None):
        command.extend(['-x', networkInterface.status['ipaddress'] + '/' + str(networkInterface.status['cidr'])])
        #command.extend(['-l', networkInterface.status['ipaddress'] + ":0"])
      
    if subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
      self.logger.error("Failed to start %s" % self.name)
      self.stop()
      return False
    self.logger.info("Started %s" % self.name)

    # Wait till the PID file is created
    while not os.path.exists(self.pidFile):
      time.sleep(0.1)

    # Read the PID from the PID file
    try:
      with open(self.pidFile, 'r') as pidFile:
        self.pid = int(pidFile.read().strip())
      self.logger.debug("PID: %s" % self.pid)
    except IOError:
      self.logger.error("Failed to read PID")
      self.status['status'] = 'nopid'
      status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      self.status = status
      return False

    proc = subprocess.Popen(['/usr/bin/lsof', '-aPi', '-Fn', '-iTCP', '-sTCP:LISTEN', '-p', str(self.pid)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    stdout = ""
    while proc.poll() == None:
      stdout += proc.stdout.read().decode()
      self.logger.debug(stdout)
    proc.stdout.close()

    _port = re.compile("^n[^:]*:([0-9]*)$", re.MULTILINE).search(stdout).group(1)
    self.port = int(_port)
    self.logger.debug("proxy port: %s" % self.port)

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

    # Stop SSHuttle
    if self.pid:
      self.logger.info("Stopping %s" % self.name)
      try:
        os.kill(self.pid, signal.SIGTERM)
        #os.remove(self.pidFile)
        self.pid = None

        self.pid = None
        self.server = None
        self.status['server'] = None
      except ProcessLookupError as e:
        self.logger.error("Failed to stop %s" % self.name)
        self.logger.error(e)
        return False
      self.logger.info("Stopped %s" % self.name)

    self.online = False
    self.onlineSince = None
    self.status['status'] = 'offline'
    self.status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    return True

  def isProcessRunning(self, pid = None):
    if not pid:
      pid = self.pid

    try:
      os.kill(pid, 0)
    except ProcessLookupError:
      # ESRCH == No such process
      return False

    self.logger.debug("%s process is running" % self.name)
    return True

  def getNetworkInterfaceStatus(self):
    # Check if the process is running
    if not self.isProcessRunning():
      self.logger.error("%s process is not running" % self.name)
      status = {'status': 'noprocess'}
      self.status = {**self.status, **status}
      return status

    return super().getNetworkInterfaceStatus()

  def isStillOnline(self):
    # Check if the process is still running
    if not self.isProcessRunning():
      self.logger.error("%s process is not running" % self.name)
      return False

    return super().isStillOnline()

@bottle.get('/Networking/vpn/SSHuttle/publickey')
def publicKey():
  if not os.path.isfile(SSHuttle.privatekey):
    # Generate SSH public/private key
    logger.info("Generating SSH public/private key combo")
    subprocess.run(['/usr/bin/ssh-keygen', '-b', '2048', '-t', 'rsa', '-f', SSHuttle.privatekey, '-q', '-N', ''], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

  return bottle.static_file(SSHuttle.privatekey + '.pub', root = '/')

@bottle.post('/Networking/vpn/SSHuttle/add')
def configPost():
  id = bottle.request.forms.get('id')
  name = bottle.request.forms.get('name')
  username = bottle.request.forms.get('username')
  hostname = bottle.request.forms.get('hostname')
  port = int(bottle.request.forms.get('port'))

  logger.debug("username: %s" % username)
  logger.debug("hostname: %s" % hostname)
  logger.debug("port    : %s" % port)

  if username and hostname:
    if id:
      credentials = config['Networking']['VPNs'][id]
    else:
      credentials = {}

    credentials['type'] = 'SSHuttle'
    credentials['name'] = name
    credentials['username'] = username
    credentials['hostname'] = hostname
    credentials['port'] = port
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
