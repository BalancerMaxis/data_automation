import json
import os
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from typing import Dict
from typing import List
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from gql import Client
from gql import gql
from gql.transport.requests import RequestsHTTPTransport
from pycoingecko import CoinGeckoAPI
from web3 import Web3

from notebooks import fetch_all_pools_info
from notebooks import get_abi
from notebooks import get_block_by_ts
from notebooks.airdrop_arb_distribution.constants import BALANCER_GRAPH_URL
from notebooks.airdrop_arb_distribution.constants import POOLS_SNAPSHOTS_QUERY
from notebooks.arb_dao_grant_distribution.constants import ARBITRUM_TOTAL
from notebooks.arb_dao_grant_distribution.constants import ARBITRUM_TO_DISTRIBUTE
from notebooks.arb_dao_grant_distribution.constants import BALANCER_GAUGE_CONTROLLER_ABI
from notebooks.arb_dao_grant_distribution.constants import (
    BALANCER_GAUGE_CONTROLLER_ADDR,
)
from notebooks.arb_dao_grant_distribution.constants import DYNAMIC_BOOST_MULTIPLIER
from notebooks.arb_dao_grant_distribution.constants import GAUGES_WITH_BONUSES
from notebooks.arb_dao_grant_distribution.constants import MIN_BAL_IN_USD_FOR_BOOST
from notebooks.arb_dao_grant_distribution.constants import VOTE_CAP_IN_PERCENT
from notebooks.arb_dao_grant_distribution.emissions_per_year import (
    get_emissions_per_week,
)
from notebooks.arb_dao_grant_distribution.static_boosts import boost_data
from notebooks.arb_dao_grant_distribution.static_boosts import cap_override_data

# End date from timestamp

ARBITRUM_CHAIN_LITERAL = "ARBITRUM"


def make_gql_client(url: str) -> Optional[Client]:
    transport = RequestsHTTPTransport(url=url, retries=3)
    return Client(
        transport=transport, fetch_schema_from_transport=True, execute_timeout=60
    )


def get_balancer_pool_snapshots(start_ts: int, end_ts: int) -> List[Dict]:
    """
    Fetch balancer pool snapshots from the subgraph and calculate protocol fees collected for each pool.
    This works like this: fetch snapshots by time range from the graph, then find the first and last snapshot
    and calculate the difference between them. This will give us the protocol fees collected for the period.
    """
    client = make_gql_client(BALANCER_GRAPH_URL)
    all_snapthots = []
    limit = 100
    offset = 0
    while True:
        result = client.execute(
            gql(
                POOLS_SNAPSHOTS_QUERY.format(
                    first=limit, skip=offset, start_ts=start_ts, end_ts=end_ts
                )
            )
        )
        all_snapthots.extend(result["poolSnapshots"])
        offset += limit
        if len(result["poolSnapshots"]) < limit - 1:
            break
    # Need to group by pool address, since there are multiple snapshots per pool and we need to calculate
    # difference between first and last snapshot
    pools = defaultdict(list)
    for snapshot in all_snapthots:
        pools[snapshot["pool"]["address"]].append(snapshot.get("protocolFee", 0))
    # Now calculate the difference between first and last snapshot
    fees_snapshots = []
    for pool_addr, snapshots in pools.items():
        if len(snapshots) > 1:
            # Convert to int with respect that there might be null values and string values
            first_snapshot = float(snapshots[0]) if snapshots[0] else 0
            last_snapshot = float(snapshots[-1]) if snapshots[-1] else 0
            fee_collected = first_snapshot - last_snapshot
            assert fee_collected >= 0, f"Fee collected for pool {pool_addr} is negative"
            fees_snapshots.append(
                {
                    "pool": {
                        "address": pool_addr,
                    },
                    "protocolFee": fee_collected,
                }
            )
    return fees_snapshots


def get_bal_token_price() -> float:
    """
    Fetch bal token price from coingecko
    """
    # fetch balancer token usd price:
    cg = CoinGeckoAPI()
    return cg.get_price(ids="balancer", vs_currencies="usd")["balancer"]["usd"]


def recur_distribute_unspend_arb(
    vote_caps: Dict, arb_gauge_distributions: Dict
) -> None:
    """
    Recursively distribute unspent arb to uncapped gauges proportionally to their voting weight until
    there is no unspent arb left
    """
    unspent_arb = ARBITRUM_TO_DISTRIBUTE - sum(
        [gauge["distribution"] for gauge in arb_gauge_distributions.values()]
    )
    if unspent_arb > 0:
        # Find out total voting weight of uncapped gauges and mark it as 100%:
        total_uncapped_weight = sum(
            [
                g["voteWeight"]
                for g in [
                    gauge
                    for addr, gauge in arb_gauge_distributions.items()
                    if gauge["distribution"] < vote_caps[addr]
                ]
            ]
        )
        # Iterate over uncapped gauges and distribute unspent arb
        # proportionally to their voting weight which is total uncapped weight
        for a, uncap_gauge in {
            addr: gauge
            for addr, gauge in arb_gauge_distributions.items()
            if gauge["distribution"] < vote_caps[addr]
        }.items():
            # For each loop calculate unspend arb
            unspent_arb = ARBITRUM_TO_DISTRIBUTE - sum(
                [gauge["distribution"] for gauge in arb_gauge_distributions.values()]
            )
            # Don't distribute more than vote cap
            distribution = min(
                uncap_gauge["distribution"]
                + unspent_arb * uncap_gauge["voteWeight"] / total_uncapped_weight,
                vote_caps[a],
            )
            uncap_gauge["distribution"] = distribution
            uncap_gauge["pctDistribution"] = (
                uncap_gauge["distribution"] / ARBITRUM_TOTAL * 100
            )
    # Call recursively if there is still unspent arb
    if (
        ARBITRUM_TO_DISTRIBUTE
        - sum([g["distribution"] for g in arb_gauge_distributions.values()])
        > 0
    ):
        recur_distribute_unspend_arb(vote_caps, arb_gauge_distributions)


def generate_and_save_transaction(arb_gauge_distributions: Dict, start_date: datetime, end_date: datetime) -> Dict:
    """
    Take tx template and inject data into it
    """
    # Dump into output.json using:
    with open("../../data/output_tx_template.json") as f:
        output_data = json.load(f)
    # Find transaction with func name `setRecipientList` and dump gauge
    gauge_distributions = arb_gauge_distributions.values()
    for tx in output_data["transactions"]:
        if tx["contractMethod"]["name"] == "setRecipientList":
            # Inject list of gauges addresses:
            tx["contractInputsValues"][
                "gaugeAddresses"
            ] = f"[{','.join([gauge['recipientGaugeAddr'] for gauge in gauge_distributions])}]"
            # Inject vote weights:
            # Dividing by 2 since we are distributing for 2 weeks and 1 week is a period
            tx["contractInputsValues"][
                "amountsPerPeriod"
            ] = f"[{','.join([str(int(Decimal(gauge['distribution']) * Decimal(1e18) / 2)) for gauge in gauge_distributions])}]"
            tx["contractInputsValues"][
                "maxPeriods"
            ] = f"[{','.join(['2' for gauge in gauge_distributions])}]"
        if tx["contractMethod"]["name"] == "transfer":
            tx["contractInputsValues"]["amount"] = str(
                int(Decimal(ARBITRUM_TOTAL) * Decimal(1e18))
            )

    # Dump back to arb_distribution_for_msig.json
    with open(
        f"./output/dao_grant_{start_date.date()}_{end_date.date()}.json", "w"
    ) as _f:
        json.dump(output_data, _f, indent=4)
    return output_data


def main() -> None:
    """
    Main function to execute STIP calculations
    """
    load_dotenv()
    # Calculate end date approx block height

    web3 = Web3(Web3.HTTPProvider(os.environ["ETHNODEURL"]))
    end_date = datetime.fromtimestamp(1702512000)
    start_date = end_date - timedelta(days=14)
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())
    target_block = get_block_by_ts(end_ts, chain="mainnet")
    pool_snapshots = get_balancer_pool_snapshots(start_ts, end_ts)
    print(f"Collected data for dates: {start_date.date()} - {end_date.date()}")
    print(f"Block height at the end date: {target_block}")
    emissions_per_week = get_emissions_per_week()

    # Fetch all pools from Balancer API
    all_pools = fetch_all_pools_info("arbitrum")
    # Collect arb gauges
    arb_gauges = {}
    for pool in all_pools:
        # Only collect gauges for the arb chain and that are not killed
        if (
            pool["chain"] == ARBITRUM_CHAIN_LITERAL
            and pool["gauge"]["isKilled"] is False
        ):
            _gauge_addr = Web3.to_checksum_address(pool["gauge"]["address"])
            arb_gauges[_gauge_addr] = {
                "gaugeAddress": pool["gauge"]["address"],
                "poolAddress": pool["address"],
                "pool": pool["address"],
                "symbol": pool["symbol"],
                "id": pool["id"],
            }
    print(f"Total arb gauges eligible for STIP emissions: {len(arb_gauges)}")

    pool_protocol_fees = {}
    # Collect protocol fees from the pool snapshots:
    for gauge_addr, gauge_data in arb_gauges.items():
        for pool_snapshot in pool_snapshots:
            if Web3.to_checksum_address(
                pool_snapshot["pool"]["address"]
            ) == Web3.to_checksum_address(gauge_data["pool"]):
                # Since snapshots are sorted by timestamp descending,
                # we can just take the first one we find for each pool and break
                protocol_fee = (
                    float(pool_snapshot["protocolFee"])
                    if pool_snapshot["protocolFee"]
                    else 0
                )
                pool_protocol_fees[Web3.to_checksum_address(gauge_addr)] = protocol_fee
                break
    print(f"Total protocol fees collected: {sum(pool_protocol_fees.values())}")
    # Apply boost data to arb gauges
    vote_weights = {}
    combined_boost = {}
    # Dynamic boost data to print out in the final table
    dynamic_boosts = {}
    # Collect gauge voting weights from the gauge controller on chain
    gauge_c_contract = web3.eth.contract(
        address=BALANCER_GAUGE_CONTROLLER_ADDR, abi=BALANCER_GAUGE_CONTROLLER_ABI
    )
    bal_token_price = get_bal_token_price()
    for gauge_addr, gauge_data in arb_gauges.items():
        weight = (
            gauge_c_contract.functions.gauge_relative_weight(
                Web3.to_checksum_address(gauge_addr)
            ).call(block_identifier=target_block)
            / 1e18
            * 100
        )
        arb_gauges[gauge_addr]["weightNoBoost"] = weight
        # Calculate dynamic boost. Formula is `[Fees earned/value of bal emitted per pool + 1]`
        dollar_value_of_bal_emitted = (
            (weight / 100) * emissions_per_week * bal_token_price
        )
        if dollar_value_of_bal_emitted >= MIN_BAL_IN_USD_FOR_BOOST:
            dynamic_boost = ((
                pool_protocol_fees.get(gauge_addr, 0) / dollar_value_of_bal_emitted
            ) + 1) * DYNAMIC_BOOST_MULTIPLIER
        else:
            dynamic_boost = 1
        dynamic_boosts[gauge_addr] = dynamic_boost
        # Now calculate the final boost value, which uses formula - (dynamic boost + fixed boost) - 1
        boost = (dynamic_boost + boost_data.get(gauge_addr, 1)) - 1
        combined_boost[gauge_addr] = boost
        weight *= boost
        vote_weights[gauge_addr] = weight
        arb_gauges[gauge_addr]["voteWeight"] = weight
    print(
        f"Total %veBAL vote weight across eligible ARB gauges: {sum(vote_weights.values())}"
    )
    # Vote caps in percents are calculated as a percentage of the total amount of arb to distribute
    vote_caps_in_percents = {
        gauge_addr: cap_override_data.get(gauge_addr, VOTE_CAP_IN_PERCENT)
        for gauge_addr in arb_gauges.keys()
    }
    # Custom gauge caps taken from boost data, calculated as a percentage of the total amount of arb to distribute
    vote_caps = {
        gauge_addr: vote_caps_in_percents[gauge_addr] / 100 * ARBITRUM_TOTAL
        for gauge_addr in arb_gauges.keys()
    }
    # Calculate total weight
    total_weight = sum([gauge["voteWeight"] for gauge in arb_gauges.values()])
    arb_gauge_distributions = {}
    for gauge_addr, gauge_data in arb_gauges.items():
        gauge_addr = Web3.to_checksum_address(gauge_addr)
        # Calculate distribution based on vote weight and total weight
        to_distribute = ARBITRUM_TO_DISTRIBUTE * gauge_data["voteWeight"] / total_weight
        # Cap distribution
        to_distribute = (
            to_distribute
            if to_distribute < vote_caps[gauge_addr]
            else vote_caps[gauge_addr]
        )
        # Get arb gauge addr
        mainnet_arb_root_gauge_contract = web3.eth.contract(
            address=Web3.to_checksum_address(gauge_addr), abi=get_abi("ArbRootGauge")
        )
        arb_gauge_distributions[gauge_addr] = {
            "recipientGaugeAddr": mainnet_arb_root_gauge_contract.functions.getRecipient().call(),
            "poolAddress": gauge_data["poolAddress"],
            "symbol": gauge_data["symbol"],
            "voteWeight": gauge_data["voteWeight"],
            "voteWeightNoBoost": gauge_data["weightNoBoost"],
            "distribution": to_distribute
            if to_distribute < vote_caps[gauge_addr]
            else vote_caps[gauge_addr],
            "pctDistribution": to_distribute / ARBITRUM_TOTAL * 100,
            "boost": combined_boost.get(gauge_addr, 1),
            "staticBoost": boost_data.get(gauge_addr, 1),
            "dynamicBoost": dynamic_boosts.get(gauge_addr, 1),
            "cap": f"{cap_override_data.get(gauge_addr, VOTE_CAP_IN_PERCENT)}%",
            "bonus": 0,
        }
    recur_distribute_unspend_arb(vote_caps, arb_gauge_distributions)
    print(
        f"Unspent arb: {ARBITRUM_TO_DISTRIBUTE - sum([gauge['distribution'] for gauge in arb_gauge_distributions.values()])}"
    )
    print(
        f"Arb distributed: {sum([gauge['distribution'] for gauge in arb_gauge_distributions.values()])}"
    )

    # # Remove arb gauges with 0 distribution
    arb_gauge_distributions = {
        addr: gauge
        for addr, gauge in arb_gauge_distributions.items()
        if gauge["distribution"] > 0
    }
    # Toss in bonus arb to the predefined gauge:
    for gauge, gauge_info in GAUGES_WITH_BONUSES.items():
        # Calculate bonus per pool
        bonus = gauge_info["bonus"]
        # If gauge already exists, add bonus to it and recalculate % distribution, if not - create new gauge with bonus
        if arb_gauge_distributions.get(gauge):
            arb_gauge_distributions[gauge]["distribution"] += bonus
            arb_gauge_distributions[gauge]["pctDistribution"] = (
                arb_gauge_distributions[gauge]["distribution"] / ARBITRUM_TOTAL * 100
            )
            arb_gauge_distributions[gauge]["bonus"] = bonus
        else:
            arb_gauge_distributions[gauge] = {
                "recipientGaugeAddr": gauge_info["recipientGauge"],
                "poolAddress": gauge_info["poolAddress"],
                "symbol": gauge_info["symbol"],
                "voteWeight": 0,
                "voteWeightNoBoost": 0,
                "distribution": bonus,
                "pctDistribution": bonus / ARBITRUM_TOTAL * 100,
                "boost": combined_boost.get(gauge, 1),
                "staticBoost": boost_data.get(gauge, 1),
                "dynamicBoost": dynamic_boosts.get(gauge, 1),
                "cap": f"{cap_override_data.get(gauge, VOTE_CAP_IN_PERCENT)}%",
                "bonus": bonus,
            }
    arb_gauge_distributions_df = pd.DataFrame.from_dict(
        arb_gauge_distributions, orient="index"
    )
    arb_gauge_distributions_df = arb_gauge_distributions_df.sort_values(
        by="pctDistribution", ascending=False
    )
    print(
        f"Total arb distributed incl bonus: "
        f"{sum([gauge['distribution'] for gauge in arb_gauge_distributions.values()])}"
    )
    # Export to csv
    arb_gauge_distributions_df.to_csv(
        f"./output/dao_grant_{start_date.date()}_{end_date.date()}_3x.csv", index=False
    )

    generate_and_save_transaction(arb_gauge_distributions, start_date, end_date)


if __name__ == "__main__":
    main()
