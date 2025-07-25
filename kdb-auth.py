import pykx
import pandas as pd

def print_banner():
    print("""
 ██████╗ ████████╗ █████╗ 
██╔════╝ ╚══██╔══╝██╔══██╗
██║  ███╗   ██║   ███████║
██║   ██║   ██║   ██╔══██║
╚██████╔╝   ██║   ██║  ██║
 ╚═════╝    ╚═╝   ╚═╝  ╚═╝

        G  T  A   T O O L S

Thanks for writing tools without payment  
          and saving us 🙏 🙏😊✨ Thank You, Ganesh! ✨🐘🌸
""")

def print_result(result):
    try:
        if isinstance(result, pykx.Table):
            print("▶ Table result:")
            print(result.pd())
        elif isinstance(result, pykx.Dictionary):
            print("▶ Dictionary result:")
            d = result.py()
            for k, v in d.items():
                print(f"  {k}: {v}")
        elif isinstance(result, pykx.List):
            print("▶ List result:")
            lst = result.py()
            for i, item in enumerate(lst):
                print(f"  [{i}] {item}")
        elif isinstance(result, (pykx.SymbolAtom, pykx.BooleanAtom, pykx.IntAtom, pykx.FloatAtom)):
            print(f"▶ Atom result: {result.py()}")
        else:
            try:
                print("▶ Generic result:", result.py())
            except Exception:
                print("▶ Raw q result:")
                print(result.inspect())
    except Exception as e:
        print(f"⚠️ Error printing result: {e}")
        print("▶ Raw q format:")
        print(result.inspect())

def main():
    print_banner()

    ip = input("Enter IP (e.g. 127.0.0.1): ").strip()
    port = input("Enter port (e.g. 5000): ").strip()
    auth_required = input("Is authentication required? (y/n): ").strip().lower()

    username = password = None
    if auth_required == 'y':
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()

    try:
        if username and password:
            q = pykx.QConnection(host=ip, port=int(port), username=username, password=password)
        else:
            q = pykx.QConnection(host=ip, port=int(port))

        print(f"✅ Connected to kdb+ at {ip}:{port}\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
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
