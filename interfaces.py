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
loops interface definitions.

$Id$
"""

from zope.interface import Interface, Attribute
from zope.i18nmessageid import MessageFactory
from zope import schema
from zope.app.container.constraints import contains, containers
from zope.app.container.interfaces import IContainer, IOrderedContainer
from zope.app.file.interfaces import IImage as IBaseAsset
from zope.component.interfaces import IObjectEvent
from zope.size.interfaces import ISized

from cybertools.relation.interfaces import IDyadicRelation
from cybertools.tracking.interfaces import ITrackingStorage
from loops import util
from loops.util import _


# common interfaces

class ILoopsObject(Interface):
    """ Common top-level interface.
    """

    title = Attribute(u'A short line of information about an object to be '
                       'used e.g. for menu items or listing entries.')

    def getLoopsRoot():
        """ Return the loops root object.
        """

    def getAllParents(collectGrants=False):
        """ Return a sequence (or an ordered mapping / Jeep object)
            with informations about all parents of the object.

            If ``collectGrants`` is set also collect grant information
            (assigned/effective roles) together with the parents.
        """


class IPotentialTarget(Interface):
    """ For objects that may be used as target objects for views/nodes.
    """

    proxyInterface = Attribute('An interface allowing an object to be '
                               'used as a target for a view/node (and '
                               'typically specifying the corresponding schema)')


# concept interfaces

class IConceptSchema(Interface):
    """ The primary fields of a concept object.
    """

    title = schema.TextLine(
        title=_(u'Title'),
        description=_(u'Title of the concept'),
        default=u'',
        required=True)

    description = schema.Text(
        title=_(u'Description'),
        description=_(u'A medium-length description describing the '
                       'content and the purpose of the object'),
        default=u'',
        missing_value=u'',
        required=False)


class IConcept(IConceptSchema, ILoopsObject, IPotentialTarget):
    """ The concept is the central element of the loops framework.

        A concept is related to other concepts, may have resources
        associated with it and may be referenced by views.
    """

    conceptType = schema.Choice(
        title=_(u'Concept Type'),
        description=_(u"The type of the concept, specified by a relation to "
                       "a concept of type 'type'."),
        default=None,
        source="loops.conceptTypeSource",
        required=True)

    def getType():
        """ Return a concept that provides the object's type.
        """

    def getChildren(predicates=None):
        """ Return a sequence of concepts related to self as child concepts,
            optionally restricted to the predicates given.
        """

    def getChildRelations(predicates=None, children=None):
        """ Return a sequence of relations to other concepts assigned to self
            as child concepts, optionally restricted to the predicates given
            or to a certain child concept.
        """

    def getParents(predicates=None):
        """ Return a tuple of concepts related to self as parent concepts,
            optionally restricted to the predicates given.
        """

    def getParentRelations(predicates=None, parents=None):
        """ Return a sequence of relations to other concepts assigned to self
            as parent concepts, optionally restricted to the predicates given
            or to a certain parent concept.
        """

    def assignChild(concept, predicate):
        """ Assign an existing concept to self using the predicate given.
            The assigned concept will be a child concept of self.

            The predicate defaults to the concept manager's default predicate.
        """

    def assignParent(concept, predicate):
        """ Assign an existing concept to self using the predicate given.
            The assigned concept will be a parent concept of self.

            The predicate defaults to the concept manager's default predicate.
        """

    def deassignChild(child, predicates=None):
        """ Remove the child concept relations to the concept given from self,
            optionally restricting them to the predicates given.
        """

    def deassignParent(parent, predicates=None):
        """ Remove the parent concept relations to the concept given from self,
            optionally restricting them to the predicates given.
        """

    def setChildren(predicate, concepts):
        """ A convenience method for adding and removing a set of child
            relations in one call. The relations with the predicate given
            that already point to one of the concepts given as the second
            argument are kept unchanged, new ones are assigned, and existing
            ones not present in the concepts list are removed.
        """

    def getResources(predicates=None):
        """ Return a sequence of resources assigned to self,
            optionally restricted to the predicates given.
        """

    def getResourceRelations(predicates=None, resource=None):
        """ Return a sequence of relations to resources assigned to self,
            optionally restricted to the predicates given or to a certain
            resource.
        """

    def assignResource(resource, predicate):
        """ Assign an existing resource to self using the predicate given.

            The relationship defaults to ConceptResourceRelation.
        """

    def deassignResource(resource, predicates=None):
        """ Remove the relations to the resource given from self, optionally
            restricting them to the predicates given.
        """


class IConceptView(Interface):
    """ Used for accessing a concept via a node's target attribute"""


#class IConceptManager(ILoopsObject, IContainer):
class IConceptManager(ILoopsObject):
    """ A manager/container for concepts.
    """
    contains(IConcept)

    def getTypeConcept():
        """ Return the concept that provides the type object,
            i.e. the type of all types.
        """

    def getTypePredicate():
        """ Return the concept that provides the type predicate.
        """

    def getDefaultPredicate():
        """ Return the concept that provides the default (standard) predicate.
        """

    def getPredicateType():
        """ Return the concept that provides the predicate type object,
            i.e. the type of all predicates.
        """

class IConceptManagerContained(Interface):
    containers(IConceptManager)


# resource interfaces


class IBaseResource(ILoopsObject):
    """ New base interface for resources. Functionality beyond this simple
        interface is provided by adapters that are chosen via the
        resource type's typeInterface.
    """

    title = schema.TextLine(
                title=_(u'Title'),
                description=_(u'Title of the resource'),
                default=u'',
                missing_value=u'',
                required=True)

    description = schema.Text(
                title=_(u'Description'),
                description=_(u'A medium-length description describing the '
                               'content and the purpose of the object'),
                default=u'',
                missing_value=u'',
                required=False)

    resourceType = schema.Choice(
        title=_(u'Resource Type'),
        description=_(u"The type of the resource, specified by a relation to "
                       "a concept of type 'type'."),
        default=None,
        source="loops.resourceTypeSource",
        required=False)

    def getType():
        """ Return a concept that provides the object's type, i.e. the
            resourceType attribute.
        """

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


class IBaseResourceSchema(Interface):
    """ New schema for resources; to be used by sub-interfaces that will
        be implemented by type adapters.
    """


class IResourceSchema(Interface):

    title = schema.TextLine(
                title=_(u'Title'),
                description=_(u'Title of the resource'),
                default=u'',
                missing_value=u'',
                required=True)

    description = schema.Text(
                title=_(u'Description'),
                description=_(u'A medium-length description describing the '
                               'content and the purpose of the object'),
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
        """ Return a sequence of objects that the resource is the target of.
        """

    def getConcepts(predicates=None):
        """ Return a tuple of concepts related to self as parent concepts,
            optionally restricted to the predicates given.
        """

    def getConceptRelations(predicates=None, concepts=None):
        """ Return a sequence of relations to concepts assigned to self
            as parent concepts, optionally restricted to the predicates given
            or to a certain concept.
        """

    def assignConcept(concept, predicate):
        """ Assign an existing concept to self using the predicate given.
            The assigned concept will be a parent concept of self.

            The predicate defaults to the concept manager's default predicate.
        """

    def deassignConcept(concept, predicates=None):
        """ Remove the concept relations to the concept given from self,
            optionally restricting them to the predicates given.
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
                        'text/plain', 'text/xml', 'text/css'),
                default='text/restructured',
                required=True)


class IDocumentView(IDocumentSchema):
    """ Used for accessing a document via a node's target attribute"""


class IDocument(IDocumentSchema, IResource):
    """ A resource containing an editable body.
    """


# media asset is obsolete - replaced by plain Resource with
# resourceType = file.

class IMediaAssetView(IResourceSchema):
    """ Used for accessing a media asset via a node's target attribute"""


class IMediaAsset(IResourceSchema, IResource, IBaseAsset):
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

    viewName = schema.TextLine(
        title=_(u'View name'),
        description=_(u'Name of a special view be used for presenting '
                       'this object.'),
        default=u'',
        required=False)


class IBaseNode(IOrderedContainer):
    """ Common abstract base class for different types of nodes
    """

    def getLoopsRoot():
        """ Return the loops root object.
        """


class INodeSchema(IView):

    nodeType = schema.Choice(
        title=_(u'Node Type'),
        description=_(u'Type of the node'),
        source=util.KeywordVocabulary((
                ('text', _(u'Text')),
                ('page', _(u'Page')),
                ('menu', _(u'Menu')),
                ('info', _(u'Info')),
            )),
        default='info',
        required=True)

    body = schema.Text(
        title=_(u'Body'),
        description=_(u'Textual body that may be shown in addition to '
                       'or instead of information coming from the target'),
        default=u'',
        required=False)

    contentType = Attribute(_(u'Content type (format) of the body'))


class INode(INodeSchema, IBaseNode):
    """ A node is a view that may contain other views, thus building a
        menu or folder hierarchy.

        A node may be a content object on its own; for this reason it
        has a body attribute that may be shown e.g. on web pages.
    """
    contains(IView)

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

    def isMenuItem():
        """ Return True if this object is a menu item.
        """

    def getPageItems():
        """ Return the page items belonging to this object.
        """

    def getTextItems():
        """ Return the text items belonging to this object.
        """


class INodeAdapter(Interface):
    """ Base interface for adapters that provide nodes with additional
        capabilities.
    """


class IViewManager(ILoopsObject, IBaseNode):
    """ A manager/container for views.
    """
    contains(IView)


class INodeContained(Interface):
    containers(INode, IViewManager)


# record manager interfaces

class IRecordManager(ILoopsObject):
    contains(ITrackingStorage)


# the loops top-level container

class ILoops(ILoopsObject):
    """ The top-level object of a loops site.
    """
    contains(IConceptManager, IResourceManager, IViewManager)

    skinName = schema.ASCIILine(
        title=_(u'Skin Name'),
        description=_(u'Name of the skin to use'),
        default='',
        required=False)

    options = schema.List(
        title=_(u'Options'),
        description=_(u'Additional settings.'),
        value_type=schema.TextLine(),
        default=[],
        required=False)

    def getLoopsUri(obj):
        """ Return the relativ path to obj, starting with '.loops/...'.
        """

    def loopsTraverse(uri):
        """ Retrieve object specified by the loops uri (starting with
        '.loops/') given.
        """

    def getConceptManager():
        """ Return the (default) concept manager.
        """

    def getResourceManager():
        """ Return the (default) resource manager.
        """

    def getViewManager():
        """ Return the (default) view manager.
        """

    def getRecordManager():
        """ Return the (default) record manager.
        """


class ILoopsContained(Interface):
    containers(ILoops)


# relation interfaces

class ITargetRelation(IDyadicRelation):
    """ (Marker) interfaces for relations pointing to a target
        of a view or node.
    """


class IConceptRelation(IDyadicRelation):
    """ (Marker) interfaces for relations originating from a concept.
    """

    predicate = Attribute("A concept of type 'predicate' that defines the "
                    "type of the relation-")


# interfaces for catalog indexes

class IIndexAttributes(Interface):
    """ Attributes odr methods providing index values. Typically provided
        by an adapter.
    """

    def title():
        """ Return a text containing title and similar attributes to be
            indexed by a full-text index.
        """

    def text():
        """ Return a text with all parts to be indexed by a full-text index.
        """

    def type():
        """ Return a string that identifies the type of the object.
        """


# types stuff

class ITypeConcept(IConceptSchema):
    """ Concepts of type 'type' should be adaptable to this interface.
    """

    typeInterface = schema.Choice(
        title=_(u'Type Interface'),
        description=_(u'An interface that objects of this type can '
                        'be adapted to'),
        default=None,
        source='loops.TypeInterfaceSource',
        required=False)

    viewName = schema.TextLine(
        title=_(u'View Name'),
        description=_(u'Name of a special view be used for presenting '
                       'objects of this type.'),
        default=u'',
        required=False)

    options = schema.List(
        title=_(u'Options'),
        description=_(u'Additional settings.'),
        value_type=schema.TextLine(),
        default=[],
        required=False)

    # storage = schema.Choice()


# predicates

class IPredicate(IConceptSchema):
    """ Provided by predicates (predicate concepts that specify relation types),
        i.e. concepts of type 'predicate' should be adaptable to this interface.
    """

    predicateInterface = schema.Choice(
        title=_(u'Predicate Interface'),
        description=_(u'Optional: allows specification of additional '
                    'attributes of relations that are instances of this '
                    'predicate.'),
        default=None,
        source='loops.PredicateInterfaceSource',
        required=False)


class IMappingAttributeRelation(IConceptSchema):
    """ A relation based on a predicate ('mappingAttribute') that provides
        values for an attribute name on a parent and a corresponding
        identifiers on the the child objects that will be used as keys
        on the parent's mapping attribute.

        These values should be indexed by the relation registry to provide
        direct access.
    """

    attrName = schema.TextLine(
        title=_(u'Attribute Name'),
        description=_(u'Name of the mapping attribute this predicate '
                    'represents on the parent concept.'),
        required=True)

    attrIdentifier = schema.TextLine(
        title=_(u'Child Identifier'),
        description=_(u'Identifier of the child that may be used as a '
                    'key on the parent\'s mapping attribute.'),
        required=True)


# resources

class IResourceAdapter(IBaseResourceSchema):
    """ Base interface for adapters for resources. This is the base interface
        of the interfaces to be used as typeInterface attribute on type concepts
        specifying resource types.
    """


class IFile(IResourceAdapter, IResourceSchema):
    """ A media asset that is not shown on a (web) page like an image but
        may be downloaded instead.
    """

    data = schema.Bytes(
                title=_(u'Data'),
                description=_(u'Resource raw data'),
                default='',
                missing_value='',
                required=False)
    localFilename = Attribute('Filename provided during upload.')


class IStorageInfo(Interface):

    storageName = schema.BytesLine(
                title=_(u'Storage Name'),
                description=_(u'The name of a storage utility used for this '
                        'object.'),
                default='',
                missing_value='',
                required=False)

    storageParams = schema.BytesLine(
                title=_(u'Storage Parameters'),
                description=_(u'Information used to address the external '
                        'storage, e.g. a filename or path.'),
                default='',
                missing_value='',
                required=False)

    externalAddress = schema.BytesLine(
                title=_(u'External Address'),
                description=_(u'The full address for accessing the object '
                        'on the external storage, e.g. a filename or path.'),
                default='',
                missing_value='',
                required=False)


class IExternalFile(IFile):
#class IExternalFile(IFile, IStorageInfo):
    """ A file whose content (data attribute) is not stored in the ZODB
        but somewhere else, typically in the file system.
    """

    data = schema.Bytes(
                title=_(u'Data'),
                description=_(u'Resource raw data'),
                default='',
                missing_value='',
                required=False)


class IImage(IResourceAdapter):
    """ A media asset that may be embedded in a (web) page as an image.
    """


class ITextDocument(IResourceAdapter, IDocumentSchema):
    """ A resource containing some sort of plain text that may be rendered and
        edited without necessarily involving a special external application
        (like e.g. OpenOffice); typical content types are text/html, text/xml,
        text/restructured, etc.
    """

class INote(ITextDocument):
    """ Typically a short piece of text; in addition a note may contain
        a URL linking it to more information.
    """

    linkUrl = schema.TextLine(
                title=_(u'Link URL'),
                description=_(u'An (optional) link associated with this note'),
                default=u'http://',
                required=False)
    linkText = schema.TextLine(
                title=_(u'Link text'),
                description=_(u'Text for "more..." link.'),
                required=False,)



# events

class IAssignmentEvent(IObjectEvent):
    """ A child or resource has been assigned to a concept.
    """

    relation = Attribute('The relation that has been assigned to the concept.')


class IDeassignmentEvent(IObjectEvent):
    """ A child or resource will be deassigned from a concept.
    """

    relation = Attribute('The relation that will be removed from the concept.')


# view configurator stuff

class IViewConfiguratorSchema(Interface):

    skinName = schema.TextLine(
        title=_(u'Skin Name'),
        description=_(u'Name of the skin to use for this part of the site'),
        default=u'',
        required=False)

    options = schema.List(
        title=_(u'Options'),
        description=_(u'Additional settings.'),
        value_type=schema.TextLine(),
        default=[],
        required=False)


