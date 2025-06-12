import os
from web3 import Web3


class BlockchainClient:
    """Web3 client for interacting with the blockchain.
    
    For Ganache (development): accounts are pre-unlocked, so we use
    transact() directly without manual signing.
    
    Implemented as a singleton to prevent multiple connections.
    """
    
    _instance = None
    _rpc_url = None

    def __new__(cls, rpc_url=None):
        if cls._instance is None:
            cls._rpc_url = rpc_url or os.environ.get('BLOCKCHAIN_RPC_URL', 'http://127.0.0.1:8545')
            cls._instance = super(BlockchainClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the Web3 connection once."""
        self.w3 = Web3(Web3.HTTPProvider(self.__class__._rpc_url))

    def is_connected(self):
        return self.w3.is_connected()

    def get_block_number(self):
        return self.w3.eth.block_number

    def get_balance(self, address):
        if not self.is_connected():
            return 0
        try:
            balance = self.w3.eth.get_balance(address)
            return self.w3.from_wei(balance, 'ether')
        except Exception:
            return 0

    def send_transaction(self, contract_function, from_address, gas_limit=300000):
        """Send a transaction using transact() - works with Ganache unlocked accounts."""
        if not self.is_connected():
            raise Exception("Not connected to blockchain")

        tx_hash = contract_function.transact({
            'from': from_address,
            'gas': gas_limit,
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            'transaction_hash': tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash),
            'block_number': receipt.blockNumber,
            'gas_used': receipt.gasUsed,
            'status': receipt.status
        }

    def deploy_contract(self, contract_constructor, from_address, gas_limit=3000000):
        """Deploy a contract using transact() - works with Ganache unlocked accounts."""
        if not self.is_connected():
            raise Exception("Not connected to blockchain")

        tx_hash = contract_constructor.transact({
            'from': from_address,
            'gas': gas_limit,
        })

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            'contract_address': receipt.contractAddress,
            'transaction_hash': tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash),
            'block_number': receipt.blockNumber,
            'gas_used': receipt.gasUsed
        }

    def call_function(self, contract_function):
        """Call a view function (no transaction needed)."""
        if not self.is_connected():
            raise Exception("Not connected to blockchain")
        return contract_function.call()
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance - useful for reconnection."""
        cls._instance = None
        cls._rpc_url = None
