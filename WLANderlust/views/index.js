interfaces = {};
connectedToBSSID = null;
connectedToSSID = null;
showDevice = null

tunnels = null;
vpns = null;

function showDeviceTab(device) {
	showDevice = device;
	$("#interfaces .tab").not("#interfaceStatusTab_" + device).removeClass("selected");
	$(".interfaceStatus").not("#interfaceStatus_" + device).hide();
	$("#interfaceStatusTab_" + device).addClass("selected");
	$("#interfaceStatus_" + device).show();
}

function updateOutwardInterfaces(outwardInterfaces) {
	for(i in outwardInterfaces) {
		interfaceStatus = outwardInterfaces[i];
		interface = interfaceStatus["interface"];
		interfaceStatusID = "interfaceStatus_" + interface;

		interfaceStatusDOM = $("#" + interfaceStatusID);
		// Create the tab
		if(interfaceStatusDOM.length == 0) {
			tab = $("<span class=\"tab\">▲ " + interface + "</span>");
			$(tab).attr("id", "interfaceStatusTab_" + interface);
			$(tab).click(interface, function(event) {
				showDeviceTab(event.data);
			});
			$("#interfaces").append(tab);
			interfaces[interface] = {};

			interfaceStatusDOM = $.parseHTML(`<div class="interfaceStatus" id="${interfaceStatusID}">
				<button type="button" class="scan">Scan</button>
				<button type="button" class="sweep">Sweep</button>
				<div class="down">Down</div>
				<div class="disconnected">Disconnected</div>
				<div class="wired">Connected</div>
				<div class="nocable">Cable not connected</div>
				<div class="wifi">Connected to <span class="ssid"></span> (<span class="bssid"></span>) channel <span class="channel"></span></div>
				<div class="mobile">Connected</div>
				<div class="bluetooth">Connected to (<span class="bdaddr"></span>)</div>
				<div class="ip">IP address: <span class="ipaddress"></span> Netmask: <span class="netmask"></span> Gateway: <span class="gateway"></span></div>
				<div class="noip">No IP address assigned</div>
				<div class="nocaptiveportal">No Captive Portal present</div>
				<div class="captiveportalpresent">Captive Portal <span class="captiveportaltype"></span> <button type="button" class="solvecaptiveportal">Solve captive portal</button></div>
				<div class="solvedcaptiveportal">Captive Portal solved <span class="captiveportaltype"></span></div>
				<div class="tunnelinactive">IP tunneling not active </div>
				<div class="tunnelactive">IP tunneling active <button type="button" class="stoptunnel">Stop IP tunnel</button></div>
				<div class="tunnelerror" style="error">IP tunneling error <button type="button" class="stoptunnel">Stop IP tunnel</button></div>
				<div class="vpninactive">VPN disconnected </div>
				<div class="vpnactive">VPN connected <button type="button" class="stopvpn">Stop VPN</button></div>
				<div class="noexternalipaddress">No external IP address</div>
				<div class="hasexternalipaddress">External IP address: <span class="externalipaddress"></span></div>
				<div class="onlinesince">Online since <span class="time"></span> <button type="button" class="speedtest">Speedtest</button> <span class="speed"><span class="download"></span> <span class="upload"></span> <span class="latency"></span></span></div>
			</div>`);

			if(tunnels.length > 0) {
				if(tunnels.length == 1) {
					form = $(`<form><input type="hidden" name="id" value="${tunnels[0]["id"]}"></select></form>`);
				} else if(tunnels.length > 1) {
					form = $("<form><select name='id'></select></form>");
					for(i in tunnels) {
						$("select", form).append(`<option value="${tunnels[i]["id"]}">${tunnels[i].name}</option>`);
					}
				}
				$(form).append("<button type='button' class='starttunnel'>Start IP tunnel</button>");
				$(".tunnelinactive", interfaceStatusDOM).append(form);
				$(".starttunnel", interfaceStatusDOM).click(interface, function(event) {
					id = $("select[name='id']", $(this).parent('form')).val();
					$.get("/Networking/interface/" + event.data + "/tunnel/" + id + "/start");
					return false;
				});
				$(".stoptunnel", interfaceStatusDOM).click(interface, function(event) {
					$.get("/Networking/interface/" + event.data + "/tunnel/stop");
					return false;
				});
			}

			if(vpns.length > 0) {
				if(vpns.length == 1) {
					form = $(`<form><input type="hidden" name="id" value="${vpns[0]["id"]}"></select></form>`);
				} else if(vpns.length > 1) {
					form = $("<form><select name='id'></select></form>");
					for(i in vpns) {
						$("select", form).append(`<option value="${vpns[i]["id"]}">${vpns[i].name}</option>`);
					}
				}
				$(form).append("<button type='button' class='startvpn'>Start VPN</button>");
				$(".vpninactive", interfaceStatusDOM).append(form);
				$(".startvpn", interfaceStatusDOM).click(interface, function(event) {
					id = $("select[name='id']", $(this).parent('form')).val();
					$.get("/Networking/interface/" + event.data + "/vpn/" + id + "/start");
					return false;
				});
				$(".stopvpn", interfaceStatusDOM).click(interface, function(event) {
					$.get("/Networking/interface/" + event.data + "/vpn/stop");
					return false;
				});
			}
			$(".interfaceStatus").last().after(interfaceStatusDOM);

			$(".speedtest", interfaceStatusDOM).click(interface, function(event) {
				$.get("/Networking/interface/" + event.data + "/speedtest");
				return false;
			});

			if(interfaceStatus["type"] == "wifi") {
				$(".scan", interfaceStatusDOM).click(interface, function(event) {
					$.get("/Networking/interface/" + event.data + "/scan");
					return false;
				});
				$(".scan", interfaceStatusDOM).show();
				$(".sweep", interfaceStatusDOM).click(interface, function(event) {
					$.get("/Networking/interface/" + event.data + "/sweep/start");
					return false;
				});
				$(".sweep", interfaceStatusDOM).show();
			}

			if(showDevice == null && interfaceStatus["status"] == "online")
				showDevice = interface;
		}

		if(interfaceStatus["onlineSince"] != null) {
			onlineSince = interfaceStatus["onlineSince"];
			onlineSince = Math.floor(onlineSince / 86400) + " days, " + String(Math.floor((onlineSince % 86400) / 3600)).padStart(2, "0") + ":" + String(Math.floor((onlineSince % 3600) / 60)).padStart(2, "0") + ":" + String(onlineSince % 60).padStart(2, "0");
			$(".onlinesince .time", interfaceStatusDOM).text(onlineSince);
		}

		if(("timestamp" in interfaces[interface]) && interfaces[interface]["timestamp"] == interfaceStatus["timestamp"]) {
			continue;
		}
		interfaces[interface]["timestamp"] = interfaceStatus["timestamp"];

		if(interfaceStatus["status"] == "down") {
			$(".disconnected, .wired, .nocable, .wifi, .mobile, .bluetooth", interfaceStatusDOM).hide();
			$(".ip, .noip", interfaceStatusDOM).hide()
			$(".nocaptiveportal, .captiveportalpresent, .solvedcaptiveportal", interfaceStatusDOM).hide()
			$(".tunnelinactive, .tunnelactive, .tunnelerror", interfaceStatusDOM).hide()
			$(".vpninactive, .vpnactive, .vpnerror", interfaceStatusDOM).hide()
			$(".noexternalipaddress, .hasexternalipaddress, .onlinesince", interfaceStatusDOM).hide()
			$(".down", interfaceStatusDOM).show();
			continue;
		}

		$(".down", interfaceStatusDOM).hide();

		switch(interfaceStatus["type"]){
			case "wired":
				if(interfaceStatus["status"] == "nocable") {
					$(".down, .disconnected, .wired, .wifi, .mobile, .bluetooth", interfaceStatusDOM).hide();
					$(".wired", interfaceStatusDOM).hide();
					$(".ip, .noip", interfaceStatusDOM).hide()
					$(".nocaptiveportal, .captiveportalpresent, .solvedcaptiveportal", interfaceStatusDOM).hide()
					$(".tunnelinactive, .tunnelactive, .tunnelerror", interfaceStatusDOM).hide()
					$(".vpninactive, .vpnactive, .vpnerror", interfaceStatusDOM).hide()
					$(".noexternalipaddress, .hasexternalipaddress, .onlinesince", interfaceStatusDOM).hide()
					$(".nocable", interfaceStatusDOM).show();
					continue;
				} else {
					$(".down", interfaceStatusDOM).hide();
					$(".nocable", interfaceStatusDOM).hide();
					$(".wired", interfaceStatusDOM).show();
				}
				break
			case "wifi":
				if(("bssid" in interfaceStatus) && interfaceStatus["bssid"] != null) {
					connectedToBSSID = interfaceStatus["bssid"];
					connectedToSSID = interfaceStatus["ssid"];
					$(".disconnected", interfaceStatusDOM).hide();
					$(".bssid", interfaceStatusDOM).text(interfaceStatus["bssid"]);
					$(".ssid", interfaceStatusDOM).text(interfaceStatus["ssid"]);
					$(".channel", interfaceStatusDOM).text(interfaceStatus["channel"]);
					$(".wifi", interfaceStatusDOM).show();
				} else {
					connectedToBSSID = null;
					connectedToSSID = null;
					$(".wifi", interfaceStatusDOM).hide();
					$(".disconnected", interfaceStatusDOM).show();
				}
				break
			case "bluetooth":
				if(("bdaddr" in interfaceStatus) && interfaceStatus["bdaddr"] != null) {
					connectedToBDADDR = interfaceStatus["bdaddr"];
					$(".disconnected", interfaceStatusDOM).hide();
					$(".bdaddr", interfaceStatusDOM).text(interfaceStatus["bdaddr"]);
					$(".bluetooth", interfaceStatusDOM).show();
				} else {
					connectedToBDADDR = null;
					$(".bluetooth", interfaceStatusDOM).hide();
					$(".disconnected", interfaceStatusDOM).show();
				}
				break
			case "mobile":
				$(".mobile", interfaceStatusDOM).show();
				break
		}

		if(!("gateway" in interfaceStatus) || interfaceStatus["gateway"] == null) {
			console.log(interfaceStatus["gateway"]);
		}

		if(!("ipaddress" in interfaceStatus) || interfaceStatus["ipaddress"] == null) {
			$(".ip", interfaceStatusDOM).hide()
			$(".nocaptiveportal, .captiveportalpresent, .solvedcaptiveportal", interfaceStatusDOM).hide()
			$(".tunnelinactive, .tunnelactive, .tunnelerror", interfaceStatusDOM).hide()
			$(".vpninactive, .vpnactive, .vpnerror", interfaceStatusDOM).hide()
			$(".noexternalipaddress, .hasexternalipaddress, .onlinesince", interfaceStatusDOM).hide()
			$(".noip", interfaceStatusDOM).show()
			continue;
		}

		$(".ipaddress", interfaceStatusDOM).text(interfaceStatus["ipaddress"]);
		$(".netmask", interfaceStatusDOM).text(interfaceStatus["netmask"]);
		$(".gateway", interfaceStatusDOM).text(interfaceStatus["gateway"]);
		$(".noip", interfaceStatusDOM).hide()
		$(".ip", interfaceStatusDOM).show()

		if(!("captiveportal" in interfaceStatus) || interfaceStatus["captiveportal"]["status"] == null || interfaceStatus["captiveportal"]["type"] == "None") {
			$(".captiveportalpresent, .solvedcaptiveportal", interfaceStatusDOM).hide();
			$(".nocaptiveportal", interfaceStatusDOM).show();
		} else if(interfaceStatus["captiveportal"]["status"] == "present") {
			$(".captiveportaltype", interfaceStatusDOM).text(interfaceStatus["captiveportal"]["type"]);
			$(".nocaptiveportal, .solvedcaptiveportal", interfaceStatusDOM).hide();
			$(".captiveportalpresent", interfaceStatusDOM).show();
		} else if(interfaceStatus["captiveportal"]["status"] == "solved") {
			$(".captiveportaltype", interfaceStatusDOM).text(interfaceStatus["captiveportal"]["type"]);
			$(".nocaptiveportal, .captiveportalpresent", interfaceStatusDOM).hide();
			$(".solvedcaptiveportal", interfaceStatusDOM).show();
		}

		if(!("tunnel" in interfaceStatus) || interfaceStatus["tunnel"] == null || interfaceStatus["tunnel"]["status"] == "inactive") {
			//if(("captiveportal" in interfaceStatus) && interfaceStatus["captiveportal"]["status"] == "present") {
				$(".starttunnel", interfaceStatusDOM).show();
			//} else {
			//	$(".starttunnel", interfaceStatusDOM).hide();
			//}
			$(".tunnelactive, .tunnelerror", interfaceStatusDOM).hide();
			$(".tunnelinactive", interfaceStatusDOM).show();
		} else if(interfaceStatus["tunnel"]["status"] == "online") {
			$(".tunnelinactive, .tunnelerror", interfaceStatusDOM).hide();
			$(".tunnelactive", interfaceStatusDOM).show();
		} else {
			$(".tunnelinactive, .tunnelactive", interfaceStatusDOM).hide();
			$(".tunnelerror", interfaceStatusDOM).show();
		}

		if(!("vpn" in interfaceStatus) || interfaceStatus["vpn"] == null || interfaceStatus["vpn"]["status"] == "inactive") {
			if(interfaceStatus["status"] == "online") {
				$(".startvpn", interfaceStatusDOM).show();
			} else {
				$(".startvpn", interfaceStatusDOM).hide();
			}
			$(".vpnactive, .vpnerror", interfaceStatusDOM).hide();
			$(".vpninactive", interfaceStatusDOM).show();
		} else if(interfaceStatus["vpn"]["status"] == "online") {
			$(".vpninactive, .vpnerror", interfaceStatusDOM).hide();
			$(".vpnactive", interfaceStatusDOM).show();
		} else {
			$(".vpninactive, .vpnactive", interfaceStatusDOM).hide();
			$(".vpnerror", interfaceStatusDOM).show();
		}

		if(interfaceStatus["externalipaddress"] == null) {
			$(".hasexternalipaddress", interfaceStatusDOM).hide();
			$(".noexternalipaddress", interfaceStatusDOM).show();
		} else {
			if(interfaceStatus["vpn"] != null && interfaceStatus["vpn"]["externalipaddress"] != null) {
				$(".externalipaddress", interfaceStatusDOM).text(interfaceStatus["vpn"]["externalipaddress"]);
			} else if(interfaceStatus["tunnel"] != null && interfaceStatus["tunnel"]["externalipaddress"] != null) {
				$(".externalipaddress", interfaceStatusDOM).text(interfaceStatus["tunnel"]["externalipaddress"]);
			} else {
				$(".externalipaddress", interfaceStatusDOM).text(interfaceStatus["externalipaddress"]);
			}
			$(".noexternalipaddress", interfaceStatusDOM).hide();
			$(".hasexternalipaddress", interfaceStatusDOM).show();
		}

		if("speed" in interfaceStatus) {
			$(".speed .download").text(interfaceStatus["speed"]["download"]);
			$(".speed .upload").text(interfaceStatus["speed"]["upload"]);
			$(".speed .latency").text(interfaceStatus["speed"]["latency"]);
		}

		$(".onlinesince", interfaceStatusDOM).show()
	}

	if(showDevice == null) {
		showDevice = outwardInterfaces[0]["interface"]
	}
}

function updateInwardInterfaces(inwardInterfaces) {
	//$("#interfaces").append("<span>&nbsp;&nbsp;</span>");

	for(i in inwardInterfaces) {
		interfaceStatus = inwardInterfaces[i];
		interface = interfaceStatus["interface"];
		interfaceStatusID = "interfaceStatus_" + interface;

		interfaceStatusDOM = $("#" + interfaceStatusID);
		// Create the tab
		if(interfaceStatusDOM.length == 0) {
			tab = $("<span class=\"tab\">▼ " + interface + "</span>");
			$(tab).attr("id", "interfaceStatusTab_" + interface);
			$(tab).click(interface, function(event) {
				showDeviceTab(event.data);
			});
			$("#interfaces").append(tab);
			interfaces[interface] = {};

			interfaceStatusDOM = $.parseHTML(`<div class="interfaceStatus" id="${interfaceStatusID}">
				<div class="down">Down</div>
				<div class="disconnected">Disconnected</div>
				<div class="wired">Connected</div>
				<div class="nocable">Cable not connected</div>
				<div class="wifi"><span class="ssid"></span> (<span class="bssid"></span>) channel <span class="channel"></span></div>
				<div class="bluetooth">(<span class="bdaddr"></span>)</div>
				<div class="ip">IP address: <span class="ipaddress"></span> Netmask: <span class="netmask"></span></div>
			</div>`);
			$(".interfaceStatus").last().after(interfaceStatusDOM);
		}

		$(".down", interfaceStatusDOM).hide();

		switch(interfaceStatus["type"]){
			case "wired":
				if(interfaceStatus["status"] == "nocable") {
					$(".down, .disconnected, .wired, .wifi, .mobile, .bluetooth", interfaceStatusDOM).hide();
					$(".wired", interfaceStatusDOM).hide();
					$(".ip, .noip", interfaceStatusDOM).hide()
					$(".nocaptiveportal, .captiveportalpresent, .solvedcaptiveportal", interfaceStatusDOM).hide()
					$(".tunnelinactive, .tunnelactive, .tunnelerror", interfaceStatusDOM).hide()
					$(".vpninactive, .vpnactive, .vpnerror", interfaceStatusDOM).hide()
					$(".noexternalipaddress, .hasexternalipaddress, .onlinesince", interfaceStatusDOM).hide()
					$(".nocable", interfaceStatusDOM).show();
					continue;
				} else {
					$(".down", interfaceStatusDOM).hide();
					$(".nocable", interfaceStatusDOM).hide();
					$(".wired", interfaceStatusDOM).show();
				}
				break
			case "wifi":
				$(".disconnected", interfaceStatusDOM).hide();
				$(".bssid", interfaceStatusDOM).text(interfaceStatus["bssid"]);
				$(".ssid", interfaceStatusDOM).text(interfaceStatus["ssid"]);
				$(".channel", interfaceStatusDOM).text(interfaceStatus["channel"]);
				$(".wifi", interfaceStatusDOM).show();
				break
			case "bluetooth":
				$(".disconnected", interfaceStatusDOM).hide();
				$(".bdaddr", interfaceStatusDOM).text(interfaceStatus["bdaddr"]);
				$(".bluetooth", interfaceStatusDOM).show();
				break
		}

		if(!("ipaddress" in interfaceStatus) || interfaceStatus["ipaddress"] == null) {
			$(".ip", interfaceStatusDOM).hide()
			$(".nocaptiveportal, .captiveportalpresent, .solvedcaptiveportal", interfaceStatusDOM).hide()
			$(".tunnelinactive, .tunnelactive, .tunnelerror", interfaceStatusDOM).hide()
			$(".vpninactive, .vpnactive, .vpnerror", interfaceStatusDOM).hide()
			$(".noexternalipaddress, .hasexternalipaddress, .onlinesince", interfaceStatusDOM).hide()
			$(".noip", interfaceStatusDOM).show()
			continue;
		}

		$(".ipaddress", interfaceStatusDOM).text(interfaceStatus["ipaddress"]);
		$(".netmask", interfaceStatusDOM).text(interfaceStatus["netmask"]);
		$(".gateway", interfaceStatusDOM).text(interfaceStatus["gateway"]);
		$(".noip", interfaceStatusDOM).hide()
		$(".ip", interfaceStatusDOM).show()
	}
}

function toDMS(coordinate, cardinals) {
	var absolute = Math.abs(coordinate);
	var degrees = Math.floor(absolute);
	var minutesNotTruncated = (absolute - degrees) * 60;
	var minutes = Math.floor(minutesNotTruncated);
	var seconds = Math.floor((minutesNotTruncated - minutes) * 60);
	var cardinal = coordinate >= 0 ? cardinals.charAt(0) : cardinals.charAt(1);

	return degrees + "&deg; " + minutes +  "&prime; " + seconds + "&Prime; " + cardinal;
}

function updateGPS(status) {
	interface = "gps";
	interfaceStatusID = "interfaceStatus_" + interface;

	interfaceStatusDOM = $("#" + interfaceStatusID);
	// Create the tab
	if(interfaceStatusDOM.length == 0) {
		$("#interfaces").append("&nbsp;");
		tab = $("<span class=\"tab\">&#128752; " + interface + "</span>");
		$(tab).attr("id", "interfaceStatusTab_" + interface);
		$(tab).click(interface, function(event) {
			showDeviceTab(event.data);
		});
		$("#interfaces").append(tab);
		interfaces[interface] = {};

		interfaceStatusDOM = $.parseHTML(`<div class="interfaceStatus" id="${interfaceStatusID}">
			<div>Location: <span class="location"></span></div>
		</div>`);
		$(".interfaceStatus").last().after(interfaceStatusDOM);
	}

	if(status["location"] != null) {
		$(".location", interfaceStatusDOM).html(toDMS(status["location"][0], "NS") + " " + toDMS(status["location"][1], "EW"));
	}
}

function updateStatus() {
	$.getJSON("/status.json", success = function(status) {
		tunnels = status.Networking.Tunnels;
		vpns = status.Networking.VPNs;
		updateOutwardInterfaces(status.Networking.OutwardInterfaces);
		updateInwardInterfaces(status.Networking.InwardInterfaces);
		updateGPS(status.GPS);
		showDeviceTab(showDevice);
	}).always(function() {
		setTimeout(function() {
			updateStatus();
		}, 1000);
	});
}

function connectToNetwork(network) {
	if(network["bssid"] != null)
		var url = "/Networking/bssid/" + network["bssid"] + "/connect";
	else
		var url = "/Networking/ssid/" + network["ssid"] + "/connect";

	if(network["encryption"]["status"] == "none" || network["known"]) {
		$.getJSON(url, success = function(response) {
		});
	} else if(network["encryption"]["type"] == "wpa") {
		$("#addWPACredential .ssid").text(network["ssid"]);
		$("#addWPACredential .bssid").text(network["bssid"]);
		$("#addWPACredential form").submit(network, function(event) {
			form = this;
			$.post(url, $("#addWPACredential form").serialize()
				).done(function(data) {
					$(form).closest(".overlay").hide();
					form.reset();
				}).fail(function(data) {
				});
			return false;
		});
		$("#addWPACredential").show();
	} else if(network["encryption"]["type"] == "wpa2") {
		$("#addWPA2Credential .ssid").text(network["ssid"]);
		$("#addWPA2Credential .bssid").text(network["bssid"]);
		$("#addWPA2Credential > form").submit(network, function(event) {
			form = this;
			$.post(url, $("#addWPA2Credential form").serialize()
				).done(function(data) {
					$(form).closest(".overlay").hide();
					form.reset();
				}).fail(function(data) {
				});
			return false;
		});
		$("#addWPA2Credential").show();
	} else if(network["encryption"]["type"] == "wep") {
		$("#addWEPCredential .ssid").text(network["ssid"]);
		$("#addWEPCredential .bssid").text(network["bssid"]);
		$("#addWEPCredential form").submit(network, function(event) {
			form = this;
			$(form).closest(".overlay").hide();
			form.reset();
			return false;
		});
		$("#addWEPCredential").show();
	}
}

function updateNetworks() {
	$.getJSON("/Networking/networks.json", success = function(networks) {
		activeIDs = [];
		for(i in networks) {
			network = networks[i];
			networkStatusID = "networkStatus_" + network["ssid"].replace(/["'!?&,\.\(\)@]/g, "").replace(/ /g, "_");
			networkStatusDOM = $("#" + networkStatusID);
			if(networkStatusDOM.length == 0 && network["bssid"] != null) {
				networkStatusID = "networkStatus_" + network["bssid"].replace(/:/g, "");
				networkStatusDOM = $("#" + networkStatusID);
			}
			if(networkStatusDOM.length == 0) {
				//networkStatusDOM = $("#networkStatus").clone();
				networkStatusDOM = $.parseHTML(`<div class="networkStatus" id="${networkStatusID}">
					<div class="bssid">${network["bssid"]}</div>
					<div class="ssid"></div>
					<div class="channel"></div>
					<div class="signal"></div>
					<div class="quality"></div>
					<div class="distance"></div>
					<div class="encryption"></div>
					<div class="captiveportal"></div>
					<div class="status"></div>
					<div class="connect"><button type="button">Connect</button></div>
				</div>`);
				$(".connect button", networkStatusDOM).click(network, function(event) {
					connectToNetwork(event.data);
					return false;
				});;
				$("#networks").append(networkStatusDOM);
			}

			activeIDs.push(networkStatusID);

			$(".ssid", networkStatusDOM).text(network["ssid"]);
			$(".channel", networkStatusDOM).text(network["channel"]);
			$(".signal", networkStatusDOM).text(network["signal"]);
			$(".quality", networkStatusDOM).text(network["quality"]);
			distance = "";
			if(network["distance"] != null) {
				distance = network["distance"];
				if(distance < 1000) {
					distance = (Math.round(distance * 10) / 10) + " M";
				} else {
					distance = (Math.round(distance / 100) / 10) + " KM";
				}
			}
			$(".distance", networkStatusDOM).text(distance);
			if(network["encryption"]["status"] == "none") {
				$(".encryption", networkStatusDOM).text("None");
				$(".encryption", networkStatusDOM).addClass("none");
			} else {
				$(".encryption", networkStatusDOM).text(network["encryption"]["type"].toUpperCase());
			}
			$(".captiveportal", networkStatusDOM).text(network["captiveportal"]["type"]);
			$(".status", networkStatusDOM).text(network["status"]);

			if(network["known"])
				$(".connect button", networkStatusDOM).addClass("known");
			else if(network["captiveportal"]["solvable"])
				$(".connect button", networkStatusDOM).addClass("solvable");

			if(network["bssid"] != null && network["bssid"] == connectedToBSSID) {
				$(".connect button", networkStatusDOM).hide()
			} else if(network["ssid"] != null && network["ssid"] == connectedToSSID) {
				$(".connect button", networkStatusDOM).hide()
			} else {
				$(".connect button", networkStatusDOM).show()
			}
		}

		$("#networks > div").each(function () {
			if(activeIDs.indexOf(this.id) < 0) {
				//console.log("removing " + this.id);
				this.remove();
			}
		});

		sortNetworks();
	}).always(function() {
		setTimeout(function() {
			updateNetworks();
		}, 1000);
	});
}

var sortBy = "quality";
function sortNetworks() {
	$("#networks > div").sort(function (a, b) {
		switch(sortBy) {
			case "bssid":
			case "ssid":
			case "encryption":
			case "captiveportal":
				return $("." + sortBy, a).text().localeCompare($("." + sortBy, b).text());
			case "quality":
			case "signal":
				return eval($("." + sortBy, b).text()) - eval($("." + sortBy, a).text());
			case "channel":
			case "disance":
				return parseFloat($("." + sortBy, a).text()) - parseFloat($("." + sortBy, b).text());
		}
		return 0;
	}).appendTo("#networks");
}

$(document).ready(function() {
	updateStatus();
	updateNetworks();

	$("#refreshnetworks").click(function() {
		updateNetworks();
		return false;
	});

	$("#networks thead .ssid").click(function() {
		sortBy = "ssid";
		sortNetworks();
	});

	$("#networks thead .channel").click(function() {
		sortBy = "channel";
		sortNetworks();
	});

	$("#networks thead .quality").click(function() {
		sortBy = "quality";
		sortNetworks();
	});

	$("#networks thead .distance").click(function() {
		sortBy = "distance";
		sortNetworks();
	});

	$("#networks thead .encryption").click(function() {
		sortBy = "encryption";
		sortNetworks();
	});

	$("#networks thead .captiveportal").click(function() {
		sortBy = "captiveportal";
		sortNetworks();
	});
});
