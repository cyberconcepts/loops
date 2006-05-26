===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

Note: This package depends on cybertools.knowledge and cybertools.organize.

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
  >>> from loops.resource import ResourceManager
  >>> from loops.interfaces import IResource, IConcept, ITypeConcept

  >>> loopsRoot = site['loops'] = Loops()

  >>> from cybertools.relation.interfaces import IRelationRegistry
  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> relations = DummyRelationRegistry()
  >>> component.provideUtility(relations, IRelationRegistry)

  >>> from cybertools.typology.interfaces import IType
  >>> from loops.type import ConceptType, TypeConcept
  >>> component.provideAdapter(ConceptType, (IConcept,), IType)
  >>> component.provideAdapter(TypeConcept, (IConcept,), ITypeConcept)

  >>> concepts = loopsRoot['concepts'] = ConceptManager()
  >>> resources = loopsRoot['resources'] = ResourceManager()

  >>> hasType = concepts['hasType'] = Concept(u'has type')
  >>> type = concepts['type'] = Concept(u'Type')
  >>> type.conceptType = type

  >>> predicate = concepts['predicate'] = Concept(u'Predicate')
  >>> predicate.conceptType = type
  >>> hasType.conceptType = predicate

We need some predicates to set up the relationships between our concepts:

  >>> standard = concepts['standard'] = Concept(u'subobject')
  >>> depends = concepts['depends'] = Concept(u'depends')
  >>> knows = concepts['knows'] = Concept(u'knows')
  >>> requires = concepts['requires'] = Concept(u'requires')
  >>> provides = concepts['provides'] = Concept(u'provides')
  
  >>> for p in (standard, depends, knows, requires, provides):
  ...     p.conceptType = predicate

And last not least we need some type concepts for controlling the
meaning of the concepts objects:

  >>> from cybertools.knowledge.interfaces import IKnowledgeElement
  >>> topic = concepts['topic'] = Concept(u'Topic')
  >>> topic.conceptType = type
  >>> ITypeConcept(topic).typeInterface = IKnowledgeElement

  >>> from loops.knowledge.interfaces import IPerson
  >>> person = concepts['person'] = Concept(u'Person')
  >>> person.conceptType = type
  >>> ITypeConcept(person).typeInterface = IPerson
  
  >>> from loops.knowledge.interfaces import ITask
  >>> task = concepts['task'] = Concept(u'Task')
  >>> task.conceptType = type
  >>> ITypeConcept(task).typeInterface = ITask


Manage knowledge and knowledge requirements
===========================================

The classes used in this package are just adapters to IConcept.

  >>> from loops.knowledge.knowledge import Person, Topic, Task
  >>> component.provideAdapter(Person, (IConcept,), IPerson)
  >>> component.provideAdapter(Topic, (IConcept,), IKnowledgeElement)
  >>> component.provideAdapter(Task, (IConcept,), ITask)

First we want to set up a tree of knowledge elements (topics) and their
interdependencies. Note that in order to discern the concepts created
from their typeInterface adapters we here append a 'C' to the name of
the variables:

  >>> progLangC = concepts['progLang'] = Concept(u'Programming Language')
  >>> ooProgC = concepts['ooProg'] = Concept(u'Object-oriented Programming')
  >>> pythonC = concepts['python'] = Concept(u'Python')
  >>> pyBasicsC = concepts['pyBasics'] = Concept(u'Python Basics')
  >>> pyOoC = concepts['pyOo'] = Concept(u'OO Programming with Python')
  >>> pySpecialsC = concepts['pySpecials'] = Concept(u'Python Specials')

  >>> topicConcepts = (progLangC, ooProgC, pythonC, pyBasicsC, pyOoC, pySpecialsC)
  
  >>> for c in topicConcepts: c.conceptType = topic

  >>> progLang, ooProg, python, pyBasics, pyOo, pySpecials = (IKnowledgeElement(c)
  ...       for c in topicConcepts)

  >>> python.parent = progLang
  >>> pyBasics.parent = python
  >>> pyOo.parent = python
  >>> pySpecials.parent = python

  >>> pyOo.dependsOn(ooProg)
  >>> pyOo.dependsOn(pyBasics)

We now create a person and assign some knowledge to it:

  >>> johnC = concepts['john'] = Concept(u'John')
  >>> johnC.conceptType = person

  >>> john = IPerson(johnC)
  >>> john.knows(pyBasics)
  >>> list(john.getKnowledge())[0].title
  u'Python Basics'

Now let's get to tasks - a task is used as a requirement profile, i.e.
it requires a certain set of knowledge elements:

  >>> task01C = concepts['task01C'] = Concept('Task: needs Python OO')
  >>> task01C.conceptType = task

  >>> task01 = ITask(task01C)
  >>> task01.requires(pyOo)

Now we can ask what knowledge john is lacking if he would like to take
a position with the requirement profile:

  >>> missing = john.getMissingKnowledge(task01)
  >>> [m.title for m in missing]
  [u'Object-oriented Programming', u'OO Programming with Python']

Luckily there are a few elearning content objects out there that
provide some of the knowledge needed:

  >>> from cybertools.knowledge.interfaces import IKnowledgeProvider
  >>> from loops.knowledge.knowledge import ConceptKnowledgeProvider
  >>> component.provideAdapter(ConceptKnowledgeProvider, (IConcept,))
  >>> from loops.knowledge.knowledge import ResourceKnowledgeProvider
  >>> component.provideAdapter(ResourceKnowledgeProvider, (IResource,))

  >>> doc01C = concepts['doc01'] = Concept('Objectorienting Programming')
  >>> doc01 = IKnowledgeProvider(doc01C)
  >>> from loops.resource import Document
  >>> doc02D = resources['doc02'] = Document('oopython.pdf')
  >>> doc02 = IKnowledgeProvider(doc02D)

  >>> doc01.provides(ooProg)
  >>> doc02.provides(pyOo)

So that we are now able to find out what john has to study in order to
fulfill the position offered:

  >>> prov = list(john.getProvidersNeeded(task01))
  >>> len(prov)
  2
  >>> [list(d)[0].title for k, d in prov]
  ['Objectorienting Programming', 'oopython.pdf']


Views that make use of the knowledge management modules
-------------------------------------------------------

One of the practical applications of this stuff is searching for missing
knowledge and corresponding knowledge providers for the user currently
logged in.

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

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> request.setPrincipal(principal)

  >>> from loops.knowledge.browser import MyKnowledge
  >>> view = MyKnowledge(task01C, request)
  >>> prov = view.myKnowledgeProvidersForTask()



Fin de partie
=============

  >>> placefulTearDown()

