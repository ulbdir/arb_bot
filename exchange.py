import string
from web3 import Web3
from web3.middleware import geth_poa_middleware
import config
from abi.uniswapv2_router import uniswapv2_router_abi
from abi.uniswapv2_factory import uniswapv2_factory_abi
from abi.uniswapv2_pair import uniswapv2_pair_abi
from erc20 import Erc20
import logging
import json

class Exchange:

    def __init__(self, name: string, web3: Web3, router_address: string) -> None:
        logging.info("Initialising exchange " + name)
        self.name = name
        self.router_address = router_address
        self.router_contract = web3.eth.contract(Web3.toChecksumAddress(router_address), abi=uniswapv2_router_abi)
        self.token_paired_with_wftm = self._get_token_paired_with_wftm()

    def _get_pairs(self) -> list:
        result = self.load_pairs()

        if result is not None and len(result) > 0:
            return result

        logging.info("Queying token pairs from web3")

        w3 = self.router_contract.web3
        factory_address = self.router_contract.functions.factory().call()
        self.factory_contract = w3.eth.contract(Web3.toChecksumAddress(factory_address), abi=uniswapv2_factory_abi)
        num_pairs = self.factory_contract.functions.allPairsLength().call()
        
        for i in range(num_pairs):
            pair_address = self.factory_contract.functions.allPairs(i).call()
            pair_contract = w3.eth.contract(Web3.toChecksumAddress(pair_address), abi=uniswapv2_pair_abi)
            token0_address = pair_contract.functions.token0().call()
            token1_address = pair_contract.functions.token1().call()
            result.append([token0_address, token1_address])
            print("\r", i, "/", num_pairs, end="")

        print()

        self.save_pairs(result)

        return result

    def _get_token_paired_with_wftm(self) -> list:
        result = []
        pairs = self._get_pairs()

        wftm_address = self.router_contract.functions.WETH().call()

        for pair in pairs:
            if pair[0] == wftm_address:
                result.append(pair[1])
            elif pair[1] == wftm_address:
                result.append(pair[0])

        return result

    def save_pairs(self, pairs: list):
        with open(self.name + "_pairs.json", "w") as write_file:
            json.dump(pairs, write_file)

    def load_pairs(self) -> list:
        result = []
        try:
            with open(self.name + "_pairs.json", "r") as read_file:
                result = json.load(read_file)
        except:
            logging.info("Could not load pairs for " + self.name)
        return result

if __name__ == "__main__":
    w3 = Web3(Web3.HTTPProvider(config.rpc_provider))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    protofi = Exchange("ProtoFi", w3, "0xF4C587a0972Ac2039BFF67Bc44574bB403eF5235")
    token = protofi.token_paired_with_wftm
    print(token)