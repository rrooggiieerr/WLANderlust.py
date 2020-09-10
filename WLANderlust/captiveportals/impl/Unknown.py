from WLANderlust.captiveportals import CaptivePortalSolverImpl

class Unknown(CaptivePortalSolverImpl):
  name = "Unknown"

  # The max size for an unsigned int, this implementation should be last
  order = 65535

  def detect(self, bssid, ssid, location = None, body = None):
    return True
