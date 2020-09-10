from WLANderlust.captiveportals import CaptivePortalSolverImpl

# This seems to be a popular WiFi provider in the USA
# https://gist.github.com/aanarchyy/847f3c703be08856c0b3ab62db340b22
class Xfinity(CaptivePortalSolverImpl):
  name = "Xfinity"
  ssids = ['xfinitywifi']
