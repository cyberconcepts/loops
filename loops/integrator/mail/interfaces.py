# loops.integrator.mail.interfaces

""" Integrator interfaces for email representation.
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.integrator.interfaces import IExternalCollection
from loops.interfaces import ITextDocument
from loops.util import _


# mail collections

class IMailCollection(IExternalCollection):
    """ A concept representing a collection of emails that may be
        actively retrieved from an external system using the parameters
        given.
    """

    providerName = schema.TextLine(
            title=_(u'Provider name'),
            description=_(u'The name of a utility that provides the '
                    u'external objects; default is an IMAP collection provider.'),
            default=u'imap',
            required=False)
    baseAddress = schema.TextLine(
            title=_(u'Host name'),
            description=_(u'The host name part for accessing the '
                    u'external mail system, i.e. the mail server.'),
            required=True)
    userName = schema.TextLine(
            title=_(u'User name'),
            description=_(u'The user name for logging in to the mail server.'),
            required=False)
    password = schema.Password(
            title=_(u'Password'),
            description=_(u'The password for logging in to the mail server.'),
            required=False)


# mail resources

class IMailResource(ITextDocument):
    """ A resource adapter representing an email.
    """

    externalAddress = schema.BytesLine(
            title=_(u'External Address'),
            description=_(u'The full address of the email in the external '
                    u'email system.'),
            default=b'',
            missing_value=b'',
            required=False)
    sender = schema.TextLine(
            title=_(u'Sender'),
            description=_(u'The email address of sender of the email.'),
            required=False)
    receiver = schema.TextLine(
            title=_(u'Receiver'),
            description=_(u'One or more email addresses of the receiver(s) of '
                    u'the email message.'),
            required=False)
    date = schema.Date(
            title=_(u'Date'),
            description=_(u'The date/time the email message was sent.'),
            required=False,)
