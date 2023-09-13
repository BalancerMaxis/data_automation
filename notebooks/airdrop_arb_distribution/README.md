## Arbitrum Aidrop distribution program

Distribution program pays out 80k ARB per week based on veBAL voting for pools on Arbitrum.

Some pools have a boost factor, then ARB is distributed to all pools based on their relative boosted weight.

Pools are capped at 10% of the total weekly $ARB, except for ETH based LSD stableswap pools which are capped at 20%

Boosts and caps are defined per gauge in [arbitrumGrantGaugeMetadata.json](https://github.com/BalancerMaxis/data_automation/blob/main/data/arbitrumGrantGuageMetadata.json)

## How boost is calculated

Boost is based on 2 factors.

1. A fixed boost granted to incentive important initiatives(from file above)
2. A variable boost based on the efficiency of the pool (fees/emissions)
