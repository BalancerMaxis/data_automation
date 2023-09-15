import json
import os
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from gql import Client
from gql import gql
from gql.transport.requests import RequestsHTTPTransport
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput

BAL_GQL_URL = "https://api-v3.balancer.fi/"

BLOCKS_GQL_URL_ARB = "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-one-blocks"

BLOCKS_BY_CHAIN = {
    "mainnet": "https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks",
    "arbitrum": "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-one-blocks",
    "polygon": "https://api.thegraph.com/subgraphs/name/ianlapham/polygon-blocks",
    "base": "https://api.studio.thegraph.com/query/48427/bleu-base-blocks/version/latest",
    "gnosis": "https://api.thegraph.com/subgraphs/name/rebase-agency/gnosis-chain-blocks",
}

VE_BAL_CONTRACT = "0xC128a9954e6c874eA3d62ce62B468bA073093F25"
AURA_VEBAL_HOLDER = "0xaF52695E1bB01A16D33D7194C28C42b10e0Dbec2"

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
    "base": {
        "BALANCER_VAULT_ADDRESS": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    },
    "gnosis": {
        "BALANCER_VAULT_ADDRESS": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    },
    "avalanche": {
        "BALANCER_VAULT_ADDRESS": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    },
}

CHAIN_TO_CHAIN_ID_MAP = {
    "mainnet": 1,
    "arbitrum": "42161",
    "polygon": "137",
    "optimism": "10",
    "base": "8453",
    "gnosis": "100",
    "avalanche": "43114",
}

CHAIN_TO_CG_PLATFORM_MAP = {
    "mainnet": "ethereum",
    "arbitrum": "arbitrum-one",
    "polygon": "polygon-pos",
    "optimism": "optimistic-ethereum",
}

BAL_GQL_QUERY = """
query {{
  tokenGetPriceChartData(address:"{token_addr}", range: NINETY_DAY)   
   {{
    id
    price
    timestamp
  }}
}}
"""

BLOCKS_QUERY = """
query {{
    blocks(where:{{timestamp_gt: {ts_gt}, timestamp_lt: {ts_lt} }}) {{
    number
    timestamp
    }}
}}
"""


@dataclass
class PoolBalance:
    token_addr: str
    token_name: str
    token_symbol: str
    pool_id: str
    balance: Decimal


def get_abi(contract_name: str) -> Union[Dict, List[Dict]]:
    project_root_dir = os.path.abspath(os.path.dirname(__file__))
    with open(f"{project_root_dir}/abi/{contract_name}.json") as f:
        return json.load(f)


def _get_balancer_pool_tokens_balances(
    balancer_pool_id: str, web3: Web3, chain: str, block_number: Optional[int] = None
) -> Optional[List[PoolBalance]]:
    """
    Returns all token balances for a given balancer pool
    """
    if not block_number:
        block_number = web3.eth.block_number
    vault_addr = BALANCER_CONTRACTS[chain]["BALANCER_VAULT_ADDRESS"]
    balancer_vault = web3.eth.contract(
        address=web3.to_checksum_address(vault_addr), abi=get_abi("BalancerVault")
    )

    # Get all tokens in the pool and their balances
    tokens, balances, _ = balancer_vault.functions.getPoolTokens(
        balancer_pool_id
    ).call(block_identifier=block_number)
    token_balances = []
    for index, token in enumerate(tokens):
        token_contract = web3.eth.contract(
            address=web3.to_checksum_address(token), abi=get_abi("ERC20")
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


def fetch_token_price_balgql(
    token_addr: str,
    chain: str,
    start_date: Optional[datetime] = datetime.now(),
    twap_days: Optional[int] = 14,
) -> Optional[Decimal]:
    """
    Fetches 30 days of token prices from balancer graphql api and calculate twap over 14 days
    """
    start_date_ts = int(start_date.strftime("%s"))
    end_date_ts = int((start_date - timedelta(days=twap_days)).strftime("%s"))
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
    # Filter results so they are in between start_date and end_date timestamps
    result_slice = [
        item
        for item in result["tokenGetPriceChartData"]
        if start_date_ts >= item["timestamp"] >= end_date_ts
    ]
    if len(result_slice) == 0:
        return None
    # Sum all prices and divide by number of days
    twap_price = Decimal(
        sum([Decimal(item["price"]) for item in result_slice]) / len(result_slice)
    )
    return twap_price


def get_twap_bpt_price(
    balancer_pool_id: str,
    chain: str,
    web3: Web3,
    start_date: Optional[datetime] = datetime.now(),
    block_number: Optional[int] = None,
    twap_days: Optional[int] = 14,
) -> Optional[Decimal]:
    """
    BPT dollar price equals to Sum of all underlying ERC20 tokens in the Balancer pool divided by
    total supply of BPT token
    """
    balancer_vault = web3.eth.contract(
        address=web3.to_checksum_address(
            BALANCER_CONTRACTS[chain]["BALANCER_VAULT_ADDRESS"]
        ),
        abi=get_abi("BalancerVault"),
    )
    balancer_pool_address, _ = balancer_vault.functions.getPool(balancer_pool_id).call()
    weighed_pool_contract = web3.eth.contract(
        address=web3.to_checksum_address(balancer_pool_address),
        abi=get_abi("WeighedPool"),
    )
    decimals = weighed_pool_contract.functions.decimals().call()
    try:
        total_supply = Decimal(
            weighed_pool_contract.functions.totalSupply().call(
                block_identifier=block_number
            ) / 10 ** decimals
        )
    except BadFunctionCallOutput:
        print("Pool wasn't created at the block number")
        return None
    balances = _get_balancer_pool_tokens_balances(
        balancer_pool_id=balancer_pool_id, web3=web3, chain=chain,
        block_number=block_number or web3.eth.block_number
    )
    # Now let's calculate price with twap
    for balance in balances:
        balance.twap_price = fetch_token_price_balgql(
            balance.token_addr, chain, start_date, twap_days
        )
    # Make sure we have all prices
    if not all([balance.twap_price for balance in balances]):
        return None
    # Now we have all prices, let's calculate total price
    total_price = sum([balance.balance * balance.twap_price for balance in balances])
    return total_price / Decimal(total_supply)


def calculate_aura_vebal_share(web3: Web3, block_number: int) -> Decimal:
    """
    Function that calculate veBAL share of AURA auraBAL from the total supply of veBAL
    """
    ve_bal_contract = web3.eth.contract(
        address=web3.to_checksum_address(VE_BAL_CONTRACT), abi=get_abi("ERC20")
    )
    total_supply = ve_bal_contract.functions.totalSupply().call(
        block_identifier=block_number
    )
    aura_vebal_balance = ve_bal_contract.functions.balanceOf(
        AURA_VEBAL_HOLDER
    ).call(block_identifier=block_number)
    return Decimal(aura_vebal_balance) / Decimal(total_supply)


def get_block_by_ts(timestamp: int, chain: str) -> int:
    """
    Returns block number for a given timestamp
    """
    if timestamp > int(datetime.now().strftime("%s")):
        timestamp = int(datetime.now().strftime("%s")) - 2000
    transport = RequestsHTTPTransport(
        url=BLOCKS_BY_CHAIN[chain],
        retries=2,
    )
    query = gql(
        BLOCKS_QUERY.format(
            ts_gt=timestamp - 2000,
            ts_lt=timestamp + 2000,
        )
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    result = client.execute(query)
    # Sort result by timestamp desc
    result["blocks"].sort(key=lambda x: x["timestamp"], reverse=True)
    return int(result["blocks"][0]["number"])


if __name__ == "__main__":
    web3 = Web3(
        Web3.HTTPProvider("https://rpc.gnosischain.com")
    )
    bpt_price = get_twap_bpt_price(
        "0xbad20c15a773bf03ab973302f61fabcea5101f0a000000000000000000000034",
        "gnosis",
        web3,
        block_number=29976541,
    )
    print(bpt_price)
