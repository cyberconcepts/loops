===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

Note: This packages depends on cybertools.organize.

Let's do some basic setup

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)
  >>> from zope import component, interface

and set up a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from loops.organize.setup import SetupManager
  >>> component.provideAdapter(SetupManager, name='organize')
  >>> from loops.expert.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> from loops import util
  >>> loopsRoot = site['loops']
  >>> loopsId = util.getUidForObject(loopsRoot)

  >>> from loops.organize.tests import setupUtilitiesAndAdapters
  >>> setupData = setupUtilitiesAndAdapters(loopsRoot)

  >>> type = concepts['type']
  >>> person = concepts['person']

  >>> from loops.concept import Concept
  >>> from loops.setup import addAndConfigureObject
  >>> johnC = addAndConfigureObject(concepts, Concept, 'john', title=u'John',
  ...                               conceptType=person)


Organizations: Persons (and Users), Institutions, Addresses...
==============================================================

The classes used in this package are just adapters to IConcept.

  >>> from loops.organize.interfaces import IPerson

  >>> john = IPerson(johnC)
  >>> john.title
  u'John'
  >>> john.firstName = u'John'
  >>> johnC._firstName
  u'John'
  >>> john.lastName is None
  True
  >>> john.someOtherAttribute
  Traceback (most recent call last):
  ...
  AttributeError: ... someOtherAttribute

We can use the age calculations from the base Person class:

  >>> from datetime import date
  >>> john.birthDate = date(1980, 3, 26)
  >>> john.ageAt(date(2006, 5, 12))
  26
  >>> john.age >= 26
  True

A person can be associated with a user of the system by setting the
userId attribute; this will also register the person concept in the
corresponding principal annotations so that there is a fast way to find
the person(s) belonging to a user/principal.

For testing, we first have to provide the needed utilities and settings
(in real life this is all done during Zope startup):

  >>> auth = setupData.auth
  >>> principalAnnotations = setupData.principalAnnotations

  >>> principal = auth.definePrincipal('users.john', u'John', login='john')
  >>> john.userId = 'users.john'

  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> from loops.organize.party import ANNOTATION_KEY
  >>> annotations[ANNOTATION_KEY][loopsId] == johnC
  True

Change a userId assignment:

  >>> principal = auth.definePrincipal('users.johnny', u'Johnny', login='johnny')
  >>> john.userId = 'users.johnny'

  >>> annotations = principalAnnotations.getAnnotationsById('users.johnny')
  >>> annotations[ANNOTATION_KEY][loopsId] == johnC
  True
  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> annotations[ANNOTATION_KEY][loopsId] is None
  True

  >>> john.userId = None
  >>> annotations = principalAnnotations.getAnnotationsById('users.johnny')
  >>> annotations[ANNOTATION_KEY][loopsId] is None
  True

Deleting a person with a userId assigned removes the corresponding
principal annotation:

  >>> from zope.app.container.interfaces import IObjectRemovedEvent
  >>> from zope.app.container.contained import ObjectRemovedEvent
  >>> from zope.event import notify
  >>> from zope.interface import Interface
  >>> from loops.interfaces import IConcept
  >>> from loops.organize.party import removePersonReferenceFromPrincipal
  >>> from zope.app.testing import ztapi
  >>> ztapi.subscribe([IConcept, IObjectRemovedEvent], None,
  ...                 removePersonReferenceFromPrincipal)

  >>> john.userId = 'users.john'
  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> annotations[ANNOTATION_KEY][loopsId] == johnC
  True

  >>> del concepts['john']
  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> annotations[ANNOTATION_KEY][loopsId] is None
  True

If we try to assign a userId of a principal that already has a person
concept assigned we should get an error:

  >>> johnC = concepts['john'] = Concept(u'John')
  >>> johnC.conceptType = person
  >>> john = IPerson(johnC)
  >>> john.userId = 'users.john'
  >>> john.email = 'john@loopz.org'

  >>> marthaC = concepts['martha'] = Concept(u'Martha')
  >>> marthaC.conceptType = person
  >>> martha = IPerson(marthaC)

  >>> martha.userId = 'users.john'
  Traceback (most recent call last):
  ...
  ValueError: ...


Member Registrations
====================

The member registration needs the whole pluggable authentication stuff
with a principal folder:

  >>> from zope.app.appsetup.bootstrap import ensureUtility
  >>> from zope.app.authentication.authentication import PluggableAuthentication
  >>> from zope.app.security.interfaces import IAuthentication
  >>> ensureUtility(site, IAuthentication, '', PluggableAuthentication,
  ...               copy_to_zlog=False)
  <...PluggableAuthentication...>
  >>> pau = component.getUtility(IAuthentication, context=site)

  >>> from zope.app.authentication.principalfolder import PrincipalFolder
  >>> from zope.app.authentication.interfaces import IAuthenticatorPlugin
  >>> pFolder = PrincipalFolder('loops.')
  >>> pau['loops'] = pFolder
  >>> pau.authenticatorPlugins = ('loops',)

In addition, we have to create at least one node in the view space
and register an IMemberRegistrationManager adapter for the loops root object:

  >>> from loops.view import Node
  >>> menu = views['menu'] = Node('Home')
  >>> menu.nodeType = 'menu'

  >>> from loops.organize.member import MemberRegistrationManager
  >>> component.provideAdapter(MemberRegistrationManager)

Now we can enter the registration info for a new member (after having made
sure that a principal object can be served by a corresponding factory):

  >>> from zope.app.authentication.principalfolder import FoundPrincipalFactory
  >>> component.provideAdapter(FoundPrincipalFactory)

  >>> data = {'loginName': u'newuser',
  ...         'password': u'quack',
  ...         'passwordConfirm': u'quack',
  ...         'lastName': u'Sawyer',
  ...         'firstName': u'Tom',
  ...         'email': u'tommy@sawyer.com',
  ...         'action': 'update',}

and register it.

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest(form=data)
  >>> from loops.organize.browser.member import MemberRegistration
  >>> regView = MemberRegistration(menu, request)
  >>> regView.update()
  False

  >>> from loops.common import adapted
  >>> person = concepts['person.newuser']
  >>> pa = adapted(person)
  >>> pa.lastName, pa.userId
  (u'Sawyer', u'loops.newuser')

Now we can also retrieve it from the authentication utility:

  >>> pau.getPrincipal('loops.newuser').title
  u'Tom Sawyer'

Change Password
---------------

  >>> data = {'oldPassword': u'tiger',
  ...         'password': u'lion',
  ...         'passwordConfirm': u'lion',
  ...         'action': 'update'}

  >>> request = TestRequest(form=data)

We need a principal for testing the login stuff:

  >>> from zope.app.authentication.principalfolder import InternalPrincipal
  >>> principal = InternalPrincipal('scott', 'tiger', 'Scotty')
  >>> request.setPrincipal(principal)

  >>> from loops.organize.browser.member import PasswordChange
  >>> pwcView = PasswordChange(menu, request)
  >>> pwcView.update()
  False


Pure Person-based Authentication
================================

The person-based authenticator provides authentication without having to
store a persistent (internal) principal object.

  >>> from loops.organize.auth import PersonBasedAuthenticator
  >>> pbAuth = PersonBasedAuthenticator('persons.')
  >>> pau['persons'] = pbAuth
  >>> pau.authenticatorPlugins = ('loops', 'persons',)

  >>> eddieC = addAndConfigureObject(concepts, Concept, 'eddie', title=u'Eddie',
  ...                                conceptType=person)
  >>> eddie = adapted(eddieC)
  >>> eddie.userId = 'persons.eddie'

  >>> pbAuth.setPassword('eddie', 'secret')
  >>> pbAuth.authenticateCredentials(dict(login='eddie', password='secret'))
  PrincipalInfo(u'persons.eddie')


Security
========

Automatic security settings on persons
--------------------------------------

  >>> from zope.traversing.api import getName
  >>> list(sorted(getName(c) for c in concepts['person'].getChildren()))
  [u'jim', u'john', u'martha', u'person.newuser']

Person objects that have a user assigned to them receive this user
(principal) as their owner.

  >>> from zope.securitypolicy.interfaces import IPrincipalRoleMap
  >>> IPrincipalRoleMap(concepts['john']).getPrincipalsAndRoles()
  [('loops.Person', 'users.john', PermissionSetting: Allow)]
  >>> IPrincipalRoleMap(concepts['person.newuser']).getPrincipalsAndRoles()
  [('loops.Person', u'loops.newuser', PermissionSetting: Allow)]

The person ``martha`` hasn't got a user id, so there is no role assigned
to it.

  >>> IPrincipalRoleMap(concepts['martha']).getPrincipalsAndRoles()
  []

Only the owner (and a few other privileged people) should be able
to edit a person object.

We also need an interaction with a participation based on the principal
whose permissions we want to check.

  >>> from zope.app.authentication.principalfolder import Principal
  >>> pJohn = Principal('users.john', 'xxx', u'John')

  >>> from loops.tests.auth import login
  >>> login(pJohn)

We also want to grant some global permissions and roles, i.e. on the site or
loops root level.

  >>> rolePermissions = setupData.rolePermissions
  >>> rolePermissions.grantPermissionToRole('zope.View', 'zope.Member')

  >>> principalRoles = setupData.principalRoles
  >>> principalRoles.assignRoleToPrincipal('zope.Member', 'users.john')

Now we are ready to look for the real stuff - what John is allowed to do.

  >>> from zope.security import canAccess, canWrite, checkPermission
  >>> john = concepts['john']

  >>> canAccess(john, 'title')
  True

Person objects that have an owner may be modified by this owner.
(Changed in 2013-01-14: Owner not set automatically)

  >>> canWrite(john, 'title')
  False

was: True

So let's try with another user with another role setting.

  >>> rolePermissions.grantPermissionToRole('zope.ManageContent', 'loops.Staff')
  >>> principalRoles.assignRoleToPrincipal('loops.Staff', 'users.martha')
  >>> principalRoles.assignRoleToPrincipal('zope.Member', 'users.martha')

  >>> pMartha = Principal('users.martha', 'xxx', u'Martha')
  >>> login(pMartha)

  >>> canAccess(john, 'title')
  True
  >>> canWrite(john, 'title')
  False

If we clear the userId attribute from a person object others may be allowed
again to edit it...

  >>> adapted(john).userId = ''
  >>> canWrite(john, 'title')
  True

... but John no more...

  >>> login(pJohn)
  >>> canWrite(john, 'title')
  False


Tasks and Events
================

Task view with edit action
--------------------------

  >>> from loops.organize.interfaces import ITask
  >>> task = addAndConfigureObject(concepts, Concept, 'task', title=u'Task',
  ...                              conceptType=type, typeInterface=ITask)

  >>> from loops.organize.task import Task
  >>> component.provideAdapter(Task)

  >>> task01 = addAndConfigureObject(concepts, Concept, 'task01',
  ...                                title=u'Task #1', conceptType=task)

  >>> from loops.organize.browser.task import TaskView
  >>> view = TaskView(task01, TestRequest())
  >>> list(view.getActions('portlet'))
  [...]

OK, the action is not provided automatically any more by the TaskView
but has to be entered as a type option.

  >>> adapted(task).options = ['action.portlet:editTask']
  >>> view = TaskView(task01, TestRequest())
  >>> list(view.getActions('portlet'))
  [<loops.browser.action.DialogAction ...>]

Events listing
--------------

  >>> event = addAndConfigureObject(concepts, Concept, 'event', title=u'Event',
  ...                               conceptType=type, typeInterface=ITask)
  >>> event01 = addAndConfigureObject(concepts, Concept, 'event01',
  ...                                 title=u'Event #1', conceptType=event,
  ...                           )

  >>> from loops.organize.browser.event import Events
  >>> events = addAndConfigureObject(concepts, Concept, 'events', title=u'Events',
  ...                                conceptType=concepts['query'])
  >>> listing = Events(events, TestRequest())
  >>> listing.getActions('portlet')
  [<loops.browser.action.DialogAction ...>]

  >>> from loops.config.base import QueryOptions
  >>> component.provideAdapter(QueryOptions)

  >>> list(listing.events())
  [<loops.browser.concept.ConceptRelationView ...>]

Creation of follow-up event
---------------------------

  >>> from loops.organize.browser.event import CreateFollowUpEvent


Send Email to Members
=====================

  >>> menu.target = event01

  >>> from loops.organize.browser.party import SendEmailForm
  >>> form = SendEmailForm(menu, TestRequest())
  >>> form.members
  [{'object': <...Person...>, 'email': 'john@loopz.org', 'title': u'John'},
   {'object': <...Person...>, 'email': u'tommy@sawyer.com', 'title': u'Tom Sawyer'}]
  >>> form.subject
  u"loops Notification from '$site'"
  >>> form.mailBody
  u'\n\nEvent #1\nhttp://127.0.0.1/loops/views/menu/.113\n\n'


Show Presence of Other Users
============================

  >>> from loops.organize.presence import Presence
  >>> component.provideUtility(Presence())


Roles of Persons
================

When persons are assigned to a parent (e.g. an instutution or a project)
this assignment may be characterized by a certain role. This role may
be specified by using a special predicate that is associated with a
predicate interface that allows to specify the role.

(Note that the security-relevant assignment of persons is managed via
other special predicates: 'ismember', 'ismaster'. The 'hasrole'
predicate described here is intended for situations where the roles
may be chosen from an arbitrary list.)

  >>> from loops.organize.interfaces import IHasRole
  >>> predicate = concepts['predicate']
  >>> hasRole = addAndConfigureObject(concepts, Concept, 'hasrole',
  ...                   title=u'has Role',
  ...                   conceptType=predicate, predicateInterface=IHasRole)

Let's now assign john to task01 and have a look at the relation created.

  >>> task01.assignChild(john, hasRole)
  >>> relation = task01.getChildRelations([hasRole])[0]

The role may be accessed by getting a relation adapter

  >>> from loops.predicate import adaptedRelation
  >>> adRelation = adaptedRelation(relation)
  >>> adRelation.role is None
  True

  >>> adRelation.role = 'member'
  >>> relation._role
  'member'
  >>> adRelation = adaptedRelation(relation)
  >>> adRelation.role
  'member'


Calendar
========

  >>> from loops.organize.browser.event import CalendarInfo
  >>> calendar = CalendarInfo(menu, TestRequest(cal_year=2009, cal_month=2))
  >>> mc = calendar.monthCalendar
  >>> mc
  [[0, 0, 0, 0, 0, 0, 1],
   [2, 3, 4, 5, 6, 7, 8],
   [9, 10, 11, 12, 13, 14, 15],
   [16, 17, 18, 19, 20, 21, 22],
   [23, 24, 25, 26, 27, 28, 0]]
  >>> calendar.getWeekNumber(mc[0])
  5
  >>> calendar.isToday(18)
  False


Fin de partie
=============

  >>> placefulTearDown()
