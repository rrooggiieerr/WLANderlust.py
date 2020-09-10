import os, codecs, pycurl, urllib, re, logging
from datetime import datetime
from io import BytesIO

from WLANderlust import config

logger = logging.getLogger(__name__)

class CurlHelper():
  interface = None
  cookieJar = "/var/run/WLANderlust.cookiejar"

  logging = False
  logPath = None
  timestamp = None
  logFileCounter = 0

  responses = []

  def __init__(self, interface):
    self.interface = interface

    self.cookieJar = config.get('CaptivePortal', {}).get('CookieJar', self.cookieJar)
    logging.debug("Cookie Jar: %s" % self.cookieJar)

    self.logging = config.get('CaptivePortal', {}).get('Logging', self.logging)
    logging.debug("Captive Portal logging: %s" % self.logging)

    self.logPath = config.get('CaptivePortal', {}).get('LogPath', self.logPath)
    logging.debug("Captive Portal log path: %s" % self.logPath)
    #ToDo Sanity checks on log path

    if not self.logPath:
      self.logging = False
    else:
      if not os.path.isdir(self.logPath):
        # Make dir
        os.mkdir(self.logPath)
      if not os.access(self.logPath, os.W_OK):
        logger.error('Captive Portal log directory not accessable')

    self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    logging.debug("Timestamp %s" % self.timestamp)

  def logResponse(self, response, location):
    if response:
      if not os.path.isdir(self.logPath) or not os.access(self.logPath, os.W_OK):
        logger.error('Captive Portal log directory not accessable')
        return
      logFile = ("%s/CaptivePortal%s-%s.log" % (self.logPath, self.timestamp, self.logFileCounter))
      logging.debug("Writing Captive Portal detection response to %s" % logFile)
      try:
        f = codecs.open(logFile, 'w', 'utf-8')
        if self.interface.type == 'wifi':
          f.write("BSSID %s\n" % self.interface.bssid)
          f.write("SSID %s\n" % self.interface.ssid)
        f.write("GET %s\n" % location)
        f.write("\n")
        f.write(response)
        f.close()
      except Exception as e:
        logger.error(e)
      self.logFileCounter += 1

  def logResponses(self):
    for response in self.responses:
      self.logResponse(response[0], response[1])

  def expandLocation(self, location, previousLocation):
    # Check if it starts with a protocol
    if re.search(r'^[a-z]*://', location):
      return location

    if re.search(r'^/', location):
      location = re.search(r'^([a-z]*://[^\/]*)/?.*', previousLocation).group(1) + location
    else:
      location = re.search(r'^(.*/).*', previousLocation).group(1) + location

    logging.debug("Location expanded to: %s" % location)
    return location

  # Tries to find a location redirect in a given HTML + headers.
  # First it tries to find a Location header
  # Then a refresh meta tag
  # Then a window.location string, this is very crude
  def getLocationRedirect(self, body, previousLocation):
    location = None

    if body:
      if re.search(r'^Location: .*$', body, re.MULTILINE):
        location = re.search(r'^Location: (.*)$', body, re.MULTILINE).group(1)
        logging.debug("Location header", location)
      elif re.search(r'<meta\s*http-equiv=["\']refresh["\']\s', body, re.IGNORECASE | re.MULTILINE):
        # We found a refresh meta tag
        location = re.search(r'<meta\s*http-equiv=["\']refresh["\']\s[^>]*content=["\'][^;]*;\s*url=([^"\']*)["\']', body, re.IGNORECASE | re.MULTILINE).group(1)
        logging.debug("Refresh meta tag", location)
      else:
        if re.search(r'window\.location\s*=\s*["\']?[^"\';]*["\']?', body, re.MULTILINE):
          # We found a JavaScript redirect
          location = re.search(r'window\.location\s*=\s*(["\']?[^"\';]*["\']?)', body, re.MULTILINE).group(1)
        elif re.search(r'location\.href\s*=\s*["\']?[^"\';]*["\']?', body, re.MULTILINE):
          # We found a JavaScript redirect
          location = re.search(r'location\.href\s*=\s*(["\']?[^"\';]*["\']?)', body, re.MULTILINE).group(1)

        if location:
          if re.search(r'["\']([^"\']*)["\']', location):
            location = re.search(r'["\']([^"\']*)["\']', location).group(1)
          else:
            logging.debug("JavaScript variable", location)
            if re.search(r'%s\s*=\s*["\'][^"\']*["\'];' % re.escape(location), body):
              location = re.search(r'%s\s*=\s*["\']([^"\']*)["\'];' % re.escape(location), body).group(1)
            else:
              location = None

        if location:
          logging.debug("JavaScript redirect", location)
        else:
          logging.debug("No location found")

      if(location):
        location = self.expandLocation(location.strip(), previousLocation)

    return location

  def _get(self, location, referrer = None):
    response = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.INTERFACE, self.interface.interface)
    curl.setopt(curl.TIMEOUT, 5)
    #curl.setopt(curl.TIMEOUT, 10)
    curl.setopt(curl.COOKIEJAR, self.cookieJar)
    if referrer:
      curl.setopt(curl.COOKIEFILE, self.cookieJar)
      curl.setopt(curl.REFERER, referrer)
    curl.setopt(curl.HEADER, True)
    curl.setopt(curl.URL, location)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    try:
      curl.perform()
      response = response.getvalue()
      if response:
        response = response.decode('utf-8')
    except Exception as e:
      logger.error("%s: Failed to retrieve %s" % (self.interface.interface, location))
      logger.error(e)
      response = None
    curl.close()

    logging.debug(response)

    #self.lastResponse = response
    #self.lastLocation = location

    return response

  # Gets the HTML of a given location
  def get(self, location, referrer = None, followRedirects = False):
    response = None

    if followRedirects:
      while location:
        response = self._get(location, referrer)
        if not referrer:
          self.logFileCounter = 0
          self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
          logging.debug("Timestamp %s" % self.timestamp)
        #self.logResponse(response, location)
        if self.logging:
          self.responses.append((response, location))
        referrer = location
        location = self.getLocationRedirect(response, location)
    else:
      response = self._get(location, referrer)
      #self.logResponse(response, location)
      if self.logging:
        self.responses.append((response, location))
      referrer = location

    return (referrer , response)

  def _post(self, location, formFields, referrer = None, headers = None, cookies = None):
    response = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.INTERFACE, self.interface.interface)
    curl.setopt(curl.COOKIEJAR, self.cookieJar)
    if referrer:
      curl.setopt(curl.COOKIEFILE, self.cookieJar)
      curl.setopt(curl.REFERER, referrer)
    curl.setopt(curl.HEADER, True)
    curl.setopt(curl.POST, True)
    curl.setopt(curl.POSTFIELDS, urllib.parse.urlencode(formFields))
    curl.setopt(curl.URL, location)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    try:
      curl.perform()
      response = response.getvalue()
      if response:
        response = response.decode('utf-8')
    except Exception as e:
      logger.error("%s: Failed to retrieve %s" % (self.interface.interface, location))
      logger.error(e)
      response = None
    curl.close()

    logging.debug(response)

    #self.lastResponse = response
    #self.lastLocation = location

    return response

  def post(self, location, formFields, referrer = None, followRedirects = False):
    response = None

    response = self._post(location, formFields, referrer)
    #self.logResponse(response, location)
    if self.logging:
      self.responses.append((response, location))
    referrer = location

    if followRedirects:
      location = self.getLocationRedirect(response, location)
      while location:
        response = self._get(location, referrer)
        #self.logResponse(response, location)
        if self.logging:
          self.responses.append((response, location))
        referrer= location
        location = self.getLocationRedirect(response, location)

    return (referrer, response)
