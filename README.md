# WLANderlust
*Not all those who WLANder have lost connection*

This package configures a fresh Raspbian Lite installation to be a roaming WiFi
repeater with advanced features. Other Debian based distributions might work.
Making the Captive Portal solving work on all Unices is work in progress.

WLANderlust is developed with travelers in mind; Campers who want to connect to
the campsite WiFi, backpackers who want to connect to the hostel WiFi, sailors
who want to connect to the harbours WiFi, etc.

## Current functionality:
- Connect to open WiFi Access Points
- Detect Captive Portals and tries to solve them
- Logs in to Fon routers with Fon credentials
- Configures firewall and NAT
- Configures encrypted WiFi spots
- Supports IP over ICMP (ping) tunneling for situations where internet access is obstructed, but ICMP queries are allowed.
- Supports IP over DNS tunneling for situations where internet access is obstructed, but DNS queries are allowed.
- IP over SSH VPN support
- Web interface
- Show own Captive Portal when not connected to a network, currently only on Android
- Plugins, add your own functionality
  - Download Raspbian updates when successfully connected

### Feature wishlist:
- Stable WiFi Roaming, to connect to the best available WiFi Access Point
- WISPr authentication (some work has already been done)
- Support for other Fon services like Telekom_FON and BT Fon (some work has already been done)
- Support for MikroTik MD5 client side encrypted passwords (some work has already been done)
- Support for form based username/password Captive Portals (some work has already been done)
- Support for social media Captive Portals
- Better stealth firewall
- Support other WiFi services like T-Mobile Hotspots
- Support for 3G dongles
- GPS support for logging connections (some work has already been done)
- GPS support for logging your location to online services
- Support for more VPN types (some work has already been done)
- Support for Tor
- Transparent proxy with add blocker
- Network Time server for the local network if RTC or GPS is configured
- Retrieve password database from external source, like Wifi Map or Instabridge
- Configure Real Time Clock

## Required Hardware
- Raspberry pi 
- (Outdoor) USB WiFi antenna

### Optional Hardware
- i2c Real Time Clock module
- USB GPS

### Some remarks on Raspberry Pi power usage
The Raspberry Pi Zero W and Raspberry Pi 3 model B seem to be very sensitive to
power fluctuations. A good, stable, power supply is thus needed. Quality USB
cables make the difference.

For car usage I have good experience with the Pimoroni Power Shim.

You get the following under-voltage kernel messages on a Raspberry Pi 3 model B
if your powersupply is not sufficient:
```
[    6.231593] Under-voltage detected! (0x00050005)
[   14.551539] Voltage normalised (0x00000000)
[  341.111583] Under-voltage detected! (0x00050005)
[  347.351544] Voltage normalised (0x00000000)
```

### (Outdoor) USB WiFi antenna
Technically any USB WiFi antenna which is supported by Linux/Raspbian should
work, and depending on your means of travel your selection criteria may vary.
I'm using an Alfa Networks Tube-UN outdoor USB WiFi antenna which is mounted on
my car and I'm very pleased with it. It recevies signals from multiple
kilometers away if you're having a direct line of sight.

### Real Time Clock support
I'm using a i2c DS3231 RTC which you can get for less than $2 including shipping
from eBay:  
http://bit.ly/RaspberryPiDS3231

### External USB GPS
Any GPS which is supported by GPSd should work.

## Installation instructions
You should feel a minimum comfortable with working with the command line. First
you need to create a fresh installation of Raspbian Lite on a Micro SD
card.

### Installing Raspbian
There a plenty of instructions available on the web on how to create an SD card
with Raspbian. If you follow these instructions and want to continue the
installation of WLANderlust on your future router remotely, that is you want to
login on the device from an other computer instead of connecting a screen and
mouse/keyboard directly to the Raspberry PI, you should keep in mind to also
configure `wpa_supplicant.conf` and `ssh` in the `boot` directory of the SD
card. Also you need to have an SSH client installed on your computer, this is
most probalby already installed if you're using Linux or macOS.

If you're already a Linux user, or are usig macOS, you can use a utility script
to download the lates Raspbian Lite, install it on an SD card, configure the
WiFi and enable SSH. The utility script can be found in the `extra` directory
of the WLANderlust installation.

```
./extra/latestRaspbianLite2MicroSD
```

### Installing WLANderlust
After sucessfully installing Raspbian you login on your Raspberry Pi as user pi
with password raspbian and download the WLANderlust archive.

```
curl -L 'https://github.com/rrooggiieerr/WLANderlust.py/archive/master.tar.gz' -o WLANderlust.tar.gz
```

To configure your Raspbian as a roaming WiFi repeater unpack the WLANderlust
archive, execute the `installWLANderlust` installation script and follow the
instructions.

```
tar -xf WLANderlust.tar.gz
cd  WLANderlust-master
sudo ./installWLANderlust
```

## Using WLANderlust
After successful installation of WLANderlust the Raspberry Pi will automatically
interact with the application when new WiFi connections are being established.

### Getting passwords for encrypted Access Points and Captive Portals
Of course you can always walk into a bar/restaurant/hotel/office and ask them
their WiFi password. Further I found the following two apps very usefull for
finding passwords of WiFi Access Points:
- WiFi Map
- Instabridge

Both apps are availale for Android and iOS and can be found in their app stores.

## About the author
I used to work as a freelance IT application developer and consultant and
always enjoyed traveling in between assignments. In 2014/2015 I made an overland
trip from Amsterdam to Cape Town with my Land Rover Defender, in 2017 I decided
to retire and start traveling the world indefenetly. It took a couple of months
to do all the preparations and in April 2018 I drove off, heading from Amsterdam
towards Sydney where I'll expect to arrive in 2023. This time I'm driving a
Toyota Land Cruiser.

Of course, although I'm traveling, I'm keeping my interest for IT and
technology. I packed a couple of Raspberry Pis, Arduinos, sensors and other
components to play with on the side. My need to be online inspired me to create
some scripts to automate logging in to Access Points. Over time more
functionality was added and I decided to rewrite the scripts in Python and to
share this efford with a larger audience.

I'm always interested in short projects in the field of application development
to extend my travel budget. Contact me if you think my expertise can be of use
to our project.

You're invited to follow my adventures on the road on social media:  
https://www.instagram.com/seekingtheedge/  
https://www.facebook.com/seekingtheedge

### Contributors
I'm looking forward to your sugestions, improvements, bug fixes, support for
aditional authentication methods and new functionality.
