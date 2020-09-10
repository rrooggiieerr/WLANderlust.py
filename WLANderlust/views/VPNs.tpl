<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - VPN</title>
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
				<h3>VPN</h3>
			</div>
			<fieldset>
				<legend>VPN settings</legend>
				<form action="/VPNs/settings" method="post">
					<table id="settings">
						<tr>
							<td>Auto start VPN on succesful network connection</td>
							<td><input type="checkbox" name="AutoStart" value="True"{{!' checked' if AutoStart else ''}}/></td>
						</tr>
					</table>
					<input type="submit" value="Save VPN settings"/>
			</fieldset>
			<fieldset>
				<legend>VPNs</legend>
					<table id="vpns">
					%for vpn in vpns:
						<tr><td><a href="/VPNs/{{vpn['id']}}">{{vpn['name']}}</a></td></tr>
					%end
					</table>
				</form>
			</fieldset>
			<a href="/settings">Return to settings</a>
			<div id="footer"></div>
		</div>
	</body>
</html>
