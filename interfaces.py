#
#  Copyright (c) 2004 Helmut Merz helmutm@cy55.de
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
loops interface definitions.

$Id$
"""

from zope.interface import Interface, Attribute
from zope.i18nmessageid import MessageFactory
from zope import schema
from zope.app.container.constraints import contains, containers
from zope.app.container.interfaces import IContainer
from zope.app.file.interfaces import IFile as IBaseFile
from zope.app.folder.interfaces import IFolder

_ = MessageFactory('loops')


# concept interfaces

class IConcept(Interface):
    """ The concept is the central element of the loops framework.
    
        A concept is related to other concepts, may have resources
        associated with it and may be referenced by views.
    """

    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Title of the concept'),
        default=u'',
        required=False)

    def getSubConcepts(relationships=None):
        """ Return a sequence of concepts related to self as sub-concepts,
            possibly restricted to the relationships (typically a list of
            relation classes) given.
        """

    def getParentConcepts(relationships=None):
        """ Return a tuple of concepts related to self as parent concepts,
            possibly restricted to the relationships (typically a list of
            relation classes) given.
        """

    def assignConcept(concept, relationship):
        """ Assign an existing concept to self using the relationship given.
            The assigned concept will be a sub-concept of self.

            The relationship defaults to ConceptRelation.
        """

    def deassignConcept(concept, relationships=None):
        """ Remove the relations to the concept given from self, optionally
            restricting them to the relationships given.
        """

    def getResources(relationships=None):
        """ Return a sequence of resources assigned to self,
            possibly restricted to the relationships given.
        """        

    def assignResource(resource, relationship):
        """ Assign an existing resource to self using the relationship given.

            The relationship defaults to ConceptResourceRelation.
        """
        
    def deassignResource(resource, relationships=None):
        """ Remove the relations to the resource given from self, optionally
            restricting them to the relationships given.
        """
        

class IConceptManager(IContainer):
    """ A manager/container for concepts.
    """
    contains(IConcept)


class IConceptManagerContained(Interface):
    containers(IConceptManager)


# resource interfaces

class IResource(Interface):
    """ A resource is an atomic information element that is usually
        available via a concept.
    """

    title = schema.TextLine(
                title=_(u'Title'),
                description=_(u'Title of the document'),
                required=False)

    def getClients(relationships=None):
        """ Return a sequence of objects that are clients of the resource,
            i.e. that have some relation with it.
        """


class IDocument(IResource):
    """ A resource containing an editable body.
    """

    body = schema.Text(
                title=_(u'Body'),
                description=_(u'Body of the document'),
                required=False)

    format = schema.TextLine(
                title=_(u'Format'),
                description=_(u'Format of the body field, default is "text/xml"'),
                default=_(u'text/xml'),
                required=False)


class IFile(IResource, IBaseFile):
    """ A resource containing a (typically binary) file-like content
        or an image.
    """


class IResourceManager(IContainer):
    """ A manager/container for resources.
    """
    contains(IResource)


class IResourceManagerContained(Interface):
    containers(IResourceManager)


# view interfaces

class IView(Interface):
    """ A view is a user interface component that provides access to one
        or more concepts.
    """

    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Title of the view; this will appear e.g. in menus'),
        default=u'',
        required=True)

    description = schema.Text(
        title=_(u'Description'),
        description=_(u'Detailed description, e.g. for tooltips or listings'),
        default=u'',
        required=False)

    target = Attribute('Target object that is referenced by this view')
    

class INode(IView):
    """ A node is a view that may contain other views, thus building a
        menu or folder hierarchy.
    """
    contains(IView)


class IViewManager(IContainer):
    """ A manager/container for views.
    """
    contains(IView)


class INodeContained(Interface):
    containers(INode, IViewManager)


# the loops top-level container

class ILoops(IFolder):
    """ The top-level object of a loops site.
    """
    contains(IConceptManager, IResourceManager, IViewManager)
    

class ILoopsContained(Interface):
    containers(ILoops)


