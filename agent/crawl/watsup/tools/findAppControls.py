""" Lists the windowText and className for a given executable on the system. 
Usage:
    
c:>findAppControls.py example/example1 

c:>findAppControls.py -v example/example1 

- this does it in verbose mode
"""

# Author     : Tim Couper - tim@tizmoi.net
# Date       : 1 August 2004
# Copyright  : Copyright TAC Software Ltd, under Python-like licence.
#              Provided as-is, with no warranty.
# Notes      : Requires watsup


from optparse import OptionParser
parser = OptionParser()
parser.add_option("-v", "--verbose",

                  action="store_true", dest="verbose", default=False,

                  help="print verbose messages")

(options, args) = parser.parse_args()    
if len(args)<1:
    print 'Usage: findAppControls.py <path_to_executable>'

else:
    from watsup.AppControls import AppControls
    try:
        print 'passing',args[0]
        a=AppControls(args[0],verbose=options.verbose)
        a.run()           
       
    except:
        import sys
        print '\n** %s **\n' % sys.exc_info()[1]
        import traceback
        traceback.print_tb(sys.exc_info()[2])

