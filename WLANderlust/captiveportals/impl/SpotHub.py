from WLANderlust.captiveportals import CaptivePortalSolverImpl

# I think I have seen this type of Captive Portal only once
class SpotHub(CaptivePortalSolverImpl):
  name = "SpotHub"

  def detect(self, bssid, ssid, location = None, body = None):
    if body:
      if re.search("spothub.io", location):
        self.detectionMethod = 'contentmatch'
        if bssid:
          CaptivePortalSolverCache.getCache().store(bssid, type(self).__name__)
        return True
    else:
      return super().detect(bssid, ssid)

  def solve(self, bssid, ssid, location, body):
    # Placeholder for future implementation
    return False
