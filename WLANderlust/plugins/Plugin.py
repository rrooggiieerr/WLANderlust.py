class Plugin():
  name = 'Unknown'
  description = ''
  hasConfig = False
  started = False
  active = False

  def isConfigured(self):
    return False

  def start(self):
    self.started = True

  def stop(self):
    self.started = False

  def online(self, outwardInterface):
    return

  def offline(self, outwardInterface):
    return

  def location(self, location):
    return

  def rawScanResults(self, outwardInterface, networks):
    return

  def scanResults(self, outwardInterface, networks):
    return
