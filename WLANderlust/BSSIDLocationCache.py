import os, sqlite3, threading, time, re, pycurl, logging
from io import BytesIO

from WLANderlust import config

logger = logging.getLogger(__name__)

def bssid2int(bssid):
  if not bssid:
    return None
  return int(bssid.translate(str.maketrans('', '', ":.-, ")), 16)
  #ToDo test if result is same as translate method
  #return int(bssid.replace(':', ''), 16)

class BSSIDLocationCache():
  debug = False
  __instance = None

  bssidLocationCacheDB = None
  onlineLookupThread = None
  pauseOnlineLookup = True
  bssidLookupQueue = []
  terminate = False

  @staticmethod
  def getCache():
    logger.debug("Get instance")
    if not BSSIDLocationCache.__instance:
      logger.debug("Creating instance")
      BSSIDLocationCache()
    return BSSIDLocationCache.__instance

  def __init__(self):
    if BSSIDLocationCache.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      BSSIDLocationCache.__instance = self

    self.logger = logging.getLogger("%s()" % (self.__class__.__name__))
    self.logger.info("Starting BSSID Location Cache")

    bssidLocationCacheDBFile = "/etc/WLANderlust/BSSID.location.cache.db"

    if not os.path.isfile(bssidLocationCacheDBFile):
      self.logger.info("Creating BSSID Location Cache database")
    self.logger.info("Opening BSSID Location Cache database")

    try:
      self.bssidLocationCacheDB = sqlite3.connect(bssidLocationCacheDBFile, check_same_thread=False)
      self.bssidLocationCacheDB.execute("CREATE TABLE IF NOT EXISTS bssidCache (bssid INTEGER PRIMARY KEY NOT NULL, timestamp INTEGER NOT NULL, latitude REAL, longitude REAL);")
      #self.bssidLocationCacheDB.execute("CREATE UNIQUE INDEX IF NOT EXISTS bssid ON bssidCache(bssid)")

      if self.debug:
        cur = self.bssidLocationCacheDB.cursor()
        cur.execute("SELECT count(*) FROM bssidCache")
        n = cur.fetchone()
        self.logger.debug("Nr of BSSID Location Cache entries: %s" % n)
    except sqlite3.Error as e:
      logging.error(e)

    self.onlineLookupThread = threading.Thread(target = self.onlineLookupThreadImpl, name = "BSSID Location Cache Online Lookup")
    self.onlineLookupThread.start()

    self.logger.info("Started BSSID Location Cache")

  def stop(self):
    self.logger.info("Stopping BSSID Location Cache")
    self.terminate = True

    # Wait for threads to finish
    if self.onlineLookupThread:
      self.onlineLookupThread.join()

    if self.bssidLocationCacheDB:
      try:
        if self.debug:
          cur = self.bssidLocationCacheDB.cursor()
          cur.execute("SELECT count(*) FROM bssidCache")
          n = cur.fetchone()
          self.logger.debug("Nr of BSSID Location Cache entries: %s" % n)

        self.logger.info("Closing BSSID Location Cache database")
        self.bssidLocationCacheDB.close()
      except Error as e:
        logging.error(e)

    self.logger.info("Stopped BSSID Location Cache")

  def lookup(self, bssid, signal):
    """ Lookup Access Point BSSID in location cache """
    location = None

    if self.bssidLocationCacheDB:
      self.logger.debug("Looking up %s in location cache" % bssid)
      cur = self.bssidLocationCacheDB.cursor()
      cur.execute("SELECT timestamp, latitude, longitude FROM bssidCache WHERE bssid = ?", (bssid2int(bssid),))
      entry = cur.fetchone()

      if not entry:
        self.logger.debug("No location cache entry found for %s" % bssid)
        if bssid not in [i[0] for i in self.bssidLookupQueue]:
          self.bssidLookupQueue.append([bssid, signal])
      elif (entry[1] == None or entry[2] == None) and time.time() - entry[0] > 86400:
        self.logger.debug("Location cache entry for %s expired" % bssid)
        if bssid not in [i[0] for i in self.bssidLookupQueue]:
          self.bssidLookupQueue.append([bssid, signal])
      elif time.time() - entry[0] > 86400:
        self.logger.debug("Location cache entry for %s expired" % bssid)
        if bssid not in [i[0] for i in self.bssidLookupQueue]:
          self.bssidLookupQueue.append([bssid, signal])
      elif entry[1] == None or entry[2] == None:
        self.logger.debug("Empty location cache entry for %s found" % bssid)
      else:
        self.logger.debug("Location cache entry for  %s found: %s" % (bssid, entry))

      self.logger.debug("bssidLookupQueue:", [i[0] for i in self.bssidLookupQueue])

      if entry and entry[1] and entry[2]:
        location = [entry[1], entry[2]]

    return location

  def onlineLookupThreadImpl(self):
    self.logger.info("Starting online BSSID location lookup thread")

    queueSize = 0
    while not self.terminate:
      if self.pauseOnlineLookup:
        time.sleep(0.1)
        continue

      if queueSize != len(self.bssidLookupQueue):
        queueSize = len(self.bssidLookupQueue)
        if queueSize == 0:
          self.logger.debug("BSSID lookup queue is empty")
        if queueSize > 0:
          self.logger.debug("BSSID lookup queue contains %s item(s)" % queueSize)

      if queueSize == 0:
        time.sleep(0.1)
        continue

      bssid, signal = self.bssidLookupQueue[0]

      self.logger.debug("Looking up location of %s online" % bssid)
      try:
        bssid = bssid.replace(':', '')
        url = "http://mobile.maps.yandex.net/cellid_location/?wifinetworks=%s:%s" % (bssid, signal)
        self.logger.debug("BSSID lookup URL:", url)

        response = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEFUNCTION, response.write)
        curl.perform()

        latitude = None
        longitude = None
        if curl.getinfo(curl.HTTP_CODE) == 200:
          response = response.getvalue().decode('utf-8')
          self.logger.debug(response)
          latitude = float(re.compile(" latitude=\"([0-9.]*)\".*", re.MULTILINE).search(response).group(1))
          longitude = float(re.compile(" longitude=\"([0-9.]*)\".*", re.MULTILINE).search(response).group(1))
          location = [latitude, longitude]
          self.logger.debug("Location of %s found online %s" % (bssid, location))
        else:
          self.logger.debug("Location of %s not found online" % bssid)
        curl.close()

        cur = self.bssidLocationCacheDB.cursor()
        cur.execute("DELETE FROM bssidCache WHERE bssid = ?", (bssid2int(bssid),))
        cur.execute("INSERT INTO bssidCache(bssid, timestamp, latitude, longitude) values(?, ?, ?, ?)", (bssid2int(bssid), time.time(), latitude, longitude))
        self.bssidLocationCacheDB.commit()

        # Remove BSSID from lookup queue
        self.bssidLookupQueue.pop(0)
      except Exception as e:
        logging.error("Failed to look up location of %s online" % bssid)
        logging.error(e)

    self.logger.info("Stopped online BSSID location lookup thread")

  def online(self, outwardInterface):
    self.logger.debug("BSSIDLocationCache.online(%s)" % outwardInterface.interface)
    self.pauseOnlineLookup = False

  def offline(self, outwardInterface):
    self.logger.debug("BSSIDLocationCache.offline(%s)" % outwardInterface.interface)
    self.pauseOnlineLookup = True
