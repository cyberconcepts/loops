===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

Note: This package depends on cybertools.knowledge and loops.organize.

Let's do some basic set up

  >>> from zope import component, interface

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

and setup a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()
  >>> loopsRoot = site['loops']

We then import a loops .dmp file containing all necessary types and
predicates.

  >>> from loops.knowledge.tests import importData
  >>> importData(loopsRoot)

We need some type concepts for controlling the meaning of the concepts objects,
these have already been created during setup and .dmp import:

  >>> topic = concepts['topic']
  >>> person = concepts['person']
  >>> task = concepts['task']


Manage knowledge and knowledge requirements
===========================================

The classes used in this package are just adapters to IConcept.

  >>> from loops.interfaces import IConcept
  >>> from loops.knowledge.knowledge import Person, Topic, Task
  >>> from loops.knowledge.interfaces import IPerson
  >>> from cybertools.knowledge.interfaces import IKnowledgeElement
  >>> from loops.knowledge.interfaces import ITask
  >>> component.provideAdapter(Person, (IConcept,), IPerson)
  >>> component.provideAdapter(Topic, (IConcept,), IKnowledgeElement)
  >>> component.provideAdapter(Task, (IConcept,), ITask)

First we want to set up a tree of knowledge elements (topics) and their
interdependencies. Note that in order to discern the concepts created
from their typeInterface adapters we here append a 'C' to the name of
the variables:

  >>> from loops.concept import Concept
  >>> progLangC = concepts['progLang'] = Concept('Programming Language')
  >>> ooProgC = concepts['ooProg'] = Concept('Object-oriented Programming')
  >>> pythonC = concepts['python'] = Concept('Python')
  >>> pyBasicsC = concepts['pyBasics'] = Concept('Python Basics')
  >>> pyOoC = concepts['pyOo'] = Concept('OO Programming with Python')
  >>> pySpecialsC = concepts['pySpecials'] = Concept('Python Specials')

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

  >>> johnC = concepts['john'] = Concept('John')
  >>> johnC.conceptType = person

  >>> john = IPerson(johnC)
  >>> john.knows(pyBasics)
  >>> list(john.getKnowledge())[0].title
  'Python Basics'

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
  ['Object-oriented Programming', 'OO Programming with Python']

Luckily there are a few elearning content objects out there that
provide some of the knowledge needed:

  >>> from loops.interfaces import IResource
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

Controlling knowledge-related form fields via a schema factory
--------------------------------------------------------------

  >>> from loops.knowledge.schema import PersonSchemaFactory

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

  >>> from zope.principalannotation.interfaces import IPrincipalAnnotationUtility
  >>> from zope.principalannotation.utility import PrincipalAnnotationUtility
  >>> principalAnnotations = PrincipalAnnotationUtility()
  >>> component.provideUtility(principalAnnotations, IPrincipalAnnotationUtility)

  >>> principal = auth.definePrincipal('users.john', 'John', login='john')
  >>> john.userId = 'users.john'

  >>> from zope.publisher.browser import TestRequest
  >>> request = TestRequest()
  >>> request.setPrincipal(principal)

  >>> from loops.knowledge.browser import MyKnowledge
  >>> view = MyKnowledge(task01C, request)
  >>> prov = view.myKnowledgeProvidersForTask()


Competence and Certification Management
=======================================

  >>> tCompetence = concepts['competence']


Glossaries
==========

Glossary items are topic-like concepts that may be edited by end users.

  >>> from loops.knowledge.glossary.browser import CreateGlossaryItemForm
  >>> from loops.knowledge.glossary.browser import EditGlossaryItemForm
  >>> from loops.knowledge.glossary.browser import CreateGlossaryItem
  >>> from loops.knowledge.glossary.browser import EditGlossaryItem


Survey
======

  >>> from loops.knowledge.tests import importSurvey
  >>> importSurvey(loopsRoot)

  >>> from loops.knowledge.survey.browser import SurveyView


Fin de partie
=============

  >>> placefulTearDown()

