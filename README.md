| **S. No.** | **Test Case**                      | **Description**                                                                   | **Expected Result**                                                     |
| ---------- | ---------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| PTC-01     | SNMP Anonymous Access              | Attempt SNMP access using default community strings like `public` or `private`    | Access should be denied; if allowed, it's a security risk               |
| PTC-02     | SNMP Community String Brute Force  | Use tools to brute-force SNMP community strings (e.g., `onesixtyone`)             | If a valid string is found, it indicates weak SNMP security             |
| PTC-03     | Sensitive Data Disclosure via SNMP | Perform SNMP walk to extract system info, users, interfaces, routing tables, etc. | Any sensitive or internal data should not be accessible                 |
| PTC-04     | SNMP Write Access Attempt          | Try `snmpset` with guessed write community string to modify SNMP values           | If successful, attacker can alter settings — **critical vulnerability** |


TCL Scripting Abuse with File Write/Delete Capabilities


| **Category**                         | **Test Case**                                                        |
| ------------------------------------ | -------------------------------------------------------------------- |
| **Service Misconfigurations**        | Unquoted Service Path                                                |
|                                      | Weak Service Permissions                                             |
|                                      | Insecure Service Executables                                         |
|                                      | DLL Hijacking in Services                                            |
|                                      | Writable Registry for Service                                        |
|                                      | Auto-run Services in HKLM                                            |
|                                      | Hijackable Scheduled Tasks                                           |
| **UAC Bypasses**                     | UAC Token Impersonation                                              |
|                                      | Auto-elevated COM Interfaces                                         |
|                                      | Fodhelper Exploit                                                    |
|                                      | Event Viewer Bypass                                                  |
|                                      | SilentCleanup / sdclt.exe Exploit                                    |
| **Credential Theft**                 | SAM Hive Extraction                                                  |
|                                      | LSASS Dumping                                                        |
|                                      | Mimikatz Usage                                                       |
|                                      | DPAPI Credential Extraction                                          |
| **Token Manipulation**               | Token Impersonation (Incognito / Rogue Token)                        |
|                                      | SeImpersonatePrivilege Exploitation (e.g., Potato family)            |
|                                      | SeAssignPrimaryTokenPrivilege Abuse                                  |
|                                      | CreateProcessWithToken / S4U                                         |
| **AlwaysInstallElevated**            | MSI Exploitation                                                     |
| **Startup Folder Abuse**             | Writable Startup Folders                                             |
| **DLL Hijacking**                    | Application DLL Load Order Hijack                                    |
|                                      | Side-Loading DLLs via Trusted Apps                                   |
| **Environment Variable Abuse**       | PATH Hijacking                                                       |
|                                      | Windir Variable Manipulation                                         |
| **Insecure File/Folder Permissions** | Writable Files in System Paths                                       |
|                                      | Writable Program Files (e.g., in `Program Files`)                    |
| **Registry Attacks**                 | Writable Run Keys                                                    |
|                                      | Image File Execution Options (IFEO) Hijack                           |
|                                      | AppInit\_DLLs Injection                                              |
| **Driver Exploitation**              | Vulnerable Driver Loading (Bring Your Own Vulnerable Driver - BYOVD) |
| **Password Reuse / Weak Passwords**  | Local Admin Reuse                                                    |
|                                      | Password in Scripts or Configs                                       |
| **Named Pipe Impersonation**         | Rogue Named Pipe Server                                              |
|                                      | Juicy Potato / Rogue Potato Exploits                                 |
| **WMI Abuse**                        | Event Subscription to Gain SYSTEM                                    |
| **Abusable SUID-like Privs**         | SeDebugPrivilege                                                     |
|                                      | SeBackupPrivilege                                                    |
|                                      | SeRestorePrivilege                                                   |
|                                      | SeTakeOwnershipPrivilege                                             |
| **Insecure Scripting Engines**       | PowerShell Constrained Language Bypass                               |
|                                      | AMSI Bypass                                                          |
| **Shadow Copies / Backups**          | SAM Copy via Volume Shadow Copy (VSS)                                |
