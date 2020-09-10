from WLANderlust.captiveportals import CaptivePortalSolverImpl, CaptivePortalSolverCache

class NotAny(CaptivePortalSolverImpl):
  name = "None"
  # The minimum size for an unsigned int, this implementation should be first
  order = 1
  status = 'solved'

  def detect(self, bssid, ssid, location = None, body = None):
    if location and body:
      if self.isSolved(location, body):
        self.detectionMethod = 'contentmatch'
        if bssid:
          CaptivePortalSolverCache.getCache().store(bssid, type(self).__name__)
        return True
      return False

    return super().detect(bssid, ssid)

  def isSolvable(self, bssid, ssid, location = None, body = None):
    return True

  def solve(self, bssid, ssid, location, body):
    return self.isSolved(location, body)
