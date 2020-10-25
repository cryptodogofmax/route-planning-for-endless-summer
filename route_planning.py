import googlemaps
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

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

distance_list,duration_list = [],[]
for start_stop in stops:
    row_distances,row_durations = [],[]
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
