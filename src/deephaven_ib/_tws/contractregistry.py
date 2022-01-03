from threading import Condition, RLock
from typing import Dict

from ibapi.client import EClient
from ibapi.contract import Contract, ContractDetails

from .ibtypelogger import *
from ..utils import next_unique_id


class ContractRegistry:
    """A registry for mapping between contract requests and official contract specifications."""

    client: EClient
    lock: RLock
    requests: Dict[int, Tuple[Contract, Condition]]
    contracts: Dict[Contract, ContractDetails]

    def __init__(self, client: EClient):
        self.client = client
        self.lock = RLock()
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
        self.lock.acquire()
        req = self.requests.pop(req_id)
        self.contracts[contract_details.contract] = contract_details
        self.contracts[req[0]] = contract_details

        if req[1] is not None:
            req[1].notify_all()

        self.lock.release()

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
        """

        cd = self._get_contract_details(contract)

        if cd is not None:
            return cd
        else:
            condition = Condition()
            self._request_contract_details(contract=contract, condition=condition)
            condition.wait()
            return self._get_contract_details(contract)

    def _request_contract_details(self, contract: Contract, condition: Condition = None) -> None:
        """Request contract details, if they have not yet been retrieved.

        Args:
            contract (Contract): Contract being queried.
            condition (Condition): Condition used to notify the requester that the contract details have been received.

        Returns:
            None
        """

        self.lock.acquire()

        if self._get_contract_details(contract) is None:
            req_id = next_unique_id()
            self.requests[req_id] = (contract, condition)
            self.client.reqContractDetails(reqId=req_id, contract=contract)

        self.lock.release()

    def _get_contract_details(self, contract: Contract) -> ContractDetails:
        """Gets the contract details for a query contract."""
        self.lock.acquire()
        c = self.contracts[contract]
        self.lock.release()
        return c

# TODO: **** what happens if the contract does not exist or there is another error?
