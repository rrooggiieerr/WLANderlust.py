						<script>
							$(document).ready(function(){
								$.ajax("/Networking/vpn/SSHTunnel/publickey").done(function (response) {
									$("#SSHTunnel_publickey").text(response);
									$("#SSHTunnel_copyPublicKey").prop('disabled', false);
								});

								$("#SSHTunnel_copyPublicKey").click(function() {
									return false;
								});
							});
						</script>
						<tr>
							<td><label for="SSHTunnel_username">Username</label></td>
							<td><input type="text" id="SSHTunnel_username" name="username" value="{{get('username', '')}}" autocomplete="off"/></td>
						</tr>
						<tr>
							<td><label for="SSHTunnel_hostname">Server Hostname</label></td>
							<td><input type="text" id="SSHTunnel_hostname" name="hostname" value="{{get('hostname', '')}}" autocomplete="off"/></td>
						</tr>
						<tr>
							<td><label for="SSHTunnel_port">Port</label></td>
							<td><input type="number" id="SSHTunnel_port" name="port" value="{{get('port', '22')}}" min="1" max="65535"/></td>
						</tr>
						<tr>
							<td><label for="SSHTunnel_ipaddress">IP Address</label></td>
							<td><input type="text" id="SSHTunnel_ipaddress" name="ipaddress" value="{{get('ipaddress', '')}}" autocomplete="off"/></td>
						</tr>
						<tr>
							<td><label for="SSHTunnel_netmask">Netmask</label></td>
							<td><input type="text" id="SSHTunnel_netmask" name="netmask" value="{{get('netmask', '')}}" autocomplete="off"/></td>
						</tr>
						<tr>
							<td><label for="SSHTunnel_gateway">Gateway</label></td>
							<td><input type="text" id="SSHTunnel_gateway" name="gateway" value="{{get('gateway', '')}}" autocomplete="off"/></td>
						</tr>
						<tr>
							<td colspan="2">
								<div id="SSHTunnel_publickey" style="width: 200px"><span id="SSHTunnel_generating">Generating...</span></div>
								<div>Place this public key in the authorized_keys file of the SSH server.<br/>
								<button id="SSHTunnel_copyPublicKey" disabled>Copy public key to clipboard</button></div>
							</td>
						</tr>
