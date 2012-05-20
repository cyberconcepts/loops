# tests.py - loops.knowledge package

import os
import unittest, doctest
from zope.testing.doctestunit import DocFileSuite
from zope.app.testing import ztapi
from zope.interface.verify import verifyClass
from loops.organize.party import Person
from loops.setup import importData as baseImportData


def importData(loopsRoot):
    importPath = os.path.join(os.path.dirname(__file__), 'data')
    baseImportData(loopsRoot, importPath, 'loops_knowledge_de.dmp')


class Test(unittest.TestCase):
    "Basic tests for the knowledge sub-package."

    def testSomething(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
