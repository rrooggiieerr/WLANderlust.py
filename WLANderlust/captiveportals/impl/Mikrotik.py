# WLANderlust
#
# Captive Portal solver for Mikrotik routers
#
# The Mikrotik routers use a login form with some client side JavaScript MD5 encryption
# The MD5 part still needs to be solved
#
# https://en.wikipedia.org/wiki/Captive_portal
# https://wiki.mikrotik.com/wiki/HotSpot_external_login_page
#
# Rogier van Staveren, February 2020, initial development release

from WLANderlust.captiveportals import CaptivePortalSolverImpl, CaptivePortalSolverCache

'''
BASH implemenation:

if tr -d '\n\r' <<< "$BODY" | grep -q "function doLogin() {[^}]*hexMD5([^}]*}"; then
	logMessage 'Mikrotik Captive Portal'
	CAPTIVEPORTALTYPE='Mikrotik'

	# Remove comments
	CLEANBODY=`tr -d '\n\r' <<< "$BODY" | sed 's|\(-->\)|\1\n|g' | sed 's|<!--.*-->||'`
	FORM=`sed 's|\(</form>\)|\1\n|Ig' <<< "$CLEANBODY" | sed -n "s|^.*\(<form [^>]*\bname=[\"']login[\"'][^>]*>.*</form>\)$|\1|Ip"`

	if [ -z "$FORM" ]; then
		logError "No login form found"
		# Maybe we can find an <a href=
		AHREF=`sed -n "s|.*<a [^>]*href=['\"]\([^\"]*/login\?[^\"]*\)\".*|\1|p" <<< "$CLEANBODY" | head -n 1`
		$DEBUGLOGGING && logMessage "AHREF=$AHREF"
		[ -z "$AHREF" ] &&
			setState 'CAPTIVEPORTALSTATE' 'failure' &&
			return 1
		AHREF=`sed 's|&amp;|\&|g' <<< "$AHREF"`
		$DEBUGLOGGING && logMessage "AHREF=$AHREF"
		curlGet "$AHREF"
		return
	fi

	_STOREUSERNAME='false'
	_STOREPASSWORD='false'

	USERNAME=`sed -n "s|^.*<input [^>]*\bname=[\"']username[\"'] [^>]*\bvalue=[\"']\([^\"']*\)[\"'][^>]*>.*$|\1|p" <<< "$FORM"`
	if [ -z "$USERNAME" ]; then
		USERNAME=`getCaptivePortalUsername "$BSSID" "$SSID" "$LOCATION"`
	fi
	# If interactive and empty username ask for username
	if $INTERACTIVE && [ -z "$USERNAME" ]; then
		read -r -p 'Username: ' -e USERNAME
		_STOREUSERNAME='true'
	fi

	PASSWORD=`sed -n "s|^.*<input [^>]*\bname=[\"']password[\"'] [^>]*\bvalue=[\"']\([^\"']*\)[\"'][^>]*>.*$|\1|p" <<< "$FORM"`
	if [ -z "$PASSWORD" ]; then
		 PASSWORD=`getCaptivePortalPassword "$BSSID" "$SSID" "$LOCATION"`
	fi
	# If interactive and empty password ask for password
	if $INTERACTIVE && [ -z "$PASSWORD" ]; then
		readPassword 'Password: '
		echo
		_STOREPASSWORD='true'
	fi

	if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
		logError "No login credentials for \"$BSSID\" \"$SSID\" \"$LOCATION\""
		setState 'CAPTIVEPORTALSTATE' 'failure'
		return 1
	fi

	# Values are in octal notation
	CHAPID=`sed -n "s|^.*hexMD5([\"']\([\\0-9]*\)[\"'] \+.*).*$|\1|p" <<< "$BODY"`
	$DEBUGLOGGING && logMessage "CHAPID=$CHAPID"
	CHAPCHALLENGE=`sed -n "s|^.*hexMD5(.*\+ [\"']\([\\0-9]*\)[\"']).*$|\1|p" <<< "$BODY"`
	$DEBUGLOGGING && logMessage "CHAPCHALLENGE=$CHAPCHALLENGE"
	PASSWORD=`printf '%b%s%b' "$CHAPID" "$PASSWORD" "$CHAPCHALLENGE"`
	$DEBUGLOGGING && logMessage "PASSWORD=$PASSWORD"
	# hexMD5 password
	PASSWORD=`echo -n "$PASSWORD" | md5sum | cut -d ' ' -f 1`
	$DEBUGLOGGING && logMessage "PASSWORD=$PASSWORD"

	FORM=`sed 's|\(</form>\)|\1\n|Ig' <<< "$CLEANBODY" | sed -n "s|^.*\(<form [^>]*\bname=[\"']sendin[\"'][^>]*>.*</form>\)$|\1|Ip"`
	[ -z "$FORM" ] &&
		logError 'No form' &&
		return 1

	FORMACTION=`sed -n "s|^.*<form [^>]*\baction=[\"']\([^\"']*\)[\"'][^>]*>.*$|\1|Ip" <<< "$FORM"`
	$DEBUGLOGGING && logMessage "FORMACTION=$FORMACTION"
	[ -z "$FORMACTION" ] &&
		logError 'No form action'
	FORMACTION=`expandLocation "$FORMACTION" "$LOCATION"`
	$DEBUGLOGGING && logMessage "FORMACTION=$FORMACTION"

	# Loop trough the inputs and build the post data
	INPUTS=`sed 's|>|&\n|g' <<< "$FORM" | sed -n 's|.*\(<input [^>]*>\)$|\1|Ip'`
	OIFS="$IFS"
	IFS='
'
	for INPUT in $INPUTS; do
		INPUTNAME=`sed -n "s|.* name=[\"']\([^\"']*\)[\"'].*|\1|Ip" <<< "$INPUT"`
		case "$INPUTNAME" in
			username)
				INPUTVALUE="$USERNAME"
				;;
			password)
				INPUTVALUE="$PASSWORD"
				;;
			*) INPUTVALUE=`sed -n "s|.* value=[\"']\([^\"']*\)[\"'].*|\1|Ip" <<< "$INPUT"` ;;
		esac
		[ ! -z "$POSTDATA" ] && POSTDATA+="&"
		POSTDATA+="$INPUTNAME=$INPUTVALUE"
	done
	IFS="$OIFS"
	logMessage "POSTDATA: $POSTDATA"

	curlPost "$FORMACTION" "$POSTDATA"
	getLocationRedirect "$BODY" "$LOCATION"
	getBody "$LOCATION" true

	# Check if Captive Portal has been resolved
	if checkCaptivePortalPresence; then
		logMessage 'Captive portal still present'
	elif [ "$CAPTIVEPORTALSTATE" = 'solved' ]; then
		# Ok, we were able to authenticate
		logMessage 'Captive portal succesfully solved'
		#ToDo Store username/password
		if $_STOREUSERNAME && $_STOREPASSWORD; then
			setCaptivePortalCredentials "$BSSID" "$SSID" "$LOCATION" "$LATITUDE" "$LONGITUDE" "$USERNAME" "$PASSWORD"
		elif $_STOREUSERNAME; then
			setCaptivePortalCredentials "$BSSID" "$SSID" "$LOCATION" "$LATITUDE" "$LONGITUDE" "$USERNAME" ''
		elif $_STOREPASSWORD; then
			setCaptivePortalCredentials "$BSSID" "$SSID" "$LOCATION" "$LATITUDE" "$LONGITUDE" '' "$PASSWORD"
		fi
	fi
fi
'''

class Mikrotik(CaptivePortalSolverImpl):
  name = "Mikrotik"

  def detect(self, bssid, ssid, location = None, body = None):
    if body:
      if re.search(r'function doLogin() {[^}]*hexMD5([^}]*}', body, re.MULTILINE):
        self.detectionMethod = 'contentmatch'
        if bssid:
          CaptivePortalSolverCache.getCache().store(bssid, type(self).__name__)
        return True
    else:
      return super().detect(bssid, ssid)

  def solve(self, bssid, ssid, location, body):
    # Placeholder for future implementation
    return False
