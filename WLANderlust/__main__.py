import atexit, os, signal, sys, time, logging, argparse

from WLANderlust.plugins import Plugins
from WLANderlust import CredentialsStore, BSSIDLocationCache, GPS, config
from WLANderlust.networking import Networking
from WLANderlust.captiveportals import CaptivePortalSupervisor, CaptivePortalSolverCache
import WLANderlust.WebInterface

logger = logging.getLogger(__name__)
loglevel = logging.INFO

### WLANderlust Daemon ###
class WLANderlustDaemon(object):
  terminate = False

  pidFile = '/var/run/WLANderlustd.pid'
  logFile = '/var/log/WLANderlustd.log'

  def __init__(self, foreground):
    self.foreground = foreground

    #self.stdout = '/dev/stdout'
    #self.stderr = '/dev/stderr'

    if self.foreground:
      logging.basicConfig(format='%(levelname)-8s %(name)s.%(funcName)s() %(message)s', level=loglevel)
    else:
      logging.basicConfig(filename=self.logFile, format='%(asctime)s %(levelname)-8s %(name)s.%(funcName)s() %(message)s', datefmt='%x %X', level=loglevel)

  def delPID(self):
    """ Delete the pid file. """
    os.remove(self.pidFile)

  def daemonize(self):
    # fork 1 to spin off the child that will spawn the daemon
    if os.fork():
      sys.exit()

    # This is the child.
    # 1. cd to root for a guarenteed working dir
    # 2. clear the session id to clear the controlling TTY
    # 3. set the umask so we have access to all files created by the daemon
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # fork 2 ensures we can't get a controlling ttd.
    if os.fork():
      sys.exit()

    # This is a child that can't ever have a controlling TTY.
    # Now we shut down stdin and point stdout/stderr at log files.

    # stdin
    with open('/dev/null', 'r') as dev_null:
      os.dup2(dev_null.fileno(), sys.stdin.fileno())

    # stderr - do this before stdout so that errors about setting stdout write to the log file.
    #
    # Exceptions raised after this point will be written to the log file.
    sys.stderr.flush()
    #with open(self.stderr, 'a+') as stderr:
    #  os.dup2(stderr.fileno(), sys.stderr.fileno())

    # stdout
    #
    # Print statements after this step will not work. Use sys.stdout
    # instead.
    sys.stdout.flush()
    #with open(self.stdout, 'a+') as stdout:
    #  os.dup2(stdout.fileno(), sys.stdout.fileno())

  def get_pid_by_file(self):
    """ Return the WLANderlust daemon pid read from the pid file. """

    try:
      with open(self.pidFile, 'r') as pidFile:
        pid = int(pidFile.read().strip())
      return pid
    except IOError:
      return

  def start(self):
    """ Start the WLANderlust daemon """

    pid = self.get_pid_by_file()
    if pid:
      logger.warning('PID file %s exists', self.pidFile)
      try:
        logger.debug('Is the daemon already running?')
        os.kill(pid, 0)
        logger.warning('Daemon already running')
        sys.exit(1)
      except ProcessLookupError:
        # ESRCH == No such process
        logger.warning('Daemon not running, orphaned PID file')
        os.remove(self.pidFile)

    logger.info("Starting...")

    signal.signal(signal.SIGINT, self.stop)
    signal.signal(signal.SIGTERM, self.stop)

    if self.foreground:
      try:
        self.run()
      except (KeyboardInterrupt):
        self.stop()
    else:
      self.daemonize()
      self.run()

  def stop(self ,signum = None, frame = None):
    """ Stop the WLANderlust daemon """

    logger.info("Stopping WLANderlust daemon")
    self.terminate = True

    Networking.getInstance().stop()
    GPS.getInstance().stop()
    Plugins.getInstance().stop()
    BSSIDLocationCache.getCache().stop()
    CaptivePortalSolverCache.getCache().stop()
    CredentialsStore.getStore().stop()

    logger.info("Stopped WLANderlust daemon")

  def run(self):
    """ The main loop of the WLANderlust daemon """
    # Write pid file
    # Before file creation, make sure we'll delete the pid file on exit!
    atexit.register(self.delPID)
    with open(self.pidFile, 'w+') as pidFile:
      pidFile.write(str(os.getpid()))

    # Create threads
    CredentialsStore.getStore()
    CaptivePortalSolverCache.getCache()
    BSSIDLocationCache.getCache()
    Plugins.getInstance()
    GPS.getInstance()
    Networking.getInstance().start()

    while not self.terminate:
      time.sleep(0.1)

  def kill(self):
    pid = self.get_pid_by_file()
    if not pid:
      logger.warning("PID file %s doesn't exist. Is the WLANderlust daemon not running?" % self.pidFile)
      sys.exit(1)
    else:
      # Time to kill.
      count = 0
      try:
        print("Stopping WLANderlust daemon with PID %s " % pid, end='', flush=True)
        while True:
          if count == 60:
            os.kill(pid, signal.SIGHUP)
          os.kill(pid, signal.SIGTERM)
          print(".", end='', flush=True)
          time.sleep(1)
          count += 1
      except OSError as err:
        #if 'No such process' in err.strerror and os.path.exists(self.pidFile):
        #  os.remove(self.pidFile)
        if not 'No such process' in err.strerror:
          logger.error(err)
          sys.exit(1)
      print(" OK")

def main():
  # Read command line arguments
  argparser = argparse.ArgumentParser()
  argparser.add_argument('action', choices=['start', 'stop', 'restart'])
  argparser.add_argument("-f", "--foreground", dest="foreground", action="store_const", const=True)
  #argparser.add_argument("--disableplugins", dest="enablePlugins", action="store_false")
  #argparser.add_argument("--verbose", dest="verboseLogging", action="store_true")
  argparser.add_argument("--debug", dest="debugLogging", action="store_true")
  #argparser.add_argument("--solve", dest="solveCaptivePortal", action="store_true")
  #argparser.add_argument("--scan", dest="scan", action="store_true")
  #argparser.add_argument("--reassociate", dest="autoReassociateWiFi", action="store_true")
  #argparser.add_argument("--web", dest="webInterface", action="store_true")
  args = argparser.parse_args()

  if args.debugLogging:
    global loglevel
    loglevel = logging.DEBUG

  daemon = WLANderlustDaemon(args.foreground)

  if args.action in ['stop', 'restart']:
    daemon.kill()

  if args.action in ['start', 'restart']:
    daemon.start()

if __name__ == '__main__':
  main()
