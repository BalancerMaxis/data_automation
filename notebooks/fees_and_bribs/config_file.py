import os
from enum import Enum

from munch import Munch
from web3 import Web3
from web3.middleware import geth_poa_middleware


# Copied from https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json
class Chains(Enum):
    POLYGON = "polygon"
    MAINNET = "mainnet"
    ARBITRUM = "arbitrum"
    # OPTIMISM = "optimism"
    GNOSIS = "gnosis"
    AVALANCHE = "avalanche"
    BASE = "base"


INFURA_KEY = os.environ["WEB3_INFURA_PROJECT_ID"]

## This makes it much easier to setup a dev environment and much easier to read the config, it's also in a few other scripts
## Maybe move to bal_addresses but creates requirement for env var with infura key
WEB3_INSTANCES = Munch({
    "mainnet": Web3(Web3.HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_KEY}")),
    "arbitrum": Web3(Web3.HTTPProvider(f"https://arbitrum-mainnet.infura.io/v3/{INFURA_KEY}")),
    "optimism": Web3(Web3.HTTPProvider(f"https://optimism-rpc.gateway.pokt.network")),
    "polygon": Web3(Web3.HTTPProvider(f"https://polygon-mainnet.infura.io/v3/{INFURA_KEY}")),
    "zkevm": Web3(Web3.HTTPProvider(f"https://zkevm-rpc.com")),
    "base":  Web3(Web3.HTTPProvider("https://developer-access-mainnet.base.org")),
    "avalanche": Web3(Web3.HTTPProvider(f"https://avalanche-mainnet.infura.io/v3/{INFURA_KEY}")),
    "gnosis": Web3(Web3.HTTPProvider(f"https://rpc.gnosischain.com/")),
    "goerli": Web3(Web3.HTTPProvider(f"https://goerli.infura.io/v3/{INFURA_KEY}")),
    "sepolia": Web3(Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{INFURA_KEY}")),
})


#WEB3_INSTANCES = Munch()
#WEB3_INSTANCES[Chains.MAINNET.value] = Web3(Web3.HTTPProvider(os.environ["ETHNODEURL"]))
## poly_web3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
#poly_web3 = Web3(Web3.HTTPProvider(os.environ["POLYNODEURL"]))
#poly_web3.middleware_onion.inject(geth_poa_middleware, layer=0)
#WEB3_INSTANCES[Chains.POLYGON.value] = poly_web3
#WEB3_INSTANCES[Chains.ARBITRUM.value] = Web3(
#    Web3.HTTPProvider(os.environ["ARBNODEURL"])
#)
#WEB3_INSTANCES[Chains.GNOSIS.value] = Web3(
#    Web3.HTTPProvider(os.environ["GNOSISNODEURL"])
#)
#WEB3_INSTANCES[Chains.BASE.value] = Web3(Web3.HTTPProvider(os.environ["BASENODEURL"]))
#WEB3_INSTANCES[Chains.AVALANCHE.value] = Web3(
#    Web3.HTTPProvider(os.environ["AVALANCHENODEURL"])
#)

# Define constants for Arbitrum:
BALANCER_GRAPH_URLS = Munch()
BALANCER_GRAPH_URLS[
    Chains.ARBITRUM.value
] = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-arbitrum-v2"
BALANCER_GRAPH_URLS[
    Chains.MAINNET.value
] = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2"
BALANCER_GRAPH_URLS[
    Chains.POLYGON.value
] = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-polygon-v2"
BALANCER_GRAPH_URLS[
    Chains.GNOSIS.value
] = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-gnosis-chain-v2"
BALANCER_GRAPH_URLS[
    Chains.BASE.value
] = "https://api.studio.thegraph.com/query/24660/balancer-base-v2/version/latest"
BALANCER_GRAPH_URLS[
    Chains.AVALANCHE.value
] = "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-avalanche-v2"
