import os

from WLANderlust.networking import InwardNetworkInterface

class InwardEthernetInterface(InwardNetworkInterface):
  type = 'wired'

  def getNetworkInterfaceStatus(self):
    status = super().getNetworkInterfaceStatus()

    if 'status' in status:
      return status

    # Check if cable is connected
    operstateFile = "/sys/class/net/%s/operstate" % self.interface
    if os.path.isfile(operstateFile):
      with open(operstateFile) as f:
        operstate = f.read().strip()
        f.close()
        if operstate == 'down':
          if self.status.get('status', None) != 'nocable': self.logger.warning("Cable not connected")
          status['status'] = 'nocable'
        else: self.logger.debug("Cable connected")

    self.status = {**self.status, **status}

    return status
