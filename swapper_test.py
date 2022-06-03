import string
from web3 import Web3
from web3.middleware import geth_poa_middleware
from spookyswap_abi import spooky_abi
from abi.erc20_abi import erc20_abi
import config


swapper_abi = '''[
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "r1",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "r2",
				"type": "address"
			},
			{
				"internalType": "address",
				"name": "token",
				"type": "address"
			},
			{
				"internalType": "uint256",
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "multiswap",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "previousOwner",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "address",
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "OwnershipTransferred",
		"type": "event"
	},
	{
		"inputs": [],
		"name": "renounceOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "transferOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "withdrawNative",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "_token",
				"type": "address"
			}
		],
		"name": "withdrawTokens",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"stateMutability": "payable",
		"type": "receive"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "tc1",
				"type": "address"
			}
		],
		"name": "getBalance",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]'''
swapper_address = "0x8Cc7A08506cBb138363cE22Cb4FfC9D341781cC3"

spookyswap_router = "0xF491e7B69E4244ad4002BC14e878a34207E38c29"
spiritswap_router = "0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52"
protofi_router = "0xF4C587a0972Ac2039BFF67Bc44574bB403eF5235"
sushi_router = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
wigo_router = "0x5023882f4D1EC10544FCB2066abE9C1645E95AA0"

def getWeb3Ftm():
  w3 = Web3(Web3.HTTPProvider('https://rpc.ftm.tools/'))
  #w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/fantom"))
  w3.middleware_onion.inject(geth_poa_middleware, layer=0)
  return w3

w3 = getWeb3Ftm()
spooky_contract = w3.eth.contract(Web3.toChecksumAddress(spookyswap_router), abi=spooky_abi)
spirit_contract = w3.eth.contract(Web3.toChecksumAddress(spiritswap_router), abi=spooky_abi) # same abi for now
protofi_contract = w3.eth.contract(Web3.toChecksumAddress(protofi_router), abi=spooky_abi) # same abi for now
sushi_contract = w3.eth.contract(Web3.toChecksumAddress(sushi_router), abi=spooky_abi) # same abi for now
wigo_contract = w3.eth.contract(Web3.toChecksumAddress(wigo_router), abi=spooky_abi) # same abi for now

swapper_contract = w3.eth.contract(Web3.toChecksumAddress(swapper_address), abi=swapper_abi)

wftm = "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83"
usdc = "0x04068DA6C83AFCFA0e13ba15A6696662335D5B75"

class erc20:
    def __init__(self, address: string) -> None:
        self.address = address
        self.contract = contract = w3.eth.contract(Web3.toChecksumAddress(self.address), abi=erc20_abi)
        self.decimals = self.contract.functions.decimals().call()
        self.name = self.contract.functions.name().call()
        print(self.name, self.decimals)
    
    def convert_amount_to_web3(self, amount: float) -> float:
        return amount * pow(10, self.decimals)
    
    def convert_amount_from_web3(self, amount: float) -> float:
        return amount / pow(10, self.decimals)

wftm_erc20 = erc20(wftm)

wftm_contract = w3.eth.contract(Web3.toChecksumAddress(wftm), abi=erc20_abi)
approve_fun = wftm_contract.functions.approve(swapper_address, wftm_erc20.convert_amount_to_web3(1000000))
requiredGas = approve_fun.estimateGas({"from": config.account_address})
print(requiredGas)

# approve_tx = approve_fun.buildTransaction({
#   'from': config.account_address,
#   'nonce': w3.eth.getTransactionCount(config.account_address),
#   'gasPrice': w3.eth.gas_price,
#   'gas': requiredGas,
# })
# signed_tx = w3.eth.account.signTransaction(approve_tx, config.account_key)
# emitted = w3.eth.sendRawTransaction(signed_tx.rawTransaction)

# print(emitted)

fun = swapper_contract.functions.multiswap(spookyswap_router, protofi_router, usdc, wftm_erc20.convert_amount_to_web3(10))
tx = fun.buildTransaction({
  'from': config.account_address,
  'nonce': w3.eth.getTransactionCount(config.account_address),
  'gasPrice': w3.eth.gas_price,
})
signed_tx = w3.eth.account.signTransaction(tx, config.account_key)
emitted = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
logging.debug("Transaction send, waiting for completion")
w3.eth.wait_for_transaction_receipt(emitted)