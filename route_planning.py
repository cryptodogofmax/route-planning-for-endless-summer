from collections import defaultdict
from datetime import datetime, timedelta

import googlemaps
import numpy as np
import pandas as pd
from __future__ import print_function
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

gmaps_client = googlemaps.Client(key="AIzaSyAPldhz_3zhaTEzHdhSQ0J5HUzOVLiDmZk")
# nine_hours_from_now = datetime.now() + timedelta(hours=9)

JE = "21 Jurong East Street, 600201"
BV = "100 North Buona Vista Rd, 139349"
CCK = "Choa Chu Kang"
RE = "920 Tiong Bahru Rd, Singapore 158792"
TB = "Tiong Bahru"
UT = "Aft NUS High Sch Stop ID: 17129"
WO = "Q30, Woodlands Ave 2, Singapore 738343"
YI = "Yishun"
stops = [JE, BV, CCK, RE, TB, UT, WO, YI]

stop_name_dict = {
    "JE": JE,
    "BV": BV,
    "CCK": CCK,
    "RE": RE,
    "TB": TB,
    "UT": UT,
    "WO": WO,
    "YI": YI,
}
name_stop_dict = {v: i for i, v in stop_name_dict.items()}
locations_dict = {
    "JE": JE,
    "BV": BV,
    "CCK": CCK,
    "RE": RE,
    "TB": TB,
    "UT": UT,
    "WO": WO,
    "YI": YI,
}
file_name = "route_planning_2.xlsx"
time_windows = [
    (540, 1200),
    (870, 900),
    (890, 920),
    (1020, 1050),
    (900, 930),
    (840, 870),
    (920, 950),
    (960, 990),
]


def get_geo_loc(one_stop):
    geocode_result = gmaps_client.geocode(one_stop)
    loc = geocode_result[0]["geometry"]["location"]
    geo_loc = (loc["lat"], loc["lng"])
    return geo_loc


class distance_duration_calculator:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2
        self.time = datetime.now()

    def node_preprocessing(node):
        return str(node[0]) + "," + str(node[1])

    def get_distance_duration(self):
        direction_results = gmaps_client.directions(
            distance_duration_calculator.node_preprocessing(self.node1),
            distance_duration_calculator.node_preprocessing(self.node2),
            mode="transit",
            transit_mode="train|tram|subway|bus",
            transit_routing_preference="less_walking",
            departure_time=self.time,
        )
        print(self.node1, self.node2)
        total_distance = round(
            direction_results[0]["legs"][0]["distance"]["value"] / 1000, 2
        )
        total_duration = round(
            direction_results[0]["legs"][0]["duration"]["value"] / 3600, 2
        )
        total_duration_in_min = int(np.ceil(total_duration * 60))
        res = {
            "distance_in_km": total_distance,
            "duration_in_hours": total_duration,
            "duration_in_min": total_duration_in_min,
        }
        return res


distance_list, duration_list = [], []
for start_stop in stops:
    row_distances, row_durations = [], []
    for end_stop in stops:
        start_node, end_node = get_geo_loc(start_stop), get_geo_loc(end_stop)
        dd = distance_duration_calculator(node1=start_node, node2=end_node)
        distance_res = dd.get_distance_duration()
        distance_in_km, duration_in_hours, duration_in_min = (
            distance_res["distance_in_km"],
            distance_res["duration_in_hours"],
            distance_res["duration_in_min"],
        )
        row_distances.append(distance_in_km)
        row_durations.append(duration_in_min)
    distance_list.append(row_distances)
    duration_list.append(row_durations)

distance_matrix = pd.DataFrame(
    distance_list,
    columns=list(locations_dict.keys()),
    index=list(locations_dict.keys()),
)
distance_matrix.to_excel("25Oct_distance_matrix.xlsx")
duration_matrix = pd.DataFrame(
    duration_list,
    columns=list(locations_dict.keys()),
    index=list(locations_dict.keys()),
)
duration_matrix.to_excel("25Oct_duration_matrix.xlsx")


def print_solution(data, manager, routing, solution):
    routes = defaultdict(list)
    max_route_distance = 0
    time_dimension = routing.GetDimensionOrDie("Time")
    total_time = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            routes[vehicle_id].append(node_index)
            time_var = time_dimension.CumulVar(index)
            plan_output += "{0} Time({1},{2}) -> ".format(
                manager.IndexToNode(index),
                solution.Min(time_var),
                solution.Max(time_var),
            )
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        time_var = time_dimension.CumulVar(index)
        plan_output += "{0} Time({1},{2})\n".format(
            manager.IndexToNode(index),
            solution.Min(time_var),
            solution.Max(time_var),
        )
        plan_output += "Distance of the route: {}m\n".format(route_distance)
        print(plan_output)
        max_route_distance = max(route_distance, max_route_distance)
        total_time += solution.Min(time_var)
    print("Maximum of the route distances: {}m".format(max_route_distance))
    print("Total time of all routes: {}min".format(total_time))
    print(routes)
    return routes


def get_time_in_minute(t):
    year, month, day = 2020, 10, 25
    e = datetime(year, month, day, t.hour, t.minute)
    s = datetime(year, month, day, 0, 0)
    duration = e - s
    duration_in_s = duration.total_seconds()
    minutes_diff = divmod(duration_in_s, 60)[0]
    return int(minutes_diff)


timetable = pd.read_excel(file_name)
timetable["Start_In_Minute"] = timetable["Start"].apply(
    lambda x: get_time_in_minute(x)
)
timetable["End_In_Minute"] = timetable["End"].apply(
    lambda x: get_time_in_minute(x)
)
timetable = (
    timetable.groupby("Location")
    .agg({"Start_In_Minute": "max", "End_In_Minute": "max"})
    .reset_index()
)
timetable["time_window"] = timetable[
    ["Start_In_Minute", "End_In_Minute"]
].apply(tuple, axis=1)


def create_data_model():
    data = {}
    data["distance_matrix"] = distance_matrix.values.tolist()
    data["time_matrix"] = duration_matrix.values.tolist()
    data["time_windows"] = time_windows
    data["num_vehicles"] = 2
    data["depot"] = 0
    return data


data = create_data_model()
manager = pywrapcp.RoutingIndexManager(
    len(data["time_matrix"]), data["num_vehicles"], data["depot"]
)
routing = pywrapcp.RoutingModel(manager)


def distance_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data["distance_matrix"][from_node][to_node]


def time_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data["time_matrix"][from_node][to_node]


transit_callback_index = routing.RegisterTransitCallback(distance_callback)

routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

dimension_name = "Distance"
routing.AddDimension(
    transit_callback_index,
    0,  # no slack
    3000,  # vehicle maximum travel distance
    True,  # start cumul to zero
    dimension_name,
)
distance_dimension = routing.GetDimensionOrDie(dimension_name)
distance_dimension.SetGlobalSpanCostCoefficient(100)

time = "Time"
routing.AddDimension(
    transit_callback_index,
    1000,  # allow waiting time
    60 * 60,  # maximum time per vehicle
    False,  # Don't force start cumul to zero.
    time,
)
time_dimension = routing.GetDimensionOrDie(time)
# Add time window constraints for each location except depot.
for location_idx, time_window in enumerate(data["time_windows"]):
    if location_idx == 0:
        continue
    index = manager.NodeToIndex(location_idx)
    time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
# Add time window constraints for each vehicle start node.
for vehicle_id in range(data["num_vehicles"]):
    index = routing.Start(vehicle_id)
    time_dimension.CumulVar(index).SetRange(
        data["time_windows"][0][0], data["time_windows"][0][1]
    )

# Instantiate route start and end times to produce feasible times.
for i in range(data["num_vehicles"]):
    routing.AddVariableMinimizedByFinalizer(
        time_dimension.CumulVar(routing.Start(i))
    )
    routing.AddVariableMinimizedByFinalizer(
        time_dimension.CumulVar(routing.End(i))
    )

# Setting first solution heuristic.
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)
search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH
)
search_parameters.time_limit.seconds = 10
search_parameters.log_search = True

# Solve the problem.
solution = routing.SolveWithParameters(search_parameters)

if solution:
    routes = print_solution(data, manager, routing, solution)
print("There is no solution.")
