| **S. No.** | **Test Case**                      | **Description**                                                                   | **Expected Result**                                                     |
| ---------- | ---------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| PTC-01     | SNMP Anonymous Access              | Attempt SNMP access using default community strings like `public` or `private`    | Access should be denied; if allowed, it's a security risk               |
| PTC-02     | SNMP Community String Brute Force  | Use tools to brute-force SNMP community strings (e.g., `onesixtyone`)             | If a valid string is found, it indicates weak SNMP security             |
| PTC-03     | Sensitive Data Disclosure via SNMP | Perform SNMP walk to extract system info, users, interfaces, routing tables, etc. | Any sensitive or internal data should not be accessible                 |
| PTC-04     | SNMP Write Access Attempt          | Try `snmpset` with guessed write community string to modify SNMP values           | If successful, attacker can alter settings — **critical vulnerability** |


TCL Scripting Abuse with File Write/Delete Capabilities
