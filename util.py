#
#  Copyright (c) 2006 Helmut Merz helmutm@cy55.de
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

$Id$
"""

from zope import component
from zope.app.intid.interfaces import IIntIds
from zope.interface import directlyProvides, directlyProvidedBy
from zope.i18nmessageid import MessageFactory
from zope.schema import vocabulary
#from view import TargetRelation

#_ = MessageFactory('loops')
_ = MessageFactory('zope')  # it's easier not use a special i18n domain...


class KeywordVocabulary(vocabulary.SimpleVocabulary):

    def __init__(self, items, *interfaces):
        terms = [vocabulary.SimpleTerm(token, token, title)
                        for token, title in items]
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

def getObjectForUid(uid):
    if uid == '*': # wild card
        return '*'
    intIds = component.getUtility(IIntIds)
    return intIds.getObject(int(uid))

def getUidForObject(obj):
    if obj == '*': # wild card
        return '*'
    intIds = component.getUtility(IIntIds)
    return intIds.queryId(obj)
