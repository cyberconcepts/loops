# loops.media.tests

""" Tests for the 'loops.media' package.
"""

import unittest, doctest
from zope.interface.verify import verifyClass


class Test(unittest.TestCase):
    "Basic tests for the media package."

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
