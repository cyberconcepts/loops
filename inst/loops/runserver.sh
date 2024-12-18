# inst/loops/runserver.sh
set -a

# use environment variables for instance-specific configuration:
#SERVER_ID=0

python -c "from loops.server.main import main; main()"
