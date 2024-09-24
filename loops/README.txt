===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

The loops platform consists up of three basic types of objects:

(1) concepts: simple interconnected objects usually representing
    meta-information
(2) resources: (possibly large) atomic objects like documents and files
(3) views: objects (usually hierarchically organized nodes) providing
    access to and presenting concepts or resources

Note that there is another doctest file called helpers.txt that deals
with lower-level aspects like type or state management.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from zope import component
  >>> from zope.interface import Interface
  >>> from zope.publisher.browser import TestRequest
  >>> from zope.traversing.api import getName

Let's also import some common stuff needed later.

  >>> from loops.common import adapted, baseObject
  >>> from loops.setup import addAndConfigureObject


Concepts and Relations
======================

Let's start with creating a few example concepts, putting them in a
top-level loops container and a concept manager:

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> #sorted(concepts)
  >>> #sorted(resources)
  >>> len(concepts) + len(resources)
  13

  >>> loopsRoot = site['loops']

  >>> from loops.concept import ConceptManager, Concept
  >>> cc1 = Concept()
  >>> concepts['cc1'] = cc1
  >>> cc1.title
  ''
  >>> loopsRoot.getLoopsUri(cc1)
  '.loops/concepts/cc1'

  >>> cc2 = Concept('Zope 3')
  >>> concepts['cc2'] = cc2
  >>> cc2.title
  'Zope 3'

Now we want to relate the second concept to the first one.

  >>> from cybertools.relation.registry import RelationRegistry

As relationships are based on predicates that are themselves concepts we
also need a default predicate concept; the default name for this is
'standard'. It has already been created during setup.

Now we can assign the concept c2 as a child to c1 (using the standard
ConceptRelation):

  >>> cc1.assignChild(cc2)

We can now ask our concepts for their related child and parent concepts:

  >>> [getName(c) for c in cc1.getChildren()]
  ['cc2']
  >>> len(cc1.getParents())
  0
  >>> [getName(p) for p in cc2.getParents()]
  ['cc1']

  >>> len(cc2.getChildren())
  0

Each concept should have a concept type; this is in fact provided by a
relation to a special kind of concept object with the magic name 'type'.
This type object is its own type. The type relations themselves are of
a special predicate 'hasType'.

  >>> typeObject = concepts['type']
  >>> typeObject.setConceptType(typeObject)
  >>> typeObject.getConceptType().title
  'Type'

  >>> concepts['unknown'] = Concept('Unknown Type')
  >>> unknown = concepts['unknown']
  >>> unknown.setConceptType(typeObject)
  >>> unknown.getConceptType().title
  'Type'

  >>> cc1.setConceptType(unknown)
  >>> cc1.getConceptType().title
  'Unknown Type'

  >>> concepts['topic'] = Concept('Topic')
  >>> topic = concepts['topic']
  >>> topic.setConceptType(typeObject)
  >>> cc1.setConceptType(topic)
  >>> cc1.getConceptType().title
  'Topic'

We get a list of types using the ConceptTypeSourceList.
In order for the type machinery to work we first have to provide a
type manager.

  >>> from cybertools.typology.interfaces import ITypeManager
  >>> from loops.interfaces import ILoopsObject
  >>> from loops.type import LoopsTypeManager, LoopsType
  >>> component.provideAdapter(LoopsTypeManager, (ILoopsObject,), ITypeManager)

  >>> from loops.type import TypeConcept
  >>> component.provideAdapter(TypeConcept)

  >>> from loops.concept import ConceptTypeSourceList
  >>> types = ConceptTypeSourceList(cc1)
  >>> sorted(t.title for t in types)
  ['Customer', 'Domain', 'Predicate', 'Topic', 'Type', 'Unknown Type']

Using a PredicateSourceList we can retrieve a list of the available
predicates.

  >>> from loops.concept import PredicateSourceList
  >>> predicates = PredicateSourceList(cc1)

Note that the 'hasType' predicate is suppressed from this list as the
corresponding relation is only assigned via the conceptType attribute:

  >>> sorted(t.title for t in predicates)
  ['subobject']

Concept Views
-------------

  >>> from loops.browser.concept import ConceptView, ConceptConfigureView
  >>> view = ConceptView(cc1, TestRequest())

  >>> children = list(view.children())
  >>> [c.title for c in children]
  ['Zope 3']

The token attribute provided with the items returned by the children() and
parents() methods identifies identifies not only the item itself but
also the relationship to the context object using a combination
of URIs to item and the predicate of the relationship:

  >>> [c.token for c in children]
  ['.loops/concepts/cc2:.loops/concepts/standard']

There is also a concept configuration view that allows updating the
underlying context object:

  >>> cc3 = Concept('loops for Zope 3')
  >>> concepts['cc3'] = cc3
  >>> view = ConceptConfigureView(cc1,
  ...           TestRequest(action='assign', tokens=['.loops/concepts/cc3']))
  >>> view.update()
  True
  >>> sorted(c.title for c in cc1.getChildren())
  ['Zope 3', 'loops for Zope 3']

  >>> input = {'action': 'remove', 'qualifier': 'children',
  ...          'form.button.submit': 'Remove Chiildren',
  ...           'tokens': ['.loops/concepts/cc2:.loops/concepts/standard']}
  >>> view = ConceptConfigureView(cc1, TestRequest(form=input))
  >>> view.update()
  True
  >>> sorted(c.title for c in cc1.getChildren())
  ['loops for Zope 3']

We can also create a new concept and assign it.

  >>> params = {'action': 'create', 'create.name': 'cc4',
  ...           'create.title': 'New concept',
  ...           'create.type': '.loops/concepts/topic'}
  >>> view = ConceptConfigureView(cc1, TestRequest(**params))
  >>> view.update()
  True
  >>> sorted(c.title for c in cc1.getChildren())
  ['New concept', 'loops for Zope 3']

The concept configuration view provides methods for displaying concept
types and predicates.

  >>> from zope.publisher.interfaces.browser import IBrowserRequest
  >>> from loops.browser.common import LoopsTerms
  >>> from zope.app.form.browser.interfaces import ITerms
  >>> from zope.schema.interfaces import IIterableSource
  >>> component.provideAdapter(LoopsTerms, (IIterableSource, IBrowserRequest), ITerms)

  >>> sorted((t.title, t.token) for t in view.conceptTypes())
  [('Customer', '.loops/concepts/customer'),
   ('Domain', '.loops/concepts/domain'),
   ('Predicate', '.loops/concepts/predicate'),
   ('Topic', '.loops/concepts/topic'),
   ('Type', '.loops/concepts/type'),
   ('Unknown Type', '.loops/concepts/unknown')]

  >>> sorted((t.title, t.token) for t in view.predicates())
  [('subobject', '.loops/concepts/standard')]

Index attributes adapter
------------------------

  >>> from loops.concept import IndexAttributes
  >>> idx = IndexAttributes(cc2)
  >>> idx.text()
  'cc2 Zope 3'

  >>> idx.title()
  'cc2 Zope 3'


Resources and what they have to do with Concepts
================================================

  >>> from loops.interfaces import IResource, IDocument

We first need a resource manager:

  >>> from loops.resource import ResourceManager, Resource

A common type of resource is a document:

  >>> from loops.interfaces import IDocument
  >>> from loops.resource import Document
  >>> doc1 = Document('Zope Info')
  >>> resources['doc1'] = doc1
  >>> doc1.title
  'Zope Info'
  >>> doc1.data
  ''
  >>> doc1.contentType
  ''

We can also directly use Resource objects; these behave like files.
In fact, by using resource types we can explicitly assign a resource
the 'file' type, but we will use this feature later:

  >>> img = Resource('A png Image')

For testing we use some simple files from the tests directory:

  >>> from loops import tests
  >>> import os
  >>> path = os.path.join(*tests.__path__)
  >>> img.data = open(os.path.join(path, 'test_icon.png')).read()
  >>> img.getSize()
  381
  >>> img.getImageSize()
  (16, 16)
  >>> img.contentType
  'image/png'

  >>> pdf = Resource('A pdf File')
  >>> pdf.data = open(os.path.join(path, 'test.pdf')).read()
  >>> pdf.getSize()
  25862
  >>> pdf.getImageSize()
  (-1, -1)
  >>> pdf.contentType
  'application/pdf'

We can associate a resource with a concept by assigning it to the concept:

  >>> cc1.assignResource(doc1)
  >>> res = cc1.getResources()
  >>> list(res)
  [<loops.resource.Document ...>]

The concept configuration view discussed above also manages the relations
from concepts to resources:

  >>> len(cc1.getResources())
  1
  >>> form = {'action': 'remove', 'qualifier': 'resources',
  ...         'form.button.submit': 'Remove Resources',
  ...         'tokens': ['.loops/resources/doc1:.loops/concepts/standard']}
  >>> view = ConceptConfigureView(cc1, TestRequest(form=form))
  >>> [getName(r.context) for r in view.resources()]
  ['doc1']
  >>> view.update()
  True
  >>> len(cc1.getResources())
  0
  >>> form = dict(action='assign', assignAs='resource',
  ...               tokens=['.loops/resources/doc1'])
  >>> view = ConceptConfigureView(cc1, TestRequest(form=form))
  >>> view.update()
  True
  >>> len(cc1.getResources())
  1

These relations may also be managed starting from a resource using
the resource configuration view:

  >>> from loops.browser.resource import ResourceConfigureView

Index attributes adapter
------------------------

  >>> from loops.resource import IndexAttributes
  >>> from loops.type import LoopsType
  >>> component.provideAdapter(LoopsType)
  >>> from loops.resource import FileAdapter
  >>> from loops.interfaces import IFile
  >>> component.provideAdapter(FileAdapter, provides=IFile)
  >>> idx = IndexAttributes(doc1)
  >>> idx.text()
  ''

  >>> idx.title()
  'doc1 Zope Info'


Views/Nodes: Menus, Menu Items, Listings, Pages, etc
====================================================

Note: the term "view" here is not directly related to the special
Zope 3 term "view" (a multiadapter for presentation purposes) but basically
bears the common sense meaning: an object (that may be persistent or
created on the fly) that provides a view to content of whatever kind.

Views (or nodes - that's the only type of views existing at the moment)
thus provide the presentation space for concepts and resources, i.e. visitors
of a site only see views or nodes but never concepts or resources directly;
the views or nodes, however, present informations coming from the concepts
or resources they are related to.

The view manager has already been created during setup.

  >>> from loops.view import ViewManager, Node

The view space is typically built up with nodes; a node may be a top-level
menu that may contain other nodes as menu or content items:

  >>> m1 = views['m1'] = Node('Menu')
  >>> m11 = m1['m11'] = Node('Zope')
  >>> m111 = m11['m111'] = Node('Zope in General')
  >>> m112 = m11['m112'] = Node('Zope 3')
  >>> m112.title
  'Zope 3'
  >>> m112.description
  ''

There are a few convienence methods for accessing parent and child nodes:

  >>> m1.getParentNode() is None
  True
  >>> m11.getParentNode() is m1
  True
  >>> [getName(child) for child in m11.getChildNodes()]
  ['m111', 'm112']

What is returned by these may be controlled by the nodeType attribute:

  >>> m1.nodeType = 'menu'
  >>> m11.nodeType = 'page'
  >>> m11.getParentNode('menu') is m1
  True
  >>> m11.getParentNode('page') is None
  True
  >>> m111.nodeType = 'info'
  >>> m112.nodeType = 'text'
  >>> len(list(m11.getChildNodes('text')))
  1

There are also shortcut methods to retrieve certain types of nodes
in a simple and logical way:

  >>> m1.getMenu() is m1
  True
  >>> m111.getMenu() is m1
  True
  >>> m1.getPage() is m1
  True
  >>> m111.getPage() is m111
  True
  >>> m112.getPage() is m11
  True
  >>> len(list(m1.getMenuItems()))
  1
  >>> len(list(m11.getMenuItems()))
  0
  >>> len(list(m111.getMenuItems()))
  0
  >>> len(list(m1.getTextItems()))
  0
  >>> len(list(m11.getTextItems()))
  1
  >>> len(list(m111.getTextItems()))
  0

Targets
-------

We can associate a node with a concept or directly with a resource via the
view class's target attribute. (We also have to supply a subscriber to
IRelationInvalidatedEvent to make sure associated actions will be carried
out - this is usually done through ZCML.)

  >>> from loops.util import removeTargetRelation
  >>> from loops.interfaces import ITargetRelation
  >>> from cybertools.relation.interfaces import IRelationInvalidatedEvent
  >>> component.getSiteManager().registerHandler(removeTargetRelation,
  ...                       (ITargetRelation, IRelationInvalidatedEvent))

  >>> m111.target = cc1
  >>> m111.target is cc1
  True
  >>> m111.target = cc1
  >>> m111.target is cc1
  True
  >>> m111.target = cc2
  >>> m111.target is cc2
  True

A resource provides access to the associated views/nodes via the
getClients() method:

  >>> len(doc1.getClients())
  0
  >>> m112.target = doc1
  >>> nodes = doc1.getClients()
  >>> nodes[0] is m112
  True

Node Views
----------

  >>> from loops.interfaces import INode
  >>> from loops.browser.node import NodeView
  >>> view = NodeView(m11, TestRequest())

  >>> page = view.page
  >>> items = page.textItems
  >>> for item in items:
  ...     print(item.url, item.editable)
  http://127.0.0.1/loops/views/m1/m11/m112 False

  >>> menu = view.menu
  >>> items = menu.menuItems
  >>> for item in items:
  ...     print(item.url, view.selected(item))
  http://127.0.0.1/loops/views/m1/m11 True

A NodeView provides an itemNum attribute that may be used to count elements
appearing on a page. Thus a template may construct unique ids for elements.

  >>> view.itemNum
  1
  >>> view.itemNum
  2

There is an openEditWindow() method that returns a JavaScript call for
opening a new browser window for editing; but only if the view is
editable:

  >>> page.openEditWindow()
  ''
  >>> page.editable = True
  >>> page.openEditWindow()
  "openEditWindow('http://127.0.0.1/loops/views/m1/m11/@@edit.html')"
  >>> page.openEditWindow('configure.html')
  "openEditWindow('http://127.0.0.1/loops/views/m1/m11/@@configure.html')"

A Node and its Target
---------------------

When configuring a node you may specify what you want to do with respect
to the node's target: associate an existing one or create a new one. When
accessing a target via a node view it is usually wrapped in a corresponding
view; these views we have to provide as multi-adapters:

  >>> from loops.browser.node import ConfigureView
  >>> from loops.browser.resource import DocumentView, ResourceView
  >>> component.provideAdapter(DocumentView, (IDocument, IBrowserRequest), Interface)
  >>> component.provideAdapter(ResourceView, (IResource, IBrowserRequest), Interface)

  >>> form = {'action': 'create', 'create.title': 'New Resource',
  ...         'create.type': 'loops.resource.MediaAsset',}
  >>> view = ConfigureView(m111, TestRequest(form = form))
  >>> tt = view.targetTypes()
  >>> len(tt)
  9
  >>> sorted((t.token, t.title) for t in view.targetTypes())[1]
  ('.loops/concepts/domain', 'Domain')
  >>> view.update()
  True
  >>> sorted(resources.keys())
  ['d001.txt', 'd002.txt', 'd003.txt', 'doc1', 'm1.m11.m111']

  >>> view.target.title, view.target.token
  ('New Resource', '.loops/resources/m1.m11.m111')

A node object provides the targetSchema of its target:

  >>> from loops.interfaces import IDocumentView
  >>> from loops.interfaces import IMediaAssetView
  >>> IDocumentView.providedBy(m111)
  False
  >>> IMediaAssetView.providedBy(m111)
  True
  >>> m111.target = None
  >>> IDocumentView.providedBy(m111)
  False
  >>> m111.target = resources['doc1']
  >>> IDocumentView.providedBy(m111)
  True
  >>> IMediaAssetView.providedBy(m111)
  False

A node's target is rendered using the NodeView's renderTargetBody()
method. This makes use of a browser view registered for the target interface,
and of a lot of other stuff needed for the rendering machine.
(Note: renderTarget is obsolete - we now use a macro provided by the target's
view for rendering.)

  >>> from zope.component.interfaces import IFactory
  >>> from zope.app.renderer import rest
  >>> component.provideUtility(rest.ReStructuredTextSourceFactory, IFactory,
  ...                          'zope.source.rest')
  >>> component.provideAdapter(rest.ReStructuredTextToHTMLRenderer,
  ...                (rest.IReStructuredTextSource, IBrowserRequest), Interface)

  >>> m112.target = doc1

  >>> component.provideAdapter(LoopsType)
  >>> view = NodeView(m112, TestRequest())
  >>> view.renderTarget()
  '<pre></pre>'
  >>> doc1.data = 'Test data\n\nAnother paragraph'
  >>> view.renderTarget()
  '<pre>Test data\n\nAnother paragraph</pre>'

  >>> doc1.contentType = 'text/restructured'
  >>> doc1.data = 'Test data\n\nAnother `paragraph <para>`_'

  >>> from loops.wiki.base import wikiLinksActive
  >>> wikiLinksActive(loopsRoot)
  False

  >>> view.renderTarget()
  '<p>Test data</p>\n<p>Another <a class="reference external" href="para">paragraph</a></p>\n'

'<p>Test data</p>\n<p>Another <a class="reference create"
    href="http://127.0.0.1/loops/wiki/create.html?linkid=0000001">?paragraph</a></p>\n'

  >>> #links = loopsRoot.getRecordManager()['links']
  >>> #links['0000001']

<Link ['42', 1, '', '... ...', 'para', None]: {}>

If the target object is removed from its container all references
to it are removed as well. (To make this work we have to handle
the IObjectRemovedEvent; this is usually done via ZCML in the
cybertools.relation package.)

  >>> from zope.app.container.interfaces import IObjectRemovedEvent
  >>> from zope.interface import Interface
  >>> from cybertools.relation.registry import invalidateRelations
  >>> component.getSiteManager().registerHandler(invalidateRelations,
  ...                                      (Interface, IObjectRemovedEvent))

  >>> del resources['doc1']
  >>> m111.target
  >>> IMediaAssetView.providedBy(m111)
  False

Target views
------------

We can directly retrieve a target's view by using the NodeView's
``targetObjectView`` property. If the target is a concept we get a ConceptView
that provides methods e.g. for retrieving the concept's relations.
These are again wrapped as views, i.e. as instances of the
ConceptRelationView class.

  >>> from loops.interfaces import IConcept
  >>> component.provideAdapter(ConceptView, (IConcept, IBrowserRequest), Interface)

  >>> m112.target = cc1
  >>> view = NodeView(m112, TestRequest())
  >>> childRels = list(view.targetObjectView.children())
  >>> childRels[0]
  <loops.browser.concept.ConceptRelationView object ...>

A fairly useful method for providing links to target objects of a node
is ``NodeView.getUrlForTarget()`` that expects a ConceptView, ResourceView,
or ConceptRelationView as its argument.

  >>> view.getUrlForTarget(childRels[0])
  'http://127.0.0.1/loops/views/m1/m11/m112/.37'

Actions
-------

  >>> from cybertools.browser.liquid.controller import Controller
  >>> request = TestRequest()
  >>> view = NodeView(m112, request)
  >>> view.controller = Controller(view, request)
  >>> #view.setupController()

  >>> actions = view.getAllowedActions('portlet')
  >>> len(actions)
  2

Clean-up:

  >>> m112.target = None

Ordering Nodes
--------------

Note: this functionality has been moved to cybertools.container; we
include some testing here to make sure it still works and give a short
demonstration.

Let's add some more nodes and reorder them:

  >>> m113 = Node()
  >>> m11['m113'] = m113
  >>> m114 = Node()
  >>> m11['m114'] = m114
  >>> m11.keys()
  ['m111', 'm112', 'm113', 'm114']

A special management view provides methods for moving objects down, up,
to the bottom, and to the top.

  >>> from cybertools.container.ordered import OrderedContainerView
  >>> view = OrderedContainerView(m11, TestRequest())
  >>> view.move_bottom(('m113',))
  >>> m11.keys()
  ['m111', 'm112', 'm114', 'm113']
  >>> view.move_up(('m114',), 1)
  >>> m11.keys()
  ['m111', 'm114', 'm112', 'm113']


Breadcrumbs
-----------

  >>> view = NodeView(m112, TestRequest())
  >>> view.breadcrumbs()
  []

  >>> loopsRoot.options = ['showBreadcrumbs']
  >>> m114.nodeType = 'page'
  >>> m114.target = cc1
  >>> request = TestRequest()
  >>> view = NodeView(m114, request)
  >>> request.annotations.setdefault('loops.view', {})['nodeView'] = view
  >>> view.breadcrumbs()
  [{'url': 'http://127.0.0.1/loops/views/m1', 'label': 'Menu'},
   {'url': 'http://127.0.0.1/loops/views/m1/m11', 'label': 'Zope'},
   {'url': 'http://127.0.0.1/loops/views/m1/m11/m114', 'label': ''}]


End-user Forms and Special Views
================================

The browser.form and related modules provide additional support for forms
that are shown in the end-user interface.

Creating an object
------------------

  >>> from loops.common import NameChooser
  >>> from loops.browser.form import CreateObjectForm, CreateObject
  >>> form = CreateObjectForm(m112, TestRequest())

The form provides a set of data entry fields derived from the interface
associated with the new object's resource (or concept) type.

In addition it allows to assign concepts as parents to the object. Beside
an integrated free search for concepts to assign there may be a list of
preset concepts, e.g. depending on the target of the current node:

  >>> form.assignments
  ()
  >>> m112.target = cc1
  >>> form = CreateObjectForm(m112, TestRequest())
  >>> form.assignments
  (<...ConceptRelationView object ...>,)

There also may be preset concept types that directly provide lists of
concepts to select from.

To show this let's start with a new type, the customer type, that has
been created during setup.

  >>> customer = concepts['customer']
  >>> customer.conceptType = concepts.getTypeConcept()
  >>> from loops.type import ConceptType, TypeConcept
  >>> custType = TypeConcept(customer)
  >>> custType.options
  []
  >>> cust1 = concepts['cust1'] = Concept('Zope Corporation')
  >>> cust2 = concepts['cust2'] = Concept('cyberconcepts')
  >>> for c in (cust1, cust2): c.conceptType = customer
  >>> custType.options = ('qualifier:assign',)
  >>> ConceptType(cust1).qualifiers
  ('concept', 'assign')

  >>> form = CreateObjectForm(m112, TestRequest())
  >>> form.presetTypesForAssignment
  [{'token': 'loops:concept:customer', 'title': 'Customer'}]

If the node's target is a type concept we don't get any assignments because
it does not make much sense to assign resources or other concepts as
children to type concepts.

  >>> m112.target = customer
  >>> form = CreateObjectForm(m112, TestRequest())
  >>> form.assignments
  ()

OK, so much about the form - now we want to create a new object based
on data provided in this form:

  >>> from loops.interfaces import INote, ITypeConcept
  >>> from loops.type import TypeConcept
  >>> from loops.resource import NoteAdapter
  >>> component.provideAdapter(TypeConcept)
  >>> component.provideAdapter(NoteAdapter, provides=INote)
  >>> note_tc = concepts['note']

  >>> component.provideAdapter(NameChooser)
  >>> request = TestRequest(form={'title': 'Test Note',
  ...                             'form.type': '.loops/concepts/note',
  ...                             'contentType': 'text/restructured',
  ...                             'linkUrl': 'http://'})
  >>> view = NodeView(m112, request)
  >>> cont = CreateObject(view, request)
  >>> cont.update()
  False
  >>> sorted(resources.keys())
  [...'test_note'...]
  >>> resources['test_note'].title
  'Test Note'

If there is a concept selected in the combo box we assign this to the newly
created object:

  >>> from loops import util
  >>> topicUid = util.getUidForObject(topic)
  >>> predicateUid = util.getUidForObject(concepts.getDefaultPredicate())
  >>> request = TestRequest(form={'title': 'Test Note',
  ...                             'form.type': '.loops/concepts/note',
  ...                             'form.assignments.selected':
  ...                                   [':'.join((topicUid, predicateUid))]})
  >>> view = NodeView(m112, request)
  >>> cont = CreateObject(view, request)
  >>> cont.update()
  False
  >>> sorted(resources.keys())
  [...'test_note-2'...]
  >>> note = resources['test_note-2']
  >>> sorted(t.__name__ for t in note.getConcepts())
  ['note', 'topic']

When creating an object its name may be automatically generated using the title
of the object. Let's make sure that the name chooser also handles special
and possibly critcal cases:

  >>> nc = NameChooser(resources)
  >>> nc.chooseName('', Resource('abc: (cde)'))
  'abc__cde'
  >>> nc.chooseName('', Resource('\xdcml\xe4ut'))
  'uemlaeut'
  >>> nc.chooseName('', Resource('A very very loooooong title'))
  'a_title'

Editing an Object
-----------------

  >>> from loops.browser.form import EditObjectForm, EditObject
  >>> m112.target = resources['test_note']
  >>> view = EditObjectForm(m112, TestRequest())

For rendering the form there are two techniques available: The
zope.formlib way and the new cybertools.composer.schema way. The
first one (possibly obsolete in the future) uses the ``setUp()`` call
that in turns calls formlibs ``setUpWidgets()``.

The new technique uses the ``fields`` and ``data`` attributes...

  >>> for f in view.fields:
  ...     print(f.name, f.fieldType, f.required, f.vocabulary)
  title textline True None
  data textarea False None
  contentType dropdown True <...SimpleVocabulary object...>
  linkUrl textline False None
  linkText textline False None

  >>> view.data
  {'title': 'Test Note', 'data': '', 'contentType': 'text/restructured', 
   'linkUrl': 'http://', 'linkText': ''}

The object is changed via a FormController adapter created for
a NodeView.

  >>> form = dict(
  ...     title='Test Note - changed',
  ...     contentType='text/plain',)
  >>> request = TestRequest(form=form)
  >>> view = NodeView(m112, request)
  >>> cont = EditObject(view, request)
  >>> cont.update()
  False
  >>> resources['test_note'].title
  'Test Note - changed'

Virtual Targets
---------------

From a node usually any object in the concept or resource space can
be accessed as a `virtual target`. This is done by putting ".targetNNN"
at the end of the URL, with NNN being the unique id of the concept
or resource.

  >>> from loops.browser.node import NodeTraverser

  >>> magic = '.target' + util.getUidForObject(resources['d001.txt'])
  >>> url = 'http://127.0.0.1/loops/views/m1/m11/m111/' + magic + '/@@node.html'
  >>> #request = TestRequest(environ=dict(SERVER_URL=url))
  >>> request = TestRequest()
  >>> NodeTraverser(m111, request).publishTraverse(request, magic)
  <loops.view.Node object ...>
  >>> view = NodeView(m111, request)
  >>> view.virtualTargetObject
  <loops.resource.Resource object ...>

A virtual target may be edited in the same way like directly assigned targets,
see above, "Editing an Object". In addition, target objects may be viewed
and edited in special ways, depending on the target object's type.

In order to provide suitable links for viewing or editing a target you may
ask a view which view and edit actions it supports. We directly use the
target object's view here:

  >>> actions = view.virtualTarget.getAllowedActions('object', page=view)
  >>> #actions[0].url

'http://127.0.0.1/loops/views/m1/m11/m111/.target23'

Special views
-------------

We may set a special view for a node by providing a view name.

  >>> from loops.browser.node import ListChildren
  >>> component.provideAdapter(ListChildren, (INode, IBrowserRequest), Interface,
  ...                          name='listchildren')

  >>> m112.viewName = 'listchildren?types=person'
  >>> view = NodeView(m112, TestRequest())

  >>> targetView = view.view

  >>> targetView.macroName
  'listchildren'

  >>> targetView.params
  {'types': ['person']}


Collecting Information about Parents
====================================

Sometimes, e.g. when checking permissions, it is important to collect
informations about all parents of an object.

  >>> parents = m113.getAllParents()
  >>> for p in parents:
  ...     print(p.object.title)
  Zope
  Menu

  >>> parents = resources['test_note'].getAllParents()
  >>> for p in parents:
  ...     print(p.object.title, len(p.relations))
  Note 1
  Type 2


Tables
======

  >>> from loops.table import IDataTable, DataTable
  >>> component.provideAdapter(DataTable)

Let's create the data table concept type and one example, a table that
relates ISO country codes with the full name of the country.

  >>> dtType = addAndConfigureObject(concepts, Concept, 'datatable',
  ...                   title='Data Table', conceptType=concepts['type'],
  ...                   typeInterface=IDataTable)
  >>> countries = adapted(addAndConfigureObject(concepts, Concept, 'countries',
  ...                   title='Countries', conceptType=concepts['datatable']))

  >>> countries.data['de'] = ['Germany']
  >>> countries.data['at'] = ['Austria']

  >>> sorted(adapted(concepts['countries']).data.items())
  [('at', ['Austria']), ('de', ['Germany'])]

  >>> countries.dataAsRecords()
  [{'key': 'at', 'value': 'Austria'}, {'key': 'de', 'value': 'Germany'}]

  >>> countries.getRowsByValue('value', 'Germany')
  [{'key': 'de', 'value': 'Germany'}]

The ``recordstable`` type is a variation of this datable type that contains
a simple list of records - without a key column. A record in this  type is a
dictionary with the field name as key and the field value as value.

  >>> from loops.table import IRecordsTable, RecordsTable
  >>> component.provideAdapter(RecordsTable, provides=IRecordsTable)

  >>> drType = addAndConfigureObject(concepts, Concept, 'recordstable',
  ...                   title='Records Table', conceptType=concepts['type'],
  ...                   typeInterface=IRecordsTable)

We just reuse the existing ``countries`` table and convert it to a records table.

  >>> baseObject(countries).setType(drType)

  >>> countries = adapted(concepts['countries'])

  >>> countries.data
  [{'key': 'at', 'value': 'Austria'}, {'key': 'de', 'value': 'Germany'}]


Caching
=======

To be done...

  >>> from loops.common import cached
  >>> obj = resources['test_note']
  >>> cxObj = cached(obj)
  >>> [p.object.title for p in cxObj.getAllParents()]
  ['Note', 'Type']


Security
========

  >>> from loops.security.browser import admin, audit


Paster Shell Utilities - Repair Scripts
=======================================

  >>> from loops.repair.base import removeRecords


Import/Export
=============

Obsolete - see package loops.external.


Fin de partie
=============

  >>> placefulTearDown()

