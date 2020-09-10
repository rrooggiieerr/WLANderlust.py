import threading, time, logging, bottle

from WLANderlust import config
from WLANderlust.plugins import Plugin
from WLANderlust import CredentialsStore
from WLANderlust import GPS

logger = logging.getLogger(__name__)

class WiGLE(Plugin):
  name = "WiGLE"
  hasConfig = True

  uploadThread = None
  uploadInterval = 3600
  terminate = False

  lastUpload = None

  def isConfigured(self):
    credentials = CredentialsStore.getStore().getCredentials(None, None, 'wigle.')

    if credentials and credentials['apitoken']:
      return True

    return False

  def stop(self):
    logger.debug("WiGLE.stop()")
    self.stopUploadThread()

  def online(self, outwardInterface):
    if not self.started:
      return

    logger.debug("WiGLE.online(%s)" % outwardInterface.interface)

    if self.uploadThread:
      logger.debug("WiGLE upload thread already running")
      return

    # Start WiGLE upload thread
    logger.debug("Starting WiGLE upload thread")

    self.uploadThread = threading.Thread(target = self.uploadThreadImpl)
    self.uploadThread.start()

    logger.info("Started WiGLE upload thread")

  def offline(self, outwardInterface):
    logger.debug("WiGLE.offline(%s)" % outwardInterface.interface)
    self.stopUploadThread()

  def scanResults(self, outwardInterface, networks):
    if not self.started:
      return

    logger.debug("WiGLE.scanResults(%s, ...)" % outwardInterface.interface)

    logger.debug("WiGLE: location ", GPS.getInstance().location)

  def stopUploadThread(self):
    if not self.uploadThread:
      logger.debug("WiGLE upload thread not running")
      return

    # Stop WiGLE Upload thread
    logger.info("Stopping WiGLE upload thread")
    self.terminate = True

    if self.uploadThread:
      self.uploadThread.join()
    self.uploadThread = None

    logger.info("Stopped WiGLE upload thread")

  def uploadThreadImpl(self):
    while not self.terminate:
      while self.lastUpload and time.time() - self.lastUpload < self.uploadInterval:
        if self.terminate:
          return
        time.sleep(0.1)

      self.lastUpload = time.time()

@bottle.get('/Plugins/WiGLE')
def getConfig():
  credentials = CredentialsStore.getStore().getCredentials(None, None, 'wigle.')

  if not credentials:
    credentials = {}
  if not credentials.get('apitoken', None):
    credentials['apitoken'] = ''

  return bottle.template("Plugins/WiGLE.tpl", credentials)

@bottle.post('/Plugins/WiGLE')
def postConfig():
  apitoken = bottle.request.forms.get('apitoken')

  if apitoken:
    credentials = CredentialsStore.getStore().getCredentials(None, None, 'wigle.') or {}
    credentials['apitoken'] = apitoken
    CredentialsStore.getStore().setCredentials(None, None, 'wigle.', False, credentials)

  return bottle.redirect('/Plugins/WiGLE')
