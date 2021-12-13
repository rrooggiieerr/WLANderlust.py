<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - cURL</title>
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel="stylesheet" type="text/css" href="/WLANderlust.css"/>
		<script src="/jquery.js"></script>
		<script src="/WLANderlust.js"></script>
		<script>
			$(document).ready(function(){
				$("button#addCredentialButton").click(function(event) {
					$("#addCredential").show();
					return false;
				});
				$("#addCredential input:submit").click(function(event) {
					$("#addCredential").hide();
				});
			});
		</script>
	</head>
	<body>
		<div id="content">
			<div id="header">
				<h1>WLANderlust</h1>
				<h2>Not all those who WLANder have lost connection</h2>
			</div>
			<div id="intro">
				<h3>cURL</h3>
			</div>
			<fieldset>
				<legend>cURL credentials</legend>
				<table id="settings">
					<tr>
						<th>BSSID</th>
						<th>SSID</th>
						<th>Domain</th>
						<th></th>
					</tr>
				%for credential in credentials:
					<tr>
						<td>{{credential[0] if credential[0] else ''}}</td>
						<td>{{credential[1] if credential[1] else ''}}</td>
						<td>{{credential[2] if credential[2] else ''}}</td>
						<td>
							<form action="/CaptivePortals/Curl/delete" method="post">
								<input type="hidden" name="bssid" value="{{credential[0] if credential[0] else ''}}"/>
								<input type="hidden" name="ssid" value="{{credential[1] if credential[1] else ''}}"/>
								<input type="hidden" name="domain" value="{{credential[2] if credential[2] else ''}}"/>
								<button type="submit" class="asText">&#x1f5d1;</button>
							</form>
						</td>
					</tr>
				%end
				</table>
				<button id="addCredentialButton">Add Credential</button><br/>
			</fieldset>
			<a href="/CaptivePortals/settings">Return to Captive Portal settings</a>
			<div id="footer"></div>
		</div>
		<div id="addCredential" class="addCredential overlay">
			<form action="/CaptivePortals/Curl/add" method="post">
				<table>
					<tr><td><label for="bssid">BSSID</label></td><td><input type="text" id="bssid" name="bssid" autocomplete="off"/></td></tr>
					<tr><td><label for="ssid">SSID</label></td><td><input type="text" id="ssid" name="ssid" autocomplete="off"/></td></tr>
					<tr><td><label for="domain">Domain</label></td><td><input type="text" id="domain" name="domain" autocomplete="off"/></td></tr>
					<tr><td><label for="url">URL</label></td><td><input id="url" type="url" name="url"/></td></tr>
					<tr><td><label for="share">Share</label></td><td><input type="checkbox" id="share" name="share" value="True"/></td></tr>
				</table>
				<input type="submit" value="Connect"/>
				<button class="cancel">Cancel</button>
			</form>
		</div>
	</body>
</html>
