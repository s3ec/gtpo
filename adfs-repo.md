Absolutely! Here's the complete **finding** for the ADFS password spray issue, with the **updated Remediation section** that includes disabling or restricting the **IDP-Initiated Sign-In page (`/adfs/ls/IdpInitiatedSignOn.aspx`)**.

---

### **Finding 1: Account Takeover via Password Spray on ADFS Authentication Portal **

---

**Description:**

The ADFS login endpoint was found to be vulnerable to password spraying — a brute-force technique where a small number of commonly used passwords are tested across many accounts to evade lockout mechanisms. When ADFS lacks appropriate rate-limiting or account lockout protections, this becomes a viable method for credential-based attacks.

During testing, the ADFS sign-in portal was accessible externally. A password spray yielded a valid user credential, which was then successfully used to authenticate into federated services such as Microsoft 365 (Outlook, Teams, OneDrive, SharePoint). The ADFS environment did not provide sufficient detection or prevention mechanisms, allowing the attacker to remain undetected and gain full access to the user’s digital workspace.

---

**Observation:**

* ADFS login page was exposed externally (`/adfs/ls/IdpInitiatedSignOn.aspx`).
* No CAPTCHA, rate-limiting, or IP throttling was present.
* A password spray attempt using common passwords succeeded in identifying a valid user credential.
* Using the compromised account, access was confirmed to:

  * **Microsoft Outlook Web Access**
  * **Microsoft Teams**
  * **SharePoint / OneDrive**
* No alerts, lockouts, or anomaly detection were triggered during the attack.
* The compromised user had unrestricted access to internal and cloud-based resources.

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
* Microsoft Docs: ADFS Smart Lockout  Absolutely! Here's the complete **finding** for the ADFS password spray issue, with the **updated Remediation section** that includes disabling or restricting the **IDP-Initiated Sign-In page (`/adfs/ls/IdpInitiatedSignOn.aspx`)**.

---

### **Finding 1: Successful Password Spray on ADFS Login Portal**

---

**Description:**

The ADFS login endpoint was found to be vulnerable to password spraying — a brute-force technique where a small number of commonly used passwords are tested across many accounts to evade lockout mechanisms. When ADFS lacks appropriate rate-limiting or account lockout protections, this becomes a viable method for credential-based attacks.

During testing, the ADFS sign-in portal was accessible externally. A password spray yielded a valid user credential, which was then successfully used to authenticate into federated services such as Microsoft 365 (Outlook, Teams, OneDrive, SharePoint). The ADFS environment did not provide sufficient detection or prevention mechanisms, allowing the attacker to remain undetected and gain full access to the user’s digital workspace.

---

**Observation:**

* ADFS login page was exposed externally (`/adfs/ls/IdpInitiatedSignOn.aspx`).
* No CAPTCHA, rate-limiting, or IP throttling was present.
* A password spray attempt using common passwords succeeded in identifying a valid user credential.
* Using the compromised account, access was confirmed to:

  * **Microsoft Outlook Web Access**
  * **Microsoft Teams**
  * **SharePoint / OneDrive**
* No alerts, lockouts, or anomaly detection were triggered during the attack.
* The compromised user had unrestricted access to internal and cloud-based resources.

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
* Microsoft Docs: ADFS Smart Lockout Absolutely! Here's the complete **finding** for the ADFS password spray issue, with the **updated Remediation section** that includes disabling or restricting the **IDP-Initiated Sign-In page (`/adfs/ls/IdpInitiatedSignOn.aspx`)**.

---

### **Finding 1: Successful Password Spray on ADFS Login Portal**

---

**Description:**

The ADFS login endpoint was found to be vulnerable to password spraying — a brute-force technique where a small number of commonly used passwords are tested across many accounts to evade lockout mechanisms. When ADFS lacks appropriate rate-limiting or account lockout protections, this becomes a viable method for credential-based attacks.

During testing, the ADFS sign-in portal was accessible externally. A password spray yielded a valid user credential, which was then successfully used to authenticate into federated services such as Microsoft 365 (Outlook, Teams, OneDrive, SharePoint). The ADFS environment did not provide sufficient detection or prevention mechanisms, allowing the attacker to remain undetected and gain full access to the user’s digital workspace.

---

**Observation:**

* ADFS login page was exposed externally (`/adfs/ls/IdpInitiatedSignOn.aspx`).
* No CAPTCHA, rate-limiting, or IP throttling was present.
* A password spray attempt using common passwords succeeded in identifying a valid user credential.
* Using the compromised account, access was confirmed to:

  * **Microsoft Outlook Web Access**
  * **Microsoft Teams**
  * **SharePoint / OneDrive**
* No alerts, lockouts, or anomaly detection were triggered during the attack.
* The compromised user had unrestricted access to internal and cloud-based resources.

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

Let me know if you want this formatted into a Word document or added to a full pentest report template.

* OWASP Authentication Cheat Sheet
* NIST SP 800-63B – Digital Identity Guidelines

---

Let me know if you want this formatted into a Word document or added to a full pentest report template.

* NIST SP 800-63B – Digital Identity Guidelines

---

Let me know if you want this formatted into a Word document or added to a full pentest report template.
