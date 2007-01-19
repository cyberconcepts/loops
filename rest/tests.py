# $Id$

import unittest, doctest
from zope.testing.doctestunit import DocFileSuite


class Test(unittest.TestCase):
    "Basic tests for the loops.rest package."

    def testBasics(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
