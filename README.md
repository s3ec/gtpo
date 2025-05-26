# gtpo

nmap -iL ips.txt -p- -A -T4 --script "default,vuln,version,safe,discovery and not dos" --script-timeout 60s -oN full_scan.txt -oX full_scan.xml
