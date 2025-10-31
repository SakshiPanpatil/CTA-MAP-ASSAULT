'use client';

import { useEffect, useMemo, useState, type CSSProperties } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Stop, Route } from '@/types';

// Fix for default marker icons in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

type MapTheme = 'day' | 'night';

type CSSVarStyle = CSSProperties & Record<string, string>;

interface MapComponentProps {
  stops: Stop[];
  routes: { [key: string]: Route };
  stopToRoutes: { [stopId: string]: string[] };
  routeShapes: { [routeId: string]: [number, number][] };
  activeRoutes: Set<string>;
  onToggleRoute: (routeId: string) => void;
  theme: MapTheme;
}

const TILE_LAYERS: Record<MapTheme, { url: string; attribution: string }> = {
  day: {
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution:
      '&copy; OpenStreetMap contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  night: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution:
      '&copy; OpenStreetMap contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
};

interface StopMarkerProps {
  stop: Stop;
  routes: { [key: string]: Route };
  stopRoutes: string[];
  onToggleRoute: (routeId: string) => void;
  icon: L.DivIcon;
}

function StopMarker({
  stop,
  routes,
  stopRoutes,
  onToggleRoute,
  icon,
}: StopMarkerProps) {
  const lat = Number.parseFloat(stop.stop_lat);
  const lon = Number.parseFloat(stop.stop_lon);

  if (Number.isNaN(lat) || Number.isNaN(lon)) return null;

  const getAccessibilityLabel = (value: string) => {
    if (value === '1') return 'Wheelchair accessible';
    if (value === '2') return 'Not wheelchair accessible';
    return 'Accessibility unknown';
  };

  return (
    <Marker position={[lat, lon]} icon={icon}>
      <Popup className="stop-popup" maxWidth={360}>
        <div className="stop-popup__title">{stop.stop_name}</div>

        <dl className="stop-popup__details">
          <dt>Description</dt>
          <dd>{stop.stop_desc || 'No description provided.'}</dd>

          <dt>Accessibility</dt>
          <dd>{getAccessibilityLabel(stop.wheelchair_boarding)}</dd>
        </dl>

        <div className="stop-popup__routes">
          <span className="stop-popup__routes-label">Routes serving this stop</span>
          <div className="stop-popup__route-grid">
            {stopRoutes.length > 0 ? (
              stopRoutes.map(routeId => {
                const route = routes[routeId];
                if (!route) return null;

                const chipStyle: CSSVarStyle = {
                  '--popup-chip-accent': `#${route.route_color || '99999C'}`,
                  '--popup-chip-text': `#${route.route_text_color || 'ffffff'}`,
                };

                return (
                  <button
                    key={routeId}
                    type="button"
                    className="stop-popup__route-chip"
                    style={chipStyle}
                    onClick={() => onToggleRoute(routeId)}
                  >
                    {route.route_short_name}
                  </button>
                );
              })
            ) : (
              <span className="stop-popup__empty">No routes found.</span>
            )}
          </div>
        </div>
      </Popup>
    </Marker>
  );
}

export default function MapComponent({
  stops,
  routes,
  stopToRoutes,
  routeShapes,
  activeRoutes,
  onToggleRoute,
  theme,
}: MapComponentProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const markerIcon = useMemo(() => {
    const accent = theme === 'night' ? '#8ec0ff' : '#0d47a1';
    const core = theme === 'night' ? '#cfe0ff' : '#1e88e5';

    return L.divIcon({
      className: 'stop-marker-icon',
      html: `<div class="stop-marker-icon__inner" style="--stop-core:${core};--stop-accent:${accent};"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
    });
  }, [theme]);

  if (!isMounted) {
    return (
      <div className="map-loading-inline">
        <div className="map-loading-inline__spinner" />
        <span>Initializing map…</span>
      </div>
    );
  }

  const tileLayer = TILE_LAYERS[theme];

  return (
    <MapContainer
      center={[41.8781, -87.6298]}
      zoom={11}
      className="map-stage__map"
      minZoom={10}
      maxZoom={19}
    >
      <TileLayer key={theme} url={tileLayer.url} attribution={tileLayer.attribution} />

      {stops.slice(0, 5000).map(stop => {
        const stopRoutes = stopToRoutes[stop.stop_id] || [];
        return (
          <StopMarker
            key={stop.stop_id}
            stop={stop}
            routes={routes}
            stopRoutes={stopRoutes}
            onToggleRoute={onToggleRoute}
            icon={markerIcon}
          />
        );
      })}

      {Array.from(activeRoutes).map(routeId => {
        const route = routes[routeId];
        const shape = routeShapes[routeId];

        if (!route || !shape || shape.length === 0) return null;

        const color = `#${route.route_color || '99999C'}`;

        return (
          <Polyline
            key={routeId}
            positions={shape}
            pathOptions={{
              color,
              weight: 4,
              opacity: 0.85,
            }}
          >
            <Popup className="route-popup">
              <strong>{route.route_short_name}</strong>
              <div className="route-popup__subtitle">{route.route_long_name}</div>
            </Popup>
          </Polyline>
        );
      })}
    </MapContainer>
  );
}
