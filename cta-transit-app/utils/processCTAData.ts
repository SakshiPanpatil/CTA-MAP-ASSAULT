import type { Stop, Route, Trip, StopTime, Shape, ProcessedData } from '@/types';

interface ProcessCTADataParams {
  stops: Stop[];
  routes: Route[];
  trips: Trip[];
  stopTimes: StopTime[];
  shapes: Shape[];
}

// Build processed CTA data from raw GTFS entities
export function processCTAData({
  stops,
  routes,
  trips,
  stopTimes,
  shapes,
}: ProcessCTADataParams): ProcessedData {
  // Create routes lookup
  const routesById: { [key: string]: Route } = {};
  routes.forEach(route => {
    routesById[route.route_id] = route;
  });

  // Track trips and which shapes belong to each route
  const tripsById: { [key: string]: Trip } = {};
  const routeToShapes: { [routeId: string]: Set<string> } = {};

  trips.forEach(trip => {
    tripsById[trip.trip_id] = trip;

    if (!routeToShapes[trip.route_id]) {
      routeToShapes[trip.route_id] = new Set();
    }

    if (trip.shape_id) {
      routeToShapes[trip.route_id].add(trip.shape_id);
    }
  });

  // Build stop -> routes map
  const stopToRoutesMap: { [stopId: string]: Set<string> } = {};

  stopTimes.forEach(stopTime => {
    const trip = tripsById[stopTime.trip_id];
    if (!trip) return;

    const stopId = stopTime.stop_id;
    if (!stopToRoutesMap[stopId]) {
      stopToRoutesMap[stopId] = new Set();
    }
    stopToRoutesMap[stopId].add(trip.route_id);
  });

  const stopToRoutes: { [stopId: string]: string[] } = {};
  Object.keys(stopToRoutesMap).forEach(stopId => {
    stopToRoutes[stopId] = Array.from(stopToRoutesMap[stopId]).sort();
  });

  // Build shapes lookup keyed by shape_id
  const shapesMap: { [shapeId: string]: Array<[number, number, number]> } = {};
  shapes.forEach(shape => {
    const lat = parseFloat(shape.shape_pt_lat);
    const lon = parseFloat(shape.shape_pt_lon);
    const sequence = Number.parseInt(shape.shape_pt_sequence, 10);

    if (Number.isNaN(lat) || Number.isNaN(lon)) return;

    if (!shapesMap[shape.shape_id]) {
      shapesMap[shape.shape_id] = [];
    }

    shapesMap[shape.shape_id].push([lat, lon, Number.isNaN(sequence) ? 0 : sequence]);
  });

  const routeShapes: { [routeId: string]: [number, number][] } = {};
  Object.keys(routeToShapes).forEach(routeId => {
    const shapeIds = Array.from(routeToShapes[routeId]);
    if (shapeIds.length === 0) return;

    const shapeId = shapeIds[0];
    const shapePoints = shapesMap[shapeId];
    if (!shapePoints) return;

    // Ensure coordinates follow the provided sequence order
    const sortedPoints = shapePoints
      .slice()
      .sort((a, b) => a[2] - b[2])
      .map(([lat, lon]) => [lat, lon] as [number, number]);

    routeShapes[routeId] = sortedPoints;
  });

  return {
    stops,
    routes: routesById,
    stopToRoutes,
    routeShapes,
  };
}

