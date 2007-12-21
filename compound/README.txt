===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

  >>> from zope import component
  >>> from zope.traversing.api import getName

Let's set up a loops site with basic and example concepts and resources.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from loops.tests.setup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()


Compund Objects - Hierarchies with Ordered Components
=====================================================

  >>> from loops.compound.base import Compound
  >>> component.provideAdapter(Compound)

  >>> tType = concepts.getTypeConcept()
  >>> from loops.setup import addAndConfigureObject
  >>> from loops.concept import Concept
  >>> from loops.compound.interfaces import ICompound

We first create the compound type and one instance of the newly created
type. We also need an ``ispartof`` predicate.

  >>> tCompound = addAndConfigureObject(concepts, Concept, 'compound',
  ...                   title=u'Compound',
  ...                   conceptType=tType, typeInterface=ICompound)
  >>> c01 = addAndConfigureObject(concepts, Concept, 'c01',
  ...                    title=u'Compound #01', conceptType=tCompound)
  >>> tPredicate = concepts.getPredicateType()
  >>> isPartof = addAndConfigureObject(concepts, Concept, 'ispartof',
  ...                   title=u'is Part of', conceptType=tPredicate)

In order to access the compound concept's attributes we have to adapt
it.

  >>> from loops.common import adapted
  >>> aC01 = adapted(c01)

Now we are able to add resources to it.

  >>> aC01.add(resources[u'd003.txt'])
  >>> aC01.add(resources[u'd001.txt'])

  >>> [getName(p) for p in aC01.getParts()]
  [u'd003.txt', u'd001.txt']

  >>> aC01.add(resources[u'd001.txt'], 0)
  >>> [getName(p) for p in aC01.getParts()]
  [u'd001.txt', u'd003.txt', u'd001.txt']

  >>> aC01.add(resources[u'd002.txt'], -1)
  >>> [getName(p) for p in aC01.getParts()]
  [u'd001.txt', u'd003.txt', u'd002.txt', u'd001.txt']

We can reorder the parts of a compound.

  >>> aC01.reorder([resources[u'd002.txt'], resources[u'd001.txt'], ])
  >>> [getName(p) for p in aC01.getParts()]
  [u'd002.txt', u'd001.txt', u'd003.txt', u'd001.txt']

And remove a part from the compound.

  >>> aC01.remove(resources[u'd001.txt'], 1)
  >>> [getName(p) for p in aC01.getParts()]
  [u'd002.txt', u'd003.txt', u'd001.txt']

