import time
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound
import logging
import config
from abi.uniswapv2_router import uniswapv2_router_abi


class BlockAnalyzer:

    def __init__(self, web3: Web3) -> None:
        self._web3 = web3
        self._filter_tx = web3.eth.filter('pending')
        self._filter_blocks = web3.eth.filter('latest')

    def process_pending_transactions(self):
        result = []

        pending_tx = self._filter_tx.get_new_entries()

        for tx_hash in pending_tx:
            try:
                tx = self._web3.eth.get_transaction(tx_hash)
                result.extend(self._process_transaction(tx))

            except TransactionNotFound as e:
                # tx was invalid or canceld
                pass
        
        return set(result)

    def process_latest_blocks(self):
        result = []

        new_blocks = self._filter_blocks.get_new_entries()

        for block_id in new_blocks:
            block = self._web3.eth.get_block(block_id, full_transactions=True)

            for tx in block["transactions"]:
                result.extend(self._process_transaction(tx))
        
        return set(result)


    def _process_transaction(self, tx):
        result = []
        # try to decode the input data as uniswap swap
        try:
            contract = self._web3.eth.contract(
                address=tx["to"], abi=uniswapv2_router_abi)
            func_obj, func_params = contract.decode_function_input(tx["input"])

            if "token" in func_params:
                result.append(func_params["token"])
            elif "tokenA" in func_params:
                result.append(func_params["tokenA"])
            elif "tokenB" in func_params:
                result.append(func_params["tokenB"])
            elif "path" in func_params:
                for token in func_params["path"]:
                    result.append(token)

        except ValueError as e:
            # abi didnt match
            pass
        
        return result



if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:   %(message)s", level=logging.INFO)
    w3 = Web3(Web3.HTTPProvider(config.rpc_provider))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    ba = BlockAnalyzer(w3)

    while True:
        r = ba.process_latest_blocks()
        logging.info(str.format("Token found: {}", len(r)))
        time.sleep(1)
