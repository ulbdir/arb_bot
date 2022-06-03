import string

from web3 import Web3
from abi.erc20_abi import erc20_abi

class Erc20:
    def __init__(self, w3: Web3, address: string) -> None:
        self.address = address
        self.contract = w3.eth.contract(Web3.toChecksumAddress(self.address), abi=erc20_abi)
        self.decimals = self.contract.functions.decimals().call()
        self.name = self.contract.functions.name().call()
    
    def convert_amount_to_web3(self, amount: float) -> float:
        return amount * pow(10, self.decimals)
    
    def convert_amount_from_web3(self, amount: float) -> float:
        return amount / pow(10, self.decimals)
