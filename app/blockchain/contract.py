from app.blockchain.client import BlockchainClient
from app.blockchain.utils import get_contract_abi
from app.blockchain.compiled_contract import CONTRACT_BYTECODE
from app.models.blockchain_config import BlockchainConfig
from app import db


class ProductRegistryContract:
    """Wrapper for the ProductRegistry smart contract.

    Uses transact() directly - Ganache accounts are pre-unlocked,
    so no manual signing is needed.
    """

    def __init__(self):
        self.config = BlockchainConfig.get_active_config()
        self.contract = None

        if self.config and self.config.contract_address:
            self._connect()

    def _connect(self):
        client = BlockchainClient()
        if client.is_connected():
            self.contract = client.w3.eth.contract(
                address=client.w3.to_checksum_address(self.config.contract_address),
                abi=get_contract_abi()
            )

    def is_ready(self):
        if not self.contract:
            self._connect()
        return self.contract is not None and BlockchainClient().is_connected()

    def deploy(self, from_address):
        """Deploy the contract to the blockchain using Ganache account 0."""
        abi = get_contract_abi()
        bytecode = CONTRACT_BYTECODE

        client = BlockchainClient()
        if not client.is_connected():
            raise Exception("Not connected to blockchain")

        Contract = client.w3.eth.contract(abi=abi, bytecode=bytecode)

        # Deploy using transact() - Ganache accounts are unlocked
        result = client.deploy_contract(
            Contract.constructor(),
            from_address=from_address,
            gas_limit=3000000
        )

        return result

    def mint_product(self, product_code, metadata_uri, creator_address, from_address):
        """Mint a new product NFT on the blockchain."""
        if not self.is_ready():
            raise Exception("Contract not ready")

        client = BlockchainClient()

        # Get next token ID before minting
        # Check both blockchain and database to avoid conflicts
        try:
            blockchain_token_id = self.contract.functions.totalSupply().call() + 1
        except Exception:
            blockchain_token_id = 1
        
        # Also check database for existing token IDs to prevent conflicts
        try:
            from app.models import BlockchainProduct
            max_db_token = db.session.query(db.func.max(BlockchainProduct.token_id)).scalar() or 0
            next_token_id = max(blockchain_token_id, max_db_token + 1)
        except Exception:
            # If database query fails, use blockchain value
            next_token_id = blockchain_token_id

        mint_func = self.contract.functions.mintProduct(
            product_code,
            metadata_uri,
            creator_address
        )

        tx_result = client.send_transaction(
            mint_func,
            from_address=from_address,
            gas_limit=300000
        )
        tx_result['token_id'] = next_token_id

        return tx_result

    def transfer_ownership(self, token_id, to_address, price, from_address):
        """Transfer ownership of a product on the blockchain."""
        if not self.is_ready():
            raise Exception("Contract not ready")

        client = BlockchainClient()

        transfer_func = self.contract.functions.transferOwnership(
            int(token_id),
            to_address,
            int(price)
        )

        return client.send_transaction(
            transfer_func,
            from_address=from_address,
            gas_limit=300000
        )

    def get_product(self, token_id):
        if not self.is_ready():
            return None
        try:
            return self.contract.functions.getProduct(int(token_id)).call()
        except Exception:
            return None

    def get_product_by_code(self, product_code):
        if not self.is_ready():
            return None
        try:
            return self.contract.functions.getProductByCode(product_code).call()
        except Exception:
            return None

    def verify_product(self, token_id):
        if not self.is_ready():
            return None
        try:
            return self.contract.functions.verifyProduct(int(token_id)).call()
        except Exception:
            return None

    def total_supply(self):
        if not self.is_ready():
            return 0
        try:
            return self.contract.functions.totalSupply().call()
        except Exception:
            return 0
