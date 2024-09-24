# loops.setup

""" Automatic setup of a loops site.

"""

import os
from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.event import notify
from zope import component
from zope.cachedescriptors.property import Lazy
from zope.component import adapts
from zope.interface import implementer, Interface
from zope.traversing.api import getName, traverse

from cybertools.typology.interfaces import IType
from loops.common import adapted
from loops.concept import ConceptManager, Concept
from loops.interfaces import ILoops, ITypeConcept, IPredicate
from loops.interfaces import IFile, IImage, ITextDocument, INote
#from loops.query import IQueryConcept
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


@implementer(ISetupManager)
class SetupManager(object):

    adapts(ILoops)

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
        predicate = self.addObject(conceptManager, Concept, 'predicate',
                                    title=u'Predicate')
        standard = self.addObject(conceptManager, Concept, 'standard',
                                    title=u'subobject')
        domain = self.addObject(conceptManager, Concept, 'domain', title=u'Domain')
        #query = self.addObject(conceptManager, Concept, 'query', title=u'Query')
        file = self.addObject(conceptManager, Concept, 'file', title=u'File')
        textdocument = self.addObject(conceptManager, Concept,
                                      'textdocument', title=u'Text')
        note = self.addObject(conceptManager, Concept, 'note', title=u'Note')
        for c in (typeConcept, domain, note, file, textdocument, predicate):
            c.conceptType = typeConcept
            notify(ObjectModifiedEvent(c))
        ITypeConcept(typeConcept).typeInterface = ITypeConcept
        #ITypeConcept(query).typeInterface = IQueryConcept
        ITypeConcept(file).typeInterface = IFile
        ITypeConcept(textdocument).typeInterface = ITextDocument
        ITypeConcept(note).typeInterface = INote
        ITypeConcept(note).viewName = 'note.html'
        ITypeConcept(predicate).typeInterface = IPredicate
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
        self.log("Setting Attribute '%s' of '%s' to '%s'." %
                 (attr, getName(concept), repr(value)))

    def assignChild(self, conceptName, childName, predicate=None, **kw):
        predicate = self.getPredicate(predicate)
        concept = self.concepts[conceptName]
        child = self.concepts[childName]
        if child in concept.getChildren([predicate]):
            self.log("Concept '%s' is already a child of '%s' with predicate '%s'." %
                     (childName, conceptName, getName(predicate)))
        else:
            concept.assignChild(child, predicate, **kw)
            self.log("Concept '%s' assigned to '%s' with predicate '%s'." %
                     (childName, conceptName, getName(predicate)))

    def deassignChild(self, conceptName, childName, predicate=None):
        predicate = self.getPredicate(predicate)
        concept = self.concepts[conceptName]
        child = self.concepts[childName]
        concept.deassignChild(child, [predicate])
        self.log("Concept '%s' deassigned from '%s' for predicate '%s'." %
                    (childName, conceptName, getName(predicate)))

    def addResource(self, name, title, resourceType, description=u'', **kw):
        if name in self.resources:
            self.log("Resource '%s' ('%s') already exists." % (name, title))
            c = self.resources[name]
            if c.resourceType != resourceType:
                self.log("Wrong resource type for '%s': '%s' instead of '%s'." %
                         (name, getName(c.resourceType), getName(resourceType)))
        else:
            c = addAndConfigureObject(self.resources, Resource, name, title=title,
                              description=description,
                              resourceType=resourceType, **kw)
            self.log("Resource '%s' ('%s') created." % (name, title))
        return c

    def assignResource(self, conceptName, resourceName, predicate=None, **kw):
        predicate = self.getPredicate(predicate)
        concept = self.concepts[conceptName]
        resource = self.resources[resourceName]
        if resource in concept.getResources([predicate]):
            self.log("Resource '%s' is already assigned to '%s' with predicate '%s'.'" %
                     (resourceName, conceptName, getName(predicate)))
        else:
            concept.assignResource(resource, predicate, **kw)
            self.log("Resource '%s' assigned to '%s' with predicate '%s'." %
                     (resourceName, conceptName, getName(predicate)))

    def deassignResource(self, conceptName, resourceName, predicate=None):
        predicate = self.getPredicate(predicate)
        concept = self.concepts[conceptName]
        resource = self.resources[resourceName]
        concept.deassignResource(resource, [predicate])
        self.log("Resource '%s' deassigned from '%s' for predicate '%s'." %
                    (resourceName, conceptName, getName(predicate)))

    def addNode(self, name, title, container=None, nodeType='page',
                description=u'', body=u'', target=None, factory=Node, **kw):
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
            n = addAndConfigureObject(container, factory, name, title=title,
                              description=description, body=body,
                              nodeType=nodeType, **kw)
            self.log("Node '%s' ('%s') created." % (name, title))
        if target is not None:
            targetObject = traverse(self, target, None)
            if targetObject is not None:
                if n.target == targetObject:
                    self.log("Target '%s' already assigned to node '%s'." %
                             (target, name))
                else:
                    n.target = targetObject
                    self.log("Target '%s' assigned to node '%s'." %
                             (target, name))
            else:
                self.log("Target '%s' for '%s' does not exist." %
                         (target, name))
        return n

    def getPredicate(self, predicate):
        if predicate is None:
            return self.concepts.getDefaultPredicate()
        if isinstance(predicate, basestring):
            return self.concepts[predicate]
        return predicate

    def log(self, message):
        if isinstance(message, unicode):
            message = message.encode('UTF-8')
        print >> self.logger, message

    def addObject(self, container, class_, name, **kw):
        return addObject(container, class_, name, **kw)

    def addAndConfigureObject(self, container, class_, name, **kw):
        return addAndConfigureObject(container, class_, name, **kw)


def addObject(container, class_, name, notifyModified=True, **kw):
    created = False
    if name in container:
        obj = container[name]
        #return obj
    else:
        obj = container[name] = class_()
        created = True
    for attr, value in kw.items():
        if attr == 'type':
            obj.setType(value)
        else:
            setattr(obj, attr, value)
    if created:
        notify(ObjectCreatedEvent(obj))
    if notifyModified:
        notify(ObjectModifiedEvent(obj))
    return obj

def addAndConfigureObject(container, class_, name, notifyModified=True, **kw):
    basicAttributes = ('title', 'description', 'conceptType', 'resourceType',
                       'nodeType', 'body')
    basicKw = dict([(k, kw[k]) for k in kw if k in basicAttributes])
    obj = addObject(container, class_, name, notifyModified=False, **basicKw)
    adapted = obj
    if class_ in (Concept, Resource):
        ti = IType(obj).typeInterface
        if ti is not None:
            adapted = ti(obj)
    adapterAttributes = [k for k in kw if k not in basicAttributes]
    for attr in adapterAttributes:
        setattr(adapted, attr, kw[attr])
    if notifyModified:
        notify(ObjectModifiedEvent(obj))
    return obj


def importData(root, importPath, importFileName):
    from loops.external.annotation import AnnotationsExtractor
    from loops.external.base import Loader
    from loops.external.pyfunc import PyReader
    component.provideAdapter(AnnotationsExtractor)
    dmpFile = open(os.path.join(importPath, importFileName))
    data = dmpFile.read()
    dmpFile.close()
    reader = PyReader()
    elements = reader.read(data)
    loader = Loader(root, os.path.join(importPath, 'resources'))
    loader.load(elements)


class SetupView(object):
    """ Allows to carry out setup actions manually.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.manager = ISetupManager(context)

    def setupLoopsSite(self):
        self.manager.setup()
        return 'Done'


