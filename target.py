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
from zope.interface import implements
from zope import schema
from zope.security.proxy import removeSecurityProxy

from loops.interfaces import IResource
from loops.interfaces import IDocument, IMediaAsset
from loops.interfaces import IDocumentView, IMediaAssetView
from loops.interfaces import IView
from loops.interfaces import IConcept, IConceptView


# proxies for accessing target objects from views/nodes

class ConceptProxy(object):

    implements(IConcept)
    adapts(IConceptView)

    def __init__(self, context):
        #self.context = context
        self.context = removeSecurityProxy(context)

    def getTitle(self): return self.target.title
    def setTitle(self, title): self.target.title = title
    title = property(getTitle, setTitle)

    def getChildren(self, relationships=None):
        return self.target.getChildren(relationships)

    def getParents(self, relationships=None):
        return self.target.getParents(relationships)


class ResourceProxy(object):

    adapts(IView)

    def __init__(self, context):
        #self.context = context
        self.context = removeSecurityProxy(context)

    def getTitle(self): return self.target.title
    def setTitle(self, title): self.target.title = title
    title = property(getTitle, setTitle)

    def setContentType(self, contentType):
        self.target.contentType = contentType
    def getContentType(self): return self.target.contentType
    contentType = property(getContentType, setContentType)

    @Lazy
    def target(self):
        return self.context.target
        

class DocumentProxy(ResourceProxy):

    implements(IDocument)
    adapts(IDocumentView)

    def setData(self, data): self.target.data = data
    def getData(self): return self.target.data
    data = property(getData, setData)


class MediaAssetProxy(ResourceProxy):

    implements(IMediaAsset)
    adapts(IMediaAssetView)

    def setData(self, data): self.target.data = data
    def getData(self): return self.target.data
    data = property(getData, setData)


# source classes for target vocabularies

class TargetSourceList(object):

    implements(schema.interfaces.IIterableSource)

    def __init__(self, context):
        #self.context = context
        self.context = removeSecurityProxy(context)
        root = self.context.getLoopsRoot()
        self.resources = root.getResourceManager()
        self.concepts = root.getConceptManager()

    def __iter__(self):
        for obj in self.resources.values():
            yield obj
        for obj in self.concepts.values():
            yield obj
        #return iter(list(self.resources.values()) + list(self.concepts.values()))

    def __len__(self):
        return len(self.resources) + len(self.concepts)


class QueryableTargetSource(object):

    implements(schema.interfaces.ISource)

    def __init__(self, context):
        self.context = context
        root = self.context.getLoopsRoot()
        self.resources = root.getResourceManager()
        self.concepts = root.getConceptManager()

    def __contains__(self, value):
        return value in self.resources.values() or value in self.concepts.values()

