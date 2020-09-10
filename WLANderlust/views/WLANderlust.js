if(location.protocol !== 'https:') {
	// Test if the self signed SSL certificate is installed, then redirect to HTTPS
	var request = new XMLHttpRequest();
	request.onreadystatechange = function() {
		console.log(request.readyState);
		console.log(request.status);
		if(request.readyState == 4 && request.status == 200) {
			// Self signed SSL certificate seems to be installed, redirect to HTTPS
			location.replace(`https:${location.href.substring(location.protocol.length)}`);
		}
	}
	request.open("GET", `https://${location.hostname}/ssltest.txt`, true);
	request.send(null);
}

function updateLocation(coords) {
	console.log(coords);
	//$.post("/GPS/location", coords);
}

function toggleShowPassword(dom) {
	if($(dom).attr("type") == "password") {
		$(dom).attr("type", "text");
		//$(dom).next("span").text("H");
	} else {
		$(dom).attr("type", "password");
		//$(dom).next("span").html("&#x1f441;");
	}
}

$(document).ready(function() {
	$("input:radio").click(function() {
		$("input[name="+$(this).attr("name")+"]").each(function() {
			$("#"+$(this).attr("value")).prop("disabled", true);
		});
		$("#" + $(this).attr("value")).prop("disabled", false);
		$("#" + $(this).attr("value")).focus();
	});

	$("form").attr("autocomplete", "off");

	$("input:password").attr("autocomplete", "new-password");
	$("input:password").each(function() {
		$(this).after("<span class=\"toggleShowPassword\">&#x1f441;</span>");
		$(this).next("span").click(this, function(event) {
			toggleShowPassword(event.data);
		});
	});

	$(".overlay .cancel").click(function(event) {
		$(this).closest(".overlay").hide();
		return false;
	});

	if(location.protocol === 'https:' && navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(function (position) {
			updateLocation(position.coords);
		});
		navigator.geolocation.watchPosition(function (position) {
			updateLocation(position.coords);
		});
	}
});
