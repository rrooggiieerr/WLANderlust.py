import os, logging, socket, bottle, json

from WLANderlust import config, GPS 
from WLANderlust.networking import Networking, WebInterface, tunnel, vpn
#from WLANderlust.captiveportals import WebInterface
from WLANderlust.plugins import WebInterface

bottle.debug(True)

logger = logging.getLogger(__name__)

webRoot = config.get('WebRoot', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'views/'))
bottle.TEMPLATE_PATH = [webRoot]

@bottle.get('/status.json')
def statusJSON():
  status = {'GPS': {}, 'Networking': {'InwardInterfaces': [], 'OutwardInterfaces': []}}

  status['GPS']['location'] = GPS.getInstance().location

  instance = Networking.getInstance()
  if instance.inwardNetworkInterfaces:
    for inwardInterface in instance.inwardNetworkInterfaces:
      status['Networking']['InwardInterfaces'].append(inwardInterface.status)

  if instance.outwardNetworkInterfaces:
    for outwardInterface in instance.outwardNetworkInterfaces:
      status['Networking']['OutwardInterfaces'].append(outwardInterface.status)

  status['Networking']['Tunnels'] = [{'id': _credential['id'], 'name': _credential['name'], 'type': _credential['type']} for _credential in tunnel.Tunnels.getCredentials()]
  status['Networking']['VPNs'] = [{'id': _credential['id'], 'name': _credential['name'], 'type': _credential['type']} for _credential in vpn.VPNs.getCredentials()]

  bottle.response.content_type = 'application/json'
  return json.dumps(status)

@bottle.get('/settings')
def getConfig():
  _config = {}

  _config['ShutdownOnUnplug'] = config.get('ShutdownOnUnplug', False)

  return bottle.template("settings.tpl", _config)

@bottle.post('/settings')
def postConfig():
  shutdownOnUnplug = bottle.request.forms.get('ShutdownOnUnplug') == 'True'

  config['ShutdownOnUnplug'] = shutdownOnUnplug
  config.save()

  return bottle.redirect('/settings')

@bottle.get('/<filepath:re:.*>')
def staticFile(filepath):
  if bottle.request.headers['Host'] != socket.getfqdn():
    bottle.response.status = 200
    bottle.response.add_header('Location', 'http://' + socket.getfqdn())
    return '<HTML><HEAD><TITLE> Web Authentication Redirect</TITLE><META http-equiv="Cache-control" content="no-cache"><META http-equiv="Pragma" content="no-cache"><META http-equiv="Expires" content="-1"><META http-equiv="refresh" content="1; URL=http://%s/"></HEAD></HTML>' % socket.getfqdn()

  if filepath == '':
    filepath = 'index.html'

  if filepath:
    return bottle.static_file(filepath, root=webRoot)

  bottle.response.status = 404

@bottle.hook('before_request')
def redirect2captiveportal():
  if bottle.request.headers['Host'] != socket.getfqdn():
    logger.debug(bottle.request.url)
    #return bottle.redirect('http://' + socket.getfqdn() + '/')

    bottle.response.status = 200
    bottle.response.add_header('Location', 'http://' + socket.getfqdn() + '/')
    return '<HTML><HEAD><TITLE> Web Authentication Redirect</TITLE><META http-equiv="Cache-control" content="no-cache"><META http-equiv="Pragma" content="no-cache"><META http-equiv="Expires" content="-1"><META http-equiv="refresh" content="1; URL=http://%s/"></HEAD></HTML>' % socket.getfqdn()
