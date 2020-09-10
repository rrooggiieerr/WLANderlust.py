import os, threading, subprocess, time, re, netifaces, logging, bottle
#import bluetooth

from WLANderlust import config, MyWSGIRefServer, BSSIDLocationCache, GPS
from WLANderlust.networking import tunnel, vpn
from WLANderlust import networking
from WLANderlust.plugins import Plugins

logger = logging.getLogger(__name__)

class Networking():
  __instance = None

  @staticmethod
  def getInstance():
    logger.debug("Get instance")
    if not Networking.__instance:
      logger.debug("Creating instance")
      Networking()
    return Networking.__instance

  def __init__(self):
    if Networking.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      Networking.__instance = self

    self.logger = logging.getLogger("%s()" % (self.__class__.__name__))

    self.detectNetworkInterfacesThread = None
    self.terminate = False

    self.webServer = None
    self.webInterfaceThread = None

    self.inwardNetworkInterfaces = []
    self.outwardNetworkInterfaces = []
    self.onlineNetworkInterfaces = []

    self.detectNetworkInterfaces()

  def start(self):
    self.logger.info("Starting Network Interfaces")
    for outwardNetworkInterface in self.outwardNetworkInterfaces:
      self.logger.info("Starting outward interface %s" % outwardNetworkInterface.interface)
      ap = next((o for o in self.inwardNetworkInterfaces if o.hwaddress == outwardNetworkInterface.hwaddress and o.type == outwardNetworkInterface.type and outwardNetworkInterface.type == 'wifi'), None)
      if ap:
        logger.info("Interface %s is simultaniously used as Clien and Access Point" % (outwardNetworkInterface.interface))
        outwardNetworkInterface.setAP(ap)
      outwardNetworkInterface.start()

    for inwardNetworkInterface in self.inwardNetworkInterfaces:
      self.logger.info("Starting inward interface %s" % inwardNetworkInterface.interface)
      #ap = next((o for o in self.outwardNetworkInterfaces if o.hwaddress == inwardNetworkInterface.hwaddress), None)
      #if ap:
      #  print(ap.interface)
      inwardNetworkInterface.start()

    self.logger.info("Started Network Interfaces")

    # Start a Web Interface on localhost if no inward network interfaces are configured
    if len(self.inwardNetworkInterfaces) == 0:
      # Start a Web Interface on the interface
      self.logger.info("lo: Starting Web Interface")
      port = 8080
      if os.geteuid() == 0:
        port = 80
      self.webServer = MyWSGIRefServer(host="127.0.0.1", port=port)
      self.webInterfaceThread = threading.Thread(target = bottle.run, kwargs=dict(server = self.webServer, quiet = True), name = "Web Interface on lo")
      self.webInterfaceThread.start()
      self.logger.info("lo: Started Web Interface")

    #self.detectNetworkInterfacesThread = threading.Thread(target = self.detectNetworkInterfacesThreadImpl)
    #self.detectNetworkInterfacesThread.start()

  def stop(self):
    self.terminate = True

    if self.webServer:
      self.logger.info("lo: Stopping Web Interface")
      self.webServer.stop()
      self.webInterfaceThread.join()
      self.logger.info("lo: Stopped Web Interface")

    # Wait for Detect Network Interfaces  thread to finish
    if self.detectNetworkInterfacesThread:
      self.detectNetworkInterfacesThread.join()

    self.logger.info("Stopping Network Interfaces")
    for outwardNetworkInterface in self.outwardNetworkInterfaces:
      self.logger.info("Stopping outward interface %s" % outwardNetworkInterface.interface)
      outwardNetworkInterface.stop()
    self.outwardNetworkInterfaces = []

    for inwardNetworkInterface in self.inwardNetworkInterfaces:
      self.logger.info("Stopping inward interface %s" % inwardNetworkInterface.interface)
      inwardNetworkInterface.stop()
    self.inwardNetworkInterfaces = []

    self.logger.info("Stopped Network Interfaces")

  def registerOnline(self, outwardInterface):
    if len(self.onlineNetworkInterfaces) == 0:
      for inwardInterface in self.inwardNetworkInterfaces:
        inwardInterface.stopCaptivePortal()

    if outwardInterface.interface not in self.onlineNetworkInterfaces:
      self.onlineNetworkInterfaces.append(outwardInterface.interface)

      self.routing()

      if self.terminate:
        return

      if outwardInterface.vpn:
        _interface = outwardInterface.vpn
      elif outwardInterface.tunnel:
        _interface = outwardInterface.tunnel
      else:
        _interface = outwardInterface

        BSSIDLocationCache.getCache().online(_interface)
        GPS.getInstance().online(_interface)

        # Start plugins online method
        Plugins.getInstance().online(_interface)

  def registerOffline(self, outwardInterface):
    if outwardInterface.interface in self.onlineNetworkInterfaces:
      self.onlineNetworkInterfaces.remove(outwardInterface.interface)

      self.routing()

      if len(self.onlineNetworkInterfaces) == 0:
        for inwardInterface in self.inwardNetworkInterfaces:
          inwardInterface.startCaptivePortal()

      # Start plugins offline method
      Plugins.getInstance().offline(outwardInterface)

      BSSIDLocationCache.getCache().offline(outwardInterface)
      GPS.getInstance().offline(outwardInterface)

  def isOnline(self):
    return len(self.onlineNetworkInterfaces) > 0

  def routing(self, outwardInterface = None):
    if not outwardInterface:
      # Decide over which interface we're going to route
      for interface in [interface for interface in self.outwardNetworkInterfaces if interface.interface in self.onlineNetworkInterfaces]:
        if not outwardInterface:
          outwardInterface = interface
          continue

        if outwardInterface.interface == interface.interface:
          continue

        # Routing over a not metered connection goes first
        if outwardInterface.status.get('metered', True) and not interface.status.get('metered', True):
          outwardInterface = interface
          continue

        # Routing over a wired connection goes first
        if outwardInterface.type != 'wired' and interface.type == 'wired':
          outwardInterface = interface
          continue

        if outwardInterface.type in ('bluetooth', 'mobile') and interface.type in ('wired', 'wifi'):
          outwardInterface = interface
          continue

        if outwardInterface.tunnel and not interface.tunel:
          outwardInterface = interface
          continue
 
    if outwardInterface:
      if outwardInterface.vpn:
        _interface = outwardInterface.vpn
      elif outwardInterface.tunnel:
        _interface = outwardInterface.tunnel
      else:
        _interface = outwardInterface

      if _interface.type == 'proxy':
        return

    # Flush existing input rules
    subprocess.run(['/sbin/iptables', '-F', 'INPUT'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Flush existing output rules
    subprocess.run(['/sbin/iptables', '-F', 'OUTPUT'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Flush existing forward rules
    subprocess.run(['/sbin/iptables', '-F', 'FORWARD'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Flush existing NAT rules
    subprocess.run(['/sbin/iptables', '-F', '-t', 'nat'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not _interface:
      return

    if len(self.inwardNetworkInterfaces) > 0:
      # Routing
      #if outwardInterface.tunnel:
      #  subprocess.run(['/sbin/ip', 'route', 'add', outwardInterface.tunnel.status['server'], 'via', outwardInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
      #if outwardInterface.vpn:
      #  if outwardInterface.tunnel:
      #    subprocess.run(['/sbin/ip', 'route', 'add', outwardInterface.vpn.status['server'], 'via', outwardInterface.tunnel.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      #  else: 
      #    subprocess.run(['/sbin/ip', 'route', 'add', outwardInterface.vpn.status['server'], 'via', outwardInterface.status['gateway']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      self.logger.info("Routing trafic over %s" % _interface.interface)
      subprocess.run(['/sbin/ip', 'route', 'replace', 'default', 'via', _interface.status['gateway']])

      # Enable IP forwarding
      with open('/proc/sys/net/ipv4/conf/%s/forwarding' % _interface.interface, 'w') as file:
        file.write('1')
        file.flush()

      for inwardNetworkInterface in self.inwardNetworkInterfaces:
        # Enable IP forwarding
        with open('/proc/sys/net/ipv4/conf/%s/forwarding' % inwardNetworkInterface.interface, 'w') as file:
          file.write('1')
          file.flush()

        # Allow all connections out and only related ones in
        command = ['/sbin/iptables', '-A', 'FORWARD', '-i', _interface.interface, '-o', inwardNetworkInterface.interface, '-m', 'conntrack', '--ctstate', 'ESTABLISHED,RELATED', '-j', 'ACCEPT']
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        command = ['/sbin/iptables', '-A', 'FORWARD', '-i', _interface.interface, '-o', inwardNetworkInterface.interface, '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT']
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        command = ['/sbin/iptables', '-A', 'FORWARD', '-i', inwardNetworkInterface.interface, '-o', _interface.interface, '-j', 'ACCEPT']
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      # Enable masquerading
      command = ['/sbin/iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', _interface.interface, '-j', 'MASQUERADE']
      subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      #ToDo Firewall

  def configureNetworkInterface(self, interfaceName: str):
    interfaceNames = set(netifaces.interfaces())
    interfaceNames.remove('lo')
    # Remove IP over DNS interfaces
    # These could exist if IP over DNS has been started outside of WLANderlust
    interfaceNames = [x for x in interfaceNames if not x.startswith("dns")]
    # Remove TUN/TAP interfaces
    interfaceNames = [x for x in interfaceNames if not x.startswith("tun")]

    inwardNetworkInterfaceNames = []
    if config.get('Networking', {}).get('InwardInterfaces', None):
      inwardNetworkInterfaceNames = [x.strip() for x in config['Networking']['InwardInterfaces'] if x != '']
    else:
      self.logger.info("Detecting Inward Network Interfaces")
      with open('/etc/dnsmasq.conf', 'r') as f:
        dnsmasqConf = f.read()
        f.close()
        inwardNetworkInterfaceNames = re.compile("^interface=(.*)$", re.MULTILINE).findall(dnsmasqConf)
        inwardNetworkInterfaceNames = [x for x in inwardNetworkInterfaceNames if x in interfaceNames]
    self.logger.info("Inward Network Interfaces: %s", inwardNetworkInterfaceNames)

    if config.get('Networking', {}).get('OutwardInterfaces', []):
      outwardNetworkInterfaceNames = [x.strip() for x in config['Networking']['OutwardInterfaces'] if x != '']
    else:
      self.logger.info("Detecting Outward Network Interfaces")
      outwardNetworkInterfaceNames = (list(set(interfaceNames) - set(inwardNetworkInterfaceNames)))
    self.logger.info("Outward Network Interfaces: %s", outwardNetworkInterfaceNames)

    if interfaceName in inwardNetworkInterfaceNames:
      inwardNetworkInterface = None

      if re.search("^eth[0-9]*$", interfaceName):
        self.logger.info("Creating InwardEthernetInterface %s", interfaceName)
        inwardNetworkInterface = networking.InwardEthernetInterface(interfaceName)
      elif re.search("^wlan[0-9]*$", interfaceName):
        self.logger.info("Creating InwardWiFiInterface %s", interfaceName)
        inwardNetworkInterface = networking.InwardWiFiInterface(interfaceName)
      elif re.search("^ap[0-9]*$", interfaceName):
        self.logger.info("Creating InwardWiFiInterface %s", interfaceName)
        inwardNetworkInterface = networking.InwardWiFiInterface(interfaceName)
      else:
        self.logger.info("Creating InwardNetworkInterface %s", interfaceName)
        inwardNetworkInterface = networking.InwardNetworkInterface(interfaceName)

      self.inwardNetworkInterfaces.append(inwardNetworkInterface)
    elif interfaceName in outwardNetworkInterfaceNames:
      outwardNetworkInterface = None

      if re.search("^eth[0-9]*$", interfaceName):
        self.logger.info("Creating OutwardEthernetInterface %s", interfaceName)
        outwardNetworkInterface = networking.OutwardEthernetInterface(interfaceName)
      elif re.search("^wlan[0-9]*$", interfaceName):
        self.logger.info("Creating OutwardWiFiInterface %s", interfaceName)
        outwardNetworkInterface = networking.OutwardWiFiInterface(interfaceName)
      #elif re.search("^wwan[0-9]*$", interfaceName):
      #  outwardNetworkInterface = networking.OutwardGPRSInterface(interfaceName)
      else:
        self.logger.info("Creating OutwardNetworkInterface %s", interfaceName)
        outwardNetworkInterface = networking.OutwardNetworkInterface(interfaceName)

      if not self.outwardNetworkInterfaces:
        self.outwardNetworkInterfaces = []

      self.outwardNetworkInterfaces.append(outwardNetworkInterface)

  def detectNetworkInterfaces(self):
    for interfaceName in netifaces.interfaces():
      self.configureNetworkInterface(interfaceName)
    #self.logger.debug(bluetooth.read_local_bdaddr())
    #self.logger.debug(bluetooth._bluetooth.hci_devid())

  def detectNetworkInterfacesThreadImpl(self):
    while not self.terminate:
      configuredInterfaces = [ interface.interface for interface in self.inwardNetworkInterfaces ] + [ interface.interface for interface in self.outwardNetworkInterfaces ]

      interfaceNames = set(netifaces.interfaces())
      interfaceNames.remove('lo')
      interfaceNames = [x for x in interfaceNames if not x.startswith("dns")]
      interfaceNames = [x for x in interfaceNames if not x.startswith("tun")]

      for interfaceName in interfaceNames:
        if interfaceName not in configuredInterfaces:
          self.logger.info("Detected new Network Interface %s" % interfaceName)
          self.configureNetworkInterface(interfaceName)

      for interfaceName in configuredInterfaces:
        if interfaceName not in interfaceNames:
          self.logger.info("Detected removed Network Interface %s" % interfaceName)

          for inwardInterface in self.inwardNetworkInterfaces:
            if inwardInterface.interface == interfaceName:
              inwardInterface.stop()
              self.inwardNetworkInterfaces.remove(inwardInterface)

          for outwardInterface in self.outwardNetworkInterfaces:
            if outwardInterface.interface == interfaceName:
              outwardInterface.stop()
              self.outwardNetworkInterfaces.remove(outwardInterface)

      time.sleep(1)

  def connect(self, interface, type, id, credentials):
    #self.logger.info(type, id)

    matches = []
    for outwardInterface in Networking.getInstance().outwardNetworkInterfaces:
      if interface and outwardInterface.interface != interface:
        continue

      if isinstance(outwardInterface, networking.OutwardTransceiverInterface) and outwardInterface.networks:
        self.logger.debug(outwardInterface.networks)
        _matches = [network for network in outwardInterface.networks if network.get(type, None) == id]
        for _match in _matches:
          matches.append([outwardInterface, _match])
    self.logger.debug(matches)

    #ToDo Order matches by signal strength

    for match in matches:
      outwardInterface = match[0]
      match = match[1]
      self.logger.info("Web Interface: Connecting to %s (%s) using interface %s" % (match['ssid'], match['bssid'], outwardInterface.interface))
      if outwardInterface.connect(match['bssid'], match['ssid'], credentials):
        return True
    return False
