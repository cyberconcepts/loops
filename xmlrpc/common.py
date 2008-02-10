#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
XML-RPC views.

$Id$
"""

from zope.app.container.interfaces import INameChooser
from zope.interface import implements
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.app.publisher.xmlrpc import XMLRPCView
from zope.app.publisher.xmlrpc import MethodPublisher
from zope.traversing.api import getName
from zope.schema.interfaces import ITextLine
from zope.security.proxy import removeSecurityProxy
from zope.cachedescriptors.property import Lazy

from cybertools.typology.interfaces import IType
from loops.common import adapted
from loops.concept import Concept
from loops.i18n.browser import I18NView
from loops.util import getUidForObject, getObjectForUid, toUnicode


class LoopsMethods(MethodPublisher, I18NView):
    """ XML-RPC methods for the loops root object.
    """

    def __init__(self, context, request):
        self.context = removeSecurityProxy(context)
        self.request = request

    @Lazy
    def concepts(self):
        return self.context.getConceptManager()

    @Lazy
    def typePredicate(self):
        return self.concepts.getTypePredicate()

    def getStartObject(self):
        so = self.concepts.get('domain', self.concepts.getTypeConcept())
        return self.getObjectWithChildren(so)

    def getObjectById(self, id):
        return self.getObjectWithChildren(getObjectForUid(id))

    def getObjectByName(self, name):
        return self.getObjectWithChildren(self.concepts[name])

    def getDefaultPredicate(self):
        return self.getObjectWithChildren(self.concepts.getDefaultPredicate())

    def getTypePredicate(self):
        return self.getObjectWithChildren(self.typePredicate)

    def getTypeConcept(self):
        return self.getObjectWithChildren(self.concepts.getTypeConcept())

    def getConceptTypes(self):
        tc = self.concepts.getTypeConcept()
        types = tc.getChildren((self.typePredicate,))
        #types = [t for t in types if ITypeConcept(t).typeInterface ... ]
        return [objectAsDict(t, self.languageInfo) for t in types]

    def getPredicates(self):
        pt = self.concepts.getDefaultPredicate().conceptType
        preds = pt.getChildren((self.concepts.getTypePredicate(),))
        return [objectAsDict(p, self.languageInfo)
                for p in preds if p is not self.typePredicate]

    def getChildren(self, id, predicates=[], child=''):
        obj = getObjectForUid(id)
        preds = [getObjectForUid(p) for p in predicates]
        child = child and getObjectForUid(child) or None
        rels = obj.getChildRelations(preds or None, child)
        return formatRelations(rels, langInfo=self.languageInfo)

    def getParents(self, id, predicates=[], parent=''):
        obj = getObjectForUid(id)
        preds = [getObjectForUid(p) for p in predicates]
        parent = parent and getObjectForUid(parent) or None
        rels = obj.getParentRelations(preds or None, parent)
        return formatRelations(rels, useSecond=False, langInfo=self.languageInfo)

    def getResources(self, id, predicates=[], resource=''):
        obj = getObjectForUid(id)
        preds = [getObjectForUid(p) for p in predicates]
        resource = resource and getObjectForUid(child) or None
        rels = obj.getResourceRelations(preds or None, resource)
        return formatRelations(rels, langInfo=self.languageInfo)

    def getObjectWithChildren(self, obj):
        mapping = objectAsDict(obj, self.languageInfo)
        mapping['children'] = formatRelations(obj.getChildRelations(sort=None),
                                        langInfo=self.languageInfo)
        mapping['parents'] = formatRelations(obj.getParentRelations(sort=None),
                                        useSecond=False,
                                        langInfo=self.languageInfo)
        mapping['resources'] = formatRelations(obj.getResourceRelations(sort=None),
                                        langInfo=self.languageInfo)
        return mapping

    def assignChild(self, objId, predicateId, childId):
        obj = getObjectForUid(objId)
        pred = getObjectForUid(predicateId)
        child = getObjectForUid(childId)
        obj.assignChild(child, pred)
        return 'OK'

    def deassignChild(self, objId, predicateId, childId):
        obj = getObjectForUid(objId)
        pred = getObjectForUid(predicateId)
        child = getObjectForUid(childId)
        obj.deassignChild(child, [pred])
        return 'OK'

    def createConcept(self, typeId, name, title):
        type = getObjectForUid(typeId)
        title = toUnicode(title)
        c = Concept(title)
        name = INameChooser(self.concepts).chooseName(name, c)
        self.concepts[name] = c
        c.conceptType = type
        adapted(c, self.languageInfo).title = title
        notify(ObjectCreatedEvent(c))
        notify(ObjectModifiedEvent(c))
        return objectAsDict(c, self.languageInfo)

    def editConcept(self, objId, attr, value):
        obj = getObjectForUid(objId)
        adapter = adapted(obj, self.languageInfo)
        # TODO: provide conversion if necessary - use cybertools.composer.schema
        value = value.strip()   # remove spaces appended by Flash
        setattr(adapter, attr, toUnicode(value))
        notify(ObjectModifiedEvent(obj))
        return 'OK'


def objectAsDict(obj, langInfo=None):
    objType = IType(obj)
    adapter = adapted(obj, langInfo)
    mapping = {'id': getUidForObject(obj), 'name': getName(obj),
               'title': adapter.title, 'description': adapter.description,
               'type': getUidForObject(objType.typeProvider)}
    ti = objType.typeInterface
    if ti is not None and adapter != obj:
        #for attr in (list(adapter._adapterAttributes) + list(ti)):
        for attr in list(ti):
            if attr not in ('__parent__', 'context', 'id', 'name',
                            'title', 'description', 'type', 'data'):
                value = getattr(adapter, attr)
                # TODO: provide conversion and schema information -
                #       use cybertools.composer.schema
                #if value is None or type(value) in (str, unicode):
                if ITextLine.providedBy(ti[attr]):
                    mapping[attr] = value or u''
                #elif type(value) is list:
                #    mapping[attr] = ' | '.join(value)
    return mapping

def formatRelations(rels, useSecond=True, langInfo=None):
    predIds = {}
    result = []
    for rel in rels:
        pred = rel.predicate
        predId = getUidForObject(pred)
        if not predId in predIds:
            predIds[predId] = len(result)
            result.append({'id': predId, 'name': getName(pred),
                           'title': pred.title, 'objects': []})
        if useSecond:
            other = rel.second
        else:
            other = rel.first
        result[predIds[predId]]['objects'].append(objectAsDict(other, langInfo))
    return sorted(result, key=lambda x: x['title'])

