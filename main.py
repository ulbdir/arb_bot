from enum import Enum
import string
from time import sleep
import time
from web3 import Web3, middleware
from web3.gas_strategies import time_based

from web3.middleware import geth_poa_middleware
from erc20 import Erc20
from exchange import Exchange
from abi.swapper_abi import swapper_abi
import logging
import requests
import config


logging.basicConfig(format = "%(asctime)s %(levelname)s:   %(message)s", level=logging.INFO)

logging.getLogger("web3.RequestManager").setLevel(logging.WARNING)
logging.getLogger("web3.providers.HTTPProvider").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

spookyswap_router = "0xF491e7B69E4244ad4002BC14e878a34207E38c29"
spiritswap_router = "0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52"
protofi_router = "0xF4C587a0972Ac2039BFF67Bc44574bB403eF5235"
sushi_router = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
wigo_router = "0x5023882f4D1EC10544FCB2066abE9C1645E95AA0"
vampire_router = "0x9AdE9Bda74a12022cC82C27Ce24C4296397b18d5"
soulswap_router = "0x6b3d631B87FE27aF29efeC61d2ab8CE4d621cCBF"
zoo_router = "0x40b12a3E261416fF0035586ff96e23c2894560f2"

def getWeb3Ftm():
  w3 = Web3(Web3.HTTPProvider(config.rpc_provider))
  w3.middleware_onion.inject(geth_poa_middleware, layer=0)
  return w3

w3 = getWeb3Ftm()

wftm = Erc20(w3, "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83")

exchanges = [
    Exchange("wigo", w3, wigo_router),
    Exchange("protofi", w3, protofi_router),
    Exchange("spirit", w3, spiritswap_router),
    Exchange("spooky", w3, spookyswap_router),
    Exchange("sushi", w3, sushi_router),
    Exchange("vampire", w3, vampire_router),
    Exchange("zoo", w3, zoo_router)
    #Exchange("soul", w3, soulswap_router)
]

swapper_contract = w3.eth.contract(Web3.toChecksumAddress(config.swapper_address), abi=swapper_abi)

def get_price(router, amount: float, route: list) -> float:
    input_quantity_wei = route[0].convert_amount_to_web3(amount)
    path = [ tk.address for tk in route ]
    result = router.functions.getAmountsOut(int(input_quantity_wei), path).call()
    return route[-1].convert_amount_from_web3(result[-1])

class swap_result(Enum):
    SUCCESSFUL = 1,
    REVERTED = 2,
    FAILED = 3

def execute_multiswap(r1: Exchange, r2: Exchange, token: Erc20, amount: float, gas_price: int) -> bool:
    result = swap_result.FAILED
    try:
        fun = swapper_contract.functions.multiswap(r1.router_address, r2.router_address, token.address, wftm.convert_amount_to_web3(amount))
        tx = fun.buildTransaction({
            'from': config.account_address,
            'nonce': w3.eth.getTransactionCount(config.account_address),
            'gasPrice': gas_price,
        })
        signed_tx = w3.eth.account.signTransaction(tx, config.account_key)
        emitted = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        logging.info("Transaction send, waiting for completion ... ")
        w3.eth.wait_for_transaction_receipt(emitted)
        receipt = w3.eth.get_transaction_receipt(emitted)
        logging.debug("Completed, receipt: " + str(receipt))
        if receipt["status"] == 1:
            result = swap_result.SUCCESSFUL
        else:
            swap_result.REVERTED
            logging.info("Transaction reverted")
    except Exception as e:
        logging.info("Sending transaction failed: " + str(e))
    return result

def discord_message(msg:string) -> None:
    data = {"content": msg}
    try:
        response = requests.post(config.discord_url, json=data)
    except Exception as e:
        logging.warning("Could not post discord message: " + str(e))

def set_approval():
    approve_fun = wftm.contract.functions.approve(config.swapper_address, wftm.convert_amount_to_web3(1000000))
    approve_tx = approve_fun.buildTransaction({
        'from': config.account_address,
        'nonce': w3.eth.getTransactionCount(config.account_address),
        'gasPrice': w3.eth.gas_price,
    })
    signed_tx = w3.eth.account.signTransaction(approve_tx, config.account_key)
    emitted = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    logging.info("Approval send, waiting for completion")
    w3.eth.wait_for_transaction_receipt(emitted)
    logging.info("Approval finished")

def get_allowance() -> float:
    return wftm.convert_amount_from_web3(wftm.contract.functions.allowance(config.account_address, config.swapper_address).call())

def compute_token_list(exchanges: list[Exchange]):
    result = []
    token_list = []
    
    # aggregate all token from all exchanges
    for exch in exchanges:
        token_list += exch.token_paired_with_wftm
    
    # remove duplicates
    token_list = list(set(token_list))

    # for each token, create a list of exchanges that support it
    for token in token_list:
        dexes = []
        for exch in exchanges:
            if token in exch.token_paired_with_wftm:
                dexes.append(exch)
        if len(dexes) > 2:
            result.append( { "token": Erc20(w3, token), "exchanges": dexes } )
    
    return result


# monitored_tokens = [
#     { "token": usdc, "exchanges":[ spookyswap, spiritswap, protofi, sushiswap, wigoswap ] },
#     { "token": btc, "exchanges": [spookyswap, spiritswap, protofi, sushiswap]},
#     { "token": eth, "exchanges": [spookyswap, spiritswap, protofi, sushiswap]},
#     { "token": lqdr, "exchanges": [spookyswap, spiritswap, protofi, sushiswap, wigoswap]},
#     ]

monitored_tokens = compute_token_list(exchanges)

print(monitored_tokens, len(monitored_tokens))

discord_message("Arb Bot started")
logging.info("Arb Bot started")

# if node is syncing, wait until it is ready and in sync
if w3.eth.syncing:
    logging.info("Node is out of sync, waiting")
    while w3.eth.syncing:
        logging.info(str.format("{} blocks to go", w3.eth.syncing["highestBlock"] - w3.eth.syncing["currentBlock"]))
        time.sleep(10)

# check allowance of swapper contract
allowance = get_allowance()
logging.info(str.format("Allowance: {}", allowance))
if allowance < 1000000:
    logging.info("Allowance too small, increasing allowance")
    set_approval()

w3.eth.set_gas_price_strategy(time_based.construct_time_based_gas_price_strategy(3, sample_size=5))
w3.middleware_onion.add(middleware.time_based_cache_middleware)
w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
w3.middleware_onion.add(middleware.simple_cache_middleware)

# initialize gas price
gas = 300000
gas_price = w3.eth.generate_gas_price()
tx_cost = float(Web3.fromWei(gas*gas_price, "ether"))
logging.info(str.format("Estimated tx cost: {:.4f} FTM", tx_cost))


while True:

    amount_to_swap = 50
    token_counter = 0

    for token in monitored_tokens:

        if not w3.eth.syncing:
            # update gas price
            token_counter += 1
            if token_counter % 5 == 0:
                gas_price = w3.eth.generate_gas_price()
                tx_cost = float(Web3.fromWei(gas*gas_price, "ether"))
                logging.info(str.format("Estimated tx cost: {:.4f} FTM", tx_cost))
            
            ex_l = [ e.name for e in token["exchanges"] ]
            logging.info(str.format("{:25} {}", token["token"].name, str(ex_l)))


            max_buy = None
            max_sell = None
            
            # get best buy price for the selected amount to swap
            for exchange in token["exchanges"]:
                try:
                    buy_price = get_price(exchange.router_contract, amount_to_swap, [wftm, token["token"]])
                    logging.debug(str.format("{:>12}    buy {:>12.6f}", exchange.name, buy_price))

                    if max_buy is None or max_buy["price"] < buy_price:
                        max_buy = {"exchange": exchange, "price": buy_price}
                except:
                    pass

            # now find best exchange to swap the received amount back
            for exchange in token["exchanges"]:
                try:
                    sell_price = get_price(exchange.router_contract, max_buy["price"], [token["token"], wftm])
                    logging.debug(str.format("{:>12}    sell {:>12.6f}", exchange.name, sell_price))

                    if max_sell is None or max_sell["price"] < sell_price:
                        max_sell = {"exchange": exchange, "price": sell_price}
                except:
                    pass

            # if profit is expected, execute the swap and log it
            if max_buy is not None and max_sell is not None:
                if max_buy["exchange"] != max_sell["exchange"]:
                    profit = max_sell["price"] - amount_to_swap
                    if profit - tx_cost > 0.05:
                        result = execute_multiswap(max_buy["exchange"], max_sell["exchange"], token["token"], amount_to_swap, gas_price)
                        msg = str.format("{:.2f}/{:.2f} FTM {} buy@{} sell@{} -> {}",profit, amount_to_swap, token["token"].name, max_buy["exchange"].name, max_sell["exchange"].name, result)
                        logging.info(msg)
                        if result == swap_result.SUCCESSFUL or result == swap_result.REVERTED:
                            discord_message(msg)
        else:
            logging.info("Node is syncing")
            time.sleep(5)
