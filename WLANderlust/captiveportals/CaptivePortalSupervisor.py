import logging, bottle

from WLANderlust import config
from WLANderlust.captiveportals import CurlHelper, impl

logger = logging.getLogger(__name__)

class CaptivePortalSupervisor():
  interface = None
  type = None
  captivePortalSolvers = None
  captivePortalSolver = None

  detectionURL = "http://google.com/generate_204"
  detectionResponse = "^HTTP/1.1 204 No Content"

  lastLocation = None
  lastResponse = None

  curlHelper = None

  terminate = False

  def __init__(self, interface):
    logger.info("%s: Creating Captive Portal Supervisor" % interface.interface)
    self.interface = interface

    self.detectionURL = config.get('CaptivePortal', {}).get('DetectionURL', self.detectionURL)
    self.detectionResponse = config.get('CaptivePortal', {}).get('DetectionResponse', self.detectionResponse)

    self.curlHelper = CurlHelper(interface)

    self.captivePortalSolvers = []
    for implementation in impl.getImplementations():
      logger.debug(implementation[0])
      self.captivePortalSolvers.append(implementation[1](self))

    logger.info("%s: Created Captive Portal Supervisor" % interface.interface)

  def stop(self):
    self.terminate = True

    for captivePortalSolver in self.captivePortalSolvers:
      captivePortalSolver.stop()

  def detect(self, bssid, ssid, location = None, body = None):
    captivePortalSolver = None

    if bssid:
      bssid = bssid.lower()

    for captivePortalSolver in self.captivePortalSolvers:
      #logger.debug("Detecting if Captive Portal is of type %s" % captivePortalSolver.name)

      if self.interface.interface != captivePortalSolver.supervisor.interface.interface:
        #ToDo Something strange is going on here
        logger.info("%s: %s" % (self.interface.interface, type(self.interface).__name__))
        logger.info("%s: %s" % (captivePortalSolver.supervisor.interface.interface, type(captivePortalSolver.supervisor.interface).__name__))

      if(captivePortalSolver.detect(bssid, ssid, location, body)):
        #logger.debug("Yes")
        break
      #logger.debug("No")

    logger.debug("%s: %s: Captive Portal is of type %s" % (self.interface.interface, ssid, captivePortalSolver.name))
    self.captivePortalSolver = captivePortalSolver
    return captivePortalSolver

  def hasCaptivePortal(self):
    """ Checks if we have a Captive Portal """
    bssid = None
    ssid = None

    if self.terminate:
      return False

    if self.interface.type == 'wifi':
      bssid = self.interface.bssid
      ssid = self.interface.ssid

    (self.lastLocation, self.lastResponse) = self.curlHelper.get(self.detectionURL, None, True)

    captivePortalSolver = self.detect(bssid, ssid, self.lastLocation, self.lastResponse)

    if isinstance(captivePortalSolver, impl.NotAny):
      return False

    logger.info("%s: Captive Portal detected %s" % (self.interface.interface, self.captivePortalSolver.name))

    return True

  def solve(self):
    bssid = None
    ssid = None

    if self.terminate:
      return False

    if self.interface.type == 'wifi':
      bssid = self.interface.bssid
      ssid = self.interface.ssid

    if not self.captivePortalSolver or isinstance(self.captivePortalSolver, impl.NotAny):
      logger.info("%s: No Captive Portal detected" % self.interface.interface)
    elif not self.captivePortalSolver.isSolvable(bssid, ssid, self.lastLocation, self.lastResponse):
      logger.info("%s: Captive Portal can not be solved using %s" % (self.interface.interface, self.captivePortalSolver.name))
      self.curlHelper.logResponses()
    elif self.lastLocation and self.lastResponse:
      logger.info("%s: Trying to solve Captive Portal using %s" % (self.interface.interface, self.captivePortalSolver.name))
      return self.captivePortalSolver.solve(bssid, ssid, self.lastLocation, self.lastResponse)

    return False

@bottle.get('/CaptivePortals/settings')
def getConfig():
  _config = {}

  _config['AutoSolve'] = config.get('CaptivePortal', {}).get('AutoSolve', True)

  _config['DetectionURL'] = config.get('CaptivePortal', {}).get('DetectionURL', CaptivePortalSupervisor.detectionURL)
  _config['DetectionResponse'] = config.get('CaptivePortal', {}).get('DetectionResponse', CaptivePortalSupervisor.detectionResponse)

  _config['Logging'] = config.get('CaptivePortal', {}).get('Logging', False)
  _config['LogPath'] = config.get('CaptivePortal', {}).get('LogPath', '')

  _config['captiveportals'] = []
  for implementation in impl.getImplementations():
    if implementation[1].hasConfig:
      _config['captiveportals'].append({'id': implementation[0], 'name': implementation[1].name, 'description': implementation[1].description})

  return bottle.template("CaptivePortals.tpl", _config)

@bottle.post('/CaptivePortals/settings')
def postConfig():
  autoSolve = bottle.request.forms.get('AutoSolve') == 'True'

  detectionURL = bottle.request.forms.get('DetectionURL')
  #ToDo Validate URL
  detectionResponse = bottle.request.forms.get('DetectionResponse')

  logging = bottle.request.forms.get('Logging') == 'True'
  logPath = bottle.request.forms.get('LogPath')
  #ToDo Validate path

  if 'CaptivePortal' not in config:
    config['CaptivePortal'] = {}

  config['CaptivePortal']['AutoSolve'] = autoSolve
  config['CaptivePortal']['DetectionURL'] = detectionURL
  config['CaptivePortal']['DetectionResponse'] = detectionResponse
  config['CaptivePortal']['Logging'] = logging
  config['CaptivePortal']['LogPath'] = logPath

  config.save()

  return bottle.redirect('/CaptivePortals/settings')
