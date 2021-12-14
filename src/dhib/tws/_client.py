from threading import Thread

from ibapi.client import EClient

from ._listener import IbListener


class IbClient(EClient):
    """Client for connecting to IB TWS.  Can be used to request data, send orders, etc."""

    def __init__(self, listener: IbListener):
        EClient.__init__(self, listener)
        self.thread = None

    def connect(self, host: str = "", port: int = 7497, clientId: int = 0) -> None:
        """Connect to an IB TWS session.  Raises an exception if already connected.

        Args:
            host (str): The host name or IP address of the machine where TWS is running. Leave blank to connect to the local host.
            port (int): TWS port, specified in TWS on the Configure>API>Socket Port field.
                By default production trading uses port 7496 and paper trading uses port 7497.
            clientId (int): A number used to identify this client connection.
                All orders placed/modified from this client will be associated with this client identifier.

                Note: Each client MUST connect with a unique clientId.

        Returns:
              None

        Raises:
              Exception
        """

        if self.thread is not None:
            raise Exception("IbClient is already connected.")

        EClient.connect(self, host, port, clientId)

        self.thread = Thread(target=self.run)
        self.thread.start()
        setattr(self, "_thread", self.thread)  # TODO: ???

    def disconnect(self) -> None:
        """Disconnect from an IB TWS session.  Raises an exception if not already connected.

        Returns:
            None

        Raises:
            Exception
        """

        if self.thread is None:
            raise Exception("IbClient is not connected.")

        EClient.disconnect(self)
        self.thread = None

# # Below is the program execution
#
# if __name__ == '__main__':
#
#     # Specifies that we are on local host with port 7497 (paper trading port number)
#     app = TestApp("127.0.0.1", 7497, 0)
#
#     # A printout to show the program began
#     print("The program has begun")
#
#     #assigning the return from our clock method to a variable
#     requested_time = app.server_clock()
#
#     #printing the return from the server
#     print("")
#     print("This is the current time from the server " )
#     print(requested_time)
#
#     #disconnect the app when we are done with this one execution
#     # app.disconnect()
#
# # Below is the input area
