def readPID(pidFile):
  pid = None

  while not os.path.exists(pidFile):
    time.sleep(0.1)

  # Read the PID from the PID file
  try:
    with open(pidFile, 'r') as pidFile:
      pid = int(pidFile.read().strip())
  except IOError:
    print("Failed to read PID from %s" % pidFile)

  if debug: print("PID: %s" % pid)
  return pid

def isRunning(pid):
  try:
    os.kill(self.pid, 0)
  except ProcessLookupError:
    # ESRCH == No such process
    print("Process with PID %s is not running" % pid)
    return False

  if self.debug: print("Process with PID %s is running" % pid)

  return True

def stopPID(pid):
  if not pid:
    return False

  try:
    print("Stopping process with PID %s" % pid)
    os.kill(self.pid, signal.SIGTERM)
  except ProcessLookupError as e:
    print("Failed to stop process with PID %s" % pid)
    print(e)
    return False

  if os.path.exists(pidFile):
    os.remove(self.pidFile)
  print("Stopped process with PID %s" % pid)

  return True
