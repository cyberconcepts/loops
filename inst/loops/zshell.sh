# inst/loops/zshell.sh

# use environment variables for instance-specific configuration:
#ZOPE_CONF=zope.conf
#LOOPS_PATH=sites/mysite

python -ic "from loops.server import psu; psu.setup()"

