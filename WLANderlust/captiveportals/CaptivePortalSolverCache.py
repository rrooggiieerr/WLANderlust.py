import os, time, sqlite3, logging

from WLANderlust import config

logger = logging.getLogger(__name__)
def bssid2int(bssid):
  if not bssid:
    return None
  return int(bssid.translate(str.maketrans('', '', ":.-, ")), 16)

class CaptivePortalSolverCache():
  debug = False
  __instance = None

  captivePortalSolverCacheDB = None

  @staticmethod
  def getCache():
    if not CaptivePortalSolverCache.__instance:
      CaptivePortalSolverCache()
    return CaptivePortalSolverCache.__instance

  def __init__(self):
    if CaptivePortalSolverCache.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      CaptivePortalSolverCache.__instance = self

    logger.info("Initialising Captive Portal Solver Cache")

    captivePortalSolverCacheDBFile = "/etc/WLANderlust/CaptivePortal.solver.cache.db"
    if not os.path.isfile(captivePortalSolverCacheDBFile):
      logger.info("Creating Captive Portal Solver Cache database")
    logger.info("Opening Captive Portal Solver Cache database")

    try:
      self.captivePortalSolverCacheDB = sqlite3.connect(captivePortalSolverCacheDBFile, check_same_thread=False)
      self.captivePortalSolverCacheDB.execute("CREATE TABLE IF NOT EXISTS captivePortalSolverCache (bssid INTEGER PRIMARY KEY NOT NULL, timestamp INTEGER NOT NULL, solver TEXT NOT NULL);")

      if self.debug:
        cur = self.captivePortalSolverCacheDB.cursor()
        cur.execute("SELECT count(*) FROM captivePortalSolverCache")
        n = cur.fetchone()
        logger.debug("Nr of Captive Portal Solver Cache entries: %s" % n)
    except sqlite3.Error as e:
      logger.error(e)

    logger.info("Initialised Captive Portal Solver Cache")

  #RS def __del__(self):
  def stop(self):
    logger.info("Stopping Captive Portal Solver Cache")

    if self.captivePortalSolverCacheDB:
      try:
        if self.debug:
          cur = self.captivePortalSolverCacheDB.cursor()
          cur.execute("SELECT count(*) FROM captivePortalSolverCache")
          n = cur.fetchone()
          logger.debug("Nr of Captive Portal Solver Cache entries: %s" % n)

        logger.info("Closing Captive Portal Solver Cache database")
        self.captivePortalSolverCacheDB.close()
      except sqlite3.Error as e:
        logger.error(e)

    logger.info("Stopped Captive Portal Solver Cache")

  def lookup(self, bssid):
    """ Lookup Access Point BSSID in Captive Portal Solver Cache """
    solver = None

    if not bssid:
      return None

    if not self.captivePortalSolverCacheDB:
      return None

    if self.captivePortalSolverCacheDB:
      #logger.debug("Looking up %s in Captive Portal Solver cache" % bssid)
      cur = self.captivePortalSolverCacheDB.cursor()
      cur.execute("SELECT solver FROM captivePortalSolverCache WHERE bssid = ?", (bssid2int(bssid),))
      entry = cur.fetchone()

      if entry:
        logger.debug("Captive Portal Solver cache entry for %s found: %s" % (bssid, entry))
        solver = entry[0]
      #else:
      #  logger.debug("No Captive Portal Solver cache entry found for %s" % bssid)

    return solver

  def store(self, bssid, solver):
    if not bssid or not solver:
      return False

    if not self.captivePortalSolverCacheDB:
      return False

    previousSolver = self.lookup(bssid)
    if solver == previousSolver:
      return True

    if previousSolver and solver == 'None':
      return False

    try:
      cur = self.captivePortalSolverCacheDB.cursor()
      cur.execute("INSERT OR REPLACE INTO captivePortalSolverCache(bssid, timestamp, solver) values(?, ?, ?)",
        (bssid2int(bssid), time.time(), solver))
      self.captivePortalSolverCacheDB.commit()
      return True
    except sqlite3.Error as e:
      logger.error(e)

    return False
