import bottle

from WLANderlust.networking.vpn import VPN
from WLANderlust import CredentialsStore

class IPsec(VPN):
  name = "IPsec"
  debug = True
  description = ''

  def isConfigured(self):
    return False

  def start(self):
    return False

  def stop(self):
    return False

@bottle.post('/Networking/vpn/IPsec/add')
def configPost():
  bottle.response.status = 404
