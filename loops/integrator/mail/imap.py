# loops.integrator.mail.imap

""" Concept adapter(s) for external collections, e.g. a directory in the
file system.
"""

from datetime import datetime
import email, email.header, email.utils
from logging import getLogger
import os
import time

from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.container.interfaces import INameChooser
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.event import notify
from zope.interface import implementer
from zope.traversing.api import getName, getParent

from loops.common import AdapterBase, adapted
from loops.interfaces import IResource, IConcept
from loops.integrator.interfaces import IExternalCollectionProvider
from loops.integrator.mail.system import IMAP4
from loops.resource import Resource
from loops.setup import addAndConfigureObject


@implementer(IExternalCollectionProvider)
class IMAPCollectionProvider(object):
    """ A utility that provides access to an IMAP folder.
    """

    def collect(self, client):
        client._collectedObjects = {}
        hostName = client.baseAddress
        if hostName in ('', None, 'localhost'):
            hostName = os.uname()[1]
        baseId = 'imap://%s@%s' % (client.userName, hostName)
        imap = IMAP4(client.baseAddress)
        imap.login(client.userName, client.password)
        mailbox = 'INBOX'
        addr = client.address
        if addr:
            mailbox = mailbox + '.' + addr.replace('/', '.')
        imap.select(mailbox)
        type, data = imap.search(None, 'ALL')
        for num in data[0].split():
            type, data = imap.fetch(num, '(RFC822)')
            raw_msg = data[0][1]
            msg = email.message_from_string(raw_msg)
            msgId = msg['Message-ID'].replace('<', '').replace('>', '')
            externalAddress = '/'.join((baseId, msgId))
            #mtime = datetime.today()
            client._collectedObjects[externalAddress] = msg
            yield externalAddress, None

    def createExtFileObjects(self, client, addresses, extFileTypes=None):
        loopsRoot = client.context.getLoopsRoot()
        container = loopsRoot.getResourceManager()
        contentType = 'text/plain'
        resourceType = loopsRoot.getConceptManager()['email']
        for addr in addresses:
            msg = client._collectedObjects[addr]
            title = decodeHeader(msg['Subject'])
            sender = decodeHeader(msg['From'])
            receiver = decodeHeader(msg['To'])
            #raw_date = msg['Date'].rsplit(' ', 1)[0]
            #fmt = '%a,  %d %b %Y %H:%M:%S'
            #date = datetime(*(time.strptime(raw_date, fmt)[0:6]))
            date = datetime(*(email.utils.parsedate(msg['Date'])[0:6]))
            parts = getPayload(msg)
            if 'html' in parts:
                text = '<br /><br /><hr /><br /><br />'.join(parts['html'])
                ct = 'text/html'
            else:
                textList = parts.get('plain') or [u'No message found.']
                text = '\n\n-------\n\n'.join(textList)
                ct = 'text/plain'
            obj = Resource(title)
            name = INameChooser(container).chooseName(None, obj)
            container[name] = obj
            obj.resourceType = resourceType
            adObj = adapted(obj)
            adObj.externalAddress = addr
            adObj.contentType = ct
            adObj.sender = sender
            adObj.receiver = receiver
            adObj.date = date
            adObj.data = text
            notify(ObjectCreatedEvent(obj))
            notify(ObjectModifiedEvent(obj))
            yield obj


def decodeHeader(h):
    result = []
    for v, dec in email.header.decode_header(h):
        if dec:
            v = v.decode(dec)
        result.append(v)
    return ''.join(result)

def getPayload(msg):
    parts = {}
    for msg in msg.walk():
        ct = msg.get_content_type()
        if ct == 'text/html':
            parts.setdefault('html', []).append(getText(msg))
        elif ct == 'text/plain':
            parts.setdefault('plain', []).append(getText(msg))
    return parts

def getText(msg):
    return msg.get_payload(decode=True).decode(getCharset(msg))

def getCharset(msg):
    params = msg.get_params()
    if params:
        return dict(params).get('charset') or 'ISO8859-1'
    return 'ISO8859-1'
