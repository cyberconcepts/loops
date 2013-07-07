#
#  Copyright (c) 2012 Helmut Merz helmutm@cy55.de
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
Utility functions.
"""

import os
from zope import component
from zope.app.intid.interfaces import IIntIds
from zope.interface import directlyProvides, directlyProvidedBy
from zope.i18nmessageid import MessageFactory
from zope.schema import vocabulary
from zope import thread

import cybertools
from loops.browser.util import html_quote

_ = MessageFactory('loops')


renderingFactories = {
    'text/plain': 'zope.source.plaintext',
    'text/stx': 'zope.source.stx',
    'text/structured': 'zope.source.stx',
    'text/rest': 'zope.source.rest',
    'text/restructured': 'zope.source.rest',
}


class KeywordVocabulary(vocabulary.SimpleVocabulary):

    def __init__(self, items, *interfaces):
        """ ``items`` may be a tuple of (token, title) or a dictionary
            with corresponding elements named 'token' and 'title'.
        """
        terms = []
        for t in items:
            if type(t) is dict:
                token, title = t['token'], t['title']
            else:
                token, title = t
            terms.append(vocabulary.SimpleTerm(token, token, title))
        super(KeywordVocabulary, self).__init__(terms, *interfaces)


def removeTargetRelation(context, event):
    """ Handles IRelationInvalidatedEvent by doing some cleanup work.
    """
    targetIfc = context.second.proxyInterface
    if targetIfc:
        directlyProvides(context.first, directlyProvidedBy(context) - targetIfc)


def nl2br(text):
    if not text: return text
    if '\n' in text: # Unix or DOS line endings
        return '<br />\n'.join(x.replace('\r', '') for x in text.split('\n'))
    else: # gracefully handle Mac line endings
        return '<br />\n'.join(text.split('\r'))

def toUnicode(value, encoding='UTF-8'):
    if type(value) is not unicode:
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            return value.decode('ISO8859-15')
    else:
        return value


def getObjectForUid(uid, intIds=None):
    if uid == '*': # wild card
        return '*'
    if isinstance(uid, basestring) and not uid.isdigit():   # not a valid uid
        return None
    if intIds is None:
        intIds = component.getUtility(IIntIds)
    try:
        return intIds.getObject(int(uid))
    except KeyError:
        return None

def getUidForObject(obj, intIds=None):
    if obj == '*': # wild card
        return '*'
    if intIds is None:
        intIds = component.getUtility(IIntIds)
    return str(intIds.queryId(obj))

def getObjectsForUids(uids, adapt=True):
    intIds = component.getUtility(IIntIds)
    result = [getObjectForUid(uid, intIds) for uid in uids]
    if adapt:
        from loops.common import adapted
        return [adapted(obj) for obj in result if obj is not None]
    return [obj for obj in result if obj is not None]


def getVarDirectory(request=None):
    varDir = None
    if request is not None:
        pub = request.publication
        if pub is not None:
            varDir = os.path.dirname(pub.db.getName())
    if varDir is None:
        instanceHome = os.path.dirname(os.path.dirname(os.path.dirname(
                                os.path.dirname(cybertools.__file__))))
        varDir = os.path.join(instanceHome, 'var')
    return varDir

def getEtcDirectory(request=None):
    varDir = getVarDirectory(request)
    return os.path.join(os.path.dirname(varDir), 'etc')

def getLogDirectory(request=None):
    varDir = getVarDirectory(request)
    return os.path.join(os.path.dirname(varDir), 'log')


# store thread-local stuff

local_data = thread.local()

def saveRequest(request):
    local_data.request = request

def getRequest():
    try:
        return local_data.request
    except AttributeError:
        return None
