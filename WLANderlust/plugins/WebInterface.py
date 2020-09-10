import bottle, json, logging

from WLANderlust import config
from WLANderlust.plugins import Plugins, impl
from WLANderlust.networking import Networking

logger = logging.getLogger(__name__)

@bottle.get('/Plugins/settings')
def getConfig():
  _config = {}
  _config['plugins'] = []

  enabled = Plugins.getInstance().enabled
  logging.debug("Enabled plugins:", enabled)

  for implementation in impl.getImplementations():
    _config['plugins'].append({ 'id': implementation[0], 'name': implementation[1].name, 'description': implementation[1].description, 'enabled': implementation[0] in enabled, 'configured': implementation[1]().isConfigured()})
  return bottle.template("Plugins.tpl", _config)

@bottle.post('/Plugins/settings')
def postConfig():
  enabled = ','.join(bottle.request.forms.getlist('Enabled'))
  logging.debug("Enabled plugins:", enabled)

  if not 'Plugins' in config:
    config['Plugins'] = {}

  config['Plugins']['Enabled'] = enabled

  config.save()

  return bottle.redirect('/Plugins/settings')

@bottle.get('/Plugins/status.json')
def getStatus():
  status = []

  for (id, plugin) in Plugins.getInstance().plugins:
    status.append([type(plugin).__name__, plugin.active])

  bottle.response.content_type = 'application/json'
  return json.dumps(status)

@bottle.get('/Plugins/<id>/start')
def startPlugin(id):
  for (id, plugin) in Plugins.getInstance().plugins:
    if type(plugin).__name__ == id:
      plugin.start()

      logging.debug(Networking.getInstance().onlineNetworkInterfaces)
      for interfaceName in Networking.getInstance().onlineNetworkInterfaces:
        interface = [interface for interface in Networking.getInstance().outwardNetworkInterfaces if interface.interface == interfaceName][0]
        plugin.online(interface)

      bottle.response.status = 200
      return

  bottle.response.status = 404

@bottle.get('/Plugins/<id>/stop')
def stopPlugin(id):
  for (id, plugin) in Plugins.getInstance().plugins:
    if type(plugin).__name__ == id:
      plugin.stop()
      bottle.response.status = 200
      return

  bottle.response.status = 404
