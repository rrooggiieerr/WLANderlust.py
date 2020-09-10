<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - Plugins</title>
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel="stylesheet" type="text/css" href="/WLANderlust.css"/>
		<script src="/jquery.js"></script>
		<script src="/WLANderlust.js"></script>
		<script>
function updateStatus() {
	$.getJSON("/Plugins/status", success = function(status) {
		$("table#plugins td.status").text("");
		for(i in status) {
			if(status[i][1])
				$("tr#plugin_" + status[i][0] + " td.status").text("Y");
		}
	}).always(function() {
		setTimeout(function() {
			updateStatus();
		}, 100);
	});

}

$(document).ready(function() {
	updateStatus();
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
				<h3>Plugins</h3>
			</div>
			<fieldset>
				<legend>Plugins settings</legend>
				<form action="/Plugins/settings" method="post">
					<table id="plugins">
						<tr>
							<th colspan="2">Plugin name</th>
							<th>Active</th>
							<th>Enabled</th>
						</tr>
					%for plugin in plugins:
						<tr id="plugin_{{plugin['id']}}">
							<td><a href="/Plugins/{{plugin['id']}}">{{plugin['name']}}</a></td>
							<td>{{plugin['description']}}</td>
							<td class="status"></td>
							<td><input type="checkbox" name="Enabled" value="{{plugin['id']}}"{{' disabled' if not plugin['configured'] else ' checked' if plugin['enabled'] else ''}}/></td>
						</tr>
					%end
					</table>
					<input type="submit" value="Save Plugin settings"/>
				</form>
			</fieldset>
			<a href="/settings">Return to settings</a>
			<div id="footer"></div>
		</div>
	</body>
</html>
