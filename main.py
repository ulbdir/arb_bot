import string
from time import sleep
from web3 import Web3
from web3.middleware import geth_poa_middleware
from erc20_abi import erc20_abi
from spookyswap_abi import spooky_abi
import logging
import requests

#Webhook of my channel. Click on edit channel --> Webhooks --> Creates webhook
discord_url = "https://discord.com/api/webhooks/978684379494760518/KTYWVtAUjourCWxc17g38bq-0SjrVUtjY_aM1FXd1tzP035rGWYfDNuRVlInsdCs4YhB"

logging.basicConfig(format = "%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)

logging.getLogger("web3.RequestManager").setLevel(logging.WARNING)
logging.getLogger("web3.providers.HTTPProvider").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

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

usdc = erc20("0x04068DA6C83AFCFA0e13ba15A6696662335D5B75")
wftm = erc20("0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83")
btc = erc20("0x321162Cd933E2Be498Cd2267a90534A804051b11")
eth = erc20("0x74b23882a30290451A17c44f4F05243b6b58C76d")
lqdr = erc20("0x10b620b2dbAC4Faa7D7FFD71Da486f5D44cd86f9")

def get_price(router, amount: float, route: list) -> float:
    input_quantity_wei = route[0].convert_amount_to_web3(amount)
    path = [ token.address for token in route ]
    result = router.functions.getAmountsOut(int(input_quantity_wei), path).call()
    return route[-1].convert_amount_from_web3(result[-1])

def discord_message(msg:string) -> None:
    data = {"content": msg}
    response = requests.post(discord_url, json=data)


monitored_tokens = [
    { "token": wftm, "sell_amount": 1, "exchanges":[
        { "name": "spooky", "router": spooky_contract, "buy_route": [usdc, wftm], "sell_route":[wftm, usdc] },
        { "name": "spirit", "router": spirit_contract, "buy_route": [usdc, wftm], "sell_route":[wftm, usdc] },
        { "name": "protofi", "router": protofi_contract, "buy_route": [usdc, wftm], "sell_route":[wftm, usdc] },
        { "name": "wigo", "router": wigo_contract, "buy_route": [usdc, wftm], "sell_route":[wftm, usdc] },
        { "name": "sushi", "router": sushi_contract, "buy_route": [usdc, wftm], "sell_route":[wftm, usdc] },
        ]},
    { "token": btc, "sell_amount": 0.01, "exchanges": [
        { "name": "spooky", "router": spooky_contract, "buy_route": [usdc, wftm, btc], "sell_route":[btc, wftm, usdc] },
        { "name": "spirit", "router": spirit_contract, "buy_route": [usdc, wftm, btc], "sell_route":[btc, wftm, usdc] },
        { "name": "protofi", "router": protofi_contract, "buy_route": [usdc, btc], "sell_route":[btc, usdc] },
        { "name": "wigo", "router": wigo_contract, "buy_route": [usdc, wftm, eth, btc], "sell_route":[btc, eth, wftm, usdc] },
        { "name": "sushi", "router": sushi_contract, "buy_route": [usdc, wftm, eth, btc], "sell_route":[btc, eth, wftm, usdc] },
        ]},
    { "token": eth, "sell_amount": 0.1, "exchanges": [
        { "name": "spooky", "router": spooky_contract, "buy_route": [usdc, wftm, eth], "sell_route":[eth, wftm, usdc] },
        { "name": "spirit", "router": spirit_contract, "buy_route": [usdc, wftm, eth], "sell_route":[eth, wftm, usdc] },
        { "name": "protofi", "router": protofi_contract, "buy_route": [usdc, eth], "sell_route":[eth, usdc] },
        { "name": "wigo", "router": wigo_contract, "buy_route": [usdc, wftm, eth], "sell_route":[eth, wftm, usdc] },
        { "name": "sushi", "router": sushi_contract, "buy_route": [usdc, wftm, eth], "sell_route":[eth, wftm, usdc] },
        ]},
    {
        "token": lqdr, "sell_amount": 1, "exchanges": [
            { "name": "protofi", "router": protofi_contract, "buy_route": [usdc, wftm, lqdr], "sell_route":[lqdr, wftm, usdc] },
            { "name": "spooky", "router": spooky_contract, "buy_route": [usdc, wftm, lqdr], "sell_route":[lqdr, wftm, usdc] },
            { "name": "sushi", "router": sushi_contract, "buy_route": [usdc, wftm, lqdr], "sell_route":[lqdr, wftm, usdc] },
            { "name": "spirit", "router": spirit_contract, "buy_route": [usdc, wftm, lqdr], "sell_route":[lqdr, wftm, usdc] },
        ]
    }
    ]

discord_message("Arb Bot started")

while True:
    
    for token in monitored_tokens:
        logging.debug(token["token"].name)
        max_buy = None
        max_sell = None
        for exchange in token["exchanges"]:
            buy_price = get_price(exchange["router"], 100, exchange["buy_route"])
            sell_price = get_price(exchange["router"], token["sell_amount"], exchange["sell_route"])
            logging.debug(str.format("{:>12}    buy {:>12.6f}    sell {:>12.6f}", exchange["name"], buy_price, sell_price))

            if max_buy is None or max_buy["price"] < buy_price:
                max_buy = {"exchange": exchange, "price": buy_price}

            if max_sell is None or max_sell["price"] < sell_price:
                max_sell = {"exchange": exchange, "price": sell_price}

        if (max_buy["exchange"] != max_sell["exchange"]):
            amount_bought = get_price(max_buy["exchange"]["router"], 100, max_buy["exchange"]["buy_route"])
            end_amount = get_price(max_sell["exchange"]["router"], amount_bought, max_sell["exchange"]["sell_route"])
            profit = end_amount - 100
            if profit > 0.05:
                msg = str.format("{:.2f}/$100 {} buy@{} sell@{}",profit, token["token"].name, max_buy["exchange"]["name"], max_sell["exchange"]["name"])
                logging.info(msg)
                discord_message(msg)
                
    sleep(1)