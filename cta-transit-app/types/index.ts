export interface Stop {
  stop_id: string;
  stop_code: string;
  stop_name: string;
  stop_desc: string;
  stop_lat: string;
  stop_lon: string;
  location_type: string;
  parent_station: string;
  wheelchair_boarding: string;
}

export interface Route {
  route_id: string;
  route_short_name: string;
  route_long_name: string;
  route_type: string;
  route_url: string;
  route_color: string;
  route_text_color: string;
}

export interface Trip {
  route_id: string;
  service_id: string;
  trip_id: string;
  direction_id: string;
  block_id: string;
  shape_id: string;
  direction: string;
  wheelchair_accessible: string;
  schd_trip_id: string;
}

export interface StopTime {
  trip_id: string;
  arrival_time: string;
  departure_time: string;
  stop_id: string;
  stop_sequence: string;
  stop_headsign: string;
  pickup_type: string;
  shape_dist_traveled: string;
}

export interface Shape {
  shape_id: string;
  shape_pt_lat: string;
  shape_pt_lon: string;
  shape_pt_sequence: string;
  shape_dist_traveled: string;
}

export interface ProcessedData {
  stops: Stop[];
  routes: { [key: string]: Route };
  stopToRoutes: { [stopId: string]: string[] };
  routeShapes: { [routeId: string]: [number, number][] };
}