# inst/loops/zshell.sh
set -a

# use environment variables for instance-specific configuration:
#ZOPE_CONF=zope-1.conf
#LOOPS_PATH=sites/mysite

python -ic "from loops.server import psu; psu.setup()"

