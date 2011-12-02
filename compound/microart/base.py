#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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
Micro articles (MicroArt).
"""

from zope.cachedescriptors.property import Lazy
from zope.dublincore.interfaces import IZopeDublinCore
from zope.interface import implements
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope import schema
from zope.traversing.api import getName

from loops.common import adapted
from loops.compound.base import Compound
from loops.compound.microart.interfaces import IMicroArt
from loops.resource import Resource
from loops.setup import addAndConfigureObject
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IMicroArt,)


class MicroArt(Compound):

    implements(IMicroArt)

    _contextAttributes = list(IMicroArt)
    _adapterAttributes = Compound._adapterAttributes + ('story',)
    _noexportAttributes = ('story',)
    _textIndexAttributes = ('story', 'insight', 'consequences', 'folloUps')

    defaultTextContentType = 'text/html'
    textContentType = defaultTextContentType

    def getStory(self):
        res = self.getParts()
        if len(res) > 0:
            return adapted(res[0]).data
        return u''
    def setStory(self, value):
        res = self.getParts()
        if len(res) > 0:
            res = adapted(res[0])
        else:
            tTextDocument = self.conceptManager['textdocument']
            name = getName(self.context) + '_story'
            res = addAndConfigureObject(self.resourceManager, Resource, name,
                    title=self.title, contentType=self.defaultTextContentType,
                    resourceType=tTextDocument)
            #notify(ObjectCreatedEvent(res))
            self.add(res, position=0)
            res = adapted(res)
        res.data = value
        notify(ObjectModifiedEvent(res.context))
    story = property(getStory, setStory)
