import bluetooth

from WLANderlust.networking import OutwardTransceiverInterface

class OutwardBluetoothInterface(OutwardTransceiverInterface):
  debug = True
  type = 'bluetooth'

  def getNetworkInterfaceStatus(self):
    status = super().getNetworkInterfaceStatus()

    if 'status' in status:
      return status

    #ToDo Bluetooth specific statuses

    self.status = {**self.status, **status}

    return status

  def scanImpl(self):
    return False
