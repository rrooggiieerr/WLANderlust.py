import os, threading, subprocess, netifaces, wifi, re, time

from WLANderlust import config, BSSIDLocationCache, GPS, captiveportals, CredentialsStore
from WLANderlust.plugins import Plugins
from WLANderlust.networking import OutwardTransceiverInterface, inwardBSSIDs
from .Networking import Networking

class OutwardWiFiInterface(OutwardTransceiverInterface):
  debug = False
  type = 'wifi'

  ap = None

  configuredAPs = None

  bssid = None
  ssid = None

  reassociateThread = None

  def __init__(self, interface):
    super().__init__(interface)

    #ToDo Check if this is the onboard Raspberry Pi Zero WiFi

  def setAP(self, ap):
    self.ap = ap

  def start(self):
    self.logger.info("Starting WLANderlust controller for outward WiFi interface")

    if os.geteuid() == 0:
      _interfacesFile = '/etc/network/interfaces.d/' + self.interface
      if not os.path.isfile(_interfacesFile):
        self.logger.warning("Interfaces.d file missing")
        if config.get('Networking', {}).get('CreateInterfacesdFile', False):
          self.logger.info("Creating interfaces.d file")
        #  #subprocess.run(['/sbin/ifconfig', self.interface, 'down'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #  #subprocess.run(['/sbin/ifconfig', self.interface, 'down'])
          completed = subprocess.run(['/sbin/ifdown', '--force', self.interface])
          if not completed.returncode == 0:
            subprocess.run(['/sbin/ifconfig', self.interface, 'down'])

          with open(_interfacesFile, 'w') as f:
            f.write('''allow-hotplug %s
iface %s inet manual
	wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf''' % (self.interface, self.interface))
            f.close()
        #  #subprocess.run(['/sbin/ifup', self.interface], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
          subprocess.run(['/sbin/ifup', self.interface])

    super().start()

    if os.geteuid() == 0:
      self.reassociateThread = threading.Thread(target = self.reassociateThreadImpl, name = "%s reassociate WiFi thread")
      self.reassociateThread.start()

    self.logger.info("Started WLANderlust controller for outward WiFi interface")

  def stop(self):
    super().stop();

    if self.reassociateThread:
      self.reassociateThread.join()

  def getNetworkInterfaceStatus(self):
    status = super().getNetworkInterfaceStatus()

    if 'status' in status:
      return status

    bssid = None
    ssid = None

    # Check if we are connected to an AP
    if not os.path.isfile("/sbin/iw"):
      status['status'] = 'notools'
      return status

    proc = subprocess.Popen(['/sbin/iw', 'dev', self.interface, 'link'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    proc.wait()
    output = proc.stdout.read().decode().strip()
    proc.stdout.close()

    if output == "Not connected.":
      if self.status.get('status', None) != 'notconnected': self.logger.warning("Not connected to a WiFi")
      status['status'] = 'notconnected'
      return status

    try:
      bssid = re.compile("^Connected to (.*) \(on %s\)$" % self.interface, re.MULTILINE).search(output).group(1)
      ssid = re.compile("^\tSSID: (.*)$", re.MULTILINE).search(output).group(1)
      status['frequency'] = int(re.compile("^\tfreq: (.*)$", re.MULTILINE).search(output).group(1))
      frequencychannelmap = {2412: 1, 2417: 2, 2422: 3, 2427: 4, 2432: 5, 2437: 6, 2442: 7, 2447: 8, 2452: 9, 2457: 10, 2462: 11, 2467: 12, 2472: 13, 2484: 14}
      status['channel'] = frequencychannelmap[status['frequency']]
      status['rx'] = None
      status['tx'] = None
      status['signal'] = re.compile("^\tsignal: (.*) dBm$", re.MULTILINE).search(output).group(1)
      if self.bssid != bssid:
        self.logger.info("Connected to a WiFi %s (%s)" % (ssid, bssid))
    except Exception as e:
      status['status'] = 'exception'
      self.logger.error(e)
      self.logger.debug("/sbin/iw dev %s link" % self.interface)
      self.logger.debug(output)

    status['bssid'] = bssid
    self.bssid = bssid
    status['ssid'] = ssid
    self.ssid = ssid

    self.status = {**self.status, **status}

    return status

  def getConfiguredAPs(self):
    if self.configuredAPs == None:
      self.configuredAPs = []
      proc = subprocess.Popen(['/sbin/wpa_cli', '-i', self.interface, 'list_networks'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      proc.wait()
      output = proc.stdout.read().decode()
      proc.stdout.close()
      self.configuredAPs = re.findall("^([0-9]*)\t([^\t]*)\t([^\t]*)\t(.*)", output, re.MULTILINE)

    return self.configuredAPs

  def configureAP(self, bssid, ssid, credentials, save = True):
    if not ssid:
      return False

    #ToDo Check if network is not ready configured

    self.logger.debug("add_network")
    completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'add_network'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if completed.returncode != 0: return False

    networkID = completed.stdout.decode().strip()
    self.logger.debug("Network ID: %s", networkID)

    if bssid:
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'bssid', bssid], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      if completed.returncode != 0 or completed.stdout.decode().strip() != 'OK': return False
    completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'ssid', '"' + ssid + '"'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if completed.returncode != 0 or completed.stdout.decode().strip() != 'OK': return False

    if not credentials:
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'key_mgmt', 'NONE'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      if completed.returncode != 0 or completed.stdout.decode().strip() != 'OK': return False
    elif 'wpapassphrase' in credentials:
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'psk', '"' + credentials['wpapassphrase'] + '"'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      if completed.returncode != 0 or completed.stdout.decode().strip() != 'OK': return False
    elif 'wpa2passphrase' in credentials:
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'psk', '"' + credentials['wpa2passphrase'] + '"'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      if completed.returncode != 0 or completed.stdout.decode().strip() != 'OK': return False
    elif 'wepkey0' in credentials:
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'key_mgmt', 'NONE'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'wep_key0', '"' + credentials['wepkey0'] + '"'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'wep_key1', '"' + credentials['wepkey1'] + '"'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'wep_key2', '"' + credentials['wepkey2'] + '"'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'wep_key3', '"' + credentials['wepkey3'] + '"'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      if completed.returncode != 0 or completed.stdout.decode().strip() != 'OK': return False
    else:
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'remove_network', networkID], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      return False
    completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'set_network', networkID, 'priority', '50'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if completed.returncode != 0 or completed.stdout.decode().strip() != 'OK': return False
    if save:
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'save_config'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      if completed.returncode != 0 or completed.stdout.decode().strip() != 'OK': return False

      self.configuredAPs = None
      self.getConfiguredAPs()

      return True

    return networkID

    entry = """
network={
	ssid="%s"
	key_mgmt=NONE
	priority=50
}
""" % ssid

  def scanImpl(self):
    # Scan for WiFi APs
    networks = []
    cells = None
    try:
      #self.logger.debug("%s %s: Scanning for APs" % (threading.get_ident(), self.interface))
      self.logger.debug("Scanning for APs")
      cells = wifi.Cell.all(self.interface)
      self.logger.debug("Finished scanning for APs")
      #self.logger.debug(len(cells))
    except wifi.exceptions.InterfaceError as e:
      if self.stopScanning:
        self.logger.warning("Canceled scanning for APs")
        return False
      #else:
      #  raise e

    configuredAPs = self.getConfiguredAPs()

    if self.terminate:
      return False

    if cells:
      # Process detected WiFi APsP
      # Remove own AP from scan results
      self.logger.debug("Inward BSSIDs: %s" % inwardBSSIDs)
      cells = [cell for cell in cells if not cell.address.upper() in inwardBSSIDs]

      # Lowercase the BSSID
      for cell in cells:
        cell.address = cell.address.lower()

      Plugins.getInstance().rawScanResults(self, cells)

      # Look up location of the Access Point
      for cell in cells:
        cell.location = BSSIDLocationCache.getCache().lookup(cell.address, cell.signal)
        # Calculate distance to Access Point
        cell.distance = GPS.getInstance().distance(cell.location)

      GPS.getInstance().scanResults(self, cells)

      # Only Master mode Access Points
      cells = [cell for cell in cells if cell.mode == 'Master']
      #ToDo Maybe support other modes? Which modes are there?
      #cells = [cell for cell in cells if cell.mode in ['Master']]

      # Remove hidden SSIDs
      cells = [cell for cell in cells if not cell.ssid.startswith('\\x00')]
      # Remove empty SSIDs
      cells = [cell for cell in cells if not cell.ssid == '']

      # Sort the APs on signal strength
      cells.sort(key=lambda cell: cell.signal, reverse=True)

      # Remove duplicate SSIDs
      seenSSIDs = []
      duplicateSSIDs = []
      _cells = cells
      cells = []
      for cell in _cells:
        if cell.ssid not in seenSSIDs:
          cells.append(cell)
          seenSSIDs.append(cell.ssid)
        else:
          self.logger.debug("Skipping %s" % cell)
          duplicateSSIDs.append(cell.ssid)

      # Remove BSSIDs from duplicate SSIDs
      for cell in cells:
        if cell.ssid in duplicateSSIDs:
          cell.address = None

      for cell in cells:
        if cell.ssid.startswith(r'\x'):
          ssid = cell.ssid
          ssid = ssid.replace(r'\x', '')
          ssid = bytes.fromhex(ssid)
          ssid = ssid.decode('utf-8')
          cell.ssid = ssid

      for cell in cells:
        captivePortal = None

        #if self.captivePortalSupervisor:
        captivePortalSolver = self.captivePortalSupervisor.detect(cell.address, cell.ssid)
        #else:
        #  captivePortalSolver = captiveportals.impl.Unknown(None)

        if captivePortalSolver:
          captivePortal = {}
          if cell.encrypted and isinstance(captivePortalSolver, captiveportals.impl.Unknown):
            captivePortalSolver = captiveportals.impl.NotAny(self.captivePortalSupervisor)
            captivePortalSolver.detectionMethod = 'guess'
          captivePortal['status'] = captivePortalSolver.status
          captivePortal['type'] = captivePortalSolver.name
          captivePortal['detectionMethod'] = captivePortalSolver.detectionMethod
          captivePortal['solvable'] = captivePortalSolver.isSolvable(cell.address, cell.ssid)

        known = False
        if cell.ssid in [ap[1] for ap in self.getConfiguredAPs()]:
          known = True

        encryption = { 'status': 'none' }
        if cell.encrypted:
          encryption = { 'status': 'encrypted', 'type': cell.encryption_type }
        networks.append({'bssid': cell.address,
          'ssid': cell.ssid,
          'encryption': encryption,
          'channel': cell.channel,
          'signal': cell.signal,
          'quality': cell.quality,
          'location': cell.location,
          'distance': cell.distance,
          'captiveportal': captivePortal,
          'known': known})

        #self.logger.debug("%s %-20s %-5s %-10s %2s %s %s %s" % 
        #  (cell.address, cell.ssid, cell.encrypted, captivePortal['type'], cell.channel, cell.signal, cell.quality, (cell.distance * 1000) if cell.distance else "unknown"))

      Plugins.getInstance().scanResults(self, cells)

      self.networks = networks
      return networks

  def sweepImpl(self):
    self.pauseIsOnlineThread = True
    self.pauseScanning = True
    Networking.getInstance().registerOffline(self)

    networks = self.scanImpl()

    for network in networks:
      if self.stopSweeping:
        break
      bssid = network.get('bssid', None)
      ssid = network.get('ssid', None)

      # Is the Access Point we want to connect to encrypted?
      encrypted = network['encryption']['status'] != 'none'
    
      # Check if the Access Point we want to connect to is allready configured
      match = self.getAPFromConfiguredAPs(bssid, ssid)
      if match:
        id = match[0]
      else:
        credentials = None
        if encrypted:
          if bssid:
            credentials = CredentialsStore.getStore().getCredentials(bssid, None, None)
          if not credentials and ssid:
            credentials = CredentialsStore.getStore().getCredentials(None, ssid, None)
          if not credentials:
            continue
          self.logger.debug("Credentials: %s" % credentials)

        id = self.configureAP(bssid, ssid, credentials, False)

      if not id:
        continue

      self.logger.debug("Investigating network %s (%s)" % (ssid, bssid))
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'select_network', id], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      if not (completed.returncode == 0 and completed.stdout.decode().strip() == 'OK'):
        self.logger.warning("Failed to join network %s (%s)" % (ssid, bssid))
        continue

      # Check if we are successfully connected to the Access Point
      for i in range(100):
        if self.stopSweeping:
          break
        time.sleep(1)
        status = self.getStatus()
        if (bssid and status.get('bssid', None) == bssid) or (ssid and status.get('ssid', None) == ssid):
          break
      if self.stopSweeping:
        break

      self.logger.debug("Network Interface Status: %s" % status)
      if not((bssid and status.get('bssid', None) == bssid) or (ssid and status.get('ssid', None) == ssid)):
        self.logger.error("Failed to join network %s (%s)" % (ssid, bssid))
        continue

      self.logger.info("Joined network %s (%s)" % (ssid, bssid))
      for i in range(100):
        if self.stopSweeping:
          break
        time.sleep(1)
        status = self.getStatus()
        if self.isOnline():
          break
      if self.stopSweeping:
        break

  def getAPFromConfiguredAPs(self, bssid, ssid):
    if bssid:
      match = [ap for ap in self.getConfiguredAPs() if ap[2] == bssid]
      if not match or len(match) == 0:
        match = None
      elif len(match) == 1:
        return match[0]
      else:
        return False

    if ssid:
      match = [ap for ap in self.getConfiguredAPs() if ap[1] == ssid]
      if not match or len(match) == 0:
        match = None
      elif len(match) == 1:
        return match[0]
      else:
        return False

    return None

  def connect(self, bssid = None, ssid = None, credentials = None):
    self.logger.debug("connect(%s, %s, ...)" % (bssid, ssid))

    # Get the Access Point we want to connect to
    ap = [ap for ap in self.networks if ap['bssid'] == bssid and ap['ssid'] == ssid]
    if len(ap) != 1:
      return False
    ap = ap[0]
    self.logger.debug("AP: %s" % ap)

    # Check if we currently are connected to the Access Point we want to connect to
    if self.online and (self.bssid == ap['bssid'] or self.ssid == ap['ssid']):
      self.logger.warning("Already joined network %s (%s)" % (ap['ssid'], ap['bssid']))
      return True

    # Is the Access Point we want to connect to encrypted?
    encrypted = ap['encryption']['status'] != 'none'
    self.logger.debug("Encrypted: %s" % encrypted)
    
    # Check if the Access Point we want to connect to is allready configured
    match = self.getAPFromConfiguredAPs(bssid, ssid)

    # If the Access Point we want to connect to is already configured connect to it
    if match:
      self.pauseIsOnlineThread = True
      self.pauseScanning = True
      Networking.getInstance().registerOffline(self)

      self.logger.info("Joining network %s (%s)" % (match[1], match[2]))
      success = False
      completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'select_network', match[0]], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
      if completed.returncode == 0 and completed.stdout.decode().strip() == 'OK':
        self.logger.info("Joined network %s (%s)" % (match[1], match[2]))
        success = True
      else:
        self.logger.error("Failed to join network %s (%s)" % (match[1], match[2]))

      self.pauseScanning = False
      self.pauseIsOnlineThread = False

      return success

    # If the Access Point we want to connect to is not yet configured, is encrypted and no credentials are given
    # try to get the required credentials from the Credentials Store
    if encrypted and not credentials:
      if bssid:
        credentials = CredentialsStore.getStore().getCredentials(bssid, None, None)
      if not credentials and ssid:
        credentials = CredentialsStore.getStore().getCredentials(None, ssid, None)
      self.logger.debug("Credentials: %s" % credentials)
    if encrypted and not credentials:
      self.logger.warning("Network %s (%s) not configured" % (ssid, bssid))
      return False

    # If the Access Point we want to connect to is not yet configured but is not encrypted or we have the required credentials
    # configure the Access Point
    if not encrypted or credentials:
      id = self.configureAP(bssid, ssid, credentials, False)
      success = False
      if id:
        # Try to connect to the just configured Access Point
        Networking.getInstance().registerOffline(self)
        self.pauseIsOnlineThread = True
        self.pauseScanning = True

        completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'select_network', id], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if completed.returncode == 0 and completed.stdout.decode().strip() == 'OK':
          # Check if we are successfully connected to the Access Point
          for i in range(20):
            if self.terminate:
              break
            time.sleep(0.1)
            status = self.getStatus()
            if (bssid and status.get('bssid', None) == bssid) or (ssid and status.get('ssid', None) == ssid):
              break

          self.logger.debug("Network Interface Status: %s" % status)
          if (bssid and status.get('bssid', None) == bssid) or (ssid and status.get('ssid', None) == ssid):
            self.logger.info("Joining network %s (%s)" % (ssid, bssid))
            completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'save_config'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            if completed.returncode == 0 and completed.stdout.decode().strip() == 'OK':
              self.logger.info("Joined network %s (%s)" % (ssid, bssid))
              success = True

        self.pauseScanning = False
        self.pauseIsOnlineThread = False

      if not success:
        self.logger.error("Failed to join network %s (%s)" % (ssid, bssid))
        completed = subprocess.run(['/sbin/wpa_cli', '-i', self.interface, 'remove_network', id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      self.configuredAPs = None
      self.getConfiguredAPs()

      return success

  def reassociate(self):
    self.logger.info("Reassociating...")

    for ap in self.networks:
      if self.terminate:
        break

      if self.connect(ap['bssid'], ap['ssid']):
        # Check if we are successfully connected to the Access Point
        for i in range(300):
          if self.terminate:
            break
          time.sleep(0.1)
          if self.online:
            return True

    return False

  def reassociateThreadImpl(self):
    self.logger.info("Starting reassociate thread")

    while not self.terminate:
      if self.interface not in netifaces.interfaces():
        break

      if not config.get('Networking', {}).get('AutoReassociateWiFi', False):
        time.sleep(0.1)
        continue

      if self.online:
        time.sleep(0.1)
        continue

      if self.networks == None:
        time.sleep(0.1)
        continue

      self.reassociate()

    self.logger.info("Stopped reassociate thread")
