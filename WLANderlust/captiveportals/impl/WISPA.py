import re, logging

from WLANderlust.captiveportals import CaptivePortalSolverImpl, CaptivePortalSolverCache

logger = logging.getLogger(__name__)

class WISPA(CaptivePortalSolverImpl):
  name = "WISPA"
  order = 1000

  def detect(self, bssid, ssid, location = None, body = None):
    if body:
      if re.search("<WISPAccessGatewayParam", body, re.MULTILINE):
        logger.warning('WISPA not yet implemented')
        #self.detectionMethod = 'contentmatch'
        #if bssid:
        #  CaptivePortalSolverCache.getCache().store(bssid, type(self).__name__)
        #return True
      return False
    else:
      return super().detect(bssid, ssid)
