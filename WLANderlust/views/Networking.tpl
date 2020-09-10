<!DOCTYPE html>
<html lang="en">
	<head>
		<title>WLANderlust - Networking</title>
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel="stylesheet" type="text/css" href="/WLANderlust.css"/>
		<style>
			#addTunnel, #addVPN {
				display: none;
			}
		</style>
		<script src="/jquery.js"></script>
		<script src="/WLANderlust.js"></script>
		<script>
			$(document).ready(function(){
				$("button#addTunnelButton").click(function(event) {
					$("#addTunnel").show();
					return false;
				});
				$("select#TunnelType").change(function(event) {
					$(".TunnelType").hide();
					$("#TunnelType_" + this.value).show();
				});

				$("button#addVPNButton").click(function(event) {
					$("#addVPN").show();
					return false;
				});
				$("select#VPNType").change(function(event) {
					$(".VPNType").hide();
					$("#VPNType_" + this.value).show();
				});

				$("#addTunnel form, #addVPN form").submit(function(event) {
					form = this;
					$.post(form.action, $(form).serialize()
						).done(function(data) {
							$(form).closest(".overlay").hide();
							form.reset();
						}).fail(function(data) {
						});
					return false;
				});

				$(".TunnelType").first().show();
				$(".VPNType").first().show();
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
				<h3>Networking</h3>
			</div>
			<form action="/Networking/settings" method="post">
				<fieldset>
					<legend>Inward Networking settings</legend>
					<table class="settings">
						<tr>
							<td><label for="AutoSwitchHostAPChannel">Automatically switch host Access Point channel</label>
								<div class="description">Switch the host AP to a channel which is not interfering with the AP currently connected to.</div></td>
							<td><input type="checkbox" id="AutoSwitchHostAPChannel" name="AutoSwitchHostAPChannel" value="True"{{!' checked' if AutoSwitchHostAPChannel else ''}}/></td>
						</tr>
					</table>
					<h4>Inward Network Interfaces</h4>
					<table id="inwardNetworkInterfaces">
						<tr>
							<th>Name</th>
							<th>Type</th>
						</tr>
					%for inwardInterface in InwardInterfaces:
						<tr>
							<td><a href="#">{{inwardInterface['interface']}}</a></td>
							<td>{{inwardInterface['type']}}</td>
						</tr>
					%end
					</table>
				</fieldset>
				<fieldset>
					<legend>Outward Networking settings</legend>
					<table class="settings">
						<tr>
							<td><label for="DetectExternalIPURL">Detect external IP URL</label></td>
							<td><input type="url" id="DetectExternalIPURL" name="DetectExternalIPURL" value="{{DetectExternalIPURL}}"/></td>
						</tr>
						<tr>
							<td><label for="Scan">Scan Networks</label></td>
							<td><input type="checkbox" id="Scan" name="Scan" value="True"{{!' checked' if Scan else ''}}/></td>
						</tr>
						<tr>
							<td><label for="AutoReassociateWiFi">Automatically reassociate Wi-Fi</label>
								<div class="description">Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</div></td>
							<td><input type="checkbox" id="AutoReassociateWiFi" name="AutoReassociateWiFi" value="True"{{!' checked' if AutoReassociateWiFi else ''}}/></td>
						</tr>
						<tr>
							<td><label for="OverrideMetered">Override Metered Connections</label>
								<div class="description"></div></td>
							<td><input type="checkbox" id="OverrideMetered" name="OverrideMetered" value="True"{{!' checked' if OverrideMetered else ''}}/></td>
						</tr>
					</table>
					<h4>Outward Network Interfaces</h4>
					<table id="outwardNetworkInterfaces">
						<tr>
							<th>Name</th>
							<th>Type</th>
						</tr>
					%for outwardInterface in OutwardInterfaces:
						<tr>
							<td><a href="#">{{outwardInterface['interface']}}</a></td>
							<td>{{outwardInterface['type']}}</td>
						</tr>
					%end
					</table>
				</fieldset>
				<fieldset>
					<legend>Configured WiFi Networks</legend>
				</fieldset>
				<fieldset>
					<legend>IP Tunneling</legend>
					<table class="settings">
						<tr>
							<td><label for="autostarttunnel">Auto start IP tunneling when Captive Portal cannot be solved</label></td>
							<td><input type="checkbox" id="autostarttunnel" name="AutoStartTunnel" value="True"{{!' checked' if AutoStartTunnel else ''}}/></td>
						</tr>
					</table>
					<h4>Configured IP Tunnels</h4>
					<table id="tunnels">
						<tr>
							<th>Name</th>
							<th>Type</th>
						</tr>
					%for tunnel in tunnels:
						<tr>
							<td><a href="#">{{tunnel['name']}}</a></td>
							<td>{{tunnel['type']}}</td>
						</tr>
					%end
					</table>
					<button id="addTunnelButton">Add IP Tunnel</button>
				</fieldset>
				<fieldset>
					<legend>VPN</legend>
					<table class="settings">
						<tr>
							<td>Auto start VPN on succesful network connection</td>
							<td><input type="checkbox" name="AutoStartVPN" value="True"{{!' checked' if AutoStartVPN else ''}}/></td>
						</tr>
					</table>
					<h4>Configured VPNs</h4>
					<table id="vpns">
						<tr>
							<th>Name</th>
							<th>Type</th>
						</tr>
					%for vpn in vpns:
						<tr>
							<td><a href="#">{{vpn['name']}}</a></td>
							<td>{{vpn['type']}}</td>
						</tr>
					%end
					</table>
					<button id="addVPNButton">Add VPN</button>
				</fieldset>
				<input type="submit" value="Save Networking settings"/>
			</form>
			<a href="/settings">Return to settings</a>
			<div id="footer"></div>
		</div>
		<div id="addTunnel" class="addTunnel overlay">
			<fieldset>
				<legend>Add IP Tunnel</legend>
				<form action="#">
					<select id="TunnelType">
					%for tunnelType in tunnelTypes:
						<option value="{{tunnelType['id']}}">{{tunnelType['name']}} - {{tunnelType['description']}}</option>
					%end
					</select>
				</form>
				%for tunnelType in tunnelTypes:
				<form id="TunnelType_{{tunnelType['id']}}" class="TunnelType" style="display: none;" action="/Tunnels/add/{{tunnelType['id']}}" method="post">
					<input type="hidden" name="type" value="{{tunnelType['id']}}"/>
					<table>
						<tr>
							<td><label for="{{tunnelType['id']}}_name">Name</label></td>
							<td><input type="text" id="{{tunnelType['id']}}_name" name="name"/></td>
						</tr>
						% include("Tunnels/" + tunnelType['id'] + ".tpl")
					</table>
					<input type="submit" value="Add IP Tunnel"/>
					<button class="cancel">Cancel</button>
				</form>
				%end
			</fieldset>
		</div>
		<div id="addVPN" class="addVPN overlay">
			<fieldset>
				<legend>Add VPN</legend>
				<form action="#">
					<select id="VPNType">
					%for vpnType in vpnTypes:
						<option value="{{vpnType['id']}}">{{vpnType['name']}}</option>
					%end
					</select>
				</form>
				%for vpnType in vpnTypes:
				<form id="VPNType_{{vpnType['id']}}" class="VPNType" style="display: none;" action="/VPNs/add/{{vpnType['id']}}" method="post">
					<table>
						<tr>
							<td><label for="{{vpnType['id']}}_name">Name</label></td>
							<td><input type="text" id="{{vpnType['id']}}_name" name="name"/></td>
						</tr>
						% include("VPNs/" + vpnType['id'] + ".tpl")
					</table>
					<input type="submit" value="Add VPN"/>
					<button class="cancel">Cancel</button>
				</form>
				%end
			</fieldset>
		</div>
	</body>
</html>
