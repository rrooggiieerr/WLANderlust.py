import logging

from argparse import ArgumentParser

from WLANderlust import WLANderlustDaemon

if __name__ == '__main__':
  # Read command line arguments
  argparser = ArgumentParser()
  argparser.add_argument('action', choices=['start', 'stop', 'restart'])
  argparser.add_argument("-f", "--foreground", dest="foreground", action="store_const", const=True)
  #argparser.add_argument("--disableplugins", dest="enablePlugins", action="store_false")
  #argparser.add_argument("--verbose", dest="verboseLogging", action="store_true")
  #argparser.add_argument("--debug", dest="debugLogging", action="store_true")
  #argparser.add_argument("--solve", dest="solveCaptivePortal", action="store_true")
  #argparser.add_argument("--scan", dest="scan", action="store_true")
  #argparser.add_argument("--reassociate", dest="autoReassociateWiFi", action="store_true")
  #argparser.add_argument("--web", dest="webInterface", action="store_true")
  args = argparser.parse_args()

  daemon = WLANderlustDaemon(args.foreground)

  if args.action in ['stop', 'restart']:
    daemon.kill()

  if args.action in ['start', 'restart']:
    daemon.start()
