<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - Captive Portals</title>
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
				<h3>Captive Portals</h3>
			</div>
			<fieldset>
				<legend>Captive Portals settings</legend>
				<form action="/CaptivePortals/settings" method="post">
					<table id="settings">
						<tr>
							<td><label for="AutoSolve">Auto solve Captive Portals when present</label></td>
							<td><input type="checkbox" id="AutoSolve" name="AutoSolve" value="True"{{!' checked' if AutoSolve else ''}}/></td>
						</tr>
						<tr>
							<td><label for="DetectionURL">Detection URL</label></td>
							<td><input type="url" id="DetectionURL" name="DetectionURL" value="{{DetectionURL}}"/></td>
						</tr>
						<tr>
							<td><label for="DetectionResponse">Detection response</label></td>
							<td><input type="text" id="DetectionResponse" name="DetectionResponse" value="{{DetectionResponse}}"/></td>
						</tr>
						<tr>
							<td><label for="Logging">Log Captive Portals</label></td>
							<td><input type="checkbox" id="Logging" name="Logging" value="True"{{!' checked' if Logging else ''}}/></td>
						</tr>
						<tr>
							<td><label for="LogPath">Captive Portals log path</label></td>
							<td><input type="text" id="LogPath" name="LogPath" value="{{LogPath}}"/></td>
						</tr>
					</table>
					<input type="submit" value="Save Captive Portals settings"/>
				</form>
			</fieldset>	
			<fieldset>
				<legend>Captive Portals</legend>
				<table id="captiveportals">
				%for captiveportal in captiveportals:
					<tr><td><a href="/CaptivePortals/{{captiveportal['id']}}">{{captiveportal['name']}} settings</a></td></tr>
				%end
				</table>
			</fieldset>
			<fieldset>
				<legend>Captive Portals credentials</legend>
			</fieldset>	
			<a href="/settings">Return to settings</a>
			<div id="footer"></div>
		</div>
	</body>
</html>
