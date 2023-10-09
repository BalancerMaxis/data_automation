import os
from decimal import Decimal
from enum import Enum

from munch import Munch
from web3 import Web3
from web3.middleware import geth_poa_middleware

FEE_TAKEN = Decimal(0.5)  # 50% goes to fees
MIN_AURA_BRIB = Decimal(500)


# Copied from https://raw.githubusercontent.com/BalancerMaxis/bal_addresses/main/extras/chains.json
class Chains(Enum):
    POLYGON = "polygon"
    MAINNET = "mainnet"
    ARBITRUM = "arbitrum"
    # OPTIMISM = "optimism"
    GNOSIS = "gnosis"
    AVALANCHE = "avalanche"
    BASE = "base"


# Rerouting bribs:
REROUTE_CONFIG = Munch()
REROUTE_CONFIG[Chains.MAINNET.value] = {
    'SOURCE_POOL': 'DESTINATION_POOL',
}


CORE_POOLS = Munch()
CORE_POOLS[Chains.MAINNET.value] = [
    "0x93d199263632a4ef4bb438f1feb99e57b4b5f0bd0000000000000000000005c2",
    "0x1e19cf2d73a72ef1332c882f20534b6519be0276000200000000000000000112",
    "0xe7e2c68d3b13d905bbb636709cf4dfd21076b9d20000000000000000000005ca",
    "0xf7a826d47c8e02835d94fb0aa40f0cc9505cb1340002000000000000000005e0",
    "0xf16aee6a71af1a9bc8f56975a4c2705ca7a782bc0002000000000000000004bb",
    "0xb08885e6026bab4333a80024ec25a1a3e1ff2b8a000200000000000000000445",
    "0x8353157092ed8be69a9df8f95af097bbf33cb2af0000000000000000000005d9",
    "0xdfe6e7e18f6cc65fa13c8d8966013d4fda74b6ba000000000000000000000558",
    "0x5f1f4e50ba51d723f12385a8a9606afc3a0555f5000200000000000000000465",
    "0x1ee442b5326009bb18f2f472d3e0061513d1a0ff000200000000000000000464",
    "0x9f9d900462492d4c21e9523ca95a7cd86142f298000200000000000000000462",
    "0x3ff3a210e57cfe679d9ad1e9ba6453a716c56a2e0002000000000000000005d5",
    "0xf01b0684c98cd7ada480bfdf6e43876422fa1fc10002000000000000000005de",
    "0x36be1e97ea98ab43b4debf92742517266f5731a3000200000000000000000466",
]
CORE_POOLS[Chains.POLYGON.value] = [
    "0xf0ad209e2e969eaaa8c882aac71f02d8a047d5c2000200000000000000000b49",
    "0xee278d943584dd8640eaf4cc6c7a5c80c0073e85000200000000000000000bc7",
]
CORE_POOLS[Chains.ARBITRUM.value] = [
    "0xade4a71bb62bec25154cfc7e6ff49a513b491e81000000000000000000000497",
    "0x9791d590788598535278552eecd4b211bfc790cb000000000000000000000498",
    "0x4a2f6ae7f3e5d715689530873ec35593dc28951b000000000000000000000481",
    "0x423a1323c871abc9d89eb06855bf5347048fc4a5000000000000000000000496",
    "0x32df62dc3aed2cd6224193052ce665dc181658410002000000000000000003bd",
    "0x0c8972437a38b389ec83d1e666b69b8a4fcf8bfd00000000000000000000049e",
]
# CORE_POOLS[Chains.GNOSIS.value] = [
#     "0xbad20c15a773bf03ab973302f61fabcea5101f0a000000000000000000000034",
# ]
CORE_POOLS[Chains.BASE.value] = [
    "0xfb4c2e6e6e27b5b4a07a36360c89ede29bb3c9b6000000000000000000000026",
    "0xc771c1a5905420daec317b154eb13e4198ba97d0000000000000000000000023",
    "0x0c659734f1eef9c63b7ebdf78a164cdd745586db000000000000000000000046",
]
CORE_POOLS[Chains.AVALANCHE.value] = [
    "0xfd2620c9cfcec7d152467633b3b0ca338d3d78cc00000000000000000000001c",
    "0xc13546b97b9b1b15372368dc06529d7191081f5b00000000000000000000001d",
    "0x9fa6ab3d78984a69e712730a2227f20bcc8b5ad900000000000000000000001f",
    "0xb26f0e66317846bd5fe0cbaa1d269f0efeb05c9600000000000000000000001e",
    "0x55bec22f8f6c69137ceaf284d9b441db1b9bfedc000200000000000000000011",
]


WEB3_INSTANCES = Munch()
WEB3_INSTANCES[Chains.MAINNET.value] = Web3(Web3.HTTPProvider(os.environ["ETHNODEURL"]))
poly_web3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
poly_web3.middleware_onion.inject(geth_poa_middleware, layer=0)
WEB3_INSTANCES[Chains.POLYGON.value] = poly_web3
WEB3_INSTANCES[Chains.ARBITRUM.value] = Web3(Web3.HTTPProvider(os.environ["ARBNODEURL"]))
WEB3_INSTANCES[Chains.GNOSIS.value] = Web3(Web3.HTTPProvider(os.environ["GNOSISNODEURL"]))
WEB3_INSTANCES[Chains.BASE.value] = Web3(Web3.HTTPProvider(os.environ["BASENODEURL"]))
WEB3_INSTANCES[Chains.AVALANCHE.value] = Web3(Web3.HTTPProvider(os.environ["AVALANCHENODEURL"]))

# Define constants for Arbitrum:
BALANCER_GRAPH_URLS = Munch()
BALANCER_GRAPH_URLS[Chains.ARBITRUM.value] = (
    "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-arbitrum-v2"
)
BALANCER_GRAPH_URLS[Chains.MAINNET.value] = (
    "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2"
)
BALANCER_GRAPH_URLS[Chains.POLYGON.value] = (
    "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-polygon-v2"
)
BALANCER_GRAPH_URLS[Chains.GNOSIS.value] = (
    "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-gnosis-chain-v2"
)
BALANCER_GRAPH_URLS[Chains.BASE.value] = (
    "https://api.studio.thegraph.com/query/24660/balancer-base-v2/version/latest"
)
BALANCER_GRAPH_URLS[Chains.AVALANCHE.value] = (
    "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-avalanche-v2"
)
