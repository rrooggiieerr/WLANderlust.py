import os, threading, netifaces, time

from WLANderlust import config
from WLANderlust.networking import OutwardHardwareInterface

class OutwardTransceiverInterface(OutwardHardwareInterface):
  networks = None

  scanThread = None
  stopScanning = False
  pauseScanning = False
  sweepThread = None
  stopSweeping = False

  def start(self):
    super().start()

    if config.get('Networking', {}).get('Scan', True):
      self.startScan()

  def stop(self):
    super().stop();

    self.stopScan()
    self.stopSweep()

  def scanImpl(self):
    return False

  def scan(self):
    if self.down:
      self.logger.warning("Interface is down, not scanning")
      return False

    if os.geteuid() == 0 and not self.scanThread or not config.get('Networking', {}).get('Scan', True):
      self.logger.info("Start scan")
      results = self.scanImpl()
      self.logger.info("Finished scan")
      return results

    return False

  def startScan(self):
    if self.down:
      self.logger.warning("Interface is down, not scanning")
      return False

    if os.geteuid() == 0:
      self.logger.info("Start scanning")
      self.stopScanning = False
      self.scanThread = threading.Thread(target = self.scanThreadImpl, name = "%s scan thread" % self.interface)
      self.scanThread.start()
      return True

    return False

  def stopScan(self):
    if self.scanThread:
      self.logger.info("Stop scanning")
      self.stopScanning = True
      self.scanThread.join()
      return True

    return False

  def scanThreadImpl(self):
    self.logger.info("Starting scan thread")

    while not self.stopScanning:
      if self.interface not in netifaces.interfaces():
        break

      if self.pauseScanning:
        self.logger.debug("Pause scanning")
        time.sleep(0.1)
        continue

      self.scanImpl()

    self.logger.info("Stopped scan thread")

  def startSweep(self):
    if self.down:
      self.logger.warning("Interface is down, not scanning")
      return False

    if os.geteuid() == 0 and not self.sweepThread:
      self.logger.info("Start sweep")
      self.stopScanning = True
      self.stopSweeping = False
      self.sweepThread = threading.Thread(target = self.sweepThreadImpl, name = "%s sweep thread" % self.interface)
      self.sweepThread.start()
      return True

    return False

  def stopSweep(self):
    if self.sweepThread:
      self.logger.info("Stop sweep")
      self.stopSweeping = True
      self.sweepThread.join()
      return True

    return False

  def sweepImpl(self):
    return False

  def sweepThreadImpl(self):
    self.logger.info("Started sweep thread")
    self.pauseScanning = True

    self.sweepImpl()

    self.pauseScanning = False
    self.logger.info("Stopped sweep thread")

  def connect(self, id, credentials):
    return False
