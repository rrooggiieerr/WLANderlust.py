from WLANderlust.networking import OutwardTransceiverInterface

class OutwardGPRSInterface(OutwardTransceiverInterface):
  debug = True
  type = 'mobile'

  def getNetworkInterfaceStatus(self):
    status = super().getNetworkInterfaceStatus()

    if 'status' in status:
      return status

    #ToDo GPRS specific statuses like Network provider, tower, etc

    self.status = {**self.status, **status}

    return status

  def scanImpl(self):
    return False
