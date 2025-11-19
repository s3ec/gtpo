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



// -----------------------------
// 1. Run systeminfo safely
// -----------------------------
var sysRoot = shell.ExpandEnvironmentStrings("%SystemRoot%");
var sysinfoExec;

try {
    sysinfoExec = shell.Exec(sysRoot + "\\SysNative\\systeminfo.exe");
} catch(e) {
    sysinfoExec = shell.Exec(sysRoot + "\\System32\\systeminfo.exe");
}

var output = sysinfoExec.StdOut.ReadAll();
WScript.Echo("=== SYSTEMINFO ===\n\n" + output);


// -----------------------------
// 2. Run EXE in same folder
// -----------------------------

// Get current script folder
var fso = new ActiveXObject("Scripting.FileSystemObject");
var scriptFullPath = WScript.ScriptFullName;
var scriptFolder = fso.GetParentFolderName(scriptFullPath);

// Your EXE filename (same folder)
var exeName = "winner.exe";   // <-- just the name, no path

// Build full path safely
var exeFullPath = scriptFolder + "\\" + exeName;

// Run it (normal window, don’t wait)
shell.Run('"' + exeFullPath + '"', 1, false);
