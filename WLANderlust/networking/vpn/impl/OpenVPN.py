import logging, bottle

from WLANderlust.networking.vpn import VPN
from WLANderlust import CredentialsStore

class OpenVPN(VPN):
  name = "OpenVPN"
  description = ""
  executable = '/usr/sbin/openvpn'

  pidFile = None
  pid = None

  def __init__(self, parentInterface, credentials):
    super().__init__(parentInterface, credentials)

    self.pidFile = '/var/run/openvpn.%s.pid' % self.parentInterface.interface

  def install(self):
    if not os.path.isfile(self.executable):
      self.logger.info("Installing %s" % self.name)
      subprocess.call(['/usr/bin/apt', 'install', '-y', 'openvpn'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      #ToDo update-rc.d -f openvpn remove
    return True

  def isConfigured(self):
    if not os.path.isfile(self.executable) or not os.access(self.executable, os.X_OK):
      self.logger.error("%s is not installed" % self.name)
      return False

    if not self.credentials:
      self.logger.error("No credentials")
      return False
    self.logger.debug("Credentials: %s" % self.credentials)

    #if 'configfile' not in self.credentials or not self.credentials['configfile']:
    #  self.logger.error("No configuration file configured")
    #  return False

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

    self.logger.info("Starting %s" % self.name)
    if subprocess.call([self.executable, '--config', self.credentials['configfile'], '--writepid', self.pidFile, '--daemon'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
      self.logger.error("Failed to start %s" % self.name)
      self.stop()
      return False
    self.logger.info("Started %s" % self.name)

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

    #self.interface = 'lo'
    #status['interface'] = self.interface
    #status['ipaddress'] = '127.0.0.1'
    #status['netmask'] = '255.0.0.0'
    #status['cidr'] = 8
    #status['gateway'] = '127.0.0.1'

    status['status'] = 'online'
    status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    self.online = True
    self.onlineSince = time.time()
    status['onlineSince'] = int(time.time() - self.onlineSince)
    self.status = status

    return super().start()

  def stop(self):
    super().stop()

    # Stop OpenVPN
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

@bottle.post('/Networking/vpn/OpenVPN/add')
def configPost():
  bottle.response.status = 404
