
import unittest, doctest
from zope.interface.verify import verifyClass
try:
    from loops.expert import query
    ignore = False
except ImportError:
    print('Skipping loops.expert')
    ignore = True

class Test(unittest.TestCase):
    "Basic tests for the expert sub-package."

    def testSomething(self):
        pass


def test_suite():
    if ignore:
        return unittest.TestSuite()  # do nothing
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                doctest.DocFileSuite('README.txt', optionflags=flags),
                doctest.DocFileSuite('search.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
