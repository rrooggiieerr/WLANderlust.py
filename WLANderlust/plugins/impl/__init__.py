from .UpdateDebian import UpdateDebian
from .WiGLE import WiGLE

import sys, inspect

def getImplementations():
  return inspect.getmembers(sys.modules[__name__], inspect.isclass)
