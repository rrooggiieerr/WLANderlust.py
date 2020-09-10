<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - Settings</title>
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
				<h3>Settings</h3>
			</div>
			<fieldset>
				<legend>WLANderlust settings</legend>
				<form action="/settings" method="post">
					<table id="settings">
						<tr>
							<td><label for="shutdownOnUnplug">Shutdown on Wi-Fi unplug</label></td>
							<td><input type="checkbox" id="ShutdownOnUnplug" name="ShutdownOnUnplug" value="True"{{!' checked' if ShutdownOnUnplug else ''}}/></td>
						</tr>
					</table>
					<input type="submit" value="Save WLANderlust settings"/>
				</form>
			</fieldset>
			<fieldset>
				<legend>WLANderlust components</legend>
				<table>
					<tr>
						<td><a href="/Networking/settings">Networking</a></td>
					</tr>
					<tr>
						<td><a href="/CaptivePortals/settings">Captive Portals</a></td>
					</tr>
					<tr>
						<td><a href="/GPS/settings">GPS</a></td>
					</tr>
					<tr>
						<td><a href="/Plugins/settings">Plugins</a></td>
					</tr>
				</table>
			</fieldset>
			<a href="/">Return to main page</a>
			<div id="footer"></div>
		</div>
	</body>
</html>
