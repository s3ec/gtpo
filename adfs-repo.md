

### Finding 1: Account Takeover via Password Spray on ADFS Authentication Portal 





**Description:**

The ADFS (Active Directory Federation Services) authentication portal was found to be vulnerable to password spraying attacks due to weak authentication hardening. Password spraying is a brute-force technique where attackers try a small number of common passwords across many usernames. Unlike traditional brute-force attacks, password spraying avoids account lockout by limiting the number of attempts per account, making it stealthier and more effective against externally exposed login interfaces.

In this case, the ADFS portal allowed repeated authentication attempts without effective controls such as account lockout, CAPTCHA, rate limiting, or multi-factor authentication (MFA). This creates a viable path for attackers to systematically identify valid credentials and gain unauthorized access to user accounts.

---

**Observation:**

During testing, it was observed that the ADFS login portal (/adfs/ls/IdpInitiatedSignOn.aspx) was publicly accessible and responding to authentication requests over the internet. The portal did not enforce account lockout or rate-limiting mechanisms, making it susceptible to password spraying attacks.

A controlled password spray was conducted using a list of valid usernames and a small set of commonly used passwords. Following several iterations, valid credentials for a standard user account were successfully identified.Post-authentication, the compromised credentials provided full access to the user’s digital environment, including:

Email access via Outlook Web Access (OWA)

Real-time collaboration tools such as Microsoft Teams

File storage and document access via OneDrive and SharePoint

---

**Impact:**

* **Account Compromise**: Full user account control obtained.
* **Lateral Movement Risk**: Access to internal files and conversations enables further phishing or privilege escalation.
* **Data Exposure**: Email, chats, and documents accessible.
* **Stealth Persistence**: No alerts were triggered; attacker activity could go unnoticed for long periods.
* **Cloud Resource Abuse**: Access extended to integrated platforms like Teams, Outlook, and SharePoint via federated identity.

---

**Remediation (Updated & Actionable):**

1. **Disable ADFS IDP-Initiated Sign-In Page** (if not required)
   Prevent attackers from targeting `/adfs/ls/IdpInitiatedSignOn.aspx`.

   ```powershell
   Set-AdfsProperties -EnableIdpInitiatedSignonPage $false
   ```

2. **Enable ADFS Smart Lockout**
   Prevent password spraying by configuring thresholds and lockout duration.

   ```powershell
   Set-AdfsProperties -EnableExtranetLockout $true `
                      -ExtranetLockoutThreshold 5 `
                      -ExtranetObservationWindow (New-TimeSpan -Minutes 5) `
                      -ExtranetLockoutDuration (New-TimeSpan -Minutes 15)
   ```

3. **Enforce Multifactor Authentication (MFA)**
   Use Conditional Access policies in Azure AD or a third-party MFA provider to ensure a second factor is required, especially for remote access.

4. **Integrate ADFS Logs with SIEM**
   Forward ADFS logs (Security, Admin, Debug) to your SIEM platform. Create detection rules for:

   * Multiple failed login attempts
   * Successful logins following failure patterns
   * Logins from unusual geolocations or IP ranges

5. **Restrict External Access to ADFS**
   If external access is not needed:

   * Apply IP allowlisting at the firewall or WAF.
   * Use VPN or conditional access policies to gate access to ADFS endpoints.

6. **Disable Legacy Protocols**
   Remove support for outdated authentication endpoints like WS-Trust to minimize exposure.

   ```powershell
   Set-AdfsEndpoint -TargetAddressPath "/adfs/services/trust/2005/usernamemixed" -Enabled $false
   ```

7. **Harden Password Policy**

   * Enforce strong password complexity and length (min 14 characters).
   * Ban common passwords via Azure AD Password Protection or a third-party solution.
   * Periodically audit password hygiene and account usage.

8. **Immediate Response to Compromised User**

   * Disable the account:

     ```powershell
     Disable-ADAccount -Identity user@domain.com
     ```
   * Reset the password:

     ```powershell
     Set-ADAccountPassword -Identity user@domain.com -Reset -NewPassword (ConvertTo-SecureString "NewPassword123!" -AsPlainText -Force)
     ```
   * Revoke cloud tokens (if using Azure AD):

     ```powershell
     Revoke-AzureADUserAllRefreshToken -ObjectId <UserObjectId>
     ```

---

**Reference:**

* MITRE ATT\&CK ID: T1110.003 – Brute Force: Password Spraying
* Microsoft Docs: ADFS Smart Lockout https://learn.microsoft.com/en-us/windows-server/identity/ad-fs/operations/configure-ad-fs-extranet-smart-lockout-protection
* OWASP Authentication Cheat Sheet
* NIST SP 800-63B – Digital Identity Guidelines





### Finding 2: Sensitive Information Disclosure via ADFS Federation Metadata Endpoint

---

### **Description:**

Sensitive information disclosure occurs when a system unintentionally exposes internal configuration details, infrastructure metadata, or cryptographic materials to unauthorized users. These exposures do not typically grant direct access, but they significantly increase the effectiveness of targeted attacks, reconnaissance efforts, and phishing campaigns.

In this case, a publicly accessible ADFS (Active Directory Federation Services) metadata endpoint was identified. While federation metadata is intended for trusted service integrations, exposing it without restriction may leak configuration details about the organization's identity infrastructure. This can include federation service names, token signing certificates, internal URLs, and SAML/WS-Fed endpoints — all of which can support attacker planning and further exploitation.

---

### **Observation:**

During testing, the following ADFS federation metadata endpoint was found to be publicly accessible over the internet without authentication:

```
https://<redacted>/FederationMetadata/2007-06/FederationMetadata.xml
```

When accessed, the response returned the full federation metadata XML document, which included:

* **Federation service display name and entity ID**
* **Internal ADFS and WS-Federation endpoint URLs**
* **SAML 2.0 endpoint definitions**
* **Public token signing certificate** used for signing security tokens
* **Token encryption certificate details**
* **Relying party and service provider configurations**

Notably, the **token signing certificate** was exposed. While this certificate does not include a private key and cannot be directly used to impersonate a user, it does enable an attacker to:

* **Validate or parse legitimate tokens** issued by ADFS
* **Craft realistic spoofed tokens in phishing payloads**
* **Gather cryptographic configuration and algorithm details**
* **Build trust relationships in custom SAML or WS-Fed exploitation scenarios**, especially if private keys are later obtained elsewhere

Publicly exposing this data gives attackers detailed insight into the organization’s identity and federation infrastructure, and can assist in launching advanced targeted attacks.

---

### **Impact:**

The exposed metadata allows attackers to:

* **Map the ADFS authentication infrastructure and endpoint URLs**
* **Obtain token signing certificate details**, aiding in advanced SAML or WS-Federation attacks
* **Prepare spoofing, phishing, or token replay attacks**
* **Simulate federated interactions or craft malicious metadata** for use against relying parties

While no credentials or private keys were disclosed directly, this information **supports pre-exploitation reconnaissance and post-compromise abuse** of the federation architecture.

---

### **Remediation:**

**Immediate Actions:**

1. **Restrict access to the ADFS metadata endpoint:**

   * Block external unauthenticated access via firewall, WAF, or reverse proxy
   * Allow access only to trusted, known IP ranges (e.g., integration partners)

2. **Monitor and alert:**

   * Enable logging on the ADFS server for all access to `/FederationMetadata/` paths
   * Set up alerts for suspicious or repeated requests

3. **Review exposure:**

   * Evaluate the necessity of public federation metadata exposure
   * Remove or disable unused endpoints and relying party trusts

4. **Certificate hygiene:**

   * Regularly rotate token signing certificates
   * Ensure private keys are securely stored and never exposed

---

### **References:**

* Microsoft – ADFS Federation Metadata: `docs.microsoft.com/en-us/windows-server/identity/ad-fs/operations/manage-federation-metadata`
* OWASP Top 10 – A06:2021: Vulnerable and Outdated Components (information exposure)
* MITRE ATT\&CK – T1592.004: Gather Victim Host Information: Network Trust Dependencies

---






### Finding 3: Improper Session Expiration: Reusable MSISAuth Cookie After Logout



### **Description:**

Session management vulnerabilities occur when an application fails to properly manage authentication tokens or session cookies throughout a user’s login lifecycle. One critical issue is the lack of proper expiration or invalidation of session cookies after logout, which can allow unauthorized re-use of those tokens.

In ADFS environments, the `MSISAuth` cookie is used to track the user’s authenticated session. If this cookie is not properly expired or invalidated upon logout, an attacker who obtains it can reuse it to gain access without needing to reauthenticate, even after the legitimate user has logged out.

This undermines the purpose of logout functionality and exposes the system to **session hijacking** or **persistent unauthorized access**.

---

### **Observation:**

During testing, the ADFS login flow was analyzed, and the following behavior was observed:

* After successful login, a session cookie named `MSISAuth` was issued.
* Upon logging out from the ADFS session or federated application (e.g., Microsoft 365), the session appeared to terminate visually.
* However, the original `MSISAuth` cookie remained valid and usable.
* When the same cookie was reused in a separate browser session or after the logout event, access was **still granted**, bypassing the intended logout behavior.

This indicates that the server **did not invalidate or expire** the session cookie properly upon logout. The cookie remained active until it naturally expired or the browser was closed, depending on the session settings.

---

### **Impact:**

Improper session termination allows an attacker to:

* Reuse a stolen or intercepted session cookie to regain access after a user logs out
* Maintain access to authenticated resources indefinitely (until cookie expires)
* Bypass MFA or login workflows if the session token is reused
* Launch **session fixation** or **post-logout session hijacking** attacks

This can lead to **unauthorized access** to sensitive systems, data, and user accounts — especially dangerous in federated environments where a single session grants access to multiple services.

---

### **Remediation:**

To mitigate this issue:

1. **Enforce session invalidation on logout**

   * Ensure that the `MSISAuth` cookie is **explicitly cleared** or invalidated on the server side during logout events.
   * Configure ADFS to **issue short-lived session cookies** with strict expiration policies.

2. **Use non-persistent (session-based) cookies**

   * Avoid persistent cookies unless absolutely necessary.
   * Use `SessionState` configuration to tightly control the token lifetime:

     ```powershell
     Set-ADFSProperties -PersistentSsoEnabled $false
     Set-ADFSProperties -SSOLifetime 15
     ```

3. **Enable sliding expiration carefully**

   * If using sliding expiration, ensure it doesn’t allow infinite session reuse. Set reasonable inactivity timeout limits.

4. **Enable logout propagation**

   * For federated applications, ensure proper **Single Logout (SLO)** implementation to revoke sessions across systems.

5. **Secure cookie settings**

   * Mark cookies as `HttpOnly`, `Secure`, and consider using `SameSite=Strict` to reduce exposure.

---

### **References:**

* Microsoft Docs – [AD FS Single Sign-On and Session Lifetime](https://learn.microsoft.com/en-us/windows-server/identity/ad-fs/operations/ad-fs-single-sign-on-settings)
* OWASP – [Session Management Cheat Sheet](https://owasp.org/www-project-cheat-sheets/cheatsheets/Session_Management_Cheat_Sheet.html)
* CWE-613: Insufficient Session Expiration
* MITRE ATT\&CK – T1070.001: Indicator Removal on Host – Clear Cookies



Here’s a full, professional write-up for the bug:

---

## 🔒 Vulnerability:

**Sensitive Information Disclosure via IPv6 & WPAD Exposure Leading to NTLMv2 Hash Capture**

---

### 📝 **Description:**

By default, Windows systems prefer IPv6 over IPv4. If **IPv6 is enabled but not actively configured or secured**, attackers on the same network segment can abuse this to perform **rogue router advertisement attacks**. Combined with **Windows Proxy Auto-Discovery (WPAD)** behavior, this allows attackers to **force victim systems to authenticate to a fake proxy server**, thereby capturing **NTLMv2 hashes**.

This technique is commonly referred to as the **MITM6 attack**, and requires no user interaction. Captured NTLMv2 hashes can be **relayed (if signing not enforced)** or **cracked offline** to gain user credentials, leading to further compromise of internal systems.

---

### 🔍 **Observation:**

During testing, it was observed that the ADFS server and other Windows systems in the environment had **IPv6 enabled by default**, but the protocol was not actively used or monitored. Additionally, **WPAD/Auto Proxy Detection** was enabled, and **NTLM authentication** was allowed internally.

By simulating a rogue IPv6 router (RA) and DNS server, a malicious actor can:

* Assign themselves as the default gateway
* Respond to WPAD queries
* Capture NTLM authentication attempts automatically

No direct exploitation of ADFS was necessary; however, the presence of this misconfiguration in the same environment as ADFS increases the **overall attack surface** significantly.

---

### ⚠️ **Impact:**

An attacker with internal network access (e.g., via VPN, rogue device, or foothold) can:

* Capture **NTLMv2 authentication hashes**
* Attempt **offline cracking** to retrieve plaintext passwords
* Perform **NTLM relay attacks** to services like:

  * LDAP (if signing/channel binding not enforced)
  * SMB (if signing disabled)
  * Web interfaces with NTLM auth
* Potentially gain **unauthorized access**, escalate privileges, or move laterally

If high-privileged users (e.g., Domain Admins) are targeted, this could result in **full domain compromise**.

---

### 🛠️ **Remediation:**

#### ✅ 1. **Disable IPv6 if not in use**

On servers/workstations that do not require IPv6:

```reg
[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters]
"DisabledComponents"=dword:000000ff
```

> ⚠️ Requires reboot. Do **not** disable IPv6 if you use DirectAccess, Windows Hello for Business, or similar services.

---

#### ✅ 2. **Disable WPAD / Auto Proxy Discovery**

Disable via **registry (per user)**:

```cmd
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings" /v AutoDetect /t REG_DWORD /d 0 /f
```

Or via **Group Policy**:

```
User Configuration > Administrative Templates > Windows Components > Internet Explorer > Internet Control Panel > Connections Page > 
"Prevent changing proxy settings" → Enabled

"Automatically detect settings" → Disabled
```

---

#### ✅ 3. **Enforce NTLM relay protections**

* **SMB Signing** (on servers):

  ```powershell
  Set-SmbServerConfiguration -RequireSecuritySignature $true -EnableSecuritySignature $true
  ```

* **LDAP Signing & Channel Binding** (on Domain Controllers):

```reg
[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\NTDS\Parameters]
"LDAPServerIntegrity"=dword:0000002
```

* Require **Extended Protection for Authentication (EPA)** on all NTLM endpoints.

---

#### ✅ 4. **Network Monitoring**

Deploy detection and prevention mechanisms:

* Block rogue DHCPv6/Router Advertisements at switch/firewall
* Monitor for WPAD resolutions (DNS or LLMNR) to non-authorized devices
* Use Microsoft Defender for Identity or endpoint EDR for relay/hash capture attempts

---

### 📚 **References:**

* MITM6 Tool: [https://github.com/fox-it/mitm6](https://github.com/fox-it/mitm6)
* Responder: [https://github.com/lgandx/Responder](https://github.com/lgandx/Responder)
* Microsoft: [Mitigating NTLM Relay Attacks](https://learn.microsoft.com/en-us/archive/blogs/miriamxyra/mitigating-ntlm-relay-attacks-on-active-directory-certificates-services-ad-cs)
* CWE-319: Cleartext Transmission of Sensitive Information
* CWE-664: Improper Control of a Resource Through Its Lifetime
* OWASP A05:2021 – Security Misconfiguration

---


