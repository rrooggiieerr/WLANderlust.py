from WLANderlust.captiveportals import CaptivePortalSolverImpl

class Failure(CaptivePortalSolverImpl):
  name = "Failure"

  # The minimum size for an unsigned int, this implementation should be first
  order = 0

  def detect(self, bssid, ssid, location = None, body = None):
    if location and not body:
      self.detectionMethod = 'contentmatch'
      return True

    return super().detect(bssid, ssid)

  def isSolvable(self, bssid, ssid, location = None, body = None):
    return False

  def solve(self, bssid, ssid, location, body):
    return self.isSolved(location, body)
