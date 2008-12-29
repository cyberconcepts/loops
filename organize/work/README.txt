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

  >>> from cybertools.organize.work import WorkItems
  >>> component.provideAdapter(WorkItems)

  >>> from cybertools.organize.interfaces import IWorkItems
  >>> workItems = IWorkItems(records['work'])

  >>> from cybertools.organize.work import workItemStates
  >>> component.provideUtility(workItemStates(), name='organize.workItemStates')

More setup
----------

In order to be able to login and store favorites and other personal data
we have to prepare our environment. We need some basic adapter registrations,
and a pluggable authentication utility with a principal folder.

  >>> from loops.organize.tests import setupObjectsForTesting
  >>> setupData = setupObjectsForTesting(site, concepts)
  >>> johnC = setupData.johnC

  >>> from zope.app.authentication.principalfolder import Principal
  >>> pJohn = Principal('users.john', 'xxx', u'John')
  >>> from loops.tests.auth import login
  >>> login(pJohn)

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

  >>> input = {u'form.action': u'create_workitem', u'workitem.action': u'finish',
  ...          u'description': u'Description', u'comment': u'Comment',
  ...          u'start_date': u'2008-12-28', u'start_time': u'T19:00:00',
  ...          u'end_time': u'T20:15:00', u'duration': u'1:15', u'effort': u'0:15'}
  >>> request = TestRequest(form=input)
  >>> request.setPrincipal(pJohn)

  >>> from loops.browser.node import NodeView
  >>> view = NodeView(home, request)
  >>> cwiController = CreateWorkItem(view, request)

  >>> cwiController.update()
  False

  >>> list(workItems)
  [<WorkItem ['36', 1, '33', '2008-12-28 19:15', 'finished']:
   {'comment': u'Comment', 'end': 1230491700, 'description': u'Description',
    'created': ..., 'creator': '33', 'assigned': ...,
    'start': 1230487200, 'duration': 4500, 'effort': 900}>]

  >>> from loops.organize.work.browser import WorkItemView
  >>> wi01 = workItems['0000001']
  >>> view = WorkItemView(wi01, TestRequest())
  >>> view.taskUrl
  'http://127.0.0.1/loops/concepts/loops_dev/@@SelectedManagementView.html'


Fin de partie
=============

  >>> placefulTearDown()
