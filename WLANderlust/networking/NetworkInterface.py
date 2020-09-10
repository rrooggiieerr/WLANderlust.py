import os, netifaces, ipaddress, logging
from datetime import datetime

from WLANderlust import config

class NetworkInterface():
  debug = False
  interface = None
  hwaddress = None
  type = None

  status = None
  down = True

  terminate = False

  def __init__(self, interface = None):
    if interface:
      self.interface = interface

    self.logger = logging.getLogger("%s(%s)" % (self.__class__.__name__, interface))

    self.status = {}
    self.status['interface'] = self.interface
    self.status['type'] = self.type
    self.status['status'] = None

    if self.interface:
      self.getIP()

  def start(self):
    return True

  def stop(self):
    self.terminate = True

    return True

  def getIP(self):
    status = {}
    status['ipaddress'] = None
    status['netmask'] = None

    if netifaces.AF_INET in netifaces.ifaddresses(self.interface):
      netiface = netifaces.ifaddresses(self.interface)[netifaces.AF_INET][0]
      status['ipaddress'] = netiface['addr']
      status['netmask'] = netiface['netmask']
      status['cidr'] = ipaddress.IPv4Network('0.0.0.0/' + netiface['netmask']).prefixlen

    self.status = {**self.status, **status}

    return status

  def getNetworkInterfaceStatus(self):
    status = {}
    status['interface'] = self.interface
    status['type'] = self.type
    status['mac'] = None

    if self.hwaddress:
      status['mac'] = self.hwaddress

    if self.interface in netifaces.interfaces():
      # Get the MAC address
      if not self.hwaddress and netifaces.AF_LINK in netifaces.ifaddresses(self.interface):
        status['mac'] = netifaces.ifaddresses(self.interface)[netifaces.AF_LINK][0]['addr']

      # Check if network interface is up
      # This might not work on all Operating Systems
      interfaceFlagsFile = "/sys/class/net/%s/flags" % self.interface
      if os.path.isfile(interfaceFlagsFile):
        with open(interfaceFlagsFile, 'r') as f:
          interfaceFlags = int(f.read(), 16)
          f.close()
          if (interfaceFlags & 0x1) == 0:
            if self.status.get('status', None) != 'down': self.logger.warning("Down")
            self.down = True
            status['status'] = 'down'
          else:
            self.down = False
      # If we can't determine if the interface is up we asume it is

      if not self.status.get('status', None): self.logger.debug("Up")
    else:
      status['status'] = 'nonexistent'

    self.status = {**self.status, **status}

    return status

  def getIPStatus(self):
    status = self.getIP()

    if 'status' in status:
      return status

    if not status['ipaddress']:
      if self.status.get('status', None) != 'noipaddress': self.logger.warning("No IP address assigned")
      status['status'] = 'noipaddress'
    else: self.logger.debug("IP address assigned %s" % (status['ipaddress']))

    return status

  def getStatus(self):
    status = self.getNetworkInterfaceStatus()

    if 'status' in status:
      status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      self.status = status
      return status

    status = {**status, **self.getIPStatus()}

    if 'status' in status:
      status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      self.status = status

    return status

  def Firewall(self):
    return False
