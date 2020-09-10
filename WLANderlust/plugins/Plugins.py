import logging

from WLANderlust import config
from WLANderlust.plugins import impl

logger = logging.getLogger(__name__)

class Plugins():
  debug = False

  __instance = None

  plugins = []
  enabled = []

  @staticmethod
  def getInstance():
    if not Plugins.__instance:
      Plugins()
    return Plugins.__instance

  def __init__(self):
    if Plugins.__instance != None:
      raise Plugins("This class is a singleton!")
    else:
      Plugins.__instance = self

    for implementation in impl.getImplementations():
      self.plugins.append([implementation[0], implementation[1]()])

    self.start()

  def start(self):
    self.enabled = config.get('Plugins', {}).get('Enabled', [])
    logger.debug("Enabled plugins: ", self.enabled)

    logger.debug("Starting Plugins")
    for (id, plugin) in self.plugins:
      if id in self.enabled:
        plugin.start()

  def stop(self):
    logger.debug("Plugins.stop()")
    for (id, plugin) in self.plugins:
      plugin.stop()

  def online(self, outwardInterface):
    logger.debug("Plugins.online(%s)" % outwardInterface.interface)
    for (id, plugin) in self.plugins:
      if id in self.enabled or plugin.started:
        plugin.online(outwardInterface)

  def offline(self, outwardInterface):
    logger.debug("Plugins.offline(%s)" % outwardInterface.interface)
    for (id, plugin) in self.plugins:
      if id in self.enabled or plugin.started:
        plugin.offline(outwardInterface)

  def location(self, location):
    logger.debug("Plugins.location(...)")
    for (id, plugin) in self.plugins:
      if id in self.enabled or plugin.started:
        plugin.offline(location)

  def rawScanResults(self, outwardInterface, aps):
    logger.debug("Plugins.rawScanResults(%s, ...)" % outwardInterface.interface)
    for (id, plugin) in self.plugins:
      if id in self.enabled or plugin.started:
        plugin.rawScanResults(outwardInterface, aps)

  def scanResults(self, outwardInterface, aps):
    logger.debug("Plugins.scanResults(%s, ...)" % outwardInterface.interface)
    for (id, plugin) in self.plugins:
      if id in self.enabled or plugin.started:
        plugin.scanResults(outwardInterface, aps)
