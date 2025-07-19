using System;
using System.Net.Sockets;
using System.Text;

class Program
{
    static void Main()
    {
        Console.Write("Enter q server IP: ");
        string ip = Console.ReadLine();

        Console.Write("Enter port: ");
        int port = int.Parse(Console.ReadLine());

        Console.Write("Enter q command: ");
        string userInput = Console.ReadLine();

        // Wrap q command with .Q.s for string output
        string qExpr = $".Q.s string \"{EscapeQuotes(userInput)}\"";

        try
        {
            using var client = new TcpClient(ip, port);
            var stream = client.GetStream();

            byte[] msg = BuildQMessage(qExpr);
            stream.Write(msg, 0, msg.Length);

            byte[] buffer = new byte[4096];
            int bytesRead = stream.Read(buffer, 0, buffer.Length);

            string response = Encoding.UTF8.GetString(buffer, 8, bytesRead - 8);
            Console.WriteLine("\n✅ Response:\n" + response);
        }
        catch (Exception ex)
        {
            Console.WriteLine("❌ Error: " + ex.Message);
        }
    }

    static string EscapeQuotes(string s)
    {
        return s.Replace("\"", "\"\"");
    }

    static byte[] BuildQMessage(string q)
    {
        byte[] payload = Encoding.ASCII.GetBytes(q);
        byte[] header = new byte[8] { 1, 0, 0, 0, 0, 0, 0, 0 };
        BitConverter.GetBytes(payload.Length + 8).CopyTo(header, 4);
        byte[] fullMessage = new byte[header.Length + payload.Length];
        Buffer.BlockCopy(header, 0, fullMessage, 0, 8);
        Buffer.BlockCopy(payload, 0, fullMessage, 8, payload.Length);
        return fullMessage;
    }
}


| **S. No.** | **Test Case**                       |
| ---------- | ----------------------------------- |
| PTC-01     | Unquoted Service Path               |
| PTC-02     | Weak Service Permissions            |
| PTC-03     | DLL Hijacking via Service           |
| PTC-04     | AlwaysInstallElevated Exploit       |
| PTC-05     | Writable Startup Folder             |
| PTC-06     | Fodhelper UAC Bypass                |
| PTC-07     | Token Impersonation (SeImpersonate) |
| PTC-08     | SeDebugPrivilege Abuse              |
| PTC-09     | SAM Hive Extraction via Shadow Copy |
| PTC-10     | Writable Registry Run Keys          |
| PTC-11     | PATH Environment Variable Hijack    |
| PTC-12     | Image File Execution Options Hijack |
| PTC-13     | Mimikatz LSASS Dump                 |
| PTC-14     | AMSI Bypass                         |
| PTC-15     | Writable Service Binary             |
| PTC-16     | Insecure Scheduled Task             |
| PTC-17     | SeBackupPrivilege Exploitation      |
| PTC-18     | UAC Bypass via sdclt.exe            |
| PTC-19     | Weak Local Admin Password Reuse     |
| PTC-20     | Credentials in Config/Scripts       |
