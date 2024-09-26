# loops.integrator.mail.resouurce

""" Adapter for mail resources.
"""

from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.interface import implementer

from loops.integrator.mail.interfaces import IMailResource
from loops.resource import TextDocumentAdapter
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IMailResource,)


@implementer(IMailResource)
class MailResource(TextDocumentAdapter):
    """ A concept adapter for accessing a mail collection.
        May delegate access to a named utility.
    """

    _contextAttributes = list(IMailResource)
