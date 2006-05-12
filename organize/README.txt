===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

Note: This packages depends on cybertools.organize.

Letz's do some basic set up

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)
  
  >>> from zope import component, interface
  >>> from zope.app import zapi

and setup a simple loops site with a concept manager and some concepts:
  
  >>> from loops import Loops
  >>> site['loops'] = Loops()
  >>> loopsRoot = site['loops']

  >>> from cybertools.relation.interfaces import IRelationRegistry
  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> relations = DummyRelationRegistry()
  >>> component.provideUtility(relations, IRelationRegistry)

  >>> from loops.concept import ConceptManager, Concept
  >>> loopsRoot['concepts'] = ConceptManager()
  >>> concepts = loopsRoot['concepts']

  >>> concepts['hasType'] = Concept(u'has type')
  >>> concepts['type'] = Concept(u'Type')
  >>> type = concepts['type']
  >>> type.conceptType = type

  >>> concepts['person'] = Concept(u'Person')
  >>> person = concepts['person']
  >>> person.conceptType = type
  
  >>> johnC = Concept(u'John')
  >>> concepts['john'] = johnC
  >>> johnC.conceptType = person


Organizations: Persons (and Users), Institutions, Addresses...
==============================================================

The classes used in this package are just adapters to IConcept.

  >>> from loops.interfaces import IConcept
  >>> from loops.organize.interfaces import IPerson
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
  >>> annotations.get('loops.organize.person') == relations.getUniqueIdForObject(johnC)
  True

Change a userId assignment:

  >>> principal = auth.definePrincipal('users.johnny', u'Johnny', login='johnny')
  >>> john.userId = 'users.johnny'
      
  >>> annotations = principalAnnotations.getAnnotationsById('users.johnny')
  >>> annotations.get('loops.organize.person') == relations.getUniqueIdForObject(johnC)
  True
  >>> annotations = principalAnnotations.getAnnotationsById('users.john')
  >>> annotations.get('loops.organize.person') is None
  True

  >>> john.userId = None
  >>> annotations = principalAnnotations.getAnnotationsById('users.johnny')
  >>> annotations.get('loops.organize.person') is None
  True

Deleting a person with a userId assigned removes the corresponding
principal annotation:


Fin de partie
=============

  >>> placefulTearDown()

