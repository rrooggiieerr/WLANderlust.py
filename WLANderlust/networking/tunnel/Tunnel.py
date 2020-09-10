import time, logging

from WLANderlust.networking import OutwardNetworkInterface

class Tunnel(OutwardNetworkInterface):
  name = None
  type = 'tunnel'

  parentInterface = None
  credentials = None

  server = None

  def __init__(self, parentInterface, credentials):
    super().__init__()

    self.logger = logging.getLogger("%s(%s)" % (self.__class__.__name__, parentInterface.interface))

    self.parentInterface = parentInterface
    self.credentials = credentials

  def install(self):
    return True

  def isConfigured(self):
    return False

  def getNetworkInterfaceStatus(self):
    status = super().getNetworkInterfaceStatus()

    if 'status' in status:
      return status

    status['server'] = self.server

    self.status = {**self.status, **status}

    return status

  def isOnlineThreadImpl(self):
    while not self.terminate:
      if not self.isOnline():
        time.sleep(0.1)
        continue

      while not self.terminate and self.isStillOnline():
        for i in range(50):
          if self.terminate:
            break
          time.sleep(0.1)
