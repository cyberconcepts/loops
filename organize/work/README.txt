===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

Let's do some basic setup

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)
  >>> from zope import component, interface
  >>> from zope.publisher.browser import TestRequest

and set up a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from loops.organize.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize')
  >>> from loops.organize.work.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize.work')

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()


Work Items - Plannning and Recording Activities for Tasks
=========================================================

  >>> loopsRoot = concepts.getLoopsRoot()
  >>> records = loopsRoot.getRecordManager()

More setup
----------

In order to be able to login and store favorites and other personal data
we have to prepare our environment. We need some basic adapter registrations,
and a pluggable authentication utility with a principal folder.

  >>> from loops.organize.tests import setupObjectsForTesting
  >>> setupData = setupObjectsForTesting(site, concepts)
  >>> johnC = setupData.johnC

We also assign a task as a target to the home node so that we are able
to assign work items to this task.

  >>> tTask = concepts['task']
  >>> home = views['home']
  >>> from loops.concept import Concept
  >>> from loops.setup import addAndConfigureObject
  >>> task01 = addAndConfigureObject(concepts, Concept, 'loops_dev',
  ...                   title=u'loops Development', conceptType=tTask)
  >>> home.target = task01

Forms for adding and editing work items
---------------------------------------

New work items are created using a CreateWorkItemForm.

  >>> from loops.organize.work.browser import CreateWorkItemForm, CreateWorkItem
  >>> form = CreateWorkItemForm(home, TestRequest())

When this form is submitted, a form controller is automatically created
for the view on the currently shown node. The data from the form is processed
by calling the form controller's update method

  >>> input = {'form.action': 'create_workitem', 'workitem.action': 'finish'}
  >>> request = TestRequest(form=input)
  >>> from loops.browser.node import NodeView
  >>> view = NodeView(home, request)
  >>> cwiController = CreateWorkItem(view, request)

  >>> cwiController.update()
  False


Fin de partie
=============

  >>> placefulTearDown()
