===============================================================
loops - Linked Objects for Organization and Processing Services
===============================================================

  ($Id$)

  >>> from zope import component
  >>> from zope.traversing.api import getName
  >>> from loops.common import adapted
  >>> from loops.concept import Concept
  >>> from loops.setup import addAndConfigureObject

Let's set up a loops site with basic and example concepts and resources.

  >>> from zope.app.testing.setup import placefulSetUp, placefulTearDown
  >>> site = placefulSetUp(True)

  >>> from loops.constraint.testsetup import TestSite
  >>> t = TestSite(site)
  >>> concepts, resources, views = t.setup()

  >>> tType = concepts.getTypeConcept()


Constraints - Restrict Predicates and Types for Concept and Resource Assignments
================================================================================

We create a person type and an institution type and a corresponding
predicate.

  >>> tPerson = addAndConfigureObject(concepts, Concept, 'person',
  ...                               title='Person', conceptType=tType)
  >>> tInstitution = addAndConfigureObject(concepts, Concept, 'institution',
  ...                               title='Institution', conceptType=tType)
  >>> tPredicate = concepts.getPredicateType()
  >>> isEmployedBy = addAndConfigureObject(concepts, Concept, 'isemployedby',
  ...                               title='is Employed by', conceptType=tPredicate)

The static constraint concept type has already been created during setup.
We create a simple constraint that

  >>> tStaticConstraint = concepts['staticconstraint']
  >>> cstr01 = addAndConfigureObject(concepts, Concept, 'cstr01',
  ...                   title='Demo Constraint', conceptType=tStaticConstraint)

  >>> aCstr01 = adapted(cstr01)
  >>> aCstr01.predicates = [isEmployedBy]
  >>> aCstr01.types = [tInstitution]

We can now use this constraint to control the parent concepts a person
may be assigned to.

  >>> from loops.constraint.base import hasConstraint
  >>> tPerson.assignParent(cstr01, hasConstraint)
