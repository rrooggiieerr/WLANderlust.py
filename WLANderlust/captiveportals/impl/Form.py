# WLANderlust
#
# Solver for form based Captive Portals
#
# https://en.wikipedia.org/wiki/Captive_portal
#
# Rogier van Staveren, February 2020, initial release
import re, logging
from bs4 import BeautifulSoup

from WLANderlust.captiveportals import CaptivePortalSolverImpl

logger = logging.getLogger(__name__)
'''
BASH implementation:

if grep -i -q '<form ' <<< "$BODY"; then
	# Remove comments
	FORMS=`tr -d '\n\r' <<< "$BODY" | sed 's|\(-->\)|\1\n|g' | sed 's|<!--.*-->||'`
	#FORMS=`sed 's|\(</form>\)|\1\n|Ig' <<< "$FORMS" | sed -n "s|^.*\(<form [^>]*action=[\"'][^\"']*[\"'][^>]*>.*</form>\)$|\1|Ip"`
	FORMS=`sed 's|\(</form>\)|\1\n|Ig' <<< "$FORMS" | sed -n 's|^.*\(<form .*</form>\)$|\1|Ip'`

	USERNAME=`getCaptivePortalUsername "$BSSID" "$SSID" "$LOCATION"`
	PASSWORD=`getCaptivePortalPassword "$BSSID" "$SSID" "$LOCATION"`

	OIFS="$IFS"
	IFS=$'\n'
	for FORM in $FORMS; do
		# Get form action
		FORMACTION=`sed -n "s|^.*<form [^>]*action=[\"']\([^\"']*\)[\"'][^>]*>.*$|\1|Ip" <<< "$FORM"`
		[ -z "$FORMACTION" ] &&
			FORMACTION="$LOCATION" ||
			FORMACTION=`expandLocation "$FORMACTION" "$LOCATION"`
		ONSUBMIT=`sed -n "s|^.*<form [^>]*onSubmit=[\"']\([^\"']*\)[\"'][^>]*>.*$|\1|Ip" <<< "$FORM"`
		logMessage "Form action: \"$FORMACTION\""
		if [ ! -z "$ONSUBMIT" ]; then
			logMessage 'This form uses JavaScript!'
		fi

		TEXTINPUTCOUNTER=0
		EMPTYTEXTINPUTCOUNTER=0
		PASSWORDINPUTCOUNTER=0
		EMPTYPASSWORDINPUTCOUNTER=0
		HIDDENINPUTCOUNTER=0
		EMPTYHIDDENINPUTCOUNTER=0
		CHECKBOXINPUTCOUNTER=0
		SELECTCOUNTER=0
		SUBMITCOUNTER=0

		CURLFORMARGUMENTS=''
		POSTDATA=''
		INPUTS=`sed 's|>|&\n|g' <<< "$FORM" | sed -n 's|.*\(<input [^>]*>\)$|\1|Ip'`
		for INPUT in $INPUTS; do
			INPUTTYPE=`sed -n "s|.* type=[\"']\([^\"']*\)[\"'].*|\1|Ip" <<< "$INPUT"`
			INPUTNAME=`sed -n "s|.* name=[\"']\([^\"']*\)[\"'].*|\1|Ip" <<< "$INPUT"`
			INPUTVALUE=`sed -n "s|.* value=[\"']\([^\"']*\)[\"'].*|\1|Ip" <<< "$INPUT"`

			if [ -z "$INPUTTYPE" ]; then
				$DEBUGLOGGING && logError 'Empty INPUTTYPE'
				INPUTTYPE='text'
			fi

			case "$INPUTTYPE" in
			'text')
				TEXTINPUTCOUNTER=$(($TEXTINPUTCOUNTER + 1))
				if [ -z "$INPUTVALUE" ]; then
					EMPTYTEXTINPUTCOUNTER=$(($EMPTYTEXTINPUTCOUNTER + 1))
				fi
				;;
			'email')
				TEXTINPUTCOUNTER=$(($TEXTINPUTCOUNTER + 1))
				#if [ -z "$INPUTVALUE" ]; then
				#	
				#fi
				;;
			'password')
				PASSWORDINPUTCOUNTER=$(($PASSWORDINPUTCOUNTER + 1))
				if [ -z "$INPUTVALUE" ]; then
					EMPTYPASSWORDINPUTCOUNTER=$(($EMPTYPASSWORDINPUTCOUNTER + 1))
				fi
				;;
			'hidden')
				HIDDENINPUTCOUNTER=$(($HIDDENINPUTCOUNTER + 1))
				if [ -z "$INPUTVALUE" ]; then
					EMPTYHIDDENINPUTCOUNTER=$(($EMPTYHIDDENINPUTCOUNTER + 1))
				fi
				;;
			'submit')
				SUBMITCOUNTER=$(($SUBMITCOUNTER + 1))
				;;
			'reset')
				# We ignore reset buttons
				INPUTNAME=''
				INPUTVALUE=''
				;;
			'checkbox')
				CHECKBOXINPUTCOUNTER=$(($CHECKBOXINPUTCOUNTER + 1))
				INPUTVALUE="$INPUTNAME"
				;;
			*)
				logMessage "Unsupported INPUTTYPE=$INPUTTYPE"
				logMessage "$INPUT"
				;;
			esac

			if [ ! -z "$INPUTNAME" ]; then
				CURLFORMARGUMENTS="$CURLFORMARGUMENTS -F \"$INPUTNAME=$INPUTVALUE\""
				[ ! -z "$POSTDATA" ] && POSTDATA="$POSTDATA&"
				POSTDATA="$POSTDATA$INPUTNAME=$INPUTVALUE"
			fi
		done

		SELECTS=`sed 's|\(</select>\)|\1\n|Ig' <<< "$FORM" | sed -n 's|.*\(<select .*\)$|\1|Ip'`
		for SELECT in $SELECTS; do
			if grep -i -q "language" <<< "$SELECT"; then
				logMessage "This seems to be a language select form, we can't login with this one"
				continue 2
			fi
			OPTIONS=`sed 's|\(</option>\)|\1\n|g' <<< "$SELECT" | sed -n 's|.*\(<option .*</option>\)$|\1|Ip'`
			SELECTCOUNTER=$(($SELECTCOUNTER + 1))
		done

		CAPTIVEPORTALTYPE='form'

		$DEBUGLOGGING && logMessage "TEXTINPUTCOUNTER=$TEXTINPUTCOUNTER EMPTYTEXTINPUTCOUNTER=$EMPTYTEXTINPUTCOUNTER"
		$DEBUGLOGGING && logMessage "PASSWORDINPUTCOUNTER=$PASSWORDINPUTCOUNTER EMPTYPASSWORDINPUTCOUNTER=$EMPTYPASSWORDINPUTCOUNTER"
		$DEBUGLOGGING && logMessage "HIDDENINPUTCOUNTER=$HIDDENINPUTCOUNTER EMPTYHIDDENINPUTCOUNTER=$EMPTYHIDDENINPUTCOUNTER"
		$DEBUGLOGGING && logMessage "SUBMITCOUNTER=$SUBMITCOUNTER"
		$DEBUGLOGGING && logMessage "CHECKBOXINPUTCOUNTER=$CHECKBOXINPUTCOUNTER"
		$DEBUGLOGGING && logMessage "POSTDATA=$POSTDATA"

		if [ $TEXTINPUTCOUNTER -eq 0 ] && [ $PASSWORDINPUTCOUNTER -eq 0 ] && [ $EMPTYHIDDENINPUTCOUNTER -eq 0 ] && [ $CHECKBOXINPUTCOUNTER -eq 0 ] && [ $SELECTCOUNTER -eq 0 ] && [ $SUBMITCOUNTER -eq 1 ]; then
			logMessage "This seems to be some kind of continue/proceed kind of form"
			curlPost "$FORMACTION" "$POSTDATA"
			getLocationRedirect "$BODY" "$LOCATION"
			getBody "$LOCATION" true

			# Check if Captive Portal has been resolved
			if grep -q "$CAPTIVEPORTALDETECTIONRESPONSE" <<< "$BODY"; then
				# Ok, we were able to authenticate
				setState 'CAPTIVEPORTALSTATE' 'solved'
				logMessage 'Captive portal succesfully solved'
				CAPTIVEPORTALTYPE='continue form'
				break
			elif checkCaptivePortalPresence; then
				logMessage 'Captive portal still present'
			elif [ "$CAPTIVEPORTALSTATE" = 'solved' ]; then
				# Ok, we were able to authenticate
				logMessage 'Captive portal succesfully solved'
				CAPTIVEPORTALTYPE='continue form'
				break
			fi
		elif [ $TEXTINPUTCOUNTER -eq 0 ] && [ $PASSWORDINPUTCOUNTER -eq 0 ] && [ $CHECKBOXINPUTCOUNTER -eq 0 ] && [ $SELECTCOUNTER -eq 0 ] && [ $SUBMITCOUNTER -eq 1 ] && [ ${#FORMS[@]} -eq 1 ]; then
			logMessage "This seems to be some kind of continue/proceed kind of form, but with empty hidden fields and it's the only form on the page"
			curlPost "$FORMACTION" "$POSTDATA"
			getLocationRedirect "$BODY" "$LOCATION"
			getBody "$LOCATION" true

			# Check if Captive Portal has been resolved
			if grep -q "$CAPTIVEPORTALDETECTIONRESPONSE" <<< "$BODY"; then
				# Ok, we were able to authenticate
				setState 'CAPTIVEPORTALSTATE' 'solved'
				logMessage 'Captive portal succesfully solved'
				CAPTIVEPORTALTYPE='continue form'
				break
			elif checkCaptivePortalPresence; then
				logMessage 'Captive portal still present'
			elif [ "$CAPTIVEPORTALSTATE" = 'solved' ]; then
				# Ok, we were able to authenticate
				logMessage 'Captive portal succesfully solved'
				CAPTIVEPORTALTYPE='continue form'
				break
			fi
		elif [ $TEXTINPUTCOUNTER -eq 0 ] && [ $PASSWORDINPUTCOUNTER -eq 0 ] && [ $EMPTYHIDDENINPUTCOUNTER -eq 0 ] && [ $CHECKBOXINPUTCOUNTER -eq 1 ] && [ $SELECTCOUNTER -eq 0 ] && [ $SUBMITCOUNTER -eq 1 ]; then
			logMessage "This seems to be some kind of confirm/agree kind of form"
			curlPost "$FORMACTION" "$POSTDATA"
			getLocationRedirect "$BODY" "$LOCATION"
			getBody "$LOCATION" true

			# Check if Captive Portal has been resolved
			if grep -q "$CAPTIVEPORTALDETECTIONRESPONSE" <<< "$BODY"; then
				# Ok, we were able to authenticate
				setState 'CAPTIVEPORTALSTATE' 'solved'
				logMessage 'Captive portal succesfully solved'
				CAPTIVEPORTALTYPE='conform form'
				break
			elif checkCaptivePortalPresence; then
				logMessage 'Captive portal still present'
			elif [ "$CAPTIVEPORTALSTATE" = 'solved' ]; then
				# Ok, we were able to authenticate
				logMessage 'Captive portal succesfully solved'
				CAPTIVEPORTALTYPE='conform form'
				break
			fi
		elif [ $TEXTINPUTCOUNTER -eq 0 ] && [ $PASSWORDINPUTCOUNTER -eq 0 ] && [ $HIDDENINPUTCOUNTER -eq 0 ]; then
			logMessage "This seems to be an empty form, we can't login with this one"
			CAPTIVEPORTALTYPE='unknown'
		elif [ $EMPTYTEXTINPUTCOUNTER -ge 1 ] && [ $EMPTYPASSWORDINPUTCOUNTER -ge 1 ]; then
			logMessage 'This seems to be a typical empty username/password form'
			CAPTIVEPORTALTYPE='username/password form'
			CAPTIVEPORTALSTATE='failure'
			#ToDo Get username/password from configuration file
		elif [ $EMPTYTEXTINPUTCOUNTER -eq 0 ] && [ $EMPTYPASSWORDINPUTCOUNTER -ge 1 ]; then
			logMessage 'This seems to be a typical empty password form'
			CAPTIVEPORTALTYPE='password form'
			#getCaptivePortalPassword "$BSSID" "$SSID" "$LOCATION"
			#echo $PASSWORD
			#checkCaptivePortalPresence && break
			CAPTIVEPORTALSTATE='failure'
		elif [ $EMPTYPASSWORDINPUTCOUNTER -eq 0 ] && [ $EMPTYTEXTINPUTCOUNTER -ge 1 ]; then
			logMessage 'Form based captive portal detected'
			logMessage 'This seems to be a typical empty password form'
			CAPTIVEPORTALTYPE='password form'
			CAPTIVEPORTALSTATE='failure'
			#ToDo Get password from configuration file
		else
			logMessage 'Give the following cURL a try:'
			logMessage "curl $CURLFORMARGUMENTS '$FORMACTION'"
			curlPost "$FORMACTION" "$POSTDATA"
			getLocationRedirect "$BODY" "$LOCATION"
			getBody "$LOCATION" true

			LASTLOCATION="$LOCATION"
			checkCaptivePortalPresence && break
			LOCATION="$LASTLOCATION"
		fi

	done
	IFS="$OIFS"
fi
'''

class Form(CaptivePortalSolverImpl):
  name = "Form"
  order = 1100
  debug = True

  def detect(self, bssid, ssid, location = None, body = None):
    if body:
      if re.search(r"<form\b", body, re.IGNORECASE | re.MULTILINE):
        self.detectionMethod = 'contentmatch'
        #if bssid:
        #  CaptivePortalSolverCache.getCache().store(bssid, type(self).__name__)
        return True
      return False
    else:
      return super().detect(bssid, ssid)

  def solve(self, bssid, ssid, location = None, body = None):
    if body:
      parsedBody = BeautifulSoup(body.encode("utf8"), features="html.parser")
      forms = parsedBody.body.find_all('form')
      #print(forms.prettify())
      #forms = re.findall(r"(<form\b.*?</form>)", body, re.IGNORECASE | re.MULTILINE | re.DOTALL)
      if forms:
        for form in forms:
          action = form.get('action')
          logger.debug(action)
    return False
