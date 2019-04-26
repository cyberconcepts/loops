
import unittest, doctest
from zope.interface.verify import verifyClass
#from loops.versioning import versionable

class Test(unittest.TestCase):
    "Basic tests for the integrator sub-package."

    def testSomething(self):
        pass


def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    return unittest.TestSuite((
                unittest.makeSuite(Test),
                doctest.DocFileSuite('README.txt', optionflags=flags),
            ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
