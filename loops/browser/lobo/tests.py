# loops.browser.lobo.tests

import unittest, doctest
from zope.interface.verify import verifyClass

class Test(unittest.TestCase):
    "Basic tests for the browser.lobo sub-package."

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
