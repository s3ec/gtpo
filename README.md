```
using System;
using System.Collections.Generic;
using System.Text;
using kx; // kdb+ C# client library

namespace KdbClient
{
    class Program
    {
        private static c connection = null;
        
        static void Main(string[] args)
        {
            Console.WriteLine("=== kdb+/q .NET Client ===\n");
            
            try
            {
                // Get connection details
                string ip = GetInput("Enter kdb+ server IP address", "localhost");
                int port = GetPort("Enter kdb+ server port", 5001);
                string username = GetInput("Enter username (press Enter for none)", "");
                string password = GetInput("Enter password (press Enter for none)", "");
                
                // Connect to kdb+
                ConnectToKdb(ip, port, username, password);
                
                // Command loop
                CommandLoop();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }
            finally
            {
                CloseConnection();
            }
            
            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }
        
        static void ConnectToKdb(string ip, int port, string username, string password)
        {
            try
            {
                Console.WriteLine($"\nConnecting to {ip}:{port}...");
                
                if (!string.IsNullOrEmpty(username) && !string.IsNullOrEmpty(password))
                {
                    connection = new c(ip, port, username + ":" + password);
                }
                else
                {
                    connection = new c(ip, port);
                }
                
                Console.WriteLine("✓ Connected successfully!\n");
                
                // Test connection with a simple query
                object result = connection.k("2+2");
                Console.WriteLine($"Connection test (2+2): {result}\n");
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to connect to kdb+: {ex.Message}");
            }
        }
        
        static void CommandLoop()
        {
            Console.WriteLine("Enter q commands (type 'exit' to quit, 'help' for examples):");
            Console.WriteLine("=" + new string('=', 60));
            
            while (true)
            {
                Console.Write("q) ");
                string command = Console.ReadLine()?.Trim();
                
                if (string.IsNullOrEmpty(command))
                    continue;
                
                if (command.ToLower() == "exit")
                    break;
                
                if (command.ToLower() == "help")
                {
                    ShowHelp();
                    continue;
                }
                
                ExecuteQCommand(command);
            }
        }
        
        static void ExecuteQCommand(string command)
        {
            try
            {
                Console.WriteLine($"\nExecuting: {command}");
                
                object result = connection.k(command);
                
                if (result == null)
                {
                    Console.WriteLine("(null result)");
                }
                else
                {
                    DisplayResult(result);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error executing command: {ex.Message}");
            }
            
            Console.WriteLine(); // Add spacing
        }
        
        static void DisplayResult(object result)
        {
            try
            {
                if (result is c.Dict dict)
                {
                    DisplayDictionary(dict);
                }
                else if (result is c.Flip flip)
                {
                    DisplayTable(flip);
                }
                else if (result.GetType().IsArray)
                {
                    DisplayArray((Array)result);
                }
                else
                {
                    Console.WriteLine($"Result: {result} (Type: {result.GetType().Name})");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error displaying result: {ex.Message}");
                Console.WriteLine($"Raw result: {result}");
            }
        }
        
        static void DisplayTable(c.Flip table)
        {
            if (table.x == null || table.y == null)
            {
                Console.WriteLine("Empty table");
                return;
            }
            
            string[] columns = (string[])table.x;
            object[] data = (object[])table.y;
            
            // Display column headers
            Console.WriteLine("\nTable Result:");
            Console.WriteLine(new string('-', 80));
            
            foreach (string col in columns)
            {
                Console.Write($"{col,-15} ");
            }
            Console.WriteLine();
            Console.WriteLine(new string('-', 80));
            
            // Display data rows
            int rowCount = data.Length > 0 && data[0] is Array ? ((Array)data[0]).Length : 0;
            
            for (int i = 0; i < rowCount; i++)
            {
                for (int j = 0; j < data.Length; j++)
                {
                    if (data[j] is Array arr && i < arr.Length)
                    {
                        object value = arr.GetValue(i);
                        Console.Write($"{value?.ToString() ?? "null",-15} ");
                    }
                }
                Console.WriteLine();
            }
            
            Console.WriteLine($"\n({rowCount} rows)");
        }
        
        static void DisplayDictionary(c.Dict dict)
        {
            Console.WriteLine("\nDictionary Result:");
            Console.WriteLine(new string('-', 40));
            
            if (dict.x is Array keys && dict.y is Array values)
            {
                for (int i = 0; i < keys.Length; i++)
                {
                    object key = keys.GetValue(i);
                    object value = values.GetValue(i);
                    Console.WriteLine($"{key}: {value}");
                }
            }
        }
        
        static void DisplayArray(Array array)
        {
            Console.WriteLine($"\nArray Result ({array.Length} elements):");
            Console.WriteLine(new string('-', 40));
            
            for (int i = 0; i < Math.Min(array.Length, 50); i++) // Limit display to 50 items
            {
                Console.WriteLine($"[{i}]: {array.GetValue(i)}");
            }
            
            if (array.Length > 50)
            {
                Console.WriteLine($"... and {array.Length - 50} more items");
            }
        }
        
        static void ShowHelp()
        {
            Console.WriteLine("\n=== Example q Commands ===");
            Console.WriteLine("Basic queries:");
            Console.WriteLine("  2+2");
            Console.WriteLine("  til 10");
            Console.WriteLine("  ([] sym:`AAPL`GOOGL`MSFT; price:100 200 150)");
            
            Console.WriteLine("\nSystem commands:");
            Console.WriteLine("  \\a          - list tables in default namespace");
            Console.WriteLine("  \\b          - list views");
            Console.WriteLine("  \\f          - list functions");
            Console.WriteLine("  \\v          - list variables");
            Console.WriteLine("  \\w          - workspace info");
            Console.WriteLine("  \\t          - timing info");
            
            Console.WriteLine("\nOS/System commands:");
            Console.WriteLine("  system \"pwd\"");
            Console.WriteLine("  system \"ls\"");
            Console.WriteLine("  system \"dir\"  (Windows)");
            
            Console.WriteLine("\nTable operations:");
            Console.WriteLine("  select from tablename");
            Console.WriteLine("  select from tablename where condition");
            Console.WriteLine("  update column:value from tablename");
            Console.WriteLine("  insert into tablename values ...");
            
            Console.WriteLine("\nMemory/Performance:");
            Console.WriteLine("  .Q.w[]      - workspace usage");
            Console.WriteLine("  .Q.gc[]     - garbage collection");
            Console.WriteLine("  \\ts:100000 expression  - time and space for expression");
            Console.WriteLine();
        }
        
        static string GetInput(string prompt, string defaultValue = "")
        {
            Console.Write($"{prompt} [{defaultValue}]: ");
            string input = Console.ReadLine()?.Trim();
            return string.IsNullOrEmpty(input) ? defaultValue : input;
        }
        
        static int GetPort(string prompt, int defaultPort)
        {
            while (true)
            {
                Console.Write($"{prompt} [{defaultPort}]: ");
                string input = Console.ReadLine()?.Trim();
                
                if (string.IsNullOrEmpty(input))
                    return defaultPort;
                
                if (int.TryParse(input, out int port) && port > 0 && port <= 65535)
                    return port;
                
                Console.WriteLine("Please enter a valid port number (1-65535)");
            }
        }
        
        static void CloseConnection()
        {
            try
            {
                if (connection != null)
                {
                    connection.Close();
                    Console.WriteLine("Connection closed.");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error closing connection: {ex.Message}");
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
