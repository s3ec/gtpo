// whoami_clickable.js
var wsh = WScript.CreateObject("WScript.Shell");
var username = wsh.ExpandEnvironmentStrings("%USERNAME%");
WScript.Echo("Current user: " + username);
