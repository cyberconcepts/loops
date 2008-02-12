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
Automatic setup of a loops site.

$Id$
"""

from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.event import notify
from zope import component
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implements, Interface
from zope.traversing.api import getName

from cybertools.typology.interfaces import IType
from loops.common import adapted
from loops.concept import ConceptManager, Concept
from loops.interfaces import ILoops, ITypeConcept
from loops.interfaces import IFile, IImage, ITextDocument, INote
from loops.query import IQueryConcept
from loops.record import RecordManager
from loops.resource import ResourceManager, Resource
from loops.view import ViewManager, Node


class ISetupManager(Interface):
    """ An object that controls the setup of a loops site.
    """

    def setup():
        """ Set up a loops site: create all necessary objects and the
            relations between them.
        """


class SetupManager(object):

    adapts(ILoops)
    implements(ISetupManager)

    def __init__(self, context):
        self.context = context

    def setup(self):
        concepts, resources, views = self.setupManagers()
        self.setupCoreConcepts(concepts)
        appSetups = dict(component.getAdapters((self.context,), ISetupManager))
        for smName in appSetups:
            if smName: # skip core (unnamed), i.e. this, adapter
                appSetups[smName].setup()
        return concepts, resources, views # just for convenience when testing

    def setupManagers(self):
        loopsRoot = self.context
        concepts = self.addObject(loopsRoot, ConceptManager, 'concepts')
        resources = self.addObject(loopsRoot, ResourceManager, 'resources')
        views = self.addObject(loopsRoot, ViewManager, 'views')
        records = self.addObject(loopsRoot, RecordManager, 'records')
        return concepts, resources, views

    def setupCoreConcepts(self, conceptManager):
        typeConcept = self.addObject(conceptManager, Concept, 'type', title=u'Type')
        hasType = self.addObject(conceptManager, Concept, 'hasType', title=u'has Type')
        predicate = self.addObject(conceptManager, Concept, 'predicate', title=u'Predicate')
        standard = self.addObject(conceptManager, Concept, 'standard', title=u'subobject')
        domain = self.addObject(conceptManager, Concept, 'domain', title=u'Domain')
        query = self.addObject(conceptManager, Concept, 'query', title=u'Query')
        file = self.addObject(conceptManager, Concept, 'file', title=u'File')
        textdocument = self.addObject(conceptManager, Concept,
                                      'textdocument', title=u'Text')
        note = self.addObject(conceptManager, Concept, 'note', title=u'Note')
        for c in (typeConcept, domain, query, note, file, textdocument, predicate):
            c.conceptType = typeConcept
            notify(ObjectModifiedEvent(c))
        ITypeConcept(typeConcept).typeInterface = ITypeConcept
        ITypeConcept(query).typeInterface = IQueryConcept
        ITypeConcept(file).typeInterface = IFile
        ITypeConcept(textdocument).typeInterface = ITextDocument
        ITypeConcept(note).typeInterface = INote
        ITypeConcept(note).viewName = 'note.html'
        hasType.conceptType = predicate
        standard.conceptType = predicate

    # standard properties and methods

    @Lazy
    def concepts(self):
        return self.context.getConceptManager()

    @Lazy
    def resources(self):
        return self.context.getResourceManager()

    @Lazy
    def views(self):
        return self.context.getViewManager()

    @Lazy
    def typeConcept(self):
        return self.concepts.getTypeConcept()

    @Lazy
    def predicateType(self):
        return self.concepts.getPredicateType()

    def addType(self, name, title, typeInterface=None, **kw):
        c = self.addConcept(name, title, self.typeConcept,
                            typeInterface=typeInterface, **kw)
        return c

    def addPredicate(self, name, title, **kw):
        c = self.addConcept(name, title, self.predicateType, **kw)
        return c

    def addConcept(self, name, title, conceptType, description=u'',
                   parentName=None, **kw):
        if name in self.concepts:
            self.log("Concept '%s' ('%s') already exists." % (name, title))
            c = self.concepts[name]
            if c.conceptType != conceptType:
                self.log("Wrong concept type for '%s': '%s' instead of '%s'." %
                         (name, getName(c.conceptType), getName(conceptType)))
        else:
            c = addAndConfigureObject(self.concepts, Concept, name, title=title,
                              description=description,
                              conceptType=conceptType, **kw)
            self.log("Concept '%s' ('%s') created." % (name, title))
        if parentName is not None:
            self.assignChild(parentName, name)
        return c

    def setConceptAttribute(self, concept, attr, value):
        setattr(adapted(concept), attr, value)
        self.log("Setting Attribute '%s' of '%s' to '%s'" %
                 (attr, getName(concept), repr(value)))

    def assignChild(self, conceptName, childName, predicate=None):
        if predicate is None:
            predicate = self.concepts.getDefaultPredicate()
        if isinstance(predicate, str):
            predicate = self.concepts[predicate]
        concept = self.concepts[conceptName]
        child = self.concepts[childName]
        if child in concept.getChildren([predicate]):
            self.log("Concept '%s' is already a child of '%s with predicate '%s'.'" %
                     (childName, conceptName, getName(predicate)))
        else:
            concept.assignChild(child, predicate)

    def addNode(self, name, title, container=None, nodeType='page',
                description=u'', body=u'', targetName=None, **kw):
        if container is None:
            container = self.views
            nodeType = 'menu'
        if name in container:
            self.log("Node '%s' ('%s') already exists in '%s'." %
                     (name, title, getName(container)))
            n = container[name]
            if n.nodeType != nodeType:
                self.log("Wrong node type for '%s': '%s' instead of '%s'." %
                         (name, n.nodeType, nodeType))
        else:
            n = addAndConfigureObject(container, Node, name, title=title,
                              description=description, body=body,
                              nodeType=nodeType, **kw)
            self.log("Node '%s' ('%s') created." % (name, title))
        if targetName is not None:
            if targetName in self.concepts:
                n.target = self.concepts[targetName]
        return n

    def log(self, message):
        if isinstance(message, unicode):
            message = message.encode('UTF-8')
        print >> self.logger, message

    def addObject(self, container, class_, name, **kw):
        return addObject(container, class_, name, **kw)

    def addAndConfigureObject(self, container, class_, name, **kw):
        return addAndConfigureObject(container, class_, name, **kw)


def addObject(container, class_, name, **kw):
    if name in container:
        return container[name]
    obj = container[name] = class_()
    for attr in kw:
        setattr(obj, attr, kw[attr])
    notify(ObjectCreatedEvent(obj))
    notify(ObjectModifiedEvent(obj))
    return obj

def addAndConfigureObject(container, class_, name, **kw):
    basicAttributes = ('title', 'description', 'conceptType', 'resourceType',
                       'nodeType', 'body')
    basicKw = dict([(k, kw[k]) for k in kw if k in basicAttributes])
    obj = addObject(container, class_, name, **basicKw)
    adapted = obj
    if class_ in (Concept, Resource):
        ti = IType(obj).typeInterface
        if ti is not None:
            adapted = ti(obj)
    adapterAttributes = [k for k in kw if k not in basicAttributes]
    for attr in adapterAttributes:
        setattr(adapted, attr, kw[attr])
    notify(ObjectModifiedEvent(obj))
    return obj


class SetupView(object):
    """ Allows to carry out setup actions manually.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.manager = ISetupManager(context)

    def setupLoopsSite(self):
        #self.manager.setupManagers()
        self.manager.setup()
        return 'Done'

