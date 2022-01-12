"""A registry for managing contracts."""

import threading
from typing import TYPE_CHECKING

from ibapi.contract import Contract, ContractDetails

from .ib_type_logger import *
from .._internal.requests import next_unique_id
from .._internal.threading import LoggingLock

# Type hints on IbTwsClient cause a circular dependency.
# This conditional import plus a string-based annotation avoids the problem.
if TYPE_CHECKING:
    from .tws_client import IbTwsClient


class ContractEntry:
    """Entry in the ContractRegistry."""

    contract: Contract
    contract_details: List[ContractDetails] = []
    error_string: str = None

    def __init__(self, contract: Contract):
        self.contract = contract

    def add_contract_details(self, contract_details: ContractDetails):
        """Adds contract details to the entry."""

        if self.error_string:
            raise Exception(f"Adding contract details to an entry that already has an error string: {self.contract}")

        self.contract_details.append(contract_details)

    def add_error_sring(self, error_string: str):
        """Adds an error string to the entry."""

        if self.error_string:
            raise Exception(f"Multiple error strings for a request: {self.contract} {self.error_string} {error_string}")
        elif self.contract_details:
            raise Exception(f"Adding an error string to an entry that already has contract details: {self.contract}")

        self.error_string = error_string

    def get(self) -> List[ContractDetails]:
        """Gets the details or raises an exception if there are no details."""
        if self.contract_details:
            return self.contract_details
        elif self.error_string is not None:
            raise Exception(self.error_string)
        else:
            raise Exception(f"Contract has no details and no error: {self.contract}")


class ContractRegistry:
    """A registry for mapping between contract requests and official contract specifications."""

    _client: 'IbTwsClient'
    _lock: LoggingLock
    _requests: Dict[int, Tuple[Contract, threading.Event]]
    _contracts: Dict[str, ContractEntry]


    def __init__(self, client: 'IbTwsClient'):
        self._client = client
        self._lock = LoggingLock("ContractRegistry")
        self._requests = {}
        self._contracts = {}


    def add_contract_data(self, req_id: int, contract_details: ContractDetails) -> None:
        """Add new contract details.

        Args:
            req_id (int): Request ID
            contract_details (ContractDetails): Contract details

        Returns:
            None
        """

        with self._lock:
            if not req_id in self._requests:
                return

            (contract, event) = self._requests[req_id]
            self._update_contract_details(contract, contract_details)
            self._update_contract_details(contract_details.contract, contract_details)


    def add_error_data(self, req_id: int, error_string: str) -> None:
        """Add new error details.

        Args:
            req_id (int): Request ID
            error_string (str): error string

        Returns:
            None
        """

        with self._lock:
            if not req_id in self._requests:
                return

            contract, event = self._requests[req_id]
            self._update_error(contract, error_string)

    def request_end(self, req_id: int) -> None:
        """Indicate that the request is over and all data has been received."""

        with self._lock:
            if not req_id in self._requests:
                return

            contract, event = self._requests.pop(req_id)

            if event:
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

    def request_contract_details_blocking(self, contract: Contract) -> List[ContractDetails]:
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

        key = str(contract)

        with self._lock:
            if key not in self._contracts:
                req_id = next_unique_id()
                self._requests[req_id] = (contract, event)
                self._client.log_request(req_id, "ContractDetails", contract, None)
                self._client.reqContractDetails(reqId=req_id, contract=contract)

    def _get_contract_details(self, contract: Contract) -> ContractEntry:
        """Gets the contract details for a query contract."""

        key = str(contract)

        with self._lock:
            return self._contracts.get(key, None)

    def _update_contract_details(self, contract: Contract, contract_details: ContractDetails) -> None:
        """Updates the contract details for a query contract."""

        key = str(contract)

        if key not in self._contracts:
            self._contracts[key] = ContractEntry(contract)

        self._contracts[key].add_contract_details(contract_details)

    def _update_error(self, contract: Contract, error_string: str) -> None:
        """Updates the error string for a query contract."""

        key = str(contract)

        if key not in self._contracts:
            self._contracts[key] = ContractEntry(contract)

        self._contracts[key].add_error_sring(error_string)
