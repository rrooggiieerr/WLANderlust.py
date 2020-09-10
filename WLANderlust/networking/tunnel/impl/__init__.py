from .IODine import IODine
from .ICMPTX import ICMPTX

import sys, inspect

def getImplementations():
  return inspect.getmembers(sys.modules[__name__], inspect.isclass)

def getClass(type):
  m = __import__('WLANderlust')
  m = getattr(m, 'networking')
  m = getattr(m, 'tunnel')
  m = getattr(m, 'impl')
  return  getattr(m, type)
