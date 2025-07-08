import base64, zlib

saml_b64 = "PASTE_YOUR_SAMLRequest"
decoded = zlib.decompress(base64.b64decode(saml_b64), -15)
print(decoded.decode())
