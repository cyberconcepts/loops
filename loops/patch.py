# loops.patch

# monkey patches, activate with: <module module="loops.patch" />
# in some .zcml file, e.g. application.zcml

import zope.index.text.widcode
from zope.index.text.widcode import _prog, _decode, _decoding

def patched_decode(code):
    """_prog pattern is now a string, but after updating from Python2
       code is still a bytes array."""
    get = _decoding.get
    if isinstance(code, bytes):
        # byte-wise conversion to str:
        code = ''.join(chr(b) for b in code)
    return [get(p) or _decode(p) for p in _prog.findall(code)]

zope.index.text.widcode.decode = patched_decode
print("loops.patch: monkey patch for 'zope.index.text.widcode.decode()' installed.")
