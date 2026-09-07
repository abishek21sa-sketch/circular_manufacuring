from circular_battery.routing.models import RouteNode, CVRPScenario

def demo_cvrp_scenario():
    return CVRPScenario(
        depot=RouteNode('Recovery-Hub',0,0,0),
        customers=(
            RouteNode('North-Collector',18,24,18_000),
            RouteNode('West-Collector',-28,12,21_000),
            RouteNode('South-Collector',-8,-31,16_500),
            RouteNode('East-Collector',34,-4,19_500),
            RouteNode('Northeast-Collector',27,27,14_000),
            RouteNode('Southwest-Collector',-29,-25,17_000),
        ),
        vehicle_capacity_kg=40_000,
        max_vehicles=4,
        vehicle_fixed_cost=220.0,
        distance_cost_per_km=2.35,
        kgco2e_per_km=.86,
    )
