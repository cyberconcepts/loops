#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
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
Blogs and blog posts.

$Id$
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
from loops.compound.blog.interfaces import IBlogPost
from loops.resource import Resource
from loops.security.common import restrictView
from loops.setup import addAndConfigureObject
from loops.type import TypeInterfaceSourceList


TypeInterfaceSourceList.typeInterfaces += (IBlogPost,)


class BlogPost(Compound):

    implements(IBlogPost)

    _adapterAttributes = Compound._adapterAttributes + ('text', 'private', 'creator',)
    _contextAttributes = Compound._contextAttributes + ['date', 'privateComment']
    _noexportAttributes = ('creator', 'text', 'private')
    _textIndexAttributes = ('text',)

    defaultTextContentType = 'text/restructured'
    textContentType = defaultTextContentType

    @Lazy
    def isPartOf(self):
        return self.context.getLoopsRoot().getConceptManager()['ispartof']

    def getPrivate(self):
        return getattr(self.context, '_private', False)
    def setPrivate(self, value):
        self.context._private = value
        restrictView(self.context, revert=not value)
        for r in self.context.getResources([self.isPartOf], noSecurityCheck=True):
            restrictView(r, revert=not value)
    private = property(getPrivate, setPrivate)

    def getText(self):
        res = self.getParts()
        if len(res) > 0:
            return adapted(res[0]).data
        return u''
    def setText(self, value):
        res = self.getParts()
        if len(res) > 0:
            res = adapted(res[0])
        else:
            tTextDocument = self.conceptManager['textdocument']
            name = getName(self.context) + '_text'
            res = addAndConfigureObject(self.resourceManager, Resource, name,
                    title=self.title, contentType=self.defaultTextContentType,
                    resourceType=tTextDocument)
            #notify(ObjectCreatedEvent(res))
            self.add(res, position=0)
            res = adapted(res)
        res.data = value
        notify(ObjectModifiedEvent(res.context))
    text = property(getText, setText)

    @property
    def creator(self):
        cr = IZopeDublinCore(self.context).creators
        return cr and cr[0] or None

