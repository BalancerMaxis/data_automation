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

from pycoingecko import CoinGeckoAPI
from web3 import Web3

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

CHAIN_TO_CG_PLATFORM_MAP = {
    "mainnet": "ethereum",
    "arbitrum": "arbitrum-one",
    "polygon": "polygon-pos",
    "optimism": "optimistic-ethereum",
}


@dataclass
class PoolBalance:
    token_addr: str
    token_name: str
    token_symbol: str
    pool_id: str
    balance: Decimal
    cg_token_id: str = ""
    cg_token_price: float = 0.0


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


def get_bpt_price(
    balancer_pool_id: str,
    chain: str,
    web3: Web3,
    date_of_accounting: Optional[date] = date.today() - timedelta(days=1),
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
    # Get all tokens in the pool:
    cg = CoinGeckoAPI()
    balances = _get_balancer_pool_tokens_balances(
        balancer_pool_id=balancer_pool_id, web3=web3, chain=chain
    )
    # Now we need to fetch all coins from coingecko and map them to each of our tokens symbols
    # to get their prices
    coin_list = cg.get_coins_list(include_platform=True)
    chain_to_cg_platform = CHAIN_TO_CG_PLATFORM_MAP[chain]
    for cg_coin in coin_list:
        for balance in balances:
            _token_address = cg_coin["platforms"].get(chain_to_cg_platform)
            if not _token_address:
                continue
            if Web3.toChecksumAddress(_token_address) == balance.token_addr:
                balance.cg_token_id = cg_coin["id"]

    # Now we get all token ids and we can fetch them from coingecko with date
    desired_date = (
        date.today() - timedelta(days=1)
        if not date_of_accounting
        else date_of_accounting
    )
    for balance in balances:
        # Desired date should be str format like DD-MM-YYYY
        _price = cg.get_coin_history_by_id(
            balance.cg_token_id, date=desired_date.strftime("%d-%m-%Y")
        )
        balance.cg_token_price = Decimal(_price["market_data"]["current_price"]["usd"])

    return sum(
        [balance.cg_token_price * balance.balance for balance in balances]
    ) / Decimal(
        weighed_pool_contract.functions.totalSupply().call()
        / 10 ** weighed_pool_contract.functions.decimals().call()
    )


if __name__ == "__main__":
    web3 = Web3(
        Web3.HTTPProvider(
            "https://arb-mainnet.g.alchemy.com/v2/9vSF9OOKeP0YalMNBvAegAtEYA3I9CEQ"
        )
    )
    bpt_price = get_bpt_price(
        "0x32df62dc3aed2cd6224193052ce665dc181658410002000000000000000003bd",
        "arbitrum",
        web3,
    )

    print(bpt_price)
