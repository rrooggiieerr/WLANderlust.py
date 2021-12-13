<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - WiGLE</title>
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel="stylesheet" type="text/css" href="/WLANderlust.css"/>
		<script src="/jquery.js"></script>
		<script src="/WLANderlust.js"></script>
	</head>
	<body>
		<div id="content">
			<div id="header">
				<h1>WLANderlust</h1>
				<h2>Not all those who WLANder have lost connection</h2>
			</div>
			<div id="intro">
				<h3>WiGLE</h3>
				WiGLE, the Wireless Geographic Logging Engine, is a platform for collecting information about the different wireless hotspots around the world. You can register on the website and upload hotspot data like GPS coordinates, SSID, MAC address and the encryption type used on the hotspots discovered.
			</div>
			<fieldset>
				<legend>WiGLE settings</legend>
				<form action="/Plugins/WiGLE" method="post">
					<table id="settings">
						<tr>
							<td><label for="apitoken">API Token</label></td>
							<td><input type="text" id="apitoken" name="apitoken" value="{{apitoken}}" autocomplete="off"/></td>
						</tr>
					</table>
					<input type="submit" value="Save WiGLE settings"/>
				</form>
			</fieldset>
			<a href="/Plugins/settings">Return to plugin settings</a>
			<div id="footer"></div>
		</div>
	</body>
</html>
