import pykx
import time

def main():
    ip = input("Enter IP (e.g. 127.0.0.1): ").strip()
    port = input("Enter port (e.g. 5000): ").strip()

    try:
        # Connect to kdb+ over IPC
        q = pykx.QConnection(host=ip, port=int(port))
        print(f"✅ Connected to kdb+ at {ip}:{port}\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    while True:
        try:
            cmd = input("q> ").strip()
            if cmd in {"exit", "quit", "\\q"}:
                print("Exiting.")
                break

            result = q(cmd)

            # Try showing Python-friendly output
            try:
                py_result = result.py()
                print("▶ Result (Python):", py_result)
            except Exception:
                print("▶ Result (Raw q):")
                print(result.inspect())

        except Exception as e:
            print(f"⚠️ Error running q command: {e}")

if __name__ == "__main__":
    main()
