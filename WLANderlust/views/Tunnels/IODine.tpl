						<script>
							function getStdout() {
								$.ajax("/IODine/stdout", {
									statusCode: {
										200: function (response) {
											$("#IODine_stdout").text(response);

											console.log("Finished");
										},
										206: function (response) {
											$("#IODine_stdout").text(response);

											setTimeout(function() {
												getUpdates();
											}, 50);
										}
									}
								});
							}

							$(document).ready(function() {
								//getStdout();
								$("#connect").click(function() {
									return false;
								});
							});
						</script>
						<tr>
							<td><label for="IODine_topdomain">DNS top domain</label></td>
							<td><input type="text" id="IODine_topdomain" name="topdomain" value="{{get('topdomain', '')}}"/></td>
						</tr>
						<tr>
							<td><label for="IODine_password">Password</label></td>
							<td><input type="password" id="IODine_password" name="password" value="{{get('password', '')}}"/></td>
						</tr>
						<tr><td colspan="2"><div id="IODine_stdout" style="white-space: pre-wrap;"></div></td></tr>
