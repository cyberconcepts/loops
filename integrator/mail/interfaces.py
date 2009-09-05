#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Integrator interfaces for email representation.

$Id$
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
            default='',
            missing_value='',
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
