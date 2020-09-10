						<script>
							$(document).ready(function(){
								$.ajax("/Networking/vpn/SSHuttle/publickey").done(function (response) {
									$("#SSHuttle_publickey").text(response);
									$("#SSHuttle_copyPublicKey").prop('disabled', false);
								});

								$("#SSHuttle_copyPublicKey").click(function() {
									return false;
								});
							});
						</script>
						<tr>
							<td><label for="SSHuttle_username">Username</label></td>
							<td><input type="text" id="SSHuttle_username" name="username" value="{{get('username', '')}}"/></td>
						</tr>
						<tr>
							<td><label for="SSHuttle_hostname">Server Hostname</label></td>
							<td><input type="text" id="SSHuttle_hostname" name="hostname" value="{{get('hostname', '')}}"/></td>
						</tr>
						<tr>
							<td><label for="SSHuttle_port">Port</label></td>
							<td><input type="number" id="SSHuttle_port" name="port" value="{{get('port', '22')}}" min="1" max="65535"/></td>
						</tr>
						<tr>
							<td colspan="2">
								<div id="SSHuttle_publickey"><span id="SSHuttle_generating">Generating...</span></div>
								<div>Place this public key in the authorized_keys file of the SSH server.<br/>
								<button id="SSHuttle_copyPublicKey" disabled>Copy public key to clipboard</button></div>
							</td>
						</tr>
