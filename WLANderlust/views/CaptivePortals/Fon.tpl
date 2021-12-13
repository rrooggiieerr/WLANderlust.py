<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - Fon</title>
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
				<h3>Fon</h3>
				<p>Fon is a Wi-Fi service and provides, in coorporation with mobile operators and telecommunication providers, Wi-Fi hotspots around the world.
				Fon claims to have the largest Wi-Fi network in the world with over 20 million Wi-Fi hotspots.</p>
				<p><b>Participating providers</b><br/>
				If you are a customer of one of the telecommunication providers Fon partners with you can obtain a Fon account and connect to Fon hotspots.</p>
				<p>BT (UK), SFR (France), NOS (Portugal), SoftBank (Japan), Oi (Brazil), Netia (Poland), KPN (the Netherlands), Deutsche Telekom (Germany), HT (Croatia),
				Cosmote (Greece), Telekom Romania (Romania), Magyar Telekom (Hungary), MWEB ADSL (South Africa), Telstra (Australia), Vodafone (Spain), Vodafone (Italy)</p>
			</div>
			<fieldset>
				<legend>Fon settings</legend>
				<form action="/CaptivePortals/Fon" method="post">
					<table id="settings">
						<tr>
							<td><label for="username">Username</label></td>
							<td><input type="text" id="username" name="username" value="{{username}}" autocomplete="off"/></td>
						</tr>
						<tr>
							<td><label for="password">Password</label></td>
							<td><input type="password" id="password" name="password" value="{{password}}" autocomplete="off"/></td>
						</tr>
					</table>
					<input type="submit" value="Save Fon settings"/>
				</form>
			</fieldset>
			<a href="/CaptivePortals/settings">Return to Captive Portal settings</a>
			<div id="footer"></div>
		</div>
	</body>
</html>
