import logging
import traceback
from threading import Thread
from time import sleep

from ibapi.client import EClient
from ibapi.common import *
from ibapi.wrapper import EWrapper

logging.basicConfig(level=logging.DEBUG)


# noinspection PyPep8Naming
class IbTwsClient(EWrapper, EClient):
    thread: Thread

    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.thread = None

    def connect(self, host: str, port: int, client_id: int) -> None:
        print("LOG_MSG start connect")
        print("LOG_MSG isConnected", self.isConnected())

        print("LOG_MSG EClient.connect")
        EClient.connect(self, host, port, client_id)

        # for i in range(100):
        #     ic = self.isConnected()
        #     print(f"DEBUG: connect check {i} {ic}")
        #     if ic:
        #         break
        #     sleep(0.1)

        print("LOG_MSG Thread create")
        self.thread = Thread(target=self.run)
        print("LOG_MSG Thread start")
        self.thread.start()

        print("DEBUG end connect")

    def disconnect(self) -> None:
        print("LOG_MSG start disconnect")
        print("LOG_MSG isConnected", self.isConnected())
        print("LOG_MSG msg_queue.empty", self.msg_queue.empty())
        traceback.print_stack()
        EClient.disconnect(self)
        self.thread = None
        print("LOG_MSG end disconnect")

    def subscribe(self) -> None:
        print("LOG_MSG start subscribe")
        print("LOG_MSG isConnected", self.isConnected())

        # print("LOG_MSG reqManagedAccts")
        # self.reqManagedAccts()
        print("LOG_MSG reqPositions")
        self.reqPositions()
        # print("LOG_MSG reqNewsBulletins")
        # self.reqNewsBulletins(allMsgs=True)
        # print("LOG_MSG reqExecutions")
        # self.reqExecutions(reqId=2, execFilter=ExecutionFilter())
        # print("LOG_MSG reqCompletedOrders")
        # self.reqCompletedOrders(apiOnly=False)
        print("LOG_MSG reqNewsProviders")
        self.reqNewsProviders()
        # print("LOG_MSG reqAllOpenOrders")
        # self.reqAllOpenOrders()
        # print("LOG_MSG reqFamilyCodes")
        # self.reqFamilyCodes()

        print("LOG_MSG isConnected", self.isConnected())
        print("LOG_MSG end subscribe")

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        EWrapper.error(self, reqId, errorCode, errorString)
        print("LOG ERROR: ", reqId, errorCode, errorString)


client = IbTwsClient()
# client.connect(host="host.docker.internal", port=7496, client_id=8)
client.connect(host="", port=7496, client_id=8)

sleep(1)

client.subscribe()
# client.disconnect()

# from time import sleep
# sleep(100)
