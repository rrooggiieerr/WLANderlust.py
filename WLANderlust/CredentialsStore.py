import os, re, time, sqlite3, json, logging

logger = logging.getLogger(__name__)

# Regexp implementation for sqlite
# Example code from https://stackoverflow.com/questions/5365451/problem-with-regexp-python-and-sqlite
def regexp(expr, item):
  if item:
    reg = re.compile(expr)
    if reg.search(item):
      return True
  return False

def bssid2int(bssid):
  if not bssid:
    return None
  return int(bssid.translate(str.maketrans('', '', ":.-, ")), 16)

class CredentialsStore():
  __instance = None
  credentialsStoreDB = None

  @staticmethod
  def getStore():
    if not CredentialsStore.__instance:
      CredentialsStore()
    return CredentialsStore.__instance

  def __init__(self):
    if CredentialsStore.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      CredentialsStore.__instance = self

    logger.info("Starting Credentials Store")

    credentialsStoreDBFile = "/etc/WLANderlust/WLANderlust.credentials.db"

    if not os.path.isfile(credentialsStoreDBFile):
      logger.info("Creating Credentials Store database %s" % credentialsStoreDBFile)
    logger.info("Opening Credentials Store database %s" % credentialsStoreDBFile)

    try:
      self.credentialsStoreDB = sqlite3.connect(credentialsStoreDBFile, check_same_thread=False)
      self.credentialsStoreDB.create_function("REGEXP", 2, regexp)
      self.credentialsStoreDB.execute("CREATE TABLE IF NOT EXISTS credentialsStore (bssid INTEGER, ssid TEXT, domain TEXT, timestamp INTEGER NOT NULL, share BOOLEAN NOT NULL, credentials TEXT NOT NULL)")
      self.credentialsStoreDB.execute("CREATE UNIQUE INDEX IF NOT EXISTS bssid ON credentialsStore(bssid)")
      self.credentialsStoreDB.execute("CREATE UNIQUE INDEX IF NOT EXISTS ssid_domain ON credentialsStore(ifnull(ssid, 0), domain)")

      if logger.isEnabledFor(logging.DEBUG):
        cur = self.credentialsStoreDB.cursor()
        cur.execute("SELECT count(*) FROM credentialsStore")
        n = cur.fetchone()
        logger.debug("Nr of Credentials stored: %s" % n)
    except sqlite3.Error as e:
      logger.error(e)

    logger.info("Started Credentials Store")

  def __del__(self):
    logger.info("Stopping Credentials Store")

    if self.credentialsStoreDB:
      try:
        if logger.isEnabledFor(logging.DEBUG):
          cur = self.credentialsStoreDB.cursor()
          cur.execute("SELECT count(*) FROM credentialsStore")
          n = cur.fetchone()
          logger.debug("Nr of Credentials stored: %s" % n)

        logger.info("Closing Credentials Store database")
        self.credentialsStoreDB.close()
      except sqlite3.Error as e:
        logger.error(e)

    logger.info("Stopped Credentials Store")

  def stop(self):
    ''' '''

  def getCredentials(self, bssid, ssid, domain):
    credentials = None

    if not self.credentialsStoreDB:
      logger.error("Credentials Store not available")
      return None
    if not bssid and not ssid and not domain:
      logger.error("At least one of BSSID, SSID or domain needs to be given")
      return None
    if bssid and (ssid or domain):
      logger.error("if BSSID is given no SSID or domain can be given")
      return None

    logger.debug("Getting credentials for ('%s', '%s', '%s')" % (bssid, ssid, domain))

    if bssid:
      try:
        cur = self.credentialsStoreDB.cursor()
        cur.execute("SELECT credentials FROM credentialsStore WHERE bssid = ? AND ssid IS NULL AND domain IS NULL ORDER BY timestamp", (bssid2int(bssid),))
        credentials = cur.fetchone()
        logger.debug("Found credentials: %s" % credentials)
      except sqlite3.Error as e:
        logger.error(e)

    if ssid or domain:
      try:
        cur = self.credentialsStoreDB.cursor()
        cur.execute("SELECT credentials FROM credentialsStore WHERE bssid IS NULL AND (ssid = ? OR domain = ?) ORDER BY timestamp", (ssid, domain))
        credentials = cur.fetchone()
        logger.debug("Found credentials: %s" % credentials)
      except sqlite3.Error as e:
        logger.error(e)

    if not credentials:
      logger.info("No credentials found")
      return None

    credentials = json.loads(credentials[0])
    logger.debug("Found credentials: %s" % credentials)

    return credentials

  def setCredentials(self, bssid, ssid, domain, share, credentials):
    if not credentials:
      logger.error("No credentials given")
      return False

    if not self.credentialsStoreDB:
      logger.error("Credentials Store not available")
      return False
    if not bssid and not ssid and not domain:
      logger.error("At least one of BSSID, SSID or domain needs to be given")
      return False
    if bssid and (ssid or domain):
      logger.error("If BSSID is given no SSID or domain can be given")
      return False

    logger.debug("Adding credentials for ('%s', '%s', '%s')" % (bssid, ssid, domain))
    logger.debug("Credentials: '%s'" % credentials)
    logger.debug("Share: '%s'" % share)

    try:
      cur = self.credentialsStoreDB.cursor()
      cur.execute("REPLACE INTO credentialsStore(bssid, ssid, domain, timestamp, share, credentials) values(?, ?, ?, ?, ?, ?)",
        (bssid2int(bssid), ssid, domain, time.time(), share, json.dumps(credentials)))
      self.credentialsStoreDB.commit()
      logger.debug("Credentials added")
    except sqlite3.Error as e:
      logger.error(e)

  def deleteCredentials(self, bssid, ssid, domain):
    if not self.credentialsStoreDB:
      logger.error("Credentials Store not available")
      return False
    if not bssid and not ssid and not domain:
      logger.error("At least one of BSSID, SSID or domain needs to be given")
      return False
    if bssid and (ssid or domain):
      logger.error("if BSSID is given no SSID or domain can be given")
      return False

    logger.debug("Deleting credentials for ('%s', '%s', '%s')" % (bssid, ssid, domain))

    try:
      cur = self.credentialsStoreDB.cursor()
      cur.execute("DELETE FROM credentialsStore WHERE bssid IS ? AND ssid IS ? AND domain IS ?", (bssid2int(bssid), ssid, domain))
      self.credentialsStoreDB.commit()
      logger.debug("Credentials deleted")
    except sqlite3.Error as e:
      logger.error(e)
