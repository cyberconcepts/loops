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

import transaction
from zope.app.event.objectevent import ObjectCreatedEvent, ObjectModifiedEvent
from zope.event import notify
from zope.component import adapts
from zope.interface import implements, Interface
from zope.cachedescriptors.property import Lazy

from loops.interfaces import ILoops
from loops.concept import ConceptManager, Concept
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

    def setupManagers(self):
        loopsRoot = self.context
        concepts = self.addObject(loopsRoot, ConceptManager, 'concepts')
        resources = self.addObject(loopsRoot, ResourceManager, 'resources')
        views = self.addObject(loopsRoot, ViewManager, 'views')
        return concepts, resources, views
        
    def setupCoreConcepts(self, conceptManager):
        typeConcept = self.addObject(conceptManager, Concept, 'type', u'Type')
        hasType = self.addObject(conceptManager, Concept, 'hasType', u'has type')
        predicate = self.addObject(conceptManager, Concept, 'predicate', u'Predicate')
        standard = self.addObject(conceptManager, Concept, 'standard', u'subobject')
        typeConcept.conceptType = typeConcept
        predicate.conceptType = typeConcept
        hasType.conceptType = predicate
        standard.conceptType = predicate

    def addObject(self, container, class_, name, title=None):
        if name in container:
            return container[name]
        if title:
            obj = container[name] = class_(title)
        else:
            obj = container[name] = class_()
        notify(ObjectCreatedEvent(obj))
        notify(ObjectModifiedEvent(obj))
        return obj
