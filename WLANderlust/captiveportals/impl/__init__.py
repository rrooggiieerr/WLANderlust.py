from .Failure import Failure
from .NotAny import NotAny
from .Curl import Curl
from .Fon import Fon
from .ATCafe import ATCafe
#from .Mikrotik import Mikrotik
#from .SpotHub import SpotHub
#from .Waveloc import Waveloc
#from .Xfinity import Xfinity
#from .KPN import KPN
from .WISPA import WISPA
from .Form import Form
from .Ahref import Ahref
from .Unknown import Unknown

import sys, inspect

def getImplementations():
  return sorted(inspect.getmembers(sys.modules[__name__], inspect.isclass), key=lambda member: member[1].order)
