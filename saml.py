import base64
import zlib

saml_b64 = "PASTE_YOUR_SAMLRequest_BASE64_HERE"
try:
    saml_bytes = base64.b64decode(saml_b64)
    saml_xml = zlib.decompress(saml_bytes, -15)  # raw DEFLATE
    print(saml_xml.decode())
except Exception as e:
    print("❌ Error decoding SAMLRequest:", e)
