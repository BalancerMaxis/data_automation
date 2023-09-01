import json
import os
from dataclasses import dataclass
from datetime import date
from datetime import timedelta
from decimal import Decimal
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from web3 import Web3
from gql import Client
from gql import gql
from gql.transport.requests import RequestsHTTPTransport

BALANCER_CONTRACTS = {
    "mainnet": {
        "BALANCER_VAULT_ADDRESS": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    },
    "arbitrum": {
        "BALANCER_VAULT_ADDRESS": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    },
    "polygon": {
        "BALANCER_VAULT_ADDRESS": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    },
}

CHAIN_TO_CHAIN_ID_MAP = {
    "mainnet": 1,
    "arbitrum": "42161",
    "polygon": "137",
    "optimism": "10",
}

CHAIN_TO_CG_PLATFORM_MAP = {
    "mainnet": "ethereum",
    "arbitrum": "arbitrum-one",
    "polygon": "polygon-pos",
    "optimism": "optimistic-ethereum",
}

BAL_GQL_QUERY = """
query {{
  tokenGetPriceChartData(address:"{token_addr}", range: THIRTY_DAY)   
   {{
    id
    price
    timestamp
  }}
}}
"""
BAL_GQL_URL = "https://api-v3.balancer.fi/"


@dataclass
class PoolBalance:
    token_addr: str
    token_name: str
    token_symbol: str
    pool_id: str
    balance: Decimal
    cg_token_id: str = ""
    cg_token_price: float = 0.0
    cg_token_prices: List[Decimal] = None


def get_abi(contract_name: str) -> Union[Dict, List[Dict]]:
    project_root_dir = os.path.abspath(os.path.dirname(__file__))
    with open(f"{project_root_dir}/abi/{contract_name}.json") as f:
        return json.load(f)


def _get_balancer_pool_tokens_balances(
    balancer_pool_id: str, web3: Web3, chain: str
) -> Optional[List[PoolBalance]]:
    """
    Returns all token balances for a given balancer pool
    """
    vault_addr = BALANCER_CONTRACTS[chain]["BALANCER_VAULT_ADDRESS"]
    balancer_vault = web3.eth.contract(
        address=web3.toChecksumAddress(vault_addr), abi=get_abi("BalancerVault")
    )

    tokens, balances, _ = balancer_vault.functions.getPoolTokens(
        balancer_pool_id
    ).call()
    token_balances = []
    for index, token in enumerate(tokens):
        token_contract = web3.eth.contract(
            address=web3.toChecksumAddress(token), abi=get_abi("ERC20")
        )
        decimals = token_contract.functions.decimals().call()
        balance = Decimal(balances[index]) / Decimal(10**decimals)
        pool_token_balance = PoolBalance(
            token_addr=token,
            token_name=token_contract.functions.name().call(),
            token_symbol=token_contract.functions.symbol().call(),
            pool_id=balancer_pool_id,
            balance=balance,
        )
        token_balances.append(pool_token_balance)
    return token_balances


def _fetch_token_price_balgql(
    token_addr: str, chain: str, twap_days: Optional[int] = 14
) -> Optional[Decimal]:
    """
    Fetches 30 days of token prices from balancer graphql api and calculate twap over 14 days
    """
    transport = RequestsHTTPTransport(
        url=BAL_GQL_URL,
        retries=2,
        headers={"chainId": CHAIN_TO_CHAIN_ID_MAP[chain]} if chain != "mainnet" else {},
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    query = gql(BAL_GQL_QUERY.format(token_addr=token_addr.lower()))
    result = client.execute(query)
    # Sort result by timestamp desc
    result["tokenGetPriceChartData"].sort(key=lambda x: x["timestamp"], reverse=True)
    # Cut result in half and calculate twap price for 14 days
    result_slice = result["tokenGetPriceChartData"][: len(result["tokenGetPriceChartData"]) // 2]
    # Remove all items that have timestamp before 14 days ago
    result_slice = [
        item for item in result_slice
        if date.fromtimestamp(item["timestamp"]) >= date.today() - timedelta(days=twap_days)
    ]
    # Sum all prices and divide by number of days
    twap_price = Decimal(
        sum([Decimal(item["price"]) for item in result_slice]) / len(result_slice)
    )
    return twap_price


def get_twap_bpt_price(
    balancer_pool_id: str,
    chain: str,
    web3: Web3,
    twap_days: Optional[int] = 14,
) -> Optional[Decimal]:
    """
    BPT dollar price equals to Sum of all underlying ERC20 tokens in the Balancer pool divided by
    total supply of BPT token
    """
    balancer_vault = web3.eth.contract(
        address=web3.toChecksumAddress(
            BALANCER_CONTRACTS[chain]["BALANCER_VAULT_ADDRESS"]
        ),
        abi=get_abi("BalancerVault"),
    )
    balancer_pool_address, _ = balancer_vault.functions.getPool(balancer_pool_id).call()
    weighed_pool_contract = web3.eth.contract(
        address=web3.toChecksumAddress(balancer_pool_address),
        abi=get_abi("WeighedPool"),
    )
    decimals = weighed_pool_contract.functions.decimals().call()
    total_supply = Decimal(weighed_pool_contract.functions.totalSupply().call() / 10**decimals)
    balances = _get_balancer_pool_tokens_balances(
        balancer_pool_id=balancer_pool_id, web3=web3, chain=chain
    )
    # Now let's calculate price with twap
    for balance in balances:
        balance.twap_price = _fetch_token_price_balgql(
            balance.token_addr, chain, twap_days
        )
    # Make sure we have all prices
    if not all([balance.twap_price for balance in balances]):
        return None
    # Now we have all prices, let's calculate total price
    total_price = sum(
        [
            balance.balance * balance.twap_price
            for balance in balances
        ]
    )
    return total_price / Decimal(total_supply)


if __name__ == "__main__":
    web3 = Web3(
        Web3.HTTPProvider(
            "https://arb-mainnet.g.alchemy.com/v2/9vSF9OOKeP0YalMNBvAegAtEYA3I9CEQ"
        )
    )
    bpt_price = get_twap_bpt_price(
        "0x32df62dc3aed2cd6224193052ce665dc181658410002000000000000000003bd",
        "arbitrum",
        web3,
    )

    print(bpt_price)
