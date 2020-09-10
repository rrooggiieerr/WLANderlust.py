import bottle

from WLANderlust.networking.vpn import VPN
from WLANderlust import CredentialsStore

class L2TP(VPN):
  name = "L2TP"
  debug = True
  description = ''

  def isConfigured(self):
    return False

  def start(self):
    return False

  def stop(self):
    return False

@bottle.post('/Networking/vpn/L2TP/add')
def configPost():
  bottle.response.status = 404
