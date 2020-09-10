import logging, bottle, json
from WLANderlust.networking import Networking, OutwardNetworkInterface, OutwardTransceiverInterface, tunnel, vpn

from WLANderlust import config
from WLANderlust import CredentialsStore

logger = logging.getLogger(__name__)

@bottle.get('/Networking/settings')
def getConfig():
  _config = {}

  _config['DetectExternalIPURL'] = config.get('Networking', {}).get('DetectExternalIPURL', OutwardNetworkInterface.detectExternalIPURL)
  _config['Scan'] = config.get('Networking', {}).get('Scan', True)
  _config['AutoReassociateWiFi'] = config.get('Networking', {}).get('AutoReassociateWiFi', False)
  _config['AutoSwitchHostAPChannel'] = config.get('Networking', {}).get('AutoSwitchHostAPChannel', False)
  _config['AutoStartTunnel'] = config.get('Networking', {}).get('AutoStartTunnel', False)
  _config['OverrideMetered'] = False
  _config['CreateInterfacesdFile'] = config.get('Networking', {}).get('CreateInterfacesdFile', True)

  _config['InwardInterfaces'] = []
  for inwardNetworkInterface in Networking.getInstance().inwardNetworkInterfaces:
    _interface = {}
    _interface['interface'] = inwardNetworkInterface.interface
    _interface['type'] = inwardNetworkInterface.type
    _config['InwardInterfaces'].append(_interface)

  _config['OutwardInterfaces'] = []
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    _interface = {}
    _interface['interface'] = outwardNetworkInterface.interface
    _interface['type'] = outwardNetworkInterface.type
    _config['OutwardInterfaces'].append(_interface)

  _config['tunnels'] = config.get('Networking', {}).get('Tunnels', []).copy()
  for id, _tunnel in enumerate(_config['tunnels']):
    _tunnel['id'] = id
  _config['tunnelTypes'] = []
  for implementation in tunnel.impl.getImplementations():
    _config['tunnelTypes'].append({'id': implementation[0], 'name': implementation[1].name, 'description': implementation[1].description})

  _config['AutoStartVPN'] = config.get('Networking', {}).get('AutoStartVPN', False)

  _config['vpns'] = config.get('Networking', {}).get('VPNs', [])
  for id, _vpn in enumerate(_config['vpns']):
    _vpn['id'] = id
  _config['vpnTypes'] = []
  for implementation in vpn.impl.getImplementations():
    _config['vpnTypes'].append({'id': implementation[0], 'name': implementation[1].name})

  return bottle.template("Networking.tpl", _config)

@bottle.post('/Networking/settings')
def postConfig():
  detectExternalIPURL = bottle.request.forms.get('DetectExternalIPURL')
  #ToDo Validate URL
  scan = bottle.request.forms.get('Scan') == 'True'
  autoReassociateWiFi = bottle.request.forms.get('AutoReassociateWiFi') == 'True'
  autoSwitchHostAPChannel = bottle.request.forms.get('AutoSwitchHostAPChannel') == 'True'
  autoStartTunnel = bottle.request.forms.get('AutoStartTunnel') == 'True'
  autoStartVPN = bottle.request.forms.get('AutoStartVPN') == 'True'

  if 'Networking' not in config:
    config['Networking'] = {}

  config['Networking']['DetectExternalIPURL'] = detectExternalIPURL
  config['Networking']['Scan'] = scan
  config['Networking']['AutoReassociateWiFi'] = autoReassociateWiFi
  config['Networking']['AutoSwitchHostAPChannel'] = autoSwitchHostAPChannel
  config['Networking']['AutoStartTunnel'] = autoStartTunnel
  config['Networking']['AutoStartVPN'] = autoStartVPN

  config.save()

  return bottle.redirect('/Networking/settings')

@bottle.get('/Networking/networks.json')
def getAvailableAPs():
  networks = []

  outwardNetworkInterfaces = Networking.getInstance().outwardNetworkInterfaces
  if outwardNetworkInterfaces:
    for outwardNetworkInterface in outwardNetworkInterfaces:
      if outwardNetworkInterface.type == 'wifi' and outwardNetworkInterface.networks:
        networks += outwardNetworkInterface.networks

  #ToDo Remove duplicate entries

  bottle.response.content_type = 'application/json'
  return json.dumps(networks)

@bottle.route('/Networking/<type:re:bssid>/<id:re:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}>/connect', method=['GET', 'POST'])
@bottle.route('/Networking/<type:re:ssid>/<id>/connect', method=['GET', 'POST'])
@bottle.route('/Networking/<type:re:bdaddr>/<id:re:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}>/connect', method=['GET', 'POST'])
@bottle.route('/Networking/interface/<interface:re:[a-z]*[0-9]*>/<type:re:bssid>/<id:re:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}>/connect', method=['GET', 'POST'])
@bottle.route('/Networking/interface/<interface:re:[a-z]*[0-9]*>/<type:re:ssid>/<id>/connect', method=['GET', 'POST'])
@bottle.route('/Networking/interface/<interface:re:[a-z]*[0-9]*>/<type:re:bdaddr>/<id:re:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}>/connect', method=['GET', 'POST'])
def networkConnect(type, id, interface = None):
  if type == 'bssid' or type == 'bdaddr':
    id = id.lower()

  credentials = None
  share = False

  # Check if Post
  if bottle.request.method == 'POST':
    credentials = {}

    wpapassphrase = bottle.request.forms.get('wpapassphrase')
    #ToDo Validate WPA passphrase
    wpa2passphrase = bottle.request.forms.get('wpa2passphrase')
    #ToDo Validate WPA2 passphrase
    wepkey0 = bottle.request.forms.get('wepkey0')
    wepkey1 = bottle.request.forms.get('wepkey1')
    wepkey2 = bottle.request.forms.get('wepkey2')
    wepkey3 = bottle.request.forms.get('wepkey3')
    #ToDo Validate WEP keys
    # 10 or 26 hexadecimal characters

    share = bottle.request.forms.get('share') == 'True'

    if wpapassphrase:
      credentials['wpapassphrase'] = wpapassphrase
    if wpa2passphrase:
      credentials['wpa2passphrase'] = wpa2passphrase
    if wepkey0:
      credentials['wepkey0'] = wepkey0
      credentials['wepkey1'] = wepkey1
      credentials['wepkey2'] = wepkey2
      credentials['wepkey3'] = wepkey3
    logger.debug("Credentials: %s" % credentials)

  if Networking.getInstance().connect(interface, type, id, credentials):
    if credentials and share:
      if type == 'bssid':
        CredentialsStore.getStore().setCredentials(id, None, None, share, credentials)
      elif type == 'ssid':
        CredentialsStore.getStore().setCredentials(None, id, None, share, credentials)
    bottle.response.status = 200
  else:
    bottle.response.status = 500

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/status.json')
def getAvailableAPs(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if outwardNetworkInterface.interface == interface:
      bottle.response.content_type = 'application/json'
      return json.dumps(outwardNetworkInterface.status)

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/networks.json')
def getAvailableAPs(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if outwardNetworkInterface.interface == interface:
      bottle.response.content_type = 'application/json'
      return json.dumps(outwardNetworkInterface.networks)

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/scan')
def doScan(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if isinstance(outwardNetworkInterface, OutwardTransceiverInterface) and outwardNetworkInterface.interface == interface:
      networks = outwardNetworkInterface.scan()
      if networks:
        return json.dumps(networks)

      bottle.response.status = 500
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/scan/start')
def doScan(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if isinstance(outwardNetworkInterface, OutwardTransceiverInterface) and outwardNetworkInterface.interface == interface:
      if outwardNetworkInterface.startScan():
        bottle.response.status = 200
        return
      bottle.response.status = 500
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/scan/stop')
def doScan(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if isinstance(outwardNetworkInterface, OutwardTransceiverInterface) and outwardNetworkInterface.interface == interface:
      if outwardNetworkInterface.stopScan():
        bottle.response.status = 200
        return
      bottle.response.status = 500
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/sweep/start')
def doScan(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if isinstance(outwardNetworkInterface, OutwardTransceiverInterface) and outwardNetworkInterface.interface == interface:
      if outwardNetworkInterface.startSweep():
        bottle.response.status = 200
        return
      bottle.response.status = 500
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/sweep/stop')
def doScan(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if isinstance(outwardNetworkInterface, OutwardTransceiverInterface) and outwardNetworkInterface.interface == interface:
      if outwardNetworkInterface.stopSweep():
        bottle.response.status = 200
        return
      bottle.response.status = 500
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/speedtest')
def doSpeedtest(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if outwardNetworkInterface.interface == interface:
      outwardNetworkInterface.speedtest()
      bottle.response.status = 200
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/tunnel/start')
@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/tunnel/<id:re:[0-9]*>/start')
def startTunnel(interface, id = None):
  if bottle.request.method == 'POST':
    id = bottle.request.forms.get('id')

  if id:
    id = int(id)

  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if outwardNetworkInterface.interface == interface:
      if outwardNetworkInterface.startTunnel(id):
        bottle.response.status = 200
      else:
        bottle.response.status = 500
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/tunnel/stop')
def stopTunnel(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if outwardNetworkInterface.interface == interface:
      if outwardNetworkInterface.stopTunnel():
        bottle.response.status = 200
      else:
        bottle.response.status = 500
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/vpn/start')
@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/vpn/<id:re:[0-9]*>/start')
def startVPN(interface, id = None):
  if bottle.request.method == 'POST':
    id = bottle.request.forms.get('id')

  if id:
    id = int(id)

  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if outwardNetworkInterface.interface == interface:
      if outwardNetworkInterface.startVPN(id):
        bottle.response.status = 200
      else:
        bottle.response.status = 500
      return

  bottle.response.status = 404

@bottle.get('/Networking/interface/<interface:re:[a-z]*[0-9]*>/vpn/stop')
def stopVPN(interface):
  for outwardNetworkInterface in Networking.getInstance().outwardNetworkInterfaces:
    if outwardNetworkInterface.interface == interface:
      if outwardNetworkInterface.stopVPN():
        bottle.response.status = 200
      else:
        bottle.response.status = 500
      return

  bottle.response.status = 404
