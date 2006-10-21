#
#  Copyright (c) 2005 Helmut Merz helmutm@cy55.de
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
Tournament and Assessment views.

$Id$
"""

from zope.interface import implements
from zope.app.publisher.xmlrpc import XMLRPCView
from zope.app.publisher.xmlrpc import MethodPublisher
from zope.app.traversing.api import getName
from zope.security.proxy import removeSecurityProxy
from zope.cachedescriptors.property import Lazy

from loops.util import getUidForObject, getObjectForUid

class LoopsMethods(MethodPublisher):
    """ XML-RPC methods for the loops root object.
    """

    def __init__(self, context, request):
        self.context = removeSecurityProxy(context)
        self.request = request

    @Lazy
    def concepts(self):
        return self.context.getConceptManager()

    def getStartObject(self):
        so = self.concepts.get('domain', self.concepts.getTypeConcept())
        return objectAsDict(so)

    def getObjectById(self, id):
        return objectAsDict(getObjectForUid(id))

    def getObjectByName(self, name):
        return objectAsDict(self.concepts[name])

    def getDefaultPredicate(self):
        return objectAsDict(self.concepts.getDefaultPredicate())

    def getTypePredicate(self):
        return objectAsDict(self.concepts.getTypePredicate())

    def getTypeConcept(self):
        return objectAsDict(self.concepts.getTypeConcept())

    def getConceptTypes(self):
        tc = self.concepts.getTypeConcept()
        types = tc.getChildren((self.concepts.getTypePredicate(),))
        return [objectAsDict(t) for t in types]

    def getPredicates(self):
        pt = self.concepts.getDefaultPredicate().conceptType
        types = pt.getChildren((self.concepts.getTypePredicate(),))
        return [objectAsDict(t) for t in types]

    def getChildren(self, id, predicates=[], child=''):
        obj = getObjectForUid(id)
        preds = [getObjectForUid(p) for p in predicates]
        child = child and getObjectForUid(child) or None
        rels = obj.getChildRelations(preds, child)
        return formatRelations(rels)

    def getParents(self, id, predicates=[], parent=''):
        obj = getObjectForUid(id)
        preds = [getObjectForUid(p) for p in predicates]
        parent = parent and getObjectForUid(parent) or None
        rels = obj.getParentRelations(preds, parent)
        return formatRelations(rels, useSecond=False)


def objectAsDict(obj):
    mapping = {'id': getUidForObject(obj), 'name': getName(obj), 'title': obj.title,
               'type': getUidForObject(obj.conceptType)}
    return mapping

def formatRelations(rels, useSecond=True):
    predIds = {}
    result = []
    for rel in rels:
        pred = rel.predicate
        predId = getUidForObject(pred)
        if not predId in predIds:
            predIds[predId] = len(result)
            result.append({'id': predId, 'name': getName(pred),
                           'title': pred.title, 'objects': []})
        result[predIds[predId]]['objects'].append(
            objectAsDict(useSecond and rel.second or rel.first))
    return result

