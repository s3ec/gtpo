import pykx
import pandas as pd
import time

def print_result(result):
    try:
        if isinstance(result, pykx.Table):
            # Show table as pandas
            df = result.pd()
            print("▶ Table result:")
            print(df)
        elif isinstance(result, pykx.Dictionary):
            print("▶ Dictionary result:")
            d = result.py()
            for k, v in d.items():
                print(f"  {k}: {v}")
        elif isinstance(result, pykx.List):
            print("▶ List result:")
            for i, item in enumerate(result.py()):
                print(f"  [{i}] {item}")
        elif isinstance(result, pykx.SymbolAtom) or isinstance(result, pykx.QStr):
            print("▶ Symbol/String:", result.py())
        else:
            # Scalar or other types
            print("▶ Result:", result.py())
    except Exception as e:
        print("⚠️ Could not parse result:", e)
        print("▶ Raw q format:")
        print(result.inspect())

def main():
    ip = input("Enter IP (e.g. 127.0.0.1): ").strip()
    port = input("Enter port (e.g. 5000): ").strip()

    try:
        q = pykx.QConnection(host=ip, port=int(port))
        print(f"✅ Connected to kdb+ at {ip}:{port}\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    while True:
        try:
            cmd = input("q> ").strip()
            if cmd in {"exit", "quit", "\\q"}:
                print("👋 Exiting.")
                break

            result = q(cmd)
            print_result(result)

        except Exception as e:
            print(f"⚠️ Error running q command: {e}")

if __name__ == "__main__":
    main()
