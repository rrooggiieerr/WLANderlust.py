import os, signal, subprocess, threading, re, time, netifaces, ipaddress, logging, bottle
from datetime import datetime

from WLANderlust.networking.tunnel import Tunnel
from WLANderlust import config

stdout = ''

logger = logging.getLogger(__name__)

class IODine(Tunnel):
  name = "IODine"
  description = "IP over DNS tunnel"
  executable = '/usr/sbin/iodine'

  pidFile = None
  pid = None
  mode = None

  timeout = 3

  def __init__(self, parentInterface, credentials):
    super().__init__(parentInterface, credentials)

    self.pidFile = '/var/run/iodine.' + parentInterface.interface + '.pid'

  def install(self):
    if not os.path.isfile(self.executable):
      self.logger.info("Installing %s" % self.name)
      subprocess.call(['/usr/bin/apt', 'install', '-y', 'iodine'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

  def isConfigured(self):
    if not os.path.isfile(self.executable) or not os.access(self.executable, os.X_OK):
      self.logger.error("%s is not installed" % self.name)
      return False

    if not self.credentials:
      self.logger.error("No credentials")
      return False

    if 'topdomain' not in self.credentials or not self.credentials['topdomain']:
      self.logger.error("No topdomain configured")
      return False

    if 'password' not in self.credentials or not self.credentials['password']:
      self.logger.error("No password configured")
      return False

    return True

  def start(self):
    status = {}

    if not self.isConfigured():
      self.logger.error("IP over DNS is not configured")
      return False

    if os.path.exists(self.pidFile):
      # Check if the process is already running
      with open(self.pidFile, 'r') as pidFile:
        pid = int(pidFile.read().strip())
        if self.isProcessRunning(pid):
          self.logger.error("%s process is already active" % self.name)
          return False
      self.logger.info("%s process is not running" % self.name)
      os.remove(self.pidFile)

    global stdout

    proc = subprocess.Popen(['/usr/bin/host', '-t', 'NS', self.credentials['topdomain']], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if proc.wait() != 0:
      self.logger.error("IP over DNS server host name could not be resolved")
      proc.stdout.close()
      return False

    output = proc.stdout.read().decode()
    proc.stdout.close()
    ipOverDNSServer = re.compile("^.* ([^ ]*)\.$", re.MULTILINE).search(output).group(1)

    if not ipOverDNSServer:
      self.logger.error("IP over DNS server host name could not be resolved")
      return False

    if subprocess.call(['/usr/bin/host', '-t', 'A', ipOverDNSServer], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
      self.logger.error("IP over DNS server IP address could not be resolved")
      return False

    if len(self.parentInterface.status['nameservers']) == 1:
      server = self.parentInterface.status['nameservers'][0]
    else:
      # Find nameserver which is public
      nameservers = [ns for ns in self.parentInterface.status['nameservers'] if ipaddress.ip_address(ns).is_global]
      if len(nameservers) > 0:
        server = nameservers[0]
      else:
        #ToDo Find nameserver which is outside of the netmask of the parent interface
        nameservers = self.parentInterface.status['nameservers']
        if len(nameservers) > 0:
          server = nameservers[0]
        else:
          server = self.parentInterface.status['nameservers'][0]
    self.logger.debug("nameserver: %s" % server)

    proc = subprocess.Popen([self.executable, '-u', 'iodine', '-F', self.pidFile, '-P', self.credentials['password'], server, self.credentials['topdomain']], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    stdout = ""
    while proc.poll() == None:
      stdout += proc.stderr.read().decode()
      self.logger.debug(stdout)
    proc.stderr.close()

    if proc.poll() != 0:
      self.logger.error("Failed to start %s" % self.name)
      status['status'] = 'failure'
      status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      self.status = status
      return False

    """Example iodine output:
IP over DNS tunneling started
Opened dns0
Opened IPv4 UDP socket
Sending DNS queries for v.xxxxxx.net to 192.168.1.1
Autodetecting DNS query type (use -T to override).
Using DNS type NULL queries
Version ok, both using protocol v 0x00000502. You are user #0
Setting IP of dns0 to 192.168.245.2
Setting MTU of dns0 to 1130
Server tunnel IP is 192.168.245.1
Testing raw UDP data to the server (skip with -r)
Server is at xxx.xxxx.xxx.xxx, trying raw login: OK
Sending raw traffic directly to xxx.xxx.xxx.xxx
Connection setup complete, transmitting data.
Detaching from terminal...

Opened dns0
Opened IPv4 UDP socket
Sending DNS queries for v.xxxxxx.net to 192.168.1.1
Autodetecting DNS query type (use -T to override).....................
iodine: No suitable DNS query type found. Are you connected to a network?
iodine: If you expect very long roundtrip delays, use -T explicitly.
iodine: (Also, connecting to an "ancient" version of iodined won't work.)

Opened dns0
Opened IPv4 UDP socket
Sending DNS queries for v.xxxxxx.net to 192.168.182.1
Autodetecting DNS query type (use -T to override).
Using DNS type NULL queries
Version ok, both using protocol v 0x00000502. You are user #0
Retrying login...
Setting IP of dns0 to 192.168.245.2
Setting MTU of dns0 to 1130
Server tunnel IP is 192.168.245.1
Testing raw UDP data to the server (skip with -r)
Server is at xxx.xxx.xxx.xxx, trying raw login: ....failed
Using EDNS0 extension
Switching upstream to codec Base128
Server switched upstream to codec Base128
No alternative downstream codec available, using default (Raw)
Switching to lazy mode for low-latency
Server switched to lazy mode
Autoprobing max downstream fragment size... (skip with -m fragsize)
768 ok.. .1152 ok.. ...1344 not ok.. ...1248 not ok.. ...1200 not ok.. 1176 ok.. 1188 ok.. will use 1188-2=1186
Setting downstream fragment size to max 1186...
Connection setup complete, transmitting data.
Detaching from terminal..."""

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

    self.interface = re.compile("^Opened ([a-z0-9]*)$", re.MULTILINE).search(stdout).group(1)
    status['interface'] = self.interface
    status['ipaddress'] = re.compile("^Setting IP of [a-z0-9]* to ([0-9\.]*)$", re.MULTILINE).search(stdout).group(1)
    if netifaces.AF_INET in netifaces.ifaddresses(self.interface):
      netiface = netifaces.ifaddresses(self.interface)[netifaces.AF_INET][0]
      status['netmask'] = netiface['netmask']
    status['gateway'] = re.compile("^Server tunnel IP is ([0-9\.]*)$", re.MULTILINE).search(stdout).group(1)

    if re.search("^Server is at [0-9\.]*, trying raw login: [\.]*OK$", stdout, re.MULTILINE):
      self.logger.info("Raw mode, this is the fastest mode")
      self.mode = 'raw'
      self.server = re.compile("^Server is at ([0-9\.]*), .*$", re.MULTILINE).search(stdout).group(1)
    elif re.search("^Server switched to lazy mode$", stdout, re.MULTILINE):
      self.logger.info("Lazy mode")
      self.mode = 'lazy'
      self.server = server
    else:
      self.logger.warning("Unknown mode")
      self.logger.warning(stdout)
      self.mode = 'unknown'
      self.server = server
    self.logger.debug("Server: %s" % self.server)

    status['mode'] = self.mode
    status['server'] = self.server
    self.status = {**self.status, **status}

    if self.mode == 'raw':
      subprocess.run(['/sbin/ip', 'route', 'add', self.server, 'via', self.parentInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Route DNS servers
    for nameserver in self.parentInterface.status['nameservers']:
      #ToDo check if nameserver is outside of the netmask of the parent interface
      if nameserver != self.parentInterface.status['gateway']:
        subprocess.run(['/sbin/ip', 'route', 'add', nameserver, 'via', self.parentInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    if self.mode == 'raw':
      subprocess.run(['/sbin/ip', 'route', 'del', self.server, 'via', self.parentInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    self.mode = None
    self.status['mode'] = None

    for nameserver in self.parentInterface.status['nameservers']:
      #ToDo check if nameserver is outside of the netmask of the parent interface
      if nameserver != self.parentInterface.status['gateway']:
        subprocess.run(['/sbin/ip', 'route', 'del', nameserver, 'via', self.parentInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Stop IODine
    if self.pid:
      try:
        self.logger.info("Stopping IP over DNS tunnel")
        os.kill(self.pid, signal.SIGTERM)
        os.remove(self.pidFile)
        self.pid = None

        self.server = None
        self.status['server'] = None
        self.interface = None
        self.status['interface'] = None
        self.status['ipaddress'] = None
        self.status['netmask'] = None
        self.status['gateway'] = None
        self.logger.info("Stopped IP over DNS tunnel")
      except ProcessLookupError as e:
        self.logger.error("Failed to stop IP over DNS tunnel")
        self.logger.error(e)
        return False

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
    # Check if the process is still running
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

@bottle.post('/Networking/tunnel/IODine/add')
def configAdd():
  id = bottle.request.forms.get('id', None)
  name = bottle.request.forms.get('name', None)
  topdomain = bottle.request.forms.get('topdomain')
  password = bottle.request.forms.get('password')
  logger.debug("Topdomain:", topdomain)

  if topdomain and password:
    if id:
      credentials = config['Networking']['Tunnels'][id]
    else:
      credentials = {}
    credentials['type'] = 'IODine'
    credentials['name'] = name
    credentials['topdomain'] = topdomain
    credentials['password'] = password
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

@bottle.get('/Tunnels/IODine/stdout')
def getStdout():
  return stdout
