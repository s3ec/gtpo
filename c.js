// Create WScript Shell object
var shell = WScript.CreateObject("WScript.Shell");

// 1. Open Notepad
shell.Run("notepad.exe", 1, false); // 1 = normal window, false = don't wait

// 2. Run whoami and show output
var whoamiExec = shell.Exec("whoami");
var whoamiOutput = whoamiExec.StdOut.ReadAll();
WScript.Echo("=== whoami ===\n" + whoamiOutput);

// 3. Run ipconfig and show output
var ipconfigExec = shell.Exec("ipconfig");
var ipconfigOutput = ipconfigExec.StdOut.ReadAll();
WScript.Echo("=== ipconfig ===\n" + ipconfigOutput);

// Create WScript Shell object
var shell = WScript.CreateObject("WScript.Shell");

// -------------------------
// 1. Run systeminfo
// -------------------------
var sysRoot = shell.ExpandEnvironmentStrings("%SystemRoot%");
var sysinfoExec;

// Use SysNative to avoid 32/64‑bit redirection issues
var sysinfoPath = sysRoot + "\\SysNative\\systeminfo.exe";

// Try SysNative first
try {
    sysinfoExec = shell.Exec(sysinfoPath);
} catch(e) {
    // If SysNative doesn’t exist, fall back to System32
    sysinfoExec = shell.Exec(sysRoot + "\\System32\\systeminfo.exe");
}

var sysinfoOutput = sysinfoExec.StdOut.ReadAll();

// Show output
WScript.Echo("=== SYSTEMINFO OUTPUT ===\n\n" + sysinfoOutput);



// -------------------------
// 2. Run your EXE file
// -------------------------

// Full path to your application
var appPath = "C:\\Users\\gan\\Downloads\\winner.exe";

// Run it (1 = normal window, false = don't wait)
shell.Run('"' + appPath + '"', 1, false);

