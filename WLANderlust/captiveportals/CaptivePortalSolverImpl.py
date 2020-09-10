import re

from WLANderlust import config
from WLANderlust.captiveportals import CaptivePortalSolverCache

class CaptivePortalSolverImpl():
  name = 'Unknown'
  description = ''
  order = 256
  ssids = None
  hasConfig = False
  ipOverDNSFriendly = False

  detectionURL = "http://google.com/generate_204"
  detectionResponse = "^HTTP/1.1 204 No Content"

  supervisor = None
  detectionMethod = None
  status = 'present'

  terminate = False

  def __init__(self, supervisor):
    self.supervisor = supervisor

  def stop(self):
    self.termiante = True

  def detect(self, bssid, ssid, location = None, body = None):
    if self.ssids and ssid in self.ssids:
      self.detectionMethod = 'ssidmatch'
      return True

    if bssid and CaptivePortalSolverCache.getCache().lookup(bssid) == type(self).__name__:
      self.detectionMethod = 'cache'
      return True

    return False

  def isSolvable(self, bssid, ssid, location = None, body = None):
    return self.isSolved(location, body)

  def solve(self, bssid, ssid, location, body):
    return self.isSolved(location, body)

  def isSolved(self, location = None, body = None):
    if location and body:
      self.detectionURL = config.get('CaptivePortal', {}).get('DetectionURL', self.detectionURL)
      self.detectionResponse = config.get('CaptivePortal', {}).get('DetectionResponse', self.detectionResponse)

      if location and location == self.detectionURL and body and re.compile(self.detectionResponse, re.MULTILINE).search(body):
        self.status = 'solved'
        return True

    return False
