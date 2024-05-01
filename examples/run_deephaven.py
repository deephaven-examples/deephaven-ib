
# This script runs the Deephaven server with the specified port and JVM arguments.
# The server will run until the script is interrupted.
#
# To connect to the Deephaven IDE, navigate to https://localhost:10000
# The login password is: DeephavenRocks!

import os
from time import sleep
from deephaven_server import Server

_server = Server(port=10000, jvm_args=['-Xmx4g','-Dauthentication.psk=DeephavenRocks!','-Dstorage.path=' + os.path.expanduser('~/.deephaven')])
_server.start()

while True:
    sleep(1)
