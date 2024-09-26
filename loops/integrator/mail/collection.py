# loops.integrator.mail.collection

""" Concept adapter(s) for external collections, e.g. a directory in the
file system.
"""

from zope.cachedescriptors.property import Lazy
from zope import component
from zope.component import adapts
from zope.interface import implementer

from loops.integrator.collection import ExternalCollectionAdapter
from loops.integrator.mail.interfaces import IMailCollection
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IMailCollection,)


@implementer(IMailCollection)
class MailCollectionAdapter(ExternalCollectionAdapter):
    """ A concept adapter for accessing a mail collection.
        May delegate access to a named utility.
    """

    _adapterAttributes = ExternalCollectionAdapter._adapterAttributes + (
                            'providerName', '_collectedObjects')
    _contextAttributes = list(IMailCollection)

    _collectedObjects = None

    def getProviderName(self):
        return getattr(self.context, '_providerName', None) or u'imap'
    def setProviderName(self, value):
        self.context._providerName = value
    providerName = property(getProviderName, setProviderName)
