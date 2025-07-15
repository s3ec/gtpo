

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

---


