import json, logging, bottle

from WLANderlust import config
from WLANderlust.networking.tunnel import impl

def getCredentials(id = None):
  credentials = config.get('Networking', {}).get('Tunnels', []).copy()
  for _id, _credential in enumerate(credentials):
    _credential['id'] =_id 

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

    tunnel = c(outwardInterface, credential)

    logger.info("Starting %s tunnel" % tunnel.name)
    if not tunnel.start():
      logger.error("Failed to start %s tunnel" % tunnel.name)
      tunnel = None
      continue
    logger.info("Started %s tunnel" % tunnel.name)

    return tunnel

@bottle.get('/Networking/tunnel/config.json')
def configJSON():
  credentials = [{'id': _credential['id'], 'name': _credential['name'], 'type': _credential['type']} for _credential in getCredentials()]

  bottle.response.content_type = 'application/json'
  return json.dumps(credentials)

@bottle.get('/Networking/tunnel/<id:re:[0-9]*>/delete')
def delete(id):
  id = int(id)

  if len(config.get('Networking', {}).get('Tunnels', [])) < id + 1:
    bottle.response.status = 404
    return

  config.get('Networking', {}).get('Tunnels', []).pop(id)
  config.save()

  bottle.response.status = 200
