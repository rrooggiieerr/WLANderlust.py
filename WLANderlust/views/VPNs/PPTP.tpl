						<tr>
							<td><label for="PPTP_username">Username</label></td>
							<td><input type="text" id="PPTP_username" name="username" value="{{get('username', '')}}" autocomplete="off"/></td>
						</tr>
						<tr>
							<td><label for="PPTP_hostname">Server Hostname</label></td>
							<td><input type="text" id="PPTP_hostname" name="hostname" value="{{get('hostname', '')}}" autocomplete="off"/></td>
						</tr>
						<tr>
							<th colspan="2">User Authentication</th>
						</tr>
						<tr>
							<td><input type="radio" id="PPTP_userauthmethodpassword" name="userauthmethod" value="password"{{' checked' if not defined('userauthmethod') or userauthmethod == 'password' else ''}}> <label for="PPTP_userauthmethodpassword">Password</label></td>
							<td><input type="password" name="password" value="{{get('password', '')}}"{{' disabled' if defined('userauthmethod') and userauthmethod != 'password' else ''}} autocomplete="off"/></td>
						</tr>
						<tr>
							<td><input type="radio" id="PPTP_userauthmethodcertificate" name="userauthmethod" value="usercertificate"{{' checked' if defined('userauthmethod') and userauthmethod == 'usercertificate' else ''}}> <label for="PPTP_userauthmethodcertificate">Certificate</label></td>
							<td><input type="file" name="usercertificate"{{' disabled' if not defined('userauthmethod') or userauthmethod != 'usercertificate' else ''}}/></td>
						</tr>
