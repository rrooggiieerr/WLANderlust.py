import threading, subprocess, logging, time, bottle

installPackageThread = None
logger = logging.getLogger(__name__)
stdout = ""

#apt update
#apt -y dist-upgrade

def installPackageThreadImpl(package):
  global stdout

  logger.info("Installing %s" % package)
  #subprocess.Popen(['/usr/bin/apt', 'install', '-y', package], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  #proc = subprocess.Popen(['/bin/true'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  proc = subprocess.Popen(['/bin/cat', '/etc/rsyslog.conf'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
  stdout = ""
  while proc.poll() == None:
    stdout += proc.stdout.read().decode()
    logger.debug(stdout)
    #print(stdout)
  proc.stdout.close()

  if proc.poll() != 0:
    logger.error("%s package could not be installed" % package)
    return False

  return True

def installPackage(package, _async = False):
  #from WLANderlust.networking import Networking
  #if not Networking.getInstance().isOnline():
  #  logger.error("Not online")
  #  return False

  global installPackageThread, stdout

  if not installPackageThread:
    logger.debug("Starting package installation thread")
    print("Starting package installation thread")

    stdout = ""
    installPackageThread = threading.Thread(target = installPackageThreadImpl, args = [package])
    installPackageThread.start()

    logger.debug("Started package installation thread")
    print("Started package installation thread")

  if not _async:
    while installPackageThread.is_alive():
      time.sleep(0.1)
    installPackageThread.join()
    installPackageThread = None


@bottle.get('/install/stdout')
def getStdout():
  if not installPackageThread and stdout == "":
    bottle.response.status = 404
  elif installPackageThread and installPackageThread.is_alive():
    bottle.response.status = 206
    return stdout
  else:
    bottle.response.status = 200
    return stdout

    
