# inst/loops/runserver.sh
set -a

# use environment variables for instance-specific configuration:
#ZOPE_CONF=zope-1.conf
#SERVER_PORT=8091

python -c "from loops.server.main import main; main()"
