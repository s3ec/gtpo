Perfect — let’s refine the remediation to highlight the **really good key hardening steps** for LLMNR, NetBIOS, IPv6 abuse, and WPAD. Here’s the tightened version:

---

### **Vulnerability: Hash Capture via LLMNR/NBT-NS/WPAD Spoofing**

**Description**
Link-Local Multicast Name Resolution (LLMNR) and NetBIOS Name Service (NBT-NS) are legacy name resolution protocols that allow hosts to resolve names when DNS queries fail. When enabled, an attacker on the same network can spoof responses to these queries and trick a victim machine into authenticating to the attacker’s system. This often results in the capture of NTLMv2 password hashes, which can be brute-forced offline to reveal valid user credentials. The risk is compounded in IPv6 environments, where similar behavior may occur with multicast name resolution.

**Observation**
During assessment, it was identified that the target environment LLMNR, NetBIOS, and IPv6 was enabled. This allows an attacker to intercept or spoof name resolution traffic and capture user credential hashes over the local network. Tools like *Responder* or *Inveigh* can exploit this to perform relay attacks or offline cracking.

**Impact**

* Credential exposure through NTLMv2 hash capture.
* Potential privilege escalation if captured credentials belong to privileged accounts.
* Increased attack surface for relay attacks against SMB, LDAP, HTTP, or other services.
* Facilitates lateral movement within the internal network.

**Remediation (Key Recommendations)**

* **Disable LLMNR**

  * Group Policy: *Computer Configuration > Administrative Templates > Network > DNS Client > Turn off Multicast Name Resolution = Enabled*.
  * Registry: `HKLM\Software\Policies\Microsoft\Windows NT\DNSClient\EnableMulticast` = `0`.

* **Disable NetBIOS**

  * NIC settings → TCP/IP → Advanced → WINS → *Disable NetBIOS over TCP/IP*.
  * DHCP Scope option 001 can also disable NetBIOS via server configuration.

* **Mitigate IPv6 abuse**

  * If IPv6 is not in use, disable it at the NIC level or via Group Policy.
  * Alternatively, harden IPv6 traffic by filtering rogue RA/DHCPv6 and configuring DNS6 securely.

* **Disable WPAD (Web Proxy Auto-Discovery Protocol)**

  * Group Policy: *Computer Configuration > Administrative Templates > Windows Components > Internet Explorer > Prevent changing proxy settings*.
  * Registry: `HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Wpad` = `0`.
  * Block WPAD at the DNS and DHCP level to prevent auto-discovery.

* **Additional hardening**

  * Enforce **SMB signing** and **Extended Protection for Authentication (EPA)**.
  * Deploy **strong password policies** to reduce the risk of NTLM hash cracking.
  * Monitor logs for suspicious name resolution traffic or repeated NTLM authentication attempts.

**References**

* [Microsoft: Disable LLMNR and NetBIOS](https://learn.microsoft.com/en-us/windows-server/networking/technologies/llmnr/disable-llmnr)
* [Microsoft: Configure WPAD](https://support.microsoft.com/help/318864)
* [MITRE ATT\&CK – T1557: Adversary-in-the-Middle](https://attack.mitre.org/techniques/T1557/)
* [US-CERT: LLMNR and NBT-NS Poisoning](https://www.cisa.gov/news-events/alerts/2017/08/02/alert-ta17-202a)

---

Do you want me to also **add the exact registry keys for IPv6 disablement** (like `DisabledComponents` under `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters`) so it’s super actionable for admins?
