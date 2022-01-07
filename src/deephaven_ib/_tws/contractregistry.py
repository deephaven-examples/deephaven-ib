import threading
from typing import Dict

from ibapi.client import EClient
from ibapi.contract import Contract, ContractDetails

from .ibtypelogger import *
from .loglock import LogLock
from .._utils import next_unique_id


class ContractEntry:
    """Entry in the ContractRegistry."""

    contract: Contract
    contract_details: ContractDetails
    error_string: str

    def __init__(self, contract: Contract, contract_details: ContractDetails = None, error_string: str = None):
        self.contract = contract
        self.contract_details = contract_details
        self.error_string = error_string

    def get(self) -> ContractDetails:
        """Gets the entry or raises an exception if there is no entry."""
        if self.contract_details is not None:
            return self.contract_details
        elif self.error_string is not None:
            raise Exception(self.error_string)
        else:
            raise Exception(f"Contract has no details and no error: {self.contract}")


class ContractRegistry:
    """A registry for mapping between contract requests and official contract specifications."""

    client: EClient
    lock: LogLock
    requests: Dict[int, Tuple[Contract, threading.Event]]
    contracts: Dict[Contract, ContractEntry]

    def __init__(self, client: EClient):
        self.client = client
        self.lock = LogLock("ContractRegistry")
        self.requests = {}
        self.contracts = {}

    def add_contract_data(self, req_id: int, contract_details: ContractDetails) -> None:
        """Add new contract details.

        Args:
            req_id (int): Request ID
            contract_details (ContractDetails): Contract details

        Returns:
            None
        """

        with self.lock:
            req = self.requests.pop(req_id)
            ce = ContractEntry(contract=req[0], contract_details=contract_details)
            self.contracts[contract_details.contract] = ce
            self.contracts[req[0]] = ce

            event = req[1]
            if event is not None:
                event.set()

    def add_error_data(self, req_id: int, error_string: str) -> None:
        """Add new error details.

        Args:
            req_id (int): Request ID
            error_string (str): error string

        Returns:
            None
        """

        with self.lock:
            if not req_id in self.requests:
                return

            req = self.requests.pop(req_id)

            if req is not None:
                (contract, event) = req
                self.contracts[contract] = ContractEntry(contract=contract, error_string=error_string)

                if event is not None:
                    event.set()


    def request_contract_details_nonblocking(self, contract: Contract) -> None:
        """Request contract details, if they have not yet been retrieved.
        
        Function does not block waiting for results.

        Args:
            contract (Contract): Contract being queried.
            
        Returns:
            None
        """

        self._request_contract_details(contract=contract)

    def request_contract_details_blocking(self, contract: Contract) -> ContractDetails:
        """Request contract details, if they have not yet been retrieved.
        
        Function blocks waiting for results.

        Args:
            contract (Contract): Contract being queried.
            
        Returns:
            ContractDetails

        Raises:
            Exception
        """

        cd = self._get_contract_details(contract)

        if cd is not None:
            return cd.get()
        else:
            event = threading.Event()
            self._request_contract_details(contract=contract, event=event)
            event.wait()
            cd = self._get_contract_details(contract)
            return cd.get()

    def _request_contract_details(self, contract: Contract, event: threading.Event = None) -> None:
        """Request contract details, if they have not yet been retrieved.

        Args:
            contract (Contract): Contract being queried.
            event (threading.Event): Event used to notify the requester that the contract details have been received.

        Returns:
            None
        """

        with self.lock:
            if contract not in self.contracts:
                req_id = next_unique_id()
                self.requests[req_id] = (contract, event)
                self.client.reqContractDetails(reqId=req_id, contract=contract)

    def _get_contract_details(self, contract: Contract) -> ContractEntry:
        """Gets the contract details for a query contract."""

        with self.lock:
            return self.contracts.get(contract, None)
