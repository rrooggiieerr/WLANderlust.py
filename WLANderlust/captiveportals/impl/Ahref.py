# WLANderlust
#
# Captive portal detection for 'click trough' <a href= based Captive Portals
#
# <a href='s are in almost all pages, so this is realy a lucky shot.
# That's why this script is run last
#
# https://en.wikipedia.org/wiki/Captive_portal
#
# Rogier van Staveren, February 2020, initial development release

import re

from WLANderlust.captiveportals import CaptivePortalSolverImpl, CaptivePortalSolverCache

'''
if grep -i -q '<a .*href="' <<< "$BODY"; then
	# Get all the <a href tags which are no anchor
	AHREFS=`echo "$BODY" | tr -d '\n\r' | sed 's|\(</a>\)|\1\x0D|I' | sed -n "s|^.*\(<a [^>]*href=[\"'][^\"'#][^\"'#]*[\"'][^>]*>.*</a>\).*$|\1|Ip"`
	OIFS="$IFS"
	IFS=$'\n'
	for AHREF in $AHREFS; do
		HREF=`echo "$AHREF" | tr -d '\n\r' | sed 's|.*<a [^>]*href="\([^"]*\)".*</a>.*|\1|'`
		HREF=`expandLocation "$HREF" "$LOCATION"`
		$DEBUGLOGGING && logMessage "A HREF detected: \"$HREF\""
		curlGet "$HREF"
		getLocationRedirect "$BODY" "$LOCATION"
		getBody "$LOCATION" true

		# Check if Captive Portal has been resolved
		if grep -q "$CAPTIVEPORTALDETECTIONRESPONSE" <<< "$BODY"; then
			# Ok, we were able to authenticate
			logMessage 'a href based captive portal detected'
			setState 'CAPTIVEPORTALSTATE' 'solved'
			logMessage 'Captive portal succesfully solved'
			CAPTIVEPORTALTYPE='a href'
			break
		elif checkCaptivePortalPresence; then
			logMessage 'Captive portal still present'
		elif [ "$CAPTIVEPORTALSTATE" = 'solved' ]; then
			# Ok, we were able to authenticate
			logMessage 'a href based captive portal detected'
			logMessage 'Captive portal succesfully solved'
			CAPTIVEPORTALTYPE='a href'
			break
		fi
	done
	IFS="$OIFS"
fi
'''

class Ahref(CaptivePortalSolverImpl):
  name = "a href"

  # The max size for an unsigned int, this implementation should be last
  order = 1200

  def detect(self, bssid, ssid, location = None, body = None):
    if body:
      if re.search(r"<a\b.*\bhref=", body, re.IGNORECASE | re.MULTILINE):
        self.detectionMethod = 'contentmatch'
        if bssid:
          CaptivePortalSolverCache.getCache().store(bssid, type(self).__name__)
        return True
    else:
      return super().detect(bssid, ssid)
