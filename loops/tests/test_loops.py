
import unittest, doctest
from zope.interface.verify import verifyClass
from zope.intid.interfaces import IIntIds

from loops.interfaces import ILoops
from loops.base import Loops
from loops.interfaces import IConcept, IConceptManager
from loops.interfaces import IDocument, IMediaAsset, IResourceManager
from loops.interfaces import INode, IViewManager
from loops.concept import Concept, ConceptManager
from loops.resource import Document, MediaAsset, ResourceManager
from loops.view import Node, ViewManager

# just for making sure there aren't any syntax and other errors during
# Zope startup:

from loops.browser.manager import LoopsAddForm, LoopsEditForm


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
        verifyClass(IMediaAsset, MediaAsset)
        self.assert_(IMediaAsset.providedBy(MediaAsset()))
        verifyClass(IResourceManager, ResourceManager)
        self.assert_(IResourceManager.providedBy(ResourceManager()))
        verifyClass(INode, Node)
        self.assert_(INode.providedBy(Node()))
        verifyClass(IViewManager, ViewManager)
        self.assert_(IViewManager.providedBy(ViewManager()))


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                doctest.DocFileSuite('../README.txt', optionflags=flags),
                #doctest.DocFileSuite('../helpers.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
