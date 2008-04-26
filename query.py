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
Query management stuff.

$Id$
"""

from BTrees.IOBTree import IOBTree
from BTrees.IFBTree import weightedIntersection, weightedUnion, IFBucket
from zope import schema, component
from zope.interface import Interface, Attribute, implements
from zope.app.catalog.interfaces import ICatalog
from zope.app.intid.interfaces import IIntIds
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from loops.common import AdapterBase
from loops.interfaces import IConcept, IConceptSchema
from loops.security.common import canListObject
from loops.type import TypeInterfaceSourceList
from loops.versioning.util import getVersion
from loops import util
from loops.util import _


class ScoredSet(set):

    def __init__(self, data=set(), scores={}):
        super(ScoredSet, self).__init__(data)
        self.scores = scores

    def getScore(self, obj):
        return self.scores.get(obj, -1)


class IQuery(Interface):
    """ The basic query interface.
    """

    def query(self, **kw):
        """ Execute the query and return a sequence of objects.
        """


class BaseQuery(object):

    implements(IQuery)

    def __init__(self, context):
        self.context = context

    @Lazy
    def catalog(self):
        return component.getUtility(ICatalog)

    @Lazy
    def loopsRoot(self):
        return self.context.context.getLoopsRoot()

    def queryConcepts(self, title=None, type=None, **kw):
        if type.endswith('*'):
            start = type[:-1]
            end = start + '\x7f'
        else:
            start = end = type
        cat = self.catalog
        if title:
            result = cat.searchResults(loops_type=(start, end), loops_title=title)
        else:
            result = cat.searchResults(loops_type=(start, end))
        result = set(r for r in result if r.getLoopsRoot() == self.loopsRoot
                     and canListObject(r))
        if 'exclude' in kw:
            r1 = set()
            for r in result:
                qur = IType(r).qualifiers
                if not [qux for qux in kw['exclude'] if qux in qur]:
                    r1.add(r)
            result = r1
        return result

    def queryConceptsWithChildren(self, title=None, type=None, uid=None, **kw):
        if title:  # there are a few characters that the index doesn't like
            title = title.replace('(', ' ').replace(')', ' ')
        if not title and not uid and (type is None or '*' in type):
            return None
        result = set()
        if not uid:
            queue = list(self.queryConcepts(title=title, type=type, **kw))
        else:
            queue = [util.getObjectForUid(uid)]
        concepts = []
        while queue:
            c = queue.pop(0)
            concepts.append(c)
            for child in c.getChildren():
                # TODO: check for tree level, use relevance factors, ...
                if child not in queue and child not in concepts:
                    queue.append(child)
        for c in concepts:
            result.add(c)
            result.update(getVersion(r) for r in c.getResources())
        return result


class FullQuery(BaseQuery):

    def query(self, text=None, type=None, useTitle=True, useFull=False,
                    conceptTitle=None, conceptUid=None, conceptType=None, **kw):
        result = set()
        scores = {}
        intids = component.getUtility(IIntIds)
        rc = self.queryConceptsWithChildren(title=conceptTitle, uid=conceptUid,
                                            type=conceptType)
        if not rc and not text and '*' in type: # there should be some sort of selection...
            return ScoredSet(result, scores)
        if text or type != 'loops:*':  # TODO: this may be highly inefficient!
            cat = self.catalog
            if type.endswith('*'):
                start = type[:-1]
                end = start + '\x7f'
            else:
                start = end = type
            criteria = {'loops_type': (start, end),}
            if useFull and text:
                criteria['loops_text'] = text
                r1 = cat.apply(criteria)    #r1 = set(cat.searchResults(**criteria))
            else:
                r1 = IFBucket()             #r1 = set()
            if useTitle and text:
                if 'loops_text' in criteria:
                    del criteria['loops_text']
                criteria['loops_title'] = text
                r2 = cat.apply(criteria)    #r2 = set(cat.searchResults(**criteria))
            else:
                r2 = IFBucket()             #r2 = set()
            x, uids = weightedUnion(r1, r2) #result = r1.union(r2)
            for r, score in uids.items():
                obj = intids.getObject(r)
                result.add(obj)
                scores[obj] = score
        if rc is not None:
            if result:
                result = result.intersection(rc)
            else:
                result = rc
        result = set(r for r in result
                            if r.getLoopsRoot() == self.loopsRoot
                               and canListObject(r)
                               and getVersion(r) == r)
        return ScoredSet(result, scores)


class ConceptQuery(BaseQuery):
    """ Find concepts of type `type` whose title starts with `title`.
    """

    def query(self, title=None, type=None, **kw):
        if title and not title.endswith('*'):
            title += '*'
        return self.queryConcepts(title=title, type=type, **kw)


# QueryConcept: concept objects that allow querying the database.

class IQueryConcept(IConceptSchema):
    """ The schema for the query type.
    """

    viewName = schema.TextLine(
        title=_(u'Adapter/View name'),
        description=_(u'The name of the (multi-) adapter (typically a view) '
                       'to be used for the query and for presenting '
                       'the results'),
        default=u'',
        required=True)

    options = schema.List(
        title=_(u'Options'),
        description=_(u'Additional settings.'),
        value_type=schema.TextLine(),
        default=[],
        required=False)


class QueryConcept(AdapterBase):

    implements(IQueryConcept)

    _contextAttributes = AdapterBase._contextAttributes + ['viewName']
    _adapterAttributes = AdapterBase._adapterAttributes + ('options',)

    def getOptions(self):
        return getattr(self.context, '_options', [])
    def setOptions(self, value):
        self.context._options = value
    options = property(getOptions, setOptions)


TypeInterfaceSourceList.typeInterfaces += (IQueryConcept,)

