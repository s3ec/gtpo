Absolutely — here’s a full list of **`reg query`** and related commands to check whether features like **LLMNR**, **NetBIOS**, **mDNS**, and others that affect **hash capture (e.g., NTLM via SMB/HTTP)** are enabled or disabled on a Windows system.

---

## ✅ FULL CHECKLIST – Registry & Network Settings

> Run these in **Command Prompt** or **PowerShell** (no elevation needed for reads).

---

### 🔹 1. ✅ **LLMNR (Link-Local Multicast Name Resolution)**

```cmd
reg query "HKLM\Software\Policies\Microsoft\Windows NT\DNSClient" /v EnableMulticast
```

* `EnableMulticast = 1` → ✅ LLMNR is enabled
* `EnableMulticast = 0` → ❌ LLMNR disabled by Group Policy
* If value is **missing** → ✅ Enabled by default

---

### 🔹 2. ✅ **NetBIOS over TCP/IP (for NBNS spoofing)**

Check via WMI:

```powershell
Get-WmiObject -Query "SELECT * FROM Win32_NetworkAdapterConfiguration WHERE IPEnabled = 'True'" | Select-Object Description, SettingID, TcpipNetbiosOptions
```

* `TcpipNetbiosOptions = 0` → Default (enabled if DHCP says so)
* `TcpipNetbiosOptions = 1` → ✅ NetBIOS **enabled**
* `TcpipNetbiosOptions = 2` → ❌ NetBIOS **disabled**

---

### 🔹 3. ✅ **mDNS (Multicast DNS)**

Windows 10/11 use `dnscache` service for mDNS. Check:

```powershell
sc query dnscache
```

Also check:

```cmd
reg query "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" /v EnableMDNS
```

* `EnableMDNS = 0` → ❌ mDNS disabled
* `EnableMDNS = 1` → ✅ mDNS enabled
* Missing → ❌ Default is **disabled**

---

### 🔹 4. ✅ **LLMNR via Windows Defender Firewall**

Ensure outbound UDP 5355 isn’t blocked:

```powershell
netsh advfirewall firewall show rule name=all | findstr /i "LLMNR"
```

Or inspect firewall rules in GUI:

* Outbound → UDP port **5355**
* Block rule? → LLMNR won't work

---

### 🔹 5. ✅ **SMB (for NTLM hash over port 445)**

Ensure SMBv1/2/3 are available:

```powershell
Get-SmbServerConfiguration | Select EnableSMB1Protocol, EnableSMB2Protocol
```

And check the client (victim):

```powershell
sc query mrxsmb10
sc query mrxsmb20
```

---

### 🔹 6. ✅ **NTLM Restrictions (Windows Hardening)**

NTLM may be blocked. Check:

```cmd
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LmCompatibilityLevel
```

Values:

| Value | Meaning                        |
| ----- | ------------------------------ |
| 0     | ✅ LM and NTLMv1/2 allowed      |
| 3     | ✅ Only NTLMv2                  |
| 5     | ❌ Only Kerberos (NTLM refused) |

---

### 🔹 7. ✅ **WPAD Auto Detection (for HTTP/Proxy spoofing)**

```cmd
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\Wpad" /v WpadOverride
```

Also check:

```cmd
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v AutoDetect
```

* `AutoDetect = 1` → ✅ WPAD discovery is on

---

### 🔹 8. ✅ **Proxy Settings (can trigger HTTP NTLM)**

```cmd
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyEnable
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v ProxyServer
```

---

## 🧪 Summary Table

| Feature       | Check Command                                           |                 |
| ------------- | ------------------------------------------------------- | --------------- |
| LLMNR         | `reg query HKLM\...\DNSClient /v EnableMulticast`       |                 |
| NetBIOS       | `Get-WmiObject Win32_NetworkAdapterConfiguration`       |                 |
| mDNS          | `reg query HKLM\...\Dnscache\Parameters /v EnableMDNS`  |                 |
| Firewall rule | \`netsh advfirewall firewall show rule name=all         | findstr LLMNR\` |
| SMB enabled   | `Get-SmbServerConfiguration`                            |                 |
| NTLM policy   | `reg query HKLM\SYSTEM\...\Lsa /v LmCompatibilityLevel` |                 |
| WPAD          | `reg query HKCU\...\Internet Settings /v AutoDetect`    |                 |
| Proxy         | `reg query HKCU\...\Internet Settings /v ProxyEnable`   |                 |

---

## 🛠 Want to Automate All This?

Let me know — I can give you a **PowerShell script** to check all these settings at once and print ✅/❌ for each.

Would you like that?
