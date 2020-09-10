import os, threading, math, pycurl, json, urllib, logging, bottle
from io import BytesIO
from gps import *

from WLANderlust import config
from WLANderlust import BSSIDLocationCache

logger = logging.getLogger(__name__)

ipLocationConfigs = {
	'ip-api.com': { 'url': 'http://ip-api.com/json', 'latitudeKey': 'lat', 'longitudeKey': 'lon', 'needsRegistrationKey': False},
	'ipapi.co': { 'url': 'https://ipapi.co/json/', 'latitudeKey': 'latitude', 'longitudeKey': 'longitude', 'needsRegistrationKey': False}
}

class GPS():
  debug = False
  __instance = None

  ipLocationProvider = 'ip-api.com'

  gpsd = None
  gpsThread = None
  terminate = False

  location = None
  accuracy = None
  altitude = None
  altitudeAccuracy = None
  heading = None
  speed = None
  method = None

  @staticmethod
  def getInstance():
    logger.debug("Get instance")
    if not GPS.__instance:
      logger.debug("Creating instance")
      GPS()
    return GPS.__instance

  def __init__(self):
    if GPS.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      GPS.__instance = self

    self.logger = logging.getLogger("%s()" % (self.__class__.__name__))
    self.logger.info("Starting GPS")

    try:
      self.gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)

      self.gpsThread = threading.Thread(target = self.gpsThreadImpl)
      self.gpsThread.start()
      self.logger.info("Started GPS")
    except ConnectionRefusedError as e:
      self.logger.warning("No GPS device connected or configured")

  def install(self):
    if os.path.isfile('/bin/gpsd'):
      return True

    from WLANderlust import InstallHelper
    # apt-get install -y gpsd gpsd-clients
    return InstallHelper.installPackage('gpsd')

  def stop(self):
    self.logger.info("Stopping GPS")
    self.terminate = True

    # Wait for GPS thread to finish
    if self.gpsThread:
      self.gpsThread.join()

    self.logger.info("Stopped GPS")

  def online(self, outwardInterface):
    self.logger.debug("GPS.online(%s)" % outwardInterface.interface)

    if self.gpsd:
     return

    if outwardInterface.type == 'wifi':
      _location = BSSIDLocationCache.getCache().lookup(outwardInterface.bssid, outwardInterface.status['signal'])
      if _location:
        self.location = _location
        self.method = 'bssid'
        self.logger.debug("BSSID Location: %s" % self.location)
        return

    ipLocationLookupThread = threading.Thread(target = self.ipLocationLookupThreadImpl, args=(outwardInterface,))
    ipLocationLookupThread.start()

  def ipLocationLookupThreadImpl(self, outwardInterface):
    ipLocationConfig = ipLocationConfigs[self.ipLocationProvider]
    response = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.INTERFACE, outwardInterface.interface)
    curl.setopt(curl.HTTPHEADER, ['User-Agent: WLANderlust', 'Accept: application/json'])
    curl.setopt(curl.TIMEOUT, 5)
    curl.setopt(curl.URL, ipLocationConfig['url'])
    curl.setopt(curl.WRITEFUNCTION, response.write)
    try:
      curl.perform()
      response = response.getvalue().decode('utf-8')
      response = json.loads(response)
      self.logger.debug(response)
      self.location = [ response[ipLocationConfig['latitudeKey']], response[ipLocationConfig['longitudeKey']] ]
      self.method = 'ip'
      self.logger.debug("External IP Location: %s" % self.location)
    except Exception as e:
      self.logger.error(e)
      response = None
    curl.close()

  def offline(self, outwardInterface):
    self.logger.debug("GPS.offline(%s)" % outwardInterface.interface)

    if not self.gpsd:
      self.location = None

  def scanResults(self, outwardInterface, aps):
    self.logger.debug("GPS.scanResults(%s, ...)" % outwardInterface.interface)

    if not self.gpsd:
      #ToDo Calculate position based on aps locations
      return

  def gpsThreadImpl(self):
    self.logger.info("Starting GPS thread")

    while not self.terminate:
      if self.gpsd:
        time.sleep(1)
        if self.gpsd.waiting():
          # Get current location from GPS device
          report = self.gpsd.next() 
          if report['class'] == 'TPV' and 'lat' in report and 'lon' in report:
            self.location = [ report['lat'], report['lon'] ]
            self.method = 'gpsd'
            self.logger.debug(self.location)
          #elif report['class'] == 'SKY':
          #  print(report['satellites'])
          #elif report['class'] == 'DEVICES':
          #  print(report)
          #else:
          #  self.logger.debug(report)
        else:
          time.sleep(0.1)
      else:
        time.sleep(0.1)

    self.logger.info("Stopped GPS thread")

  def distance(self, location):
    # Calculate distance to Access Point
    distance = None

    if location and self.location:
      self.logger.debug("Calculating distance from %s to %s" % (self.location, location))
      radius = 6371000  # meters

      dlat = math.radians(location[0] - self.location[0])
      dlon = math.radians(location[1] - self.location[1])
      a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
        math.cos(math.radians(self.location[0])) * math.cos(math.radians(location[0])) *
        math.sin(dlon / 2) * math.sin(dlon / 2))
      c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
      distance = radius * c # meters

      self.logger.debug("Distance %f meters" % distance)

    return distance

@bottle.get('/GPS/settings')
def getConfig():
  _config = {}

  return bottle.template("GPS.tpl", _config)

@bottle.post('/GPS/settings')
def postConfig():
  return bottle.redirect('/GPS/settings')

@bottle.get('/GPS/install')
def install():
  GPS.getInstance().install()

@bottle.get('/GPS/location.json')
def getLocation():
  if GPS.getInstance().location:
    bottle.response.content_type = 'application/json'
    return json.dumps(GPS.getInstance().location)

  bottle.response.status = 503

@bottle.post('/GPS/location')
def postLocation():
  latitude = bottle.request.forms.get('latitude', None)
  longitude = bottle.request.forms.get('longitude', None)
  accuracy = bottle.request.forms.get('accuracy', None)

  _gps = GPS.getInstance()
  if not _gps.gpsd and latitude and longitude and accuracy:
    if _gps.accuracy == None or _gps.accuracy <= accuracy:
      _gps.location = [latitude, longitude]
      _gps.accuracy = accuracy
      _gps.method = 'js'
      logger.debug("Location:", _gps.location)

    altitude = bottle.request.forms.get('altitude', None)
    altitudeAccuracy = bottle.request.forms.get('altitudeAccuracy', None)
    if altitude and altitudeAccuracy and altitudeAccuracy <= _gps.altitudeAccuracy:
      _gps.altitude = altitude
      _gps.altitudeAccuracy = altitudeAccuracy
      logger.debug("Altitude:", _gps.altitude)

    speed = bottle.request.forms.get('speed', None)
    heading = bottle.request.forms.get('heading', None)
    if speed != None and heading:
      _gps.speed = speed
      _gps.heading = heading
      logger.debug("Speed:", _gps.speed)
      logger.debug("Heading:", _gps.heading)

    bottle.response.status = 200
    return

  bottle.response.status = 503
