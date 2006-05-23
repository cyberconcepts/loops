===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

Note: This packages depends on cybertools.organize.

Let's do some basic set up

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)
  
  >>> from zope import component, interface
  >>> from zope.app import zapi

and setup a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):
  
  >>> from loops import Loops
  >>> from loops.concept import ConceptManager, Concept
  >>> from loops.interfaces import IConcept, ITypeConcept

  >>> loopsRoot = site['loops'] = Loops()

  >>> from cybertools.relation.interfaces import IRelationRegistry
  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> relations = DummyRelationRegistry()
  >>> component.provideUtility(relations, IRelationRegistry)

  >>> from cybertools.typology.interfaces import IType
  >>> from loops.type import ConceptType, TypeConcept
  >>> component.provideAdapter(ConceptType, (IConcept,), IType)
  >>> component.provideAdapter(TypeConcept, (IConcept,), ITypeConcept)

  >>> loopsRoot['concepts'] = ConceptManager()
  >>> concepts = loopsRoot['concepts']

  >>> concepts['hasType'] = Concept(u'has type')
  >>> concepts['type'] = Concept(u'Type')
  >>> type = concepts['type']
  >>> type.conceptType = type

  >>> from loops.organize.interfaces import IPerson
  >>> concepts['person'] = Concept(u'Person')
  >>> person = concepts['person']
  >>> person.conceptType = type
  >>> ITypeConcept(person).typeInterface = IPerson
  
  >>> johnC = Concept(u'John')
  >>> concepts['john'] = johnC
  >>> johnC.conceptType = person


Organizations: Persons (and Users), Institutions, Addresses...
==============================================================

The classes used in this package are just adapters to IConcept.

  >>> from loops.organize.party import Person
  >>> component.provideAdapter(Person, (IConcept,), IPerson)

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
  AttributeError: someOtherAttribute

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

  >>> from zope.app.security.interfaces import IAuthentication
  >>> from zope.app.security.principalregistry import PrincipalRegistry
  >>> auth = PrincipalRegistry()
  >>> component.provideUtility(auth, IAuthentication)
      
  >>> from zope.app.principalannotation.interfaces import IPrincipalAnnotationUtility
  >>> from zope.app.principalannotation import PrincipalAnnotationUtility
  >>> principalAnnotations = PrincipalAnnotationUtility()
  >>> component.provideUtility(principalAnnotations, IPrincipalAnnotationUtility)

  >>> principal = auth.definePrincipal('users.john', u'John', login='john')

  >>> john.userId = 'users.john'

  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> from loops.organize.party import ANNOTATION_KEY
  >>> annotations.get(ANNOTATION_KEY) == johnC
  True

Change a userId assignment:

  >>> principal = auth.definePrincipal('users.johnny', u'Johnny', login='johnny')
  >>> john.userId = 'users.johnny'
      
  >>> annotations = principalAnnotations.getAnnotationsById('users.johnny')
  >>> annotations.get(ANNOTATION_KEY) == johnC
  True
  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> annotations.get(ANNOTATION_KEY) is None
  True

  >>> john.userId = None
  >>> annotations = principalAnnotations.getAnnotationsById('users.johnny')
  >>> annotations.get(ANNOTATION_KEY) is None
  True

Deleting a person with a userId assigned removes the corresponding
principal annotation:

  >>> from zope.app.container.interfaces import IObjectRemovedEvent
  >>> from zope.app.container.contained import ObjectRemovedEvent
  >>> from zope.event import notify
  >>> from zope.interface import Interface
  >>> from loops.organize.party import removePersonReferenceFromPrincipal
  >>> from zope.app.testing import ztapi
  >>> ztapi.subscribe([IConcept, IObjectRemovedEvent], None,
  ...                 removePersonReferenceFromPrincipal)

  >>> john.userId = 'users.john'
  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> annotations.get(ANNOTATION_KEY) == johnC
  True

  >>> del concepts['john']
  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> annotations.get(ANNOTATION_KEY) is None
  True

If we try to assign a userId of a principal that already has a person
concept assigned we should get an error:

  >>> john.userId = 'users.john'

  >>> marthaC = Concept(u'Martha')
  >>> concepts['martha'] = marthaC
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
  >>> ensureUtility(site, IAuthentication, '', PluggableAuthentication,
  ...               copy_to_zlog=False)
  ''
  >>> pau = component.getUtility(IAuthentication, context=site)

  >>> from zope.app.component.site import UtilityRegistration
  >>> from zope.app.authentication.principalfolder import PrincipalFolder
  >>> from zope.app.authentication.interfaces import IAuthenticatorPlugin
  >>> pFolder = PrincipalFolder('loops.')
  >>> pau['loops'] = pFolder
  >>> reg = UtilityRegistration('loops', IAuthenticatorPlugin, pFolder)
  >>> pau.registrationManager.addRegistration(reg)
  'UtilityRegistration'  
  >>> reg.status = u'Active'
  >>> pau.authenticatorPlugins = ('loops',)

In addition, we have to create at least one node in the view space
and register an IMemberRegistrationManager adapter for the loops root object:

  >>> from loops.view import ViewManager, Node
  >>> views = loopsRoot['views'] = ViewManager()
  >>> menu = views['menu'] = Node('Home')
  >>> menu.nodeType = 'menu'

  >>> from loops.organize.member import MemberRegistrationManager
  >>> from loops.organize.interfaces import IMemberRegistrationManager
  >>> from loops.interfaces import ILoops
  >>> component.provideAdapter(MemberRegistrationManager)

Now we can enter the registration info for a new member (after having made
sure that a principal object can be served by a corresponding factory):

  >>> from zope.app.authentication.principalfolder import FoundPrincipalFactory
  >>> component.provideAdapter(FoundPrincipalFactory)
  
  >>> data = {'loginName': u'newuser',
  ...         'password': u'quack',
  ...         'passwordConfirm': u'quack',
  ...         'lastName': u'Sawyer',
  ...         'firstName': u'Tom'}

and register it

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> from loops.organize.browser import MemberRegistration
  >>> regView = MemberRegistration(menu, request)
  >>> personAdapter = regView.register(data)

  >>> personAdapter.context.__name__, personAdapter.lastName, personAdapter.userId
  (u'newuser', u'Sawyer', u'loops.newuser')

Now we can also retrieve it from the authentication utility:

  >>> pau.getPrincipal('loops.newuser').title
  u'Tom Sawyer'


Fin de partie
=============

  >>> placefulTearDown()

