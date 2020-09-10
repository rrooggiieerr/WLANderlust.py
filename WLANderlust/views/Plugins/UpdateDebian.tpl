<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - Update Debian</title>
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel="stylesheet" type="text/css" href="/WLANderlust.css"/>
		<script src="/jquery.js"></script>
		<script src="/WLANderlust.js"></script>
		<script>
function getUpdates() {
	$.ajax("/Plugins/UpdateDebian/updates", {
		statusCode: {
			200: function(response) {
				$("#stdout").text(response);
				$("#update").prop("disabled", false)
			},
			206: function(response) {
				if(response.length > 0)
					$("#stdout").text(response);

				setTimeout(function() {
					getUpdates();
				}, 50);
			}
		}
	});
}

function installUpdates() {
	$.ajax("/Plugins/UpdateDebian/update", {
		statusCode: {
			200: function(response) {
				$("#stdout").text(response);
			},
			206: function(response) {
				if(response.length > 0)
					$("#stdout").text(response);

				setTimeout(function() {
					installUpdates();
				}, 50);
			}
		}
	});
}

$(document).ready(function() {
	getUpdates();
	$("#update").click(function() {
		$("#update").prop("disabled", true)
		$("#stdout").prev("legend").text("Installation progress");
		$("#stdout").text("");
		installUpdates();
		return false;
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
				<h3>Update Debian</h3>
			</div>
			<fieldset>
				<legend>Update Debian settings</legend>
				<form action="/Plugins/UpdateDebian" method="post">
					<table id="settings">
						<tr>
							<td><label for="install">Auto install updates</label></td>
							<td><input type="checkbox" id="install" name="Install" value="True"{{!' checked="checked"' if Install else ''}}/></td>
						</tr>
					</table>
					<input type="submit" value="Save Update Debian settings"/>
				</form>
			</fieldset>
			<fieldset>
				<legend>Available updates</legend>
				<div id="stdout" style="white-space: pre-wrap;"></div>
				<button id="update" disabled>Install updates</button>
			</fieldset>
			<a href="/Plugins/settings">Return to plugin settings</a>
			<div id="footer"></div>
		</div>
	</body>
</html>
