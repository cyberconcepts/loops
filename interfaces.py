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
from zope.app.container.interfaces import IContainer, IOrderedContainer
from zope.app.file.interfaces import IImage as IBaseAsset
from zope.app.folder.interfaces import IFolder
from cybertools.relation.interfaces import IRelation

_ = MessageFactory('loops')


# common interfaces

class ILoopsObject(Interface):
    """ Common top-level interface.
    """

    def getLoopsRoot():
        """ Return the loops root object.
        """

    def getViewManager():
        """ Return the (default) view manager.
        """


class IPotentialTarget(Interface):
    """ For objects that may be used as target objects for view objects.
    """

    proxyInterface = Attribute('An interface allowing an object to be '
                               'used as a target for a view/node (and '
                               'typically specifying the corresponding schema')


# concept interfaces

class IConcept(ILoopsObject, IPotentialTarget):
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
        

class IConceptManager(ILoopsObject, IContainer):
    """ A manager/container for concepts.
    """
    contains(IConcept)


class IConceptManagerContained(Interface):
    containers(IConceptManager)


# resource interfaces

class IResourceSchema(Interface):

    title = schema.TextLine(
                title=_(u'Title'),
                description=_(u'Title of the resource'),
                default=u'',
                missing_value=u'',
                required=False)

    data = schema.Bytes(
                title=_(u'Data'),
                description=_(u'Resource raw data'),
                default='',
                missing_value='',
                required=False)

    contentType = schema.BytesLine(
                title=_(u'Content Type'),
                description=_(u'Content type (format) of the data field'),
                default='',
                missing_value='',
                required=False)


class IResource(ILoopsObject, IPotentialTarget):
    """ A resource is an atomic information element that is made
        available via a view or a concept.
    """

    def getClients(relationships=None):
        """ Return a sequence of objects that are clients of the resource,
            i.e. that have some relation with it.
        """


class IDocumentSchema(IResourceSchema):

    data = schema.Text(
                title=_(u'Data'),
                description=_(u'Raw body data of the document'),
                default=u'',
                missing_value=u'',
                required=False)

    contentType = schema.Choice(
                title=_(u'Content Type'),
                description=_(u'Content type (format) of the data field'),
                values=('text/restructured', 'text/structured', 'text/html',
                        'text/plain',),
                default='text/restructured',
                required=True)


class IDocumentView(IDocumentSchema):
    """ Used for accessing a document via a node's target attribute"""


class IDocument(IDocumentSchema, IResource):
    """ A resource containing an editable body.
    """


class IMediaAssetSchema(IResourceSchema):

    data = schema.Bytes(
                title=_(u'Data'),
                description=_(u'Media asset file'),
                default='',
                missing_value='',
                required=False)


class IMediaAssetView(IMediaAssetSchema):
    """ Used for accessing a media asset via a node's target attribute"""


class IMediaAsset(IMediaAssetSchema, IResource, IBaseAsset):
    """ A resource containing a (typically binary) file-like content
        or an image. 
    """


class IResourceManager(ILoopsObject, IContainer):
    """ A manager/container for resources.
    """
    contains(IResource)


class IResourceManagerContained(Interface):
    containers(IResourceManager)


# view interfaces

class IView(ILoopsObject):
    """ A view is a user interface component that provides access to one
        or more concepts, resources, or other views.
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


class IBaseNode(IOrderedContainer):
    """ Common abstract base class for different types of nodes
    """

    def getLoopsRoot():
        """ Return the loops root object.
        """
    

class INode(IView, IBaseNode):
    """ A node is a view that may contain other views, thus building a
        menu or folder hierarchy.

        A node may be a content object on its own; for this reason it
        has a body attribute that may be shown e.g. on web pages.
    """
    contains(IView)

    nodeType = schema.Choice(
        title=_(u'Node Type'),
        description=_(u'Type of the node'),
        values=('text', 'page', 'menu', 'info'),
        default='info',
        required=True)

    body = schema.Text(
        title=_(u'Body'),
        description=_(u'Textual body that may be shown in addition to '
                       'or instead of information coming from the target'),
        default=u'',
        required=False)

    contentType = Attribute(_(u'Content type (format) of the body'))

    def getParentNode(nodeTypes=None):
        """ Return the next node up the node hierarchy. If the nodeTypes
            parameter is given, search for the next node that has one of
            the types in the nodeTypes list.

            Return None if no suitable node can be found.
        """

    def getChildNodes(nodeTypes=None):
        """ Return a sequence of nodes contained in this node. If the
            nodeTypes parameter is given return only nodes of these types.
        """

    def getMenu():
        """ Return the menu node this node belongs to or None if not found.
        """

    def getPage():
        """ Return a page node or None if not found.
        """

    def getMenuItems():
        """ Return the menu items belonging to this object (that should be
            a menu).
        """

    def getTextItems():
        """ Return the menu items belonging to this object (that should be
            a menu).
        """


class IViewManager(ILoopsObject, IBaseNode):
    """ A manager/container for views.
    """
    contains(IView)


class INodeContained(Interface):
    containers(INode, IViewManager)


# schemas to be used by forms on view/node objects

class ITargetProperties(Interface):
    """ Fields used for specifying a view's or node's target.
    """

    targetType = schema.Choice(
        title=_(u'Target Type'),
        description=_(u'Type of the target'),
        values=('loops.resource.Document', 'loops.resource.MediaAsset'),
        default=None,
        required=False)

    targetUri = schema.TextLine(
        title=_(u'Target URI'),
        description=_(u'An URI being a unique reference to the target'),
        required=False)


class INodeConfigSchema(INode, ITargetProperties):
    """ All fields that may be shown in the node config form.
    """

    createTarget = schema.Bool(
        title=_(u'Create Target'),
        description=_(u'Should a new target object be created?'),
        required=False)


class ITargetRelation(IRelation):
    """ (Marker) interfaces for relations pointing to a target
        of a view or node.
    """


# the loops top-level container

class ILoops(ILoopsObject, IFolder):
    """ The top-level object of a loops site.
    """
    contains(IConceptManager, IResourceManager, IViewManager)

    def getLoopsUri(obj):
        """ Return the relativ path to obj, starting with '.loops/...'.
        """
    

class ILoopsContained(Interface):
    containers(ILoops)

