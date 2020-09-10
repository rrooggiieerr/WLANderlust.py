import re, logging, bottle

from WLANderlust import config
from WLANderlust.captiveportals import CaptivePortalSolverImpl
from WLANderlust import CredentialsStore

logger = logging.getLogger(__name__)

class Fon(CaptivePortalSolverImpl):
  name = "Fon"

  # List of SSIDs associated with the Fon network
  # Probably not complete
  # Retrieved from https://wigle.net/stats#ssidstats
  #ssids = ['BTWiFi-with-FON', 'COSMOTE WiFi Fon', 'Fon', 'FON_BELGACOM', 'FON_MTS', 'Fon WiFi', 'KPN Fon', 'NOS_WIFI_Fon', 'Oi WiFi Fon', 'OTE WiFi Fon', 'PROXIMUS_AUTO_FON', 'PROXIMUS_FON', 'SFR WiFi FON', 'Telekom Fon', 'Telekom Fon WiFi HU', 'Telekom_FON']
  ssids = ['KPN Fon']
  fonPartners = ['kpn', 'ote']
  hasConfig = True

  credentials = None

  def detect(self, bssid, ssid, location = None, body = None):
    if location:
      if re.search("^https://[^/]*\.portal\.fon\.com/.*$", location):
        self.detectionMethod = 'urlmatch'
        #if bssid:
        #  CaptivePortalSolverCache.getCache().store(bssid, type(self).__name__)
        return True

    return super().detect(bssid, ssid)

  def isSolvable(self, bssid, ssid, location = None, body = None):
    #logger.info("%s: %s" % (self.supervisor.interface.interface, type(self.supervisor.interface).__name__))
    if self.isSolved(location, body):
      return True

    if location:
      fonPartner = re.compile("^https://([^/]*)\.portal\.fon\.com/.*$").search(location)
      if fonPartner:
        fonPartner = fonPartner.group(1)
        logger.debug("Fon partner:", fonPartner)

        if fonPartner not in self.fonPartners:
          return False
      else:
        return False
    elif ssid and ssid not in self.ssids:
      return False

    self.credentials = CredentialsStore.getStore().getCredentials(None, None, '.portal.fon.com')

    if self.credentials and 'username' in self.credentials and 'password' in self.credentials:
      if ssid and ssid in self.ssids and self.supervisor.interface.type == 'wifi':
        configuredAPs = self.supervisor.interface.getConfiguredAPs()
        if ssid not in [ap[1] for ap in configuredAPs]:
          logger.info("Need to configure %s" % ssid)
          self.supervisor.interface.configureAP(None, ssid, None)

      return True

    return False

  def solve(self, bssid, ssid, location, body):
    if self.isSolved(location, body):
      return True

    fonPartner = re.compile("^https://([^/]*)\.portal\.fon\.com/.*$").search(location)
    if fonPartner:
      fonPartner = fonPartner.group(1)
      logger.debug("Fon partner:", fonPartner)

      if fonPartner not in self.fonPartners:
        return False

      formAction = None
      formFields = None
      if fonPartner == 'kpn':
        formAction = re.compile('<form id="loginForm" action="([^"]*)" method="post">', re.MULTILINE).search(body)
        if formAction:
          formAction = formAction.group(1)
          formAction = formAction.replace('&amp;', '&')
        #formFields = "UserName=%s&Password=%s&_rememberMe=on" % (self.credentials['username'].replace('@', '%40'), self.credentials['password'])
        formFields = {'UserName': self.credentials['username'], 'Password': self.credentials['password'], '_rememberMe': 'on'}
      elif fonPartner == 'ote':
        #formFields = "chooseUser=passusers&USERNAME=%s&PASSWORD=%s&remember=on" % (self.credentials['username'].replace('@', '%40'), self.credentials['password'])
        formFields = {'chooseUser': 'passusers', 'USERNAME': self.credentials['username'], 'PASSWORD': self.credentials['password'], 'remember': 'on'}

      logger.debug("Form action:", formAction)
      logger.debug("Form fields:", formFields)

      if formAction and formFields:
        (location, response) = self.supervisor.curlHelper.post(formAction, formFields, location, True)

        if response and re.compile("<title>[^>]* | Fon - Success</title>", re.MULTILINE).search(response):
          return True

    return False

@bottle.get('/CaptivePortals/Fon')
def getConfig():
  credentials = CredentialsStore.getStore().getCredentials(None, None, '.portal.fon.com')
  if not credentials:
    credentials = { 'username': '', 'password': '' }
  return bottle.template("CaptivePortals/Fon.tpl", credentials)

@bottle.post('/CaptivePortals/Fon')
def postConfig():
  username = bottle.request.forms.get('username')
  password = bottle.request.forms.get('password')
  logger.debug("Username:", username)
  #logger.debug("Password:", password)

  if username and password:
    credentials = CredentialsStore.getStore().getCredentials(None, None, '.portal.fon.com') or {}
    if not credentials:
      credentials = {}
    credentials['username'] = username
    credentials['password'] = password
    CredentialsStore.getStore().setCredentials(None, None, '.portal.fon.com', False, credentials)

  return bottle.redirect('/CaptivePortals/Fon')
