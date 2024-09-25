
import unittest, doctest
import warnings
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
        warnings.filterwarnings('ignore', category=ResourceWarning)
        verifyClass(ILoops, Loops)
        self.assertTrue(ILoops.providedBy(Loops()))
        verifyClass(IConcept, Concept)
        self.assertTrue(IConcept.providedBy(Concept()))
        verifyClass(IConceptManager, ConceptManager)
        self.assertTrue(IConceptManager.providedBy(ConceptManager()))
        verifyClass(IDocument, Document)
        self.assertTrue(IDocument.providedBy(Document()))
        verifyClass(IMediaAsset, MediaAsset)
        self.assertTrue(IMediaAsset.providedBy(MediaAsset()))
        verifyClass(IResourceManager, ResourceManager)
        self.assertTrue(IResourceManager.providedBy(ResourceManager()))
        verifyClass(INode, Node)
        self.assertTrue(INode.providedBy(Node()))
        verifyClass(IViewManager, ViewManager)
        self.assertTrue(IViewManager.providedBy(ViewManager()))


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                doctest.DocFileSuite('../README.txt', optionflags=flags),
                doctest.DocFileSuite('../helpers.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
