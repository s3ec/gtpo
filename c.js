var shell = WScript.CreateObject("WScript.Shell");

// Run a command and return entire output
function run(cmd) {
    try {
        var exec = shell.Exec(cmd);
        return exec.StdOut.ReadAll();
    } catch(e) {
        return "[Error running: " + cmd + "]";
    }
}

var output = "";

// OS info
output += "=== SYSTEMINFO ===\n";
output += run("systeminfo");
output += "\n";

// CPU info
output += "=== CPU INFORMATION ===\n";
output += run("wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors /format:list");
output += "\n";

// OS version (WMIC)
output += "=== OS VERSION (WMIC) ===\n";
output += run("wmic os get Caption,Version,BuildNumber /format:list");
output += "\n";

// Memory info
output += "=== MEMORY INFORMATION ===\n";
output += run("wmic computersystem get TotalPhysicalMemory /format:list");
output += "\n";

// Disk info
output += "=== DISK INFORMATION ===\n";
output += run("wmic logicaldisk get Name,Size,FreeSpace /format:list");
output += "\n";

// Current user
output += "=== CURRENT USER ===\n";
output += run("whoami");
output += "\n";

WScript.Echo(output);
