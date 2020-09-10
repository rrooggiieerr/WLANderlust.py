						<tr>
							<td><label for="L2TP_username">Username</label></td>
							<td><input type="text" id="L2TP_username" name="username" value="{{get('username', '')}}"/></td>
						</tr>
						<tr>
							<td><label for="L2TP_hostname">Server Hostname</label></td>
							<td><input type="text" id="L2TP_hostname" name="hostname" value="{{get('hostname', '')}}"/></td>
						</tr>
						<tr>
							<th colspan="2">User Authentication</th>
						</tr>
						<tr>
							<td><input type="radio" name="userauthmethod" id="L2TP_userauthmethodpassword" value="password"{{' checked' if not defined('userauthmethod') or userauthmethod == 'password' else ''}}> <label for="L2TP_userauthmethodpassword">Password</label></td>
							<td><input type="password" name="password" value="{{get('password', '')}}"{{' disabled' if defined('userauthmethod') and userauthmethod != 'password' else ''}}/></td>
						</tr>
						<tr>
							<td><input type="radio" name="userauthmethod" id="L2TP_userauthmethodcertificate" value="usercertificate"{{' checked' if defined('userauthmethod') and userauthmethod == 'usercertificate' else ''}}> <label for="L2TP_userauthmethodcertificate">Certificate</label></td>
							<td><input type="file" name="usercertificate"{{' disabled' if not defined('userauthmethod') or userauthmethod != 'usercertificate' else ''}}/></td>
						</tr>
						<tr>
							<th colspan="2">Server Authentication</th>
						</tr>
						<tr>
							<td><input type="radio" name="serverauthmethod" id="L2TP_serverauthmethodsharedsecret" value="sharedsecret"{{' checked' if not defined('serverauthmethod') or serverauthmethod == 'sharedsecret' else ''}}> <label for="L2TP_serverauthmethodsharedsecret">Shared Secret</label></td>
							<td><input type="password" name="sharedsecret" value="{{get('sharedsecret', '')}}"{{' disabled' if defined('serverauthmethod') and serverauthmethod != 'sharedsecret' else ''}}/></td>
						</tr>
						<tr>
							<td><input type="radio" name="serverauthmethod" id="L2TP_serverauthmethodcertificate" value="servercertificate"{{' checked' if defined('serverauthmethod') and serverauthmethod == 'servercertificate' else ''}}> <label for="L2TP_serverauthmethodcertificate">Certificate</label></td>
							<td><input type="file" name="servercertificate"{{' disabled' if not defined('serverauthmethod') or serverauthmethod != 'servercertificate' else ''}}/></td>
						</tr>
