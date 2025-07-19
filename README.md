```
using System;
using System.Data;
using kx;  // Kx namespace from kdb+.net

namespace QInteractiveTool
{
    class Program
    {
        static void PrintBanner()
        {
            Console.WriteLine(@"
 ██████╗ ████████╗ █████╗ 
██╔════╝ ╚══██╔══╝██╔══██╗
██║  ███╗   ██║   ███████║
██║   ██║   ██║   ██╔══██║
╚██████╔╝   ██║   ██║  ██║
 ╚═════╝    ╚═╝   ╚═╝  ╚═╝

        G  T  A   T O O L S

Thanks for writing tools without payment  
          and saving us 🙏 🙏😊✨ Thank You, Ganesh! ✨🐘🌸
");
        }

        static void PrintResult(object result)
        {
            if (result is c.Flip table)
            {
                Console.WriteLine("▶ Table result:");
                var cols = table.x; var data = table.y;

                for (int i = 0; i < cols.Length; i++)
                {
                    Console.Write($"{cols[i]}\t");
                }
                Console.WriteLine();

                int rowCount = ((Array)data[0]).Length;
                for (int i = 0; i < rowCount; i++)
                {
                    for (int j = 0; j < cols.Length; j++)
                    {
                        Console.Write($"{((Array)data[j]).GetValue(i)}\t");
                    }
                    Console.WriteLine();
                }
            }
            else if (result is Dictionary dict)
            {
                Console.WriteLine("▶ Dictionary result:");
                foreach (var kv in dict)
                {
                    Console.WriteLine($"  {kv.Key}: {kv.Value}");
                }
            }
            else if (result is object[] arr)
            {
                Console.WriteLine("▶ List result:");
                for (int i = 0; i < arr.Length; i++)
                    Console.WriteLine($"  [{i}] {arr[i]}");
            }
            else
            {
                Console.WriteLine($"▶ Atom result: {result}");
            }
        }

        static void Main(string[] args)
        {
            PrintBanner();

            Console.Write("Enter IP (e.g. 127.0.0.1): ");
            string ip = Console.ReadLine().Trim();

            Console.Write("Enter port (e.g. 5000): ");
            int port = int.Parse(Console.ReadLine().Trim());

            c connection;
            try
            {
                connection = new c(ip, port);
                Console.WriteLine($"✅ Connected to kdb+ at {ip}:{port}\n");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Connection failed: {ex.Message}");
                return;
            }

            while (true)
            {
                Console.Write("q> ");
                string cmd = Console.ReadLine();

                if (cmd.Trim().ToLower() is "exit" or "quit" or "\\q")
                {
                    Console.WriteLine("👋 Exiting.");
                    break;
                }

                try
                {
                    var result = connection.k(cmd);
                    PrintResult(result);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"⚠️ Error running q command: {ex.Message}");
                }
            }
        }
    }
}

```

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
