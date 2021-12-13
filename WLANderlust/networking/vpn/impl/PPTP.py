import bottle

from WLANderlust.networking.vpn import VPN
from WLANderlust import CredentialsStore

class PPTP(VPN):
  name = "PPTP"
  description = ""
  executable = ''

  def install(self):
    if not os.path.isfile(self.executable):
      self.logger.info("Installing %s" % self.name)
      subprocess.call(['/usr/bin/apt', 'install', '-y', 'pptp-linux'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

  def isConfigured(self):
    if not os.path.isfile(self.executable) or not os.access(self.executable, os.X_OK):
      self.logger.error("%s is not installed" % self.name)
      return False

    if not self.credentials:
      self.logger.error("No credentials")
      return False
    self.logger.debug("Credentials: %s" % self.credentials)

    return True

  def start(self):
    return False

  def stop(self):
    return False

@bottle.post('/Networking/vpn/PPTP/add')
def configPost():
  bottle.response.status = 404
