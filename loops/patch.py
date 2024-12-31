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

from zope.sendmail.interfaces import IMailer
from zope.sendmail.mailer import SMTPMailer
def patched_smtpMailer(_context, name, hostname="localhost", port="25",
               username=None, password=None, implicit_tls=False):
    _context.action(
        discriminator=('utility', IMailer, name),
        callable=handler,
        args=('registerUtility',
              # fix error: set 'implicit_tls' as a keyword parameter
              SMTPMailer(hostname, port, username, password, 
                         implicit_tls=implicit_tls),
              IMailer, name)
    )
import zope.sendmail.zcml
zope.sendmail.zcml.smtpMailer = patched_smtpMailer
print("loops patch: monkey patch  for 'zope.sendmail.zcml.smtpMailer()' installed")

