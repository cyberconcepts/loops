# loops.organize.process.tests

import unittest, doctest
from zope.app.testing import ztapi
from zope.interface.verify import verifyClass
from loops.organize.party import Person

class Test(unittest.TestCase):
    "Basic tests for the process sub-package."

    def testSomething(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
        unittest.TestLoader().loadTestsFromTestCase(Test),
        doctest.DocFileSuite('README.txt', optionflags=flags),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
