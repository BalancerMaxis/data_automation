# TODO: Change year
CURRENT_YEAR = 2023

EMISSIONS_PER_YEAR = {
    "meta": {
        "changeDate": "28-03",
        "description": "Emissions per week, changes each year on changeDate (time unknown)",
    },
    "data": [
        {"year": "2022", "balPerWeek": "145000"},
        {"year": "2023", "balPerWeek": "121929.98021178861"},
        {"year": "2024", "balPerWeek": "102530.4832720494"},
        {"year": "2025", "balPerWeek": "86217.51583769728"},
        {"year": "2026", "balPerWeek": "72500.00000000001"},
        {"year": "2027", "balPerWeek": "60964.99010589432"},
        {"year": "2028", "balPerWeek": "51265.24163602471"},
        {"year": "2029", "balPerWeek": "43108.75791884865"},
        {"year": "2030", "balPerWeek": "36250.00000000001"},
        {"year": "2031", "balPerWeek": "30482.49505294716"},
        {"year": "2032", "balPerWeek": "25632.620818012354"},
        {"year": "2033", "balPerWeek": "21554.378959424324"},
        {"year": "2034", "balPerWeek": "18125.000000000004"},
        {"year": "2035", "balPerWeek": "15241.24752647358"},
        {"year": "2036", "balPerWeek": "12816.310409006177"},
        {"year": "2037", "balPerWeek": "10777.189479712162"},
        {"year": "2038", "balPerWeek": "9062.500000000002"},
        {"year": "2039", "balPerWeek": "7620.62376323679"},
        {"year": "2040", "balPerWeek": "6408.1552045030885"},
        {"year": "2041", "balPerWeek": "5388.594739856081"},
        {"year": "2042", "balPerWeek": "4531.250000000001"},
        {"year": "2043", "balPerWeek": "3810.311881618395"},
        {"year": "2044", "balPerWeek": "3204.0776022515442"},
        {"year": "2045", "balPerWeek": "2694.2973699280406"},
        {"year": "2046", "balPerWeek": "2265.6250000000005"},
        {"year": "2047", "balPerWeek": "1905.1559408091975"},
        {"year": "2048", "balPerWeek": "1602.0388011257721"},
        {"year": "2049", "balPerWeek": "1347.1486849640203"},
        {"year": "2050", "balPerWeek": "1132.8125000000002"},
    ],
}


def get_emissions_per_week() -> float:
    """
    Fetch emissions per week from the balancer subgraph
    """
    emissions_per_week = 0
    for item in EMISSIONS_PER_YEAR["data"]:
        if item["year"] == str(CURRENT_YEAR):
            emissions_per_week = float(item["balPerWeek"])
            break
    return emissions_per_week
