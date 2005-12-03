loops - Linked Objects for Organizational Process Services
==========================================================

  ($Id$)

Concepts and Relations between them
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's start with creating a few example concepts, putting them in a
top-level loops container and a concept manager:

    >>> from loops import Loops
    >>> loops = Loops()
        
    >>> from loops.concept import ConceptManager, Concept
    >>> loops['concepts'] = ConceptManager()
    >>> concepts = loops['concepts']
    >>> c1 = Concept()
    >>> concepts['c1'] = c1
    >>> c1.title
    u''

    >>> c2 = Concept(u'c2', u'Second Concept')
    >>> concepts['c2'] = c2
    >>> c2.title
    u'Second Concept'

Now we want to relate the second concept to the first one.

In order to do this we first have to provide a relations registry. For
testing we use a simple dummy implementation.

    >>> from cybertools.relation.interfaces import IRelationsRegistry
    >>> from cybertools.relation.registry import DummyRelationsRegistry
    >>> from zope.app.testing import ztapi
    >>> ztapi.provideUtility(IRelationsRegistry, DummyRelationsRegistry())

We also need a Relation class to be used for connecting concepts:

    >>> from cybertools.relation import DyadicRelation

Now we can assign the concept c2 to c1:
        
    >>> c1.assignConcept(c2)

We can now ask our concepts for their related concepts:

    >>> sc1 = c1.getSubConcepts()
    >>> len(sc1)
    1
    >>> c2 in sc1
    True
    >>> len(c1.getParentConcepts())
    0

    >>> pc2 = c2.getParentConcepts()
    >>> len(pc2)
    1
        
    >>> c1 in pc2
    True
    >>> len(c2.getSubConcepts())
    0
        
