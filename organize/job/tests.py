# $Id$

import os
import unittest, doctest
from zope.testing.doctestunit import DocFileSuite


testDir = os.path.join(os.path.dirname(__file__), 'testdata')


class Test(unittest.TestCase):
    "Basic tests for the loops.organize.job package."

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
