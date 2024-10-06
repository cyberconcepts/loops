# inst/loops/runserver.sh

# use environment variables for instance-specific configuration:
#ZOPE_CONF=zope.conf
#SERVER_PORT=8099

python -c "from loops.server.main import main; main()"
