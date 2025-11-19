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

// 4. Run systeminfo and show output
var sysinfoExec = shell.Exec("systeminfo");
var sysinfoOutput = sysinfoExec.StdOut.ReadAll();
WScript.Echo("=== systeminfo ===\n" + sysinfoOutput);
