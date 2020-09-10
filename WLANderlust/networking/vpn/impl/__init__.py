from .IPsec import IPsec
from .L2TP import L2TP
from .OpenVPN import OpenVPN
from .PPTP import PPTP
from .SSHTunnel import SSHTunnel
from .SSHuttle import SSHuttle

import sys, inspect

def getImplementations():
  return inspect.getmembers(sys.modules[__name__], inspect.isclass)

def getClass(type):
  m = __import__('WLANderlust')
  m = getattr(m, 'networking')
  m = getattr(m, 'vpn')
  m = getattr(m, 'impl')
  return  getattr(m, type)
