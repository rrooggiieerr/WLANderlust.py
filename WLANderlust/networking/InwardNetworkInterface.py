import os, threading, subprocess, socket, fcntl, struct, bottle

from WLANderlust import MyWSGIServer, MySSLWSGIServer
from WLANderlust.networking import NetworkInterface

class InwardNetworkInterface(NetworkInterface):
  webServer = None
  webInterfaceThread = None
  sslWebServer = None
  sslWebInterfaceThread = None
  captivePortal = False

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
    super().start()

    # Start a Web Interface on the interface
    ip = self.getIP()
    if ip['ipaddress']:
      self.startCaptivePortal()

      self.logger.info("Starting Web Interface")
      port = 8080
      if os.geteuid() == 0:
        port = 80
      self.webServer = MyWSGIServer(host=ip['ipaddress'], port=port)
      self.webInterfaceThread = threading.Thread(target = bottle.run, kwargs=dict(server = self.webServer, quiet = True), name = "Web Interface on %s" % self.interface)
      self.webInterfaceThread.start()
      self.logger.info("Started Web Interface")

      self.logger.info("Starting SSL Web Interface")
      port = 8443
      if os.geteuid() == 0:
        port = 443
      self.sslWebServer = MySSLWSGIServer(host=ip['ipaddress'], port=port)
      self.sslWebInterfaceThread = threading.Thread(target = bottle.run, kwargs=dict(server = self.sslWebServer, quiet = True), name = "SSL Web Interface on %s" % self.interface)
      self.sslWebInterfaceThread.start()
      self.logger.info("Started SSL Web Interface")

  def stop(self):
    super().stop()

    self.stopCaptivePortal()

    if self.sslWebServer:
      self.logger.info("Stopping SSL Web Interface")
      self.sslWebServer.stop()
      self.sslWebInterfaceThread.join()
      self.logger.info("Stopped SSL Web Interface")

    if self.webServer:
      self.logger.info("Stopping Web Interface")
      self.webServer.stop()
      self.webInterfaceThread.join()
      self.logger.info("Stopped Web Interface")

  def startCaptivePortal(self):
    if self.captivePortal:
      return False
    self.captivePortal = True

    self.logger.info("Starting Captive Portal")
    # Create /etc/dnsmasq.d/captiveportal
    #with open('/etc/dnsmasq.d/%s-captiveportal' % self.interface, 'w') as f:
    #  f.write('except-interface=wlan1\n')
    #  #f.write('except-interface=wlan1\n'  % self.interface)
    #  f.write('address=/#/%s' % self.status['ipaddress'])
    #subprocess.run(['/bin/systemctl', 'restart', 'dnsmasq'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ##print("AA")
    ##subprocess.run(['/sbin/iptables', '-N', self.interface + '-captiveportal'])
    ##print("AB")
    ##subprocess.run(['/sbin/iptables', '-F', self.interface + '-captiveportal'])
    ##print("AC")
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-N', self.interface + '-captiveportal'])
    ##print("AD")
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-F', self.interface + '-captiveportal'])
    ##print("AE")
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-I', 'OUTPUT', '1', '-j', self.interface + '-captiveportal'])
    ##print("AF")
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-I', 'PREROUTING', '1', '-j', self.interface + '-captiveportal'])
    ##print("AG")
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-A', self.interface + '-captiveportal', '-i', self.interface, '-p', 'tcp', '-s', self.status['ipaddress'] + '/24', '--dport', '80', '-j', 'DNAT', '--to-destination', self.status['ipaddress']])
    ##print("AH")
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-A', self.interface + '-captiveportal', '-i', self.interface, '-p', 'tcp', '-s', self.status['ipaddress'] + '/24', '--dport', '443', '-j', 'DNAT', '--to-destination', self.status['ipaddress']])

    #print("BA")
    subprocess.run(['/sbin/iptables', '-N', self.interface + '-captiveportal'])
    #print("BB")
    subprocess.run(['/sbin/iptables', '-F', self.interface + '-captiveportal'])
    ##print("BC")
    ##subprocess.run(['/sbin/iptables', '-I', 'OUTPUT', '1', '-j', self.interface + '-captiveportal'])
    #print("BD")
    subprocess.run(['/sbin/iptables', '-I', 'INPUT', '1', '-j', self.interface + '-captiveportal'])
    ##print("BE")
    ##subprocess.run(['/sbin/iptables', '-A', self.interface + '-captiveportal', '-i', self.interface, '-p', 'tcp', '-s', self.status['ipaddress'] + '/24', '--dport', '80', '-j', 'DROP'])
    #print("BF")
    ##subprocess.run(['/sbin/iptables', '-A', self.interface + '-captiveportal', '-i', self.interface, '-p', 'tcp', '-s', self.status['ipaddress'] + '/24', '--dport', '80', '-m', 'string', '--algo', 'bm', '--string', 'Host: ozofbxoehgs', '-j', 'DROP'])
    ##subprocess.run(['/sbin/iptables', '-A', self.interface + '-captiveportal', '-i', self.interface, '-p', 'tcp', '-s', self.status['ipaddress'] + '/24', '--dport', '80', '-j', 'DROP'])

    self.logger.info("Started Captive Portal")

    return True

  def stopCaptivePortal(self):
    if not self.captivePortal:
      return False
    self.captivePortal = False

    self.logger.info("Stopping Captive Portal")
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-D', 'PREROUTING', '-j', self.interface + '-captiveportal'])
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-D', 'OUTPUT', '-j', self.interface + '-captiveportal'])
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-F', self.interface + '-captiveportal'])
    ##subprocess.run(['/sbin/iptables', '-t', 'nat', '-X', self.interface + '-captiveportal'])

    #print("DA")
    subprocess.run(['/sbin/iptables', '-D', 'INPUT', '-j', self.interface + '-captiveportal'])
    ##print("DB")
    ##subprocess.run(['/sbin/iptables', '-D', 'OUTPUT', '-j', self.interface + '-captiveportal'])
    #print("DC")
    subprocess.run(['/sbin/iptables', '-F', self.interface + '-captiveportal'])
    #print("DD")
    subprocess.run(['/sbin/iptables', '-X', self.interface + '-captiveportal'])

    if os.path.exists('/etc/dnsmasq.d/%s-captiveportal' % self.interface):
      #ToDo Empty file instead of delete
      os.remove('/etc/dnsmasq.d/%s-captiveportal' % self.interface)
      subprocess.run(['/bin/systemctl', 'restart', 'dnsmasq'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    self.logger.info("Stopped Captive Portal")

    return True

  def Firewall(self):
    return False
