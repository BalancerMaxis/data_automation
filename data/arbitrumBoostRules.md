# $ARB Liquidity incentives program override rules

The incentives program pays out 97,704 per week ARB based on veBAL voting for pools on Arbitrum.

The vote weight per pool is multiplied by a boost factor, then ARB is distributed to all pools based on their relative boosted weight.

Pools are capped at 10% of the total weekly $ARB, except for ETH based LSD stableswap pools which are capped at 20%

Boosts and caps are defined per gauge in [arbitrumGrantGaugeMetadata.json](arbitrumGrantGuageMetadata.json)
## How boost is calculated

Boost is based on 2 factors.

1. A fixed boost granted to incentive important initiatives
2. A variable boost based on the efficiency of the pool (fees/emissions)

### Fixed boost
By default, all pools have a fixed boost of 1.  The following table describes situations that receive a higher fixed boost:

| Desired Outcome/Activity | Fixed Boost |
|--------------------------|-------------|
| Ecosystem Integration    | 1.5x        |
| Core Infrastructure      | 1.75x       |
| New and Novel AMM tech   | 2x          |


#### Ecosystem Integrations (1.5x)
 - Boosted pools https://docs.balancer.fi/concepts/pools/boosted.html pools with a boosted component that deposit idle liquidity into yield bearing strategies across the Arbitrum ecosystem
- Yield splitting protocols (such as Pendle) will have extra ARB allocated to the supported pools that have TVL >$1m
- Concentrated liquidity pool types by Gyroscope 
- FXPool https://docs.xave.co/product-overview-1/amm Pools meant to facilitate low slippage trades for assets the trade at a known exchange rate
- Balancer LP Tokens (BPT) with significant TVL as collateral on lending markets 


#### Core Infra (1.75x)
- LSTs
- Boosted stablecoin pairs
- 80/20 based governance/incentive systems.

#### New and Novel AMM tech (2x)
This is to help get attention to new Custom Pool types that have just launched.  
Pools in this section may move to the "Integrations" category after some time.


### Variable Fee Based Boost (1-3x)
The variable boost is determined by using the following formula:

Variable Boost = **_Fees earned/value of BAL emitted + 1_**

The variable boosted is capped at 3 and has a minimum of 1.

The fee based boost is added to the fixed boost, so:

Total Boost = **_Fixed Boost + Variable Boost - 1_** 

where both boosts are >=1 it will be automatically computed by the model and applied. 
