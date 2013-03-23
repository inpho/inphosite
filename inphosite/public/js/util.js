// Utility namespace for InPhO JavaScript. Contains dynamic URL builder.
var inpho = inpho || {};
inpho.util = inpho.util || {};

/* inpho.util.url
 * Takes a path for the inpho rest API and builds an absolute URL based on the
 * current host and protocol.
 * 
 * // running on http://inphodev.cogs.indiana.edu:8080
 * > inpho.util.url('/entity.json')
 * http://inphodev.cogs.indiana.edu:8080/entity.json
 * */
inpho.util.base_url = null;
inpho.util.url = function(api_call) {  
  if (inpho.util.base_url == null)
    return window.location.protocol + "//" + window.location.host + api_call;
  else
    return inpho.util.base_url + api_call;
}

inpho.util.getCookieValueForName = function(cookieName) {
	console.log("Getting list of cookies...");
	var cookies = document.cookie.split(";");
	for(var i = 0; i < cookies.length; i++) {
		var pair = cookies[i].split("=");
		console.log("Cookie " + i + ": name(" + pair[0] + "), value(" + pair[1] + ")");

		if(pair[0] === cookieName) {
			console.log("Success! Cookie found: " + cookieName);
			return pair[1];
		}
	}
	console.log("Error! Cookie not found: " + cookieName);
	return null;
}