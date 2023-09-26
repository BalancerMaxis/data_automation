from web3 import Web3

ARB_CHAIN_ID = 42161
BALANCER_GAUGE_URL = (
    "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-gauges"
)
BALANCER_GRAPH_URL = (
    "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-arbitrum-v2"
)
BALANCER_GAUGE_CONTROLLER_ADDR = "0xC128468b7Ce63eA702C1f104D55A2566b13D3ABD"
BALANCER_GAUGE_CONTROLLER_ABI = [
    {
        "stateMutability": "view",
        "type": "function",
        "name": "gauge_relative_weight",
        "inputs": [{"name": "addr", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "gauge_relative_weight",
        "inputs": [
            {"name": "addr", "type": "address"},
            {"name": "time", "type": "uint256"},
        ],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]

# Query to fetch pool snapshots
POOLS_SNAPSHOTS_QUERY = """
{{
  poolSnapshots(
    first: {first}
    skip: {skip}
    orderBy: timestamp
    orderDirection: desc
    where: {{timestamp_gte: {start_ts}, timestamp_lt: {end_ts}}}
  ) {{
    pool {{
      address
      id
      symbol
    }}
    timestamp
    protocolFee
    swapFees
    swapVolume
    liquidity
  }}
}}
"""

CURRENT_YEAR = 2023


ARBITRUM_TO_DISTRIBUTE = 70_000  # 70k arb to distribute to the gauges from airdrop
ARBITRUM_TO_USD_POOL = 10_000  # Constant pool of arb to usd
VOTE_CAP_IN_PERCENT = 10  # 10% cap on any single gauge
ARB_GAUGE_WITH_BONUS = Web3.to_checksum_address("0xa14453084318277b11d38FbE05D857A4f647442B")
ARB_ROOT_GAUGE = Web3.to_checksum_address("0xBb1a15dfd849bc5a6F33C002999c8953aFA626Ad")
