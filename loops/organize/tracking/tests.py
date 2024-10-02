# loops.organize.tracking.tests

import os
import unittest, doctest


testDir = os.path.join(os.path.dirname(__file__), 'testdata')


class Test(unittest.TestCase):
    "Basic tests for the loops.organize.tracking package."

    def testBasics(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
        unittest.TestLoader().loadTestsFromTestCase(Test),
        doctest.DocFileSuite('README.txt', optionflags=flags),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
