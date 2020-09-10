import platform, subprocess, threading, netifaces, pycurl, re, time
from io import BytesIO
from datetime import datetime

from WLANderlust import config
from WLANderlust.networking import NetworkInterface

class OutwardNetworkInterface(NetworkInterface):
  isOnlineThread = None
  pauseIsOnlineThread = False

  detectExternalIPURL = 'https://api.ipify.org'

  online = None
  onlineSince = None

  timeout = 1

  lastPing = 0
  def __init__(self, interface = None):
    super().__init__(interface)

  def start(self):
    self.logger.info("Starting isOnline thread")
    self.isOnlineThread = threading.Thread(target = self.isOnlineThreadImpl, name = "%s is online thread" % self.interface)
    self.isOnlineThread.start()
    self.logger.info("Started isOnline thread")

    return super().start()

  def stop(self):
    super().stop()

    if self.isOnlineThread:
      self.logger.info("Stopping isOnline thread")
      self.isOnlineThread.join()
      self.isOnlineThread = None
      self.logger.info("Stopped isOnline thread")

  def ping(self, host: str):
    if not host:
      return False

    # Building the command
    if platform.system().lower() == "linux":
      command = ['/bin/ping', '-q', '-c', '3', '-l', '3', '-I', self.interface, '-W', str(self.timeout), '-n', host]
    elif platform.system().lower() == "darwin":
      command = ['/sbin/ping', '-q', '-c', '3', '-l', '3', '-b', self.interface, '-W', str(self.timeout), '-n', host]
    elif platform.system().lower() == "windows":
      command = ['ping', '-n', '1', host]
    else:
      return False

    try:
      return subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=self.timeout + 1).returncode == 0
    except subprocess.TimeoutExpired as e:
      self.logger.debug(e)
      return False

    return False

  def getIP(self):
    status = super().getIP()
    status['gateway'] = None

    if netifaces.AF_INET in netifaces.ifaddresses(self.interface):
      if netifaces.AF_INET in netifaces.gateways():
        for gateway in netifaces.gateways()[netifaces.AF_INET]:
          if gateway[1] == self.interface:
            status['gateway'] = gateway[0]

      #if not status['gateway']:
      #  netiface = netifaces.ifaddresses(self.interface)[netifaces.AF_INET][0]
      #  if 'peer' in netiface:
      #    status['gateway'] = netiface['peer']

    if not status['gateway'] and 'gateway' in self.status:
      status['gateway'] = self.status['gateway']

    if 'gateway' in self.status:
      self.logger.debug("Gateway: %s" % self.status['gateway'])
    else:
      self.logger.debug("No gateway")

    self.status = {**self.status, **status}

    return status

  def getIPStatus(self):
    status = super().getIPStatus()

    if 'status' in status:
      return status

    if not status['gateway']:
      if self.status.get('status', None) != 'nogateway': self.logger.warning("No gateway")
      status['status'] = 'nogateway'
    else: self.logger.debug("Gateway exists %s" % status['gateway'])

    return status

  def getExternalIP(self):
    if not self.status.get('gateway', None):
      self.logger.warning("No gateway")
      return None

    detectExternalIPURL = config.get('Networking', {}).get('DetectExternalIPURL', self.detectExternalIPURL)

    response = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.INTERFACE, self.interface)
    curl.setopt(curl.TIMEOUT, self.timeout * 5)
    curl.setopt(curl.URL, detectExternalIPURL)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    try:
      curl.perform()
      response = response.getvalue().decode('utf-8')
    except pycurl.error as e:
      if e.args[0] == 28:
        self.logger.warning("External IP address lookup timeout")
      else:
        self.logger.error(e)
      response = None
    curl.close()

    if not response:
      return None

    externalIP = None
    if re.compile("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$").search(response):
      externalIP = response
      self.logger.debug("External IP address: %s" % externalIP)
    else:
       self.logger.error("What is my IP response invallid")
       self.logger.error(response)

    return externalIP

  def isOnline(self):
    status = self.getStatus()

    if 'status' in status:
      return False

    if self.terminate:
      return False

    # Check if we can ping the gateway server
    if not self.ping(self.status['gateway']):
      self.logger.warning("Can't ping gateway")
      #status['status'] = 'cantpinggateway'
      #status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      #self.online = False
      #self.onlineSince = None
      #self.status = status
      #return False
    else:
      self.logger.debug("Can ping gateway")

    if self.terminate:
      return False

    # Check if we can ping the Google DNS server
    if not self.ping("8.8.8.8"):
      self.logger.warning("Can't ping Google DNS server")
      status['status'] = 'cantping'
      status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      self.online = False
      self.onlineSince = None
      self.status = status
      return False
    self.lastPing = time.time()
    self.logger.debug("Can ping Google DNS server")

    if self.terminate:
      return False

    externalIP = self.getExternalIP()
    if externalIP:
      status['externalipaddress'] = externalIP

    # All the checks are past, we seem to be online
    self.logger.info("We're online")
    status['status'] = 'online'
    status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    if not self.online:
      self.online = True
    if not self.onlineSince:
      self.onlineSince = time.time()
    status['onlineSince'] = int(time.time() - self.onlineSince)
    self.status = status

    return True

  def isStillOnline(self):
    lastPing = time.time() - self.lastPing
    if self.onlineSince and lastPing < self.timeout:
      self.status['onlineSince'] = int(time.time() - self.onlineSince)
      return True

    # Check if we can ping the gateway server
    if not self.ping(self.status.get('gateway', None)):
      self.logger.debug("Can't ping gateway")
      if lastPing > self.timeout * 5:
        self.logger.warning("Can't ping gateway")
        #return False
    else: self.logger.debug("Can ping gateway")

    if self.terminate or self.pauseIsOnlineThread:
      return False

    # Check if we can ping the Google DNS server
    if not self.ping("8.8.8.8"):
      self.logger.debug("Can't ping Google DNS server")
      if lastPing > self.timeout * 5:
        self.logger.warning("Can't ping Google DNS server")
        return False
    else:
      self.lastPing = time.time()
      self.logger.debug("Can ping Google DNS server")
    self.logger.debug("Last successful ping %s seconds ago" % lastPing)

    if self.terminate or self.pauseIsOnlineThread:
      return False

    if not 'externalipaddress' in self.status:
      externalIP = self.getExternalIP()
      if externalIP:
        self.status['externalipaddress'] = externalIP

    # All the checks are past, we seem to be online
    self.logger.debug("We're still online")
    if not self.onlineSince:
      self.onlineSince = time.time()
    self.status['onlineSince'] = int(time.time() - self.onlineSince)

    return True

  def isOnlineThreadImpl(self):
    while not self.terminate:
      if self.pauseIsOnlineThread:
        self.logger.debug("Pause is online thread")
        time.sleep(0.1)
        continue

      if not self.isOnline():
        if self.online != False:
          self.logger.warning("Offline")
          self.online = False
          self.onlineSince = None

        time.sleep(0.1)
        continue

      while not self.terminate and self.isStillOnline():
        if self.terminate:
          break
        if self.pauseIsOnlineThread:
          break
        time.sleep(0.1)

  def getStatus(self):
    status = super().getStatus()

    if self.onlineSince:
      status['onlineSince'] = int(time.time() - self.onlineSince)
    else:
      status['onlineSince'] = None

    return status
