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
Adapter classes (proxies, in fact), for providing access to concepts and
resources e.g. from forms that are called on view/node objects.

$Id$
"""

from zope.app import zapi
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.i18nmessageid import MessageFactory
from zope.interface import implements
from zope import schema
from zope.security.proxy import removeSecurityProxy

from zope.app.event.objectevent import ObjectModifiedEvent, Attributes
from zope.event import notify

from loops.interfaces import ILoopsObject, IResource, IDocument, IMediaAsset
from loops.interfaces import IDocumentView, IMediaAssetView
from loops.interfaces import IView
from loops.interfaces import IConcept, IConceptView

_ = MessageFactory('loops')


# proxies for accessing target objects from views/nodes


class TargetProxy(object):

    def __init__(self, context):
        #self.context = context
        self.context = removeSecurityProxy(context)

    @Lazy
    def target(self):
        return self.context.target

    def getTitle(self):
        return self.target.title
    def setTitle(self, title):
        self.target.title = title
        notify(ObjectModifiedEvent(self.target,
                                   Attributes(ILoopsObject, 'title')))
    title = property(getTitle, setTitle)


class ConceptProxy(TargetProxy):

    implements(IConcept)
    adapts(IConceptView)

    def getConceptType(self): return self.target.conceptType
    def setConceptType(self, conceptType):
        self.target.conceptType = conceptType
        notify(ObjectModifiedEvent(self.target, Attributes(IConcept, 'conceptType')))
    conceptType = property(getConceptType, setConceptType)

    def getChildren(self, predicates=None):
        return self.target.getChildren(predicates)

    def getParents(self, predicates=None):
        return self.target.getParents(predicates)

    def getResources(self, predicates=None):
        return self.target.getResources(predicates)


class ResourceProxy(TargetProxy):

    def setContentType(self, contentType):
        notify(ObjectModifiedEvent(self.target, Attributes(IResource, 'contentType')))
        self.target.contentType = contentType
    def getContentType(self): return self.target.contentType
    contentType = property(getContentType, setContentType)


class DocumentProxy(ResourceProxy):

    implements(IDocument)
    adapts(IDocumentView)

    def setData(self, data):
        self.target.data = data
        notify(ObjectModifiedEvent(self.target, Attributes(IDocument, 'data')))
    def getData(self): return self.target.data
    data = property(getData, setData)


class MediaAssetProxy(ResourceProxy):

    implements(IMediaAsset)
    adapts(IMediaAssetView)

    def setData(self, data): self.target.data = data
    def getData(self): return self.target.data
    data = property(getData, setData)

