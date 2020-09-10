						<tr>
							<td><label for="IPsec_username">Username</label></td>
							<td><input type="text" id="IPsec_username" name="username" value="{{get('username', '')}}"/></td>
						</tr>
						<tr>
							<td><label for="IPsec_hostname">Server Hostname</label></td>
							<td><input type="text" id="IPsec_hostname" name="hostname" value="{{get('hostname', '')}}"/></td>
						</tr>
						<tr>
							<td><label for="IPsec_password">Password</label></td>
							<td><input type="password" id="IPsec_password" name="password" value="{{get('password', '')}}"/></td>
						</tr>
						<tr>
							<th colspan="2">Server Authentication</th>
						</tr>
						<tr>
							<td><input type="radio" id="IPsec_serverauthmethodsharedsecret" name="serverauthmethod" value="sharedsecret"{{' checked' if not defined('serverauthmethod') or serverauthmethod == 'sharedsecret' else ''}}> <label for="IPsec_serverauthmethodsharedsecret">Shared secret</label></td>
							<td><input type="password" name="sharedsecret" value="{{get('sharedsecret', '')}}"{{' disabled' if defined('serverauthmethod') and serverauthmethod != 'sharedsecret' else ''}}/></td>
						</tr>
						<tr>
							<td><input type="radio" id="IPsec_serverauthmethodcertificate" name="serverauthmethod" value="servercertificate"{{'checked' if defined('serverauthmethod') and serverauthmethod == 'servercertificate' else ''}}> <label for="IPsec_serverauthmethodcertificate">Certificate</label></td>
							<td><input type="file" name="servercertificate"{{' disabled' if not defined('serverauthmethod') or serverauthmethod != 'servercertificate' else ''}}/></td>
						</tr>
