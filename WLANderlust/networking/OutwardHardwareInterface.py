import os, threading, subprocess, socket, fcntl, struct, re, time, json
from datetime import datetime

from WLANderlust import config, captiveportals
from WLANderlust.networking import OutwardNetworkInterface
from .Networking import Networking
from WLANderlust.networking.tunnel import Tunnels
from WLANderlust.networking.vpn import VPNs

class OutwardHardwareInterface(OutwardNetworkInterface):
  captivePortalSupervisor = None
  tunnel = None
  vpn = None

  def __init__(self, interface):
    super().__init__(interface)

    # Get the hardware (MAC) address of this interface
    # Code from https://stackoverflow.com/questions/159137/getting-mac-address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(self.interface, 'utf-8')[:15]))
    self.hwaddress = ':'.join('%02x' % b for b in info[18:24])
    self.logger.debug(self.hwaddress)
    s.close()

  def start(self):
    self.captivePortalSupervisor = captiveportals.CaptivePortalSupervisor(self)

    return super().start()

  def stop(self):
    super().stop()

    self.stopVPN()

    self.stopTunnel()

    if self.captivePortalSupervisor:
      self.captivePortalSupervisor.stop()
    self.captivePortalSupervisor = None

  def getIP(self):
    status = super().getIP()

    status['metered'] = False
    status['nameservers'] = None

    completed = subprocess.run(['/sbin/dhcpcd', '--dumplease', self.interface, '-4'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if completed.returncode != 0:
      # No DHCP?
      if self.status.get('status', None) != 'nodhcp':
        self.logger.warning("No DHCP")
      status['status'] = 'nodhcp'
      return status

    dump = completed.stdout.decode().strip()
    self.logger.debug("DHCP lease dump:")
    self.logger.debug(dump)

    match = re.search("^vendor_encapsulated_options='([^']*)'", dump, re.MULTILINE)
    if match:
      vendorOptions = match.group(1)
      self.logger.debug("Vendor options: %s" % vendorOptions)
      if vendorOptions == '414e44524f49445f4d455445524544':
        status['metered'] = True
      else:
        self.logger.warning("Unrecognised Vendor Option %s" % vendorOptions)

    self.logger.debug("Metered: %s" % status['metered'])

    match = re.search("^domain_name_servers='([^']*)'", dump, re.MULTILINE)
    if match:
      nameservers = match.group(1)
      status['nameservers'] = nameservers.split()
      self.logger.debug("Nameservers: %s" % status['nameservers'])

    self.status = {**self.status, **status}

    return status

  def getIPStatus(self):
    status = super().getIPStatus()

    if 'status' in status:
      return status

    if not status['nameservers']:
      self.logger.warning("No nameservers")
      status['status'] = 'nonameservers'

    return status

  def isOnline(self):
    status = self.getStatus()

    if 'status' in status:
      return False

    if self.terminate:
      return False

    # Check if we can ping the gateway server
    if not self.ping(status['gateway']):
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

    # Check if we have a working DNS server
    try:
      detectionHostname = re.search("^.*//([^/:]*).*$", self.captivePortalSupervisor.detectionURL).group(1)
      socket.gethostbyname(detectionHostname)
    except Exception as e:
      if self.status.get('status', None) != 'nameservererror':
        self.logger.warning("DNS not working")
      status['status'] = 'nameservererror'
      status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      self.online = False
      self.onlineSince = None
      self.status = status
      return False
    self.logger.debug("DNS is working")

    if self.terminate:
      return False

    if self.status.get('status', None) == 'captiveportal' and self.status['captiveportal']['type'] not in ['Failure', 'NotAny']:
      status['status'] = 'captiveportal'
      status['captiveportal'] = self.status['captiveportal']
      #if self.status.get('status', None) != status['status']:
      #  status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      #  self.status = status

      #if self.captivePortalSupervisor.solve():
      #  status['status'] = None
      #  status['captiveportal']['status'] = self.captivePortal.captivePortalSolver.status
      #  status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
      #else:
      #  return False

      #self.status = status
      return False
    else:
      # Check if we have a Captive Portal
      if self.captivePortalSupervisor.hasCaptivePortal():
        self.logger.warning("Captive Portal present")
        status['status'] = 'captiveportal'
        status['captiveportal'] = { 'status': self.captivePortalSupervisor.captivePortalSolver.status, 'type': self.captivePortalSupervisor.captivePortalSolver.name, 'detectionMethod': self.captivePortalSupervisor.captivePortalSolver.detectionMethod }

        if status['captiveportal']['status'] == 'solved':
          self.logger.debug("Captive Portal solved")
        else:
          if not self.captivePortalSupervisor.solve():
            status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")
            self.online = False
            self.onlineSince = None
            self.status = status
            return False

          status['captiveportal']['status'] = self.captivePortalSupervisor.captivePortalSolver.status
      elif self.status.get('captiveportal', {}).get('status', None) in ['present', 'solved']:
        self.logger.debug("Captive Portal solved")
        status['captiveportal'] = self.status['captiveportal']
        status['captiveportal']['status'] = 'solved'
      else:
        self.logger.debug("No Captive Portal present")
        status['captiveportal'] = { 'status': None }
        self.captivePortal = None

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
    if 'status' not in self.status or self.status['status'] != 'online': self.logger.info("We're online")
    status['status'] = 'online'
    status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    if not self.online:
      self.online = True
      self.onlineSince = time.time()
    status['onlineSince'] = int(time.time() - self.onlineSince)
    self.status = status

    return True

  def isOnlineThreadImpl(self):
    while not self.terminate:
      if self.pauseIsOnlineThread:
        #self.logger.debug("Pause is online thread")
        time.sleep(0.1)
        continue

      if not self.isOnline():
        if self.online != False:
          if not self.tunnel and config.get('Networking', {}).get('AutoStartTunnel', False):
            # Start IP Tunnel
            self.startTunnel()

          if not self.tunnel or not self.tunnel.status['status'] != 'online':
            self.logger.warning("Offline")
            self.online = False
            self.onlineSince = None

            Networking.getInstance().registerOffline(self)

            #ToDo Routing

            # Stop VPN
            if self.vpn:
              self.vpn.stop()
              self.vpn = None

            # Stop IP Tunnel
            if self.tunnel:
              self.stopTunnel()

        if 'captiveportal' in self.status and self.status['captiveportal']['status'] == 'present':
          print(self.status)
          Networking.getInstance().routing(self)

        time.sleep(0.1)
        continue

      if not self.online:
        if self.terminate:
          break

        self.online = True

        inwardNetworkInterfaces = Networking.getInstance().inwardNetworkInterfaces
        if self.type == 'wifi' and inwardNetworkInterfaces:
          for inwardNetworkInterface in inwardNetworkInterfaces:
            if inwardNetworkInterface.type == 'wifi':
              if self.status.het('channel', None) < 6:
                inwardNetworkInterface.changeChannel(11)
              else:
                inwardNetworkInterface.changeChannel(1)

        if self.terminate:
          break

      if not self.vpn and config.get('Networking', {}).get('AutoStartVPN', False):
        # Start VPN
        self.startVPN()

      if self.terminate:
        break

      Networking.getInstance().registerOnline(self)

      while not self.terminate and self.isStillOnline():
        if self.terminate:
          break
        if self.pauseIsOnlineThread:
          break
        time.sleep(0.1)

  def startTunnel(self, id = None):
    if 'status' not in self.status:
      self.logger.debug("status", self.status)
      return False

    if self.status.get('status', None) not in ['online', 'captiveportal']:
      return False

    if self.tunnel or self.vpn:
      return False

    if id:
      id = int(id)

    self.pauseIsOnlineThread = True

    tunnel = Tunnels.start(self, id)

    if not tunnel:
      self.pauseIsOnlineThread = False
      return False

    self.tunnel = tunnel
    Networking.getInstance().routing(self)
    self.status['tunnel'] = self.tunnel.status
    self.logger.debug(self.tunnel.status)
    self.status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    self.logger.info("Started %s tunnel" % tunnel.name)
    return True

  def stopTunnel(self):
    if not self.tunnel:
      return False

    if self.vpn:
      return False

    tunnel = self.tunnel

    self.logger.info("Stopping %s tunnel" % tunnel.name)
    if not tunnel.stop():
      self.logger.error("Failed to stop %s tunnel" % tunnel.name)
      return False

    self.tunnel = None
    Networking.getInstance().routing(self)
    self.status['tunnel'] = None
    self.status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    self.pauseIsOnlineThread = False

    self.logger.info("Stopped %s tunnel" % tunnel.name)
    return True

  def startVPN(self, id = None):
    if self.status.get('status', None) != 'online' and not self.tunnel:
      return False

    if self.vpn:
      self.logger.error("VPN already active")
      return False

    if id:
      id = int(id)

    self.pauseIsOnlineThread = True

    if self.tunnel:
      vpn = VPNs.start(self.tunnel, id)
    else:
      vpn = VPNs.start(self, id)

    if not vpn:
      if not self.tunnel:
        self.pauseIsOnlineThread = False
      return False

    self.vpn = vpn
    Networking.getInstance().routing(self)
    self.status['vpn'] = self.vpn.status
    self.logger.debug(self.vpn.status)
    self.status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    self.logger.info("Started %s VPN" % vpn.name)
    return True

  def stopVPN(self):
    if not self.vpn:
      return False

    vpn = self.vpn

    self.logger.info("Stopping %s VPN" % vpn.name)
    if not vpn.stop():
      self.logger.error("Failed to stop %s VPN" % vpn.name)
      return False

    self.vpn = None
    Networking.getInstance().routing(self)
    self.status['vpn'] = None
    self.status['timestamp'] = datetime.now().strftime("%Y%m%d%H%M%S")

    if not self.tunnel:
      self.pauseIsOnlineThread = False

    self.logger.info("Stopped %s VPN" % vpn.name)
    return True

  def getStatus(self):
    status = super().getStatus()

    if self.tunnel:
      status['tunnel'] = self.tunnel.getStatus()
    else:
      status['tunnel'] = None

    if self.vpn:
      status['vpn'] = self.vpn.getStatus()
    else:
      status['vpn'] = None

    #self.status = status

    return status

  def Firewall(self):
    #ToDo Deny everything
    #ToDo Allow SSH during testing/development/debugging
    return False

  def speedtest(self):
    if not self.online:
      return False

    self.logger.info("Start speedtest")
    stdout = ""
    proc = subprocess.Popen(['speedtest', '-f', 'json', '-I', self.interface], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    while proc.poll() == None:
      if self.terminate:
        proc.terminate()
        self.logger.info("Terminate speedtest")
      stdout += proc.stdout.read().decode()
      self.logger.debug(stdout)
      time.sleep(0.1)
    proc.stdout.close()
    result = json.loads(stdout)

    speed = {}
    speed['upload'] = result['download']['bandwidth']
    speed['download'] = result['upload']['bandwidth']
    speed['latency'] = result['ping']['latency']
    self.logger.debug(speed)
    self.status['speed'] = speed

    self.logger.info("Finished speedtest")

    return True
