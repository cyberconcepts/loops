===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

Note: This package depends on cybertools.knowledge and cybertools.organize.

Let's do some basic set up

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from zope import component, interface

and setup a simple loops site with a concept manager and some concepts
(with all the type machinery, what in real life is done via standard
ZCML setup):

  >>> from cybertools.relation.interfaces import IRelationRegistry
  >>> from cybertools.relation.registry import DummyRelationRegistry
  >>> relations = DummyRelationRegistry()
  >>> component.provideUtility(relations, IRelationRegistry)

  >>> from cybertools.typology.interfaces import IType
  >>> from loops.interfaces import IConcept, ITypeConcept
  >>> from loops.type import ConceptType, TypeConcept
  >>> component.provideAdapter(ConceptType, (IConcept,), IType)
  >>> component.provideAdapter(TypeConcept, (IConcept,), ITypeConcept)

  >>> from loops.interfaces import ILoops
  >>> from loops.setup import ISetupManager
  >>> from loops.organize.process.setup import SetupManager
  >>> component.provideAdapter(SetupManager, (ILoops,), ISetupManager,
  ...                           name='process')

  >>> from loops.base import Loops
  >>> loopsRoot = site['loops'] = Loops()

  >>> from loops.setup import SetupManager
  >>> setup = SetupManager(loopsRoot)
  >>> concepts, resources, views = setup.setup()

We need some type concepts for controlling the meaning of the concepts objects,
these have already been created during setup:

  >>> process = concepts['process']


Manage processes
================

The classes used in this package are just adapters to IConcept.

  >>> from loops.organize.process.definition import Process
  >>> from cybertools.process.interfaces import IProcess
  >>> component.provideAdapter(Process, (IConcept,), IProcess)

We start with creating a process definition.
Note that in order to discern the concepts created
from their typeInterface adapters we here append a 'C' to the name of
the variables:

  >>> from loops.concept import Concept
  >>> myProcessC = concepts['myProcess'] = Concept(u'A Simple Process')
  >>> myProcessC.conceptType = process
  >>> myProcess = IProcess(myProcessC)


Fin de partie
=============

  >>> placefulTearDown()

