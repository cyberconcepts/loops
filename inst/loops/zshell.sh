# inst/loops/zshell.sh
set -a

# use environment variables for instance-specific configuration:
#SERVER_ID=0
#LOOPS_PATH=sites/mysite

python -ic "from loops.server import psu; psu.setup()"

