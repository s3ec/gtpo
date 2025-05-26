# gtpo

nmap -p 22,111,1002,2000,3001,5004,5060,5555,7007,8001,10243 -sV -sC --script=default,vuln,safe 192.168.1.10
nmap -p 22 -sV --script=ssh-hostkey,ssh2-enum-algos,safe <target-ip>

