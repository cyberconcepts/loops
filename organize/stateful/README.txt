===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  >>> from zope import component
  >>> from zope.traversing.api import getName

First we set up a loops site with basic and example concepts and resources.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from loops.organize.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize')
  >>> from loops.expert.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']


Stateful Objects
================

A simple publishing workflow
----------------------------

Let's start with registering the states definitions and adapters needed.
The states definition (aka 'workflow') is registered as a utility; for
making an object statful we'll use an adapter.

  >>> from cybertools.stateful.interfaces import IStatesDefinition, IStateful
  >>> from cybertools.stateful.publishing import simplePublishing
  >>> component.provideUtility(simplePublishing(), name='simple_publishing')

  >>> from loops.organize.stateful.base import SimplePublishable
  >>> component.provideAdapter(SimplePublishable, name='simple_publishing')

We may now take a document and adapt it to IStateful so that we may
check the document's state and perform transitions to other states.

  >>> from loops.resource import Resource
  >>> from loops.setup import addAndConfigureObject
  >>> tText = concepts['textdocument']
  >>> doc01 = resources['doc01.txt'] = addAndConfigureObject(resources,
  ...                       Resource, 'doc01.txt', conceptType=tText)
  >>> statefulDoc01 = component.getAdapter(doc01, IStateful,
  ...                                      name='simple_publishing')

  >>> statefulDoc01.state
  'draft'

  >>> statefulDoc01.doTransition('publish')
  >>> statefulDoc01.state
  'published'

Let's check if the state is really stored in the underlying object and
not just kept in the adapter.

  >>> statefulDoc01_x = component.getAdapter(doc01, IStateful,
  ...                                        name='simple_publishing')

  >>> statefulDoc01.state
  'published'


Controlling classification quality
----------------------------------

We again first have to register states definitions and adapter classes.

  >>> from loops.organize.stateful.quality import classificationQuality
  >>> component.provideUtility(classificationQuality(),
  ...                          name='classification_quality')
  >>> from loops.organize.stateful.quality import ClassificationQualityCheckable
  >>> component.provideAdapter(ClassificationQualityCheckable,
  ...                          name='classification_quality')
  >>> from loops.organize.stateful.quality import assign, deassign
  >>> component.provideHandler(assign)
  >>> component.provideHandler(deassign)

Now we can get a stateful adapter for a resource.

  >>> qcheckedDoc01 = component.getAdapter(doc01, IStateful,
  ...                                      name='classification_quality')
  >>> qcheckedDoc01.state
  'new'

Let's create two customer objects to be used for classification of resources
later.

  >>> tCustomer = concepts['customer']
  >>> from loops.concept import Concept
  >>> c01 = addAndConfigureObject(concepts, Concept, 'c01', conceptType=tCustomer,
  ...                   title='im publishing')
  >>> c02 = addAndConfigureObject(concepts, Concept, 'c02', conceptType=tCustomer,
  ...                   title='DocFive')

When we change the concept assignments of the resource - i.e. its classification
- the classification quality state changes automatically

  >>> c01.assignResource(doc01)
  >>> qcheckedDoc01 = component.getAdapter(doc01, IStateful,
  ...                                      name='classification_quality')
  >>> qcheckedDoc01.state
  'classified'

  >>> c02.assignResource(doc01)
  >>> qcheckedDoc01.state
  'classified'

In order to mark the classification as "verified" (i.e. quality-checked)
we have to perform the corresponding transition explicitly.

  >>> qcheckedDoc01.doTransition('verify')
  >>> qcheckedDoc01.state
  'verified'

Upon later changes of classification the "verified" state gets lost again.

  >>> c02.deassignResource(doc01)
  >>> qcheckedDoc01.state
  'classified'

  >>> c01.deassignResource(doc01)
  >>> qcheckedDoc01.state
  'unclassified'

Changing states when editing
----------------------------

We first need a node that provides us access to the resource as its target

  >>> from loops.view import Node
  >>> node = addAndConfigureObject(views, Node, 'node', target=doc01)

  >>> from loops.browser.form import EditObjectForm, EditObject
  >>> from zope.publisher.browser import TestRequest

The form view gives us access to the states of the object.

  >>> loopsRoot.options = ['organize.stateful.resource:'
  ...           'classification_quality,simple_publishing']

  >>> form = EditObjectForm(node, TestRequest())
  >>> for st in form.states:
  ...     sto = st.getStateObject()
  ...     transitions = st.getAvailableTransitions()
  ...     userTrans = st.getAvailableTransitionsForUser()
  ...     print st.statesDefinition, sto.title, [t.title for t in transitions],
  ...     print [t.title for t in userTrans]
  classification_quality unclassified ['classify', 'verify'] ['verify']
  simple_publishing published ['retract', 'archive'] ['retract', 'archive']

Let's now update the form.

  >>> input = {'state.classification_quality': 'verify'}
  >>> proc = EditObject(form, TestRequest(form=input))
  >>> proc.update()
  False

  >>> qcheckedDoc01.state
  'verified'

Querying objects by state
-------------------------

  >>> stateQuery = addAndConfigureObject(concepts, Concept, 'state_query',
  ...                   conceptType=concepts['query'], viewName='select_state.html')
  >>> from loops.organize.stateful.browser import StateQuery
  >>> view = StateQuery(stateQuery, TestRequest())

  >>> view.rcStatesDefinitions
  {'concept': [], 'resource': [...StatesDefinition..., ...StatesDefinition...]}

  >>> input = {'state.resource.classification_quality': ['verified']}
  >>> view = StateQuery(stateQuery, TestRequest(form=input))
  >>> view.selectedStates
  {'state.resource.classification_quality': ['verified']}

  >>> list(view.results)
  [<...>]


Person States
=============

  >>> from loops.organize.stateful.person import personStates


Task States
===========

  >>> from loops.organize.stateful.task import taskStates, publishableTask


Fin de partie
=============

  >>> placefulTearDown()
