# $Id$

import unittest
from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import ztapi
from zope.interface.verify import verifyClass
from zope.interface import implements
from zope.app import zapi
from zope.app.intid.interfaces import IIntIds

from interfaces import ILoops
from loops import Loops
from interfaces import IConcept, IConceptManager, IDocument, IResourceManager
from interfaces import INode, IViewManager
from loops.concept import Concept, ConceptManager
from loops.resource import Document, ResourceManager
from loops.view import Node, ViewManager

class Test(unittest.TestCase):
    "Basic tests for the loops package."

    def testInterfaces(self):
        verifyClass(ILoops, Loops)
        self.assert_(ILoops.providedBy(Loops()))
        verifyClass(IConcept, Concept)
        self.assert_(IConcept.providedBy(Concept()))
        verifyClass(IConceptManager, ConceptManager)
        self.assert_(IConceptManager.providedBy(ConceptManager()))
        verifyClass(IDocument, Document)
        self.assert_(IDocument.providedBy(Document()))
        verifyClass(IResourceManager, ResourceManager)
        self.assert_(IResourceManager.providedBy(ResourceManager()))
        verifyClass(INode, Node)
        self.assert_(INode.providedBy(Node()))
        verifyClass(IViewManager, ViewManager)
        self.assert_(IViewManager.providedBy(ViewManager()))


def test_suite():
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                DocFileSuite('README.txt'),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
