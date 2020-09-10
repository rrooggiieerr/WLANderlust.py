import re, sqlite3, logging, bottle

from WLANderlust.captiveportals import CaptivePortalSolverImpl
from WLANderlust import config
from WLANderlust import CredentialsStore

logger = logging.getLogger(__name__)

class Curl(CaptivePortalSolverImpl):
  name = "cURL"
  order = 5
  hasConfig = True

  solvable = False

  url = None
  formFields = None
  referrer = None
  headers = None
  cookies = None

  def detect(self, bssid, ssid, location = None, body = None):
    self.detectionMethod = None
    self.solvable = False
    self.url = None
    self.formFields = None
    self.referrer = None
    self.headers = None
    self.cookies = None
    credentials = None

    if bssid:
      logger.debug("CaptivePortalCurl: Looking up BSSID based credentials")
      _credentials = CredentialsStore.getStore().getCredentials(bssid, None, None)
      if _credentials and 'url' in _credentials:
        logger.debug("CaptivePortalCurl: Found BSSID based credentials")
        self.detectionMethod = 'sssidmatch'
        self.solvable = True
        credentials = _credentials

    if not self.solvable and ssid:
      logger.debug("CaptivePortalCurl: Looking up SSID based credentials")
      _credentials = CredentialsStore.getStore().getCredentials(None, ssid, None)
      if _credentials and 'url' in _credentials:
        logger.debug("CaptivePortalCurl: Found SSID based credentials")
        self.detectionMethod = 'ssidmatch'
        self.solvable = True
        credentials = _credentials

    if credentials:
      if 'url' in credentials:
        self.url = credentials['url']
      if 'formFields' in credentials:
        self.formFields= credentials['formFields']
      if 'referrer' in credentials:
        self.referrer = credentials['referrer']
      if 'headers' in credentials:
        self.headers = credentials['headers']
      if 'cookies' in credentials:
        self.cookies = credentials['cookies']

    logger.debug("CaptivePortalCurl: Solvable    :", self.solvable)
    logger.debug("CaptivePortalCurl: URL         :", self.url)
    logger.debug("CaptivePortalCurl: Form Fields :", self.formFields)
    logger.debug("CaptivePortalCurl: Referrer    :", self.referrer)
    logger.debug("CaptivePortalCurl: Headers     :", self.headers)
    logger.debug("CaptivePortalCurl: Cookies     :", self.cookies)

    return self.solvable

  def isSolvable(self, bssid, ssid, location = None, body = None):
    return self.solvable

  def solve(self, bssid, ssid, location, body):
    _location = None
    _response = None
    if self.url and self.formFields:
      (_location, _response) = self.supervisor.curlHelper.post(self.url, self.formFields, self.referrer, True)
      return True
    elif self.url:
      (_location, _response) = self.supervisor.curlHelper.get(self.url, self.referrer, True)
      return True

    return self.isSolved(_location, _response)

@bottle.get('/CaptivePortals/Curl')
def getConfig():
  credentials = []
  try:
    cur = CredentialsStore.getStore().credentialsStoreDB.cursor()
    cur.execute("SELECT bssid, ssid, domain, share, credentials FROM credentialsStore WHERE (domain ISNULL or domain NOT LIKE '%.') AND credentials REGEXP ?", ('[{, ]"url": ',))
    credentials = cur.fetchall()
    logger.debug("Credentials:", credentials)
  except sqlite3.Error as e:
    logger.error(e)

  return bottle.template("CaptivePortals/Curl.tpl", credentials=credentials)

@bottle.post('/CaptivePortals/Curl/add')
def addCredential():
  bssid = bottle.request.forms.get('bssid').strip()
  if bssid == '':
    bssid = None
  ssid = bottle.request.forms.get('ssid')
  if ssid == '':
    ssid = None
  domain = bottle.request.forms.get('domain').strip()
  if domain == '':
    domain = None
  share = bottle.request.forms.get('share') == 'True'
  credentials = {'url': bottle.request.forms.get('url')}

  CredentialsStore.getStore().setCredentials(bssid, ssid, domain, share, credentials)

  return bottle.redirect('/CaptivePortals/Curl')

@bottle.post('/CaptivePortals/Curl/delete')
#ToDo @bottle.post('/CaptivePortals/Curl/<id:re:[0-9]*>/delete')
def deleteCredential(id = None):
  bssid = bottle.request.forms.get('bssid').strip()
  if bssid == '':
    bssid = None
  ssid = bottle.request.forms.get('ssid')
  if ssid == '':
    ssid = None
  domain = bottle.request.forms.get('domain').strip()
  if domain == '':
    domain = None
  logger.debug("BSSID:", bssid)
  logger.debug("SSID:", ssid)
  logger.debug("Domain:", domain)

  CredentialsStore.getStore().deleteCredentials(bssid, ssid, domain)

  return bottle.redirect('/CaptivePortals/Curl')
