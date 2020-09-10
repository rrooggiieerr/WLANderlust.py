import os, subprocess, netifaces, re

from WLANderlust.networking import InwardNetworkInterface

inwardBSSIDs = []

class InwardWiFiInterface(InwardNetworkInterface):
  debug = True
  type = 'wifi'

  hostAPMethod = None

  def __init__(self, interface):
    super().__init__(interface)

    self.status = self.getStatus()

  def start(self):
    self.logger.info("Starting WLANderlust controller for inward WiFi interface")
    super().start()
    self.logger.info("Started WLANderlust controller for inward WiFi interface")

  def getNetworkInterfaceStatus(self):
    global inwardBSSIDs
    status = super().getNetworkInterfaceStatus()

    # Get the MAC address
    #if netifaces.AF_LINK in netifaces.ifaddresses(self.interface):
    #  status['bssid'] = netifaces.ifaddresses(self.interface)[netifaces.AF_LINK][0]['addr'].upper()
    #  inwardBSSIDs.append(status['bssid'])
    #  self.logger.debug("Inward BSSIDs %s" % inwardBSSIDs)

    if os.path.isfile('/sbin/iw') and os.access('/sbin/iw', os.X_OK):
      proc = subprocess.Popen(['/sbin/iw', 'dev', self.interface, 'info'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      proc.wait()
      output = proc.stdout.read().decode()
      proc.stdout.close()

      status['bssid'] = re.compile("^\taddr (.+)$", re.MULTILINE).search(output).group(1).upper()
      inwardBSSIDs.append(status['bssid'])
      self.logger.debug("Inward BSSIDs %s" % inwardBSSIDs)
      match = re.compile("^\tssid (.+)$", re.MULTILINE).search(output)
      if match:
        status['ssid'] = match.group(1)
      match = re.compile("^\tchannel ([0-9]+) .*$", re.MULTILINE).search(output)
      if match:
        status['channel'] = match.group(1)
      match = re.compile("^\ttxpower ([0-9.]+) dBm$", re.MULTILINE).search(output)
      if match:
        status['txpower'] = match.group(1)

    if os.path.exists('/etc/hostapd/hostapd.conf'):
      with open('/etc/hostapd/hostapd.conf', 'r') as f:
        _config = f.read()
        f.close()
        _interface = re.compile("^interface=(.*)$", re.MULTILINE).search(_config).group(1)

        if _interface == self.interface:
          self.hostAPMethod = 'hostapd'

          #status['ssid'] = re.compile("^ssid=(.*)$", re.MULTILINE).search(_config).group(1)
          #status['channel'] = re.compile("^channel=(.*)$", re.MULTILINE).search(_config).group(1)

    if not self.hostAPMethod and os.path.exists('/etc/network/interfaces.d/' + self.interface):
      with open('/etc/network/interfaces.d/' + self.interface, 'r') as f:
        _config = f.read()
        f.close()
        _interface = re.compile("^iface\s+([^\s]+)\s+.*$", re.MULTILINE).search(_config).group(1)

        if _interface == self.interface:
          wpaConf = re.compile("^\s*wpa-conf ([^\s]+)$", re.MULTILINE).search(_config).group(1)

      with open(wpaConf, 'r') as f:
        _config = f.read()
        f.close()
        if re.compile("^\s*mode=2$", re.MULTILINE).search(_config):
          self.hostAPMethod = 'wpa_supplicant'

          #status['ssid'] = re.compile("^\s*ssid=\"(.*)\"$", re.MULTILINE).search(_config).group(1)
          #frequency = re.compile("^\s*frequency=(.*)$", re.MULTILINE).search(_config).group(1)

    return status

  def changeChannel(self, channel):
    if not config.get('WLANderlust', {}).get('AutoSwitchHostAPChannel', False):
      return False
    if not channel:
      return False

    if self.hostAPMethod == 'hostapd':
      if not os.path.isfile('/etc/hostapd/hostapd.conf'):
        return False

      # Read the contents if hostapd.conf in a variable
      f = open('/etc/hostapd/hostapd.conf', 'r')
      hostAPConf = f.read()
      f.close()
      currentChannel = int(re.compile("^channel=(.*)$", re.MULTILINE).search(hostAPConf).group(1))
      if channel == currentChannel:
        return False

      # Change channel in hostapd.conf
      self.logger.info("Changing channel of the Host Access Point from %s to %s" % (currentChannel, channel))
      hostAPConf = re.compile("^channel=.*$", re.MULTILINE).sub("channel=%s" % channel, hostAPConf)
      open('/etc/hostapd/hostapd.conf', 'w').write(hostAPConf)

      # restart hostapd
      self.logger.info("Restarting Host AP daemon")
      subprocess.run(['service', 'hostapd', 'stop' ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      subprocess.run(['service', 'hostapd', 'start'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      #self.status['channel'] = channel
      self.status = self.getStatus()

      return True

    if self.hostAPMethod == 'wpa_supplicant':
      return False
