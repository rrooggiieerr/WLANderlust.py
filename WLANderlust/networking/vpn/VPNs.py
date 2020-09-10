import json, logging, bottle

from WLANderlust import config
from WLANderlust.networking.vpn import impl

debug = False

def getCredentials(id = None):
  credentials = config.get('Networking', {}).get('VPNs', []).copy()
  for _id, _credential in enumerate(credentials):
    _credential['id'] = _id

  if id != None:
    for credential in credentials:
      return [credentials[id]]

    return []

  return credentials

def start(outwardInterface, id = None):
  logger = logging.getLogger("%s(%s)" % (__name__, outwardInterface.interface))

  for credential in getCredentials(id):
    c = impl.getClass(credential['type'])

    if not c:
      continue

    vpn = c(outwardInterface, credential)

    logger.info("Starting %s VPN" % vpn.name)
    if not vpn.start():
      logger.error("Failed to start %s VPN" % vpn.name)
      vpn = None
      continue
    logger.info("Started %s VPN" % vpn.name)

    return vpn

@bottle.get('/Networking/vpn/config.json')
def configJSON():
  credentials = [{'id': _credential['id'], 'name': _credential['name'], 'type': _credential['type']} for _credential in getCredentials()]

  bottle.response.content_type = 'application/json'
  return json.dumps(credentials)

@bottle.get('/Networking/vpn/<id:re:[0-9]*>/delete')
def delete(id):
  id = int(id)

  if len(config.get('Networking', {}).get('VPNs', [])) < id + 1:
    bottle.response.status = 404
    return

  config.get('Networking', {}).get('VPNs', []).pop(id)
  config.save()

  bottle.response.status = 200
