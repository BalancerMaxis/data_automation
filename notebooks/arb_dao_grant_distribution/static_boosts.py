from web3 import Web3

STATIC_BOOST = [
    {
        "gaugeAddress": "0x8135d6AbFd42707A87A7b94c5CFA3529f9b432AD",
        "fixedBoost": 1.5,
        "meta": {"symbol": "RDNT-WETH", "boostReason": "Innovation - ve80/20"},
    },
    {
        "gaugeAddress": "0xa8bb331a84032b156e5c670152a5bd48f5dec784",
        "fixedBoost": 1.5,
        "meta": {"symbol": "wstETH-4pool", "boostReason": "Innovation - ve80/20"},
    },
    {
        "gaugeAddress": "0x00b9bcd17cB049739D25FD7f826caA2E23b05620",
        "fixedBoost": 1.75,
        "capOverride": 20,
        "meta": {"symbol": "rETH-WETH-BPT", "boostReason": "Innovation - ve80/20"},
    },
    {
        "gaugeAddress": "0x671eD21480acf63b0AB7297b901505F5BccAfa9b",
        "fixedBoost": 1.75,
        "capOverride": 20,
        "meta": {"symbol": "ankrETH/wstETH-BPT", "boostReason": "Innovation - ve80/20"},
    },
    {
        "gaugeAddress": "0x56c0626E6E3931af90EbB679A321225180d4b32B",
        "fixedBoost": 1.75,
        "capOverride": 20,
        "meta": {"symbol": "wstETH/rETH/cbETH", "boostReason": "Innovation - ve80/20"},
    },
    {
        "gaugeAddress": "0xb6d101874B975083C76598542946Fe047f059066",
        "fixedBoost": 1.75,
        "capOverride": 20,
        "meta": {"symbol": "wstETH-WETH-BPT", "boostReason": "Innovation - ve80/20"},
    },
    {
        "gaugeAddress": "0x49f530b45Ae792CDF5Cbd5D25C5a9b9e59C6c3B8",
        "fixedBoost": 1.75,
        "capOverride": 20,
        "meta": {
            "symbol": "wstETH/rETH/sfrxETH/",
            "boostReason": "Innovation - ve80/20",
        },
    },
    {
        "gaugeAddress": "0xA8d4b31225BD6FAF1363DB5A0AB6c016894985d1",
        "fixedBoost": 1.0,
        "capOverride": 8,
        "meta": {"symbol": "wstETH-GOLD-USDC", "boostReason": "BIP agreement"},
    },
    {
        "gaugeAddress": "0xb66e8d615f8109ca52d47d9cb65fc4edcf9c1342",
        "fixedBoost": 1.75,
        "capOverride": 20,
        "meta": {"symbol": "plsRDNT", "boostReason": "Core"},
    },
    {
        "gaugeAddress": "0x86Cf58bD7A64f2304227d1a490660D2954dB4a91",
        "fixedBoost": 1.0,
        "capOverride": 2,
        "meta": {"symbol": "GOLD-BAL-AURA-wstETH", "boostReason": "BIP agreement"},
    },
]

# Load static boost data
boost_data = {}
cap_override_data = {}
# Load static boost here
for boost in STATIC_BOOST:
    _gauge_addr = Web3.to_checksum_address(boost["gaugeAddress"])
    boost_data[_gauge_addr] = boost.get("fixedBoost", 1)
    cap_override_data[_gauge_addr] = boost.get("capOverride", 10)
