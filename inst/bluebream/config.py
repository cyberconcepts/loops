# loops/inst/bluebream/config.py

from dotenv import load_dotenv
from os import getenv

load_dotenv()

server_port = getenv('SERVER_PORT', '8099')

