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
Automatic setup of a loops site.

$Id$
"""

from zope.lifecycleevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.event import notify
from zope import component
from zope.component import adapts
from zope.interface import implements, Interface

from loops.interfaces import ILoops, ITypeConcept
from loops.interfaces import IFile, IImage, ITextDocument, INote
from loops.concept import ConceptManager, Concept
from loops.query import IQueryConcept
from loops.resource import ResourceManager
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
        return concepts, resources, views

    def setupCoreConcepts(self, conceptManager):
        typeConcept = self.addObject(conceptManager, Concept, 'type', title=u'Type')
        hasType = self.addObject(conceptManager, Concept, 'hasType', title=u'has Type')
        predicate = self.addObject(conceptManager, Concept, 'predicate', title=u'Predicate')
        standard = self.addObject(conceptManager, Concept, 'standard', title=u'subobject')
        domain = self.addObject(conceptManager, Concept, 'domain', title=u'Domain')
        query = self.addObject(conceptManager, Concept, 'query', title=u'Query')
        file = self.addObject(conceptManager, Concept, 'file', title=u'File')
        #image = self.addObject(conceptManager, Concept, 'image', title=u'Image')
        textdocument = self.addObject(conceptManager, Concept,
                                      'textdocument', title=u'Text')
        note = self.addObject(conceptManager, Concept, 'note', title=u'Note')
        for c in (typeConcept, domain, query, note, file, textdocument, predicate):
            c.conceptType = typeConcept
        ITypeConcept(typeConcept).typeInterface = ITypeConcept
        ITypeConcept(query).typeInterface = IQueryConcept
        ITypeConcept(file).typeInterface = IFile
        #ITypeConcept(image).typeInterface = IImage
        ITypeConcept(textdocument).typeInterface = ITextDocument
        ITypeConcept(note).typeInterface = INote
        hasType.conceptType = predicate
        standard.conceptType = predicate

    def addObject(self, container, class_, name, **kw):
        return addObject(container, class_, name, **kw)


def addObject(container, class_, name, **kw):
    if name in container:
        return container[name]
    obj = container[name] = class_()
    for attr in kw:
        setattr(obj, attr, kw[attr])
    notify(ObjectCreatedEvent(obj))
    notify(ObjectModifiedEvent(obj))
    return obj
