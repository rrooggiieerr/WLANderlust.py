import threading, subprocess, time, logging, bottle

from WLANderlust.plugins import Plugin
from WLANderlust import config

logger = logging.getLogger(__name__)

class UpdateDebian(Plugin):
  name = 'Update Debian'
  hasConfig = True

  updateThread = None
  terminate = False

  lastUpdate = None
  interval = 86400

  def isConfigured(self):
    return True

  def stop(self):
    logger.debug("UpdateDebian.stop()")
    self.stopUpdateThread()

  def online(self, outwardInterface):
    if not self.started:
      return

    logger.debug("UpdateDebian.online(%s)" % outwardInterface.interface)

    if outwardInterface.status['metered']:
      logger.debug("Debian Update not running on metered interface")
      return

    if self.updateThread:
      logger.debug("Debian Update thread already running")
      return

    # Start Debian Update thread
    logger.debug("Starting Debian Update thread")

    self.updateThread = threading.Thread(target = self.updateThreadImpl)
    self.updateThread.start()

    logger.info("Started Debian Update thread")

  def offline(self, outwardInterface):
    logger.debug("UpdateDebian.offline(%s)" % outwardInterface.interface)
    self.stopUpdateThread()

  def stopUpdateThread(self):
    if not self.updateThread:
      logger.debug("Debian Update thread not running")
      return

    # Stop Debian Update thread
    logger.info("Stopping Debian Update thread")
    self.terminate = True

    if self.updateThread:
      self.updateThread.join()
    self.updateThread = None

    logger.info("Stopped Debian Update thread")

  def updateThreadImpl(self):
    while not self.terminate:
      while self.lastUpdate and time.time() - self.lastUpdate < self.interval:
        if self.terminate:
          return
        time.sleep(0.1)

      self.active = True

      print("update", end='', flush=True)
      proc = subprocess.Popen(['/usr/bin/apt-get', 'update'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      while proc.poll() == None:
        if self.terminate:
          logger.debug("Terminating update process")
          proc.terminate()
          proc.wait()
          self.active = False
          return
        print(".", end='', flush=True)
        time.sleep(0.1)
      print(" Finished")

      print("dist-upgrade", end='', flush=True)

      if config.get('UpdateDebian', {}).get('Install', True):
        proc = subprocess.Popen(['/usr/bin/apt-get', '-y', 'dist-upgrade'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      else:
        proc = subprocess.Popen(['/usr/bin/apt-get', '-y', '--download-only', 'dist-upgrade'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      while proc.poll() == None:
        if self.terminate:
          logger.debug("Terminating dist-upgrade process")
          proc.terminate()
          proc.wait()
          self.active = False
          return
        print(".", end='', flush=True)
        time.sleep(0.1)
      print(" Finished")

      print("autoclean", end='', flush=True)
      proc = subprocess.Popen(['/usr/bin/apt-get', 'autoclean'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      while proc.poll() == None:
        if self.terminate:
          logger.debug("Terminating autoclean process")
          proc.terminate()
          proc.wait()
          self.active = False
          return
        print(".", end='', flush=True)
        time.sleep(0.1)
      print(" Finished")

      self.active = False
      self.lastUpdate = time.time()

@bottle.get('/Plugins/UpdateDebian')
def getConfig():
  _config = {}
  _config['Install'] = config.get('UpdateDebian', {}).get('Install', False)

  return bottle.template("Plugins/UpdateDebian.tpl", _config)

@bottle.post('/Plugins/UpdateDebian')
def postConfig():
  install = bottle.request.forms.get('Install') == 'True'
  logger.debug("Install:", install)

  if 'UpdateDebian' not in config:
    config['UpdateDebian'] = {}

  config['UpdateDebian']['Install'] = install

  config.save()

  return bottle.redirect('/Plugins/UpdateDebian')

stdout = None
getUpdatesThread = None

def getUpdatesThreadImpl():
  global stdout

  #proc = subprocess.Popen(['/usr/bin/apt-get', '-u', 'upgrade', '--assume-no'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  proc = subprocess.Popen(['/usr/bin/apt', 'list', '--upgradable'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  logger.info("Started getUpdates")

  stdout = ""
  while proc.poll() == None:
    stdout += proc.stdout.read().decode()
  stdout += proc.stdout.read().decode()

  proc.stdout.close()

  logger.info("Finished getUpdates")

@bottle.get('/Plugins/UpdateDebian/updates')
def getUpdates():
  global getUpdatesThread, stdout

  if not getUpdatesThread:
    # Start Debian Update thread
    logger.debug("Starting Debian Update thread")

    stdout = ""
    getUpdatesThread = threading.Thread(target = getUpdatesThreadImpl)
    getUpdatesThread.start()

    logger.debug("Started Debian Update thread")
    bottle.response.status = 206
  elif getUpdatesThread.is_alive():
    bottle.response.status = 206
  else:
    getUpdatesThread.join()
    getUpdatesThread = None

  return stdout

installUpdatesThread = None

def installUpdatesThreadImpl():
  global stdout

  proc = subprocess.Popen(['/usr/bin/apt-get', '-y', '--no-download', '--ignore-missing', 'dist-upgrade'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  #proc = subprocess.Popen(['/usr/bin/apt', 'list', '--upgradable'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  logger.info("Started getUpdates")

  stdout = ""
  while proc.poll() == None:
    stdout += proc.stdout.read().decode()

  proc.stdout.close()

  logger.info("Finished installUpdates")

@bottle.get('/Plugins/UpdateDebian/update')
def installUpdates():
  global installUpdatesThread, stdout

  if not installUpdatesThread:
    logger.debug("Starting installation Debian Updates thread")

    stdout = ""
    installUpdatesThread = threading.Thread(target = installUpdatesThreadImpl)
    installUpdatesThread.start()

    logger.debug("Started installation Debian Updates thread")
    bottle.response.status = 206
  elif installUpdatesThread.is_alive():
    bottle.response.status = 206
  else:
    installUpdatesThread.join()
    installUpdatesThread = None

  return stdout
