===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

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
  >>> nodeView = NodeView(home, request)
  >>> cwiController = CreateWorkItem(nodeView, request)

  >>> cwiController.update()
  False

  >>> list(workItems)
  [<WorkItem ['36', 1, '33', '2008-12-28 19:00', 'finished']:
   {'comment': u'Comment', 'end': 1230491700, 'description': u'Description',
    'created': ..., 'creator': '33', 'start': 1230487200,
    'duration': 4500, 'effort': 900}>]

Work items views
----------------

  >>> from loops.organize.work.browser import WorkItemView, TaskWorkItems
  >>> wi01 = workItems['0000001']
  >>> view = WorkItemView(wi01, TestRequest())
  >>> view.taskUrl
  'http://127.0.0.1/loops/concepts/loops_dev/@@SelectedManagementView.html'

  >>> work = TaskWorkItems(task01, request)
  >>> from loops.organize.work.browser import WorkItemDetails
  >>> view = WorkItemDetails(work, wi01)
  >>> view.day, view.start, view.end
  (u'08/12/28', u'19:00', u'20:15')

Work items life cycle
---------------------

Let's create another work item, now in state planned.

  >>> input = {u'form.action': u'create_workitem', u'workitem.action': u'plan',
  ...          u'title': u'Install Zope',
  ...          u'start_date': u'2009-01-19', u'start_time': u'T09:00:00'}
  >>> request = TestRequest(form=input)
  >>> request.setPrincipal(pJohn)
  >>> nodeView = NodeView(home, request)
  >>> cwiController = CreateWorkItem(nodeView, request)
  >>> cwiController.update()
  False

If we now open another form, providing the identifier of the newly created
work item, the form will be pre-filled with some of the item's data.

  >>> form = CreateWorkItemForm(home, TestRequest(form=dict(id='0000002')))
  >>> form.title
  u'Install Zope'

The 'delegate' transition is omitted from the actions list because it is
only available for privileged users.

  >>> form.actions
  [{'selected': False, 'name': 'plan', 'title': 'plan'}, 
   {'selected': False, 'name': 'accept', 'title': 'accept'}, 
   {'selected': False, 'name': 'start', 'title': 'start working'}, 
   {'selected': False, 'name': 'work', 'title': 'work'}, 
   {'selected': False, 'name': 'finish', 'title': 'finish'}, 
   {'selected': False, 'name': 'delegate', 'title': 'delegate'}, 
   {'selected': False, 'name': 'move', 'title': 'move'}, 
   {'selected': False, 'name': 'cancel', 'title': 'cancel'}, 
   {'selected': False, 'name': 'modify', 'title': 'modify'}]

Work Item Queries
=================

  >>> from loops.common import adapted
  >>> from loops.expert.concept import IQueryConcept
  >>> from loops.organize.work.browser import UserWorkItems, PersonWorkItems

  >>> tQuery = addAndConfigureObject(concepts, Concept, 'query',
  ...                   title=u'Query', conceptType=concepts.getTypeConcept(),
  ...                   typeInterface=IQueryConcept)

  >>> query = addAndConfigureObject(concepts, Concept, 'userworkitems',
  ...                               conceptType=tQuery)

The UserWorkItems view does not give any results because there is no current
user (principal) available in our test setting.

  >>> work = UserWorkItems(query, TestRequest())
  >>> work.listWorkItems()

So we use the PersonWorkItems view, assigning john to the query.

  >>> query.assignParent(johnC)
  >>> adapted(query).options = ['wi_from:2009-01-01', 'wi_to:today']

  >>> input = dict()
  >>> work = PersonWorkItems(query, TestRequest(form=input))
  >>> work.listWorkItems()
  [<WorkItem ['36', 2, '33', '2009-01-19 09:00', 'planned']:
   {'title': u'Install Zope', 'created': ..., 'end': 1232352000, 
    'start': 1232352000, 'creator': '33'}>]


Work Reports
============

First we have to make sure that there is a report concept type available.
In addition we need a predicate that connects one or more tasks with a report.

  >>> from loops.expert.report import IReport, Report
  >>> component.provideAdapter(Report)
  >>> tReport = addAndConfigureObject(concepts, Concept, 'report',
  ...                   title=u'Report', conceptType=concepts.getTypeConcept(),
  ...                   typeInterface=IReport)
  >>> hasReport = addAndConfigureObject(concepts, Concept, 'hasreport',
  ...                   title=u'has Report', conceptType=concepts.getPredicateType())

Work statement report
---------------------

Now we can create a report and register it as the report for the task
used above.

  >>> workStatement = addAndConfigureObject(concepts, Concept, 'work_statement',
  ...                   title=u'Work Statement', conceptType=tReport,
  ...                   reportType='work_report')
  >>> workStatement.assignChild(task01, hasReport)

The executable report is a report instance that is an adapter to the
(adapted) report instance.

  >>> from loops.organize.work.report import WorkReportInstance
  >>> from loops.expert.report import IReportInstance
  >>> component.provideAdapter(WorkReportInstance,
  ...                          provides=IReportInstance,
  ...                          name='work_report')

The user interface is a ReportConceptView subclass that is directly associated with the task.

  >>> from loops.organize.work.report import WorkStatementView
  >>> input = dict(dayFrom='2008-01-01')
  >>> reportView = WorkStatementView(task01, TestRequest(form=input))
  >>> reportView.nodeView = nodeView

  >>> results = reportView.results()
  >>> len(list(results))
  1

  >>> for row in results:
  ...     for col in reportView.displayedColumns:
  ...         print col.getDisplayValue(row),
  ...     print
  08/12/28 19:00 20:15
    {'url': '.../home/.36', 'title': u'loops Development'}
    {'url': '.../home/.33', 'title': u'john'}  01:15 00:15
    {'actions': [...]}

  >>> results.totals.data
  {'effort': 900}

Export of work data
-------------------

  >>> from loops.organize.work.report import WorkStatementCSVExport
  >>> reportView = WorkStatementCSVExport(task01, TestRequest(form=input))
  >>> reportView.nodeView = nodeView

  >>> output = reportView()
  >>> print output
  Day;Start;End;Task;Party;Title;Duration;Effort;State
  08/12/28;19:00;20:15;loops Development;john;;1.2500;0.2500;finished


Meeting Minutes
===============

We can use an event with assigned tasks as the basis for planning a meeting
and recording information about the tasks.

Let's start with creating an a event and assigning it a task.

  >>> from loops.organize.interfaces import IEvent, IAgendaItem
  >>> tEvent = addAndConfigureObject(concepts, Concept, 'event',
  ...     title=u'Event', conceptType=concepts.getTypeConcept(),
  ...     typeInterface=IEvent)
  >>> tAgendaItem = addAndConfigureObject(concepts, Concept, 'agendaitem',
  ...     title=u'AgendaItem', conceptType=concepts.getTypeConcept(),
  ...     typeInterface=IAgendaItem)

  >>> ev01 = addAndConfigureObject(concepts, Concept, 'ev01',
  ...     title=u'loops Meeting', conceptType=tEvent)
  >>> aitem01 = addAndConfigureObject(concepts, Concept, 'aitem01',
  ...     title=u'Documentation of Features', conceptType=tAgendaItem)
  >>> ev01.assignChild(aitem01)

Now we create the meeting minutes report. We assign the event type as a
child in order to provide the information for which types of objects the
report is available.

  >>> from loops.organize.work.report import MeetingMinutes
  >>> component.provideAdapter(MeetingMinutes, provides=IReportInstance,
  ...                          name='meeting_minutes')

  >>> meetingMinutes = addAndConfigureObject(concepts, Concept, 
  ...     'meeting_minutes', title=u'Meeting Minutes', conceptType=tReport,
  ...     reportType='meeting_minutes')
  >>> meetingMinutes.assignChild(tEvent, hasReport)

We can now access the report using a corresponding report-based view.

  >>> from loops.organize.work.meeting import MeetingMinutes
  >>> reportView = MeetingMinutes(ev01, TestRequest())
  >>> reportView.nodeView = nodeView

  >>> results = reportView.results()
  >>> len(list(results))
  1
  >>> for row in results:
  ...     for col in reportView.displayedColumns:
  ...         print col.getDisplayValue(row),
  ...     print
  {'url': 'http://127.0.0.1/loops/views/home/.58', 
   'title': u'Documentation of Features'}
  <cybertools.composer.report.result.ResultSet object ...>


Fin de partie
=============

  >>> placefulTearDown()
