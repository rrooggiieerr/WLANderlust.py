import os, json, logging, time

class Config(dict):
  configFile = None

  logger = logging.getLogger(__name__)

  def __init__(self):
    super().__init__()

    if os.geteuid() == 0:
      self.configFile = '/etc/WLANderlust/WLANderlust.conf.json'
    else:
      self.configFile = os.getenv('HOME') + '.WLANderlust.conf.json'
    self.logger.debug("Configuration file: %s", self.configFile)

    if os.path.isfile(self.configFile):
      st = os.stat(self.configFile)
      if oct(st.st_mode) != "0o100600":
        self.logger.warning("Warning: Incorrect WLANderlust configuration file permissions")

      self.logger.info("Reading WLANderlust configuration")
      with open(self.configFile, 'r') as f:
        super().clear()
        try:
          super().update(json.load(f))
        except json.JSONDecodeError as e:
          self.logger.fatal(e)

  def save(self):
    self.logger.info("Saving WLANderlust configuration")

    #ToDo Create directory
    if not os.path.isfile(self.configFile):
      self.logger.info("Creating configuration file")
      with open(self.configFile, 'a') as f:
        os.utime(self.configFile, time)
        os.chmod(self.configFile, 0o600)

    with open(self.configFile, 'w') as f:
      json.dump(self, f, indent=4)

config = Config()
