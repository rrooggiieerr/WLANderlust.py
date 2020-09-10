import platform, subprocess, netifaces, pycurl, re, time, logging
from io import BytesIO
from datetime import datetime

from WLANderlust import config
from .OutwardNetworkInterface import OutwardNetworkInterface

class Proxy(OutwardNetworkInterface):
  type = 'proxy'

  parentInterface = None

  port = None

  def __init__(self, parentInterface):
    super().__init__()

    self.logger = logging.getLogger("%s(%s)" % (self.__class__.__name__, parentInterface.interface))

    self.parentInterface = parentInterface

  def getIP(self):
    status = {}

    if 'ipaddress' in self.status:
      status['ipaddress'] = self.status['ipaddress']
    if 'netmask' in self.status:
      status['netmask'] = self.status['netmask']
    if 'cidr' in self.status:
      status['cidr'] = self.status['cidr']
    if 'gateway' in self.status:
      status['gateway'] = self.status['gateway']

    return status

  def getIPStatus(self):
    return self.getIP()

  def getExternalIP(self):
    if not self.status.get('gateway', None):
      self.logger.error("No gateway")
      return None

    detectExternalIPURL = config.get('Networking', {}).get('DetectExternalIPURL', self.detectExternalIPURL)

    response = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.INTERFACE, self.interface)
    curl.setopt(curl.TIMEOUT, self.timeout * 5)
    #ToDo Implement proxy support
    # curl -p 127.0.0.1:12300 https://api.ipify.org
    # curl.setopt(curl.HTTPPROXYTUNNEL, self.status['gateway'] + ":" + str(self.port))
    curl.setopt(curl.URL, detectExternalIPURL)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    try:
      curl.perform()
      response = response.getvalue().decode('utf-8')
    except pycurl.error as e:
      if e.args[0] == 28:
        self.logger.error("External IP address lookup timeout")
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

    externalIP = self.getExternalIP()
    if externalIP:
      status['externalipaddress'] = externalIP

    # All the checks are past, we seem to be online
    self.logger.info("We're online")
    status['status'] = 'online'
    status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    if not self.online:
      self.online = True
      self.onlineSince = time.time()
    status['onlineSince'] = int(time.time() - self.onlineSince)
    self.status = status

    return True

  def isStillOnline(self):
    if not 'externalipaddress' in self.status:
      externalIP = self.getExternalIP()
      if externalIP:
        self.status['externalipaddress'] = externalIP

    # All the checks are past, we seem to be online
    self.logger.debug("We're still online")
    self.status['onlineSince'] = int(time.time() - self.onlineSince)

    return True

  def getStatus(self):
    status = super().getStatus()

    if self.onlineSince:
      status['onlineSince'] = int(time.time() - self.onlineSince)
    else:
      status['onlineSince'] = None

    return status
