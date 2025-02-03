# loops.patch

# monkey patches, activate with: <module module="loops.patch" />
# in some .zcml file, e.g. application.zcml


from zope.intid import IntIds
base_getId = IntIds.getId
base_register = IntIds.register

def patched_getId(self, ob):
    uid = getattr(ob, '_uid_int', None)
    #print('*** patched_getId, found:', uid)
    if uid is None:
        uid = base_getId(self, ob)
        ob._uid_int = uid
    return uid

def patched_register(self, ob):
    uid = base_register(self, ob)
    ob._uid_int = uid
    return uid

IntIds.getId = patched_getId
IntIds.register = patched_register


import zope.index.text.widcode
from zope.index.text.widcode import _prog, _decode, _decoding
def patched_decode(code):
    """`_prog` pattern is now a string, but after updating from Python2
       code we may still get a bytes array from ZODB."""
    get = _decoding.get
    if isinstance(code, bytes):
        # byte-wise conversion to str:
        code = ''.join(chr(b) for b in code)
    return [get(p) or _decode(p) for p in _prog.findall(code)]
zope.index.text.widcode.decode = patched_decode


from zope.index.text.baseindex import BaseIndex
from zope.index.text import widcode
from zope.index.text.setops import mass_weightedIntersection
def patched_search_phrase(self, phrase):
    wids = self._lexicon.termToWordIds(phrase)
    cleaned_wids = self._remove_oov_wids(wids)
    if len(wids) != len(cleaned_wids):
        # At least one wid was OOV:  can't possibly find it.
        return self.family.IF.BTree()
    scores = self._search_wids(wids)
    hits = mass_weightedIntersection(scores, self.family)
    if not hits:
        return hits
    code = widcode.encode(wids)
    result = self.family.IF.BTree()
    for docid, weight in hits.items():
        docwords = self._docwords[docid]
        if isinstance(docwords, bytes):  # PATCH
            # byte-wise conversion to str:
            docwords = ''.join(chr(b) for b in docwords)
        if docwords.find(code) >= 0:
            result[docid] = weight
    return result
BaseIndex.search_phrase = patched_search_phrase


import zope.sendmail.zcml
from zope.sendmail.interfaces import IMailer
from zope.sendmail.mailer import SMTPMailer
def patched_smtpMailer(_context, name, hostname="localhost", port="25",
               username=None, password=None, implicit_tls=False):
    _context.action(
        discriminator=('utility', IMailer, name),
        callable=handler,
        args=('registerUtility',
              # fix error: set `implicit_tls` as a keyword parameter
              SMTPMailer(hostname, port, username, password, 
                         implicit_tls=implicit_tls),
              IMailer, name)
    )
zope.sendmail.zcml.smtpMailer = patched_smtpMailer


import ZODB.broken
from ZODB.broken import find_global
def patched_rebuild(modulename, globalname, *args):
    class_ = find_global(modulename, globalname)
    #print('***loops.patch -> ZODB.broken.rebuild', modulename, globalname, args, class_)
    if globalname == 'unpickleMethod':
        # some spurious `twisted` relict in ZODB: a function, not a real class 
        return class_(*args)
    return class_.__new__(class_, *args)
ZODB.broken.rebuild = patched_rebuild


print("loops.patch: 5 monkey patches installed")

