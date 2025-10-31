'use client';

import type { CSSProperties } from 'react';
import type { Route } from '@/types';

interface InfoPanelProps {
  stopCount: number;
  routeCount: number;
  activeRoutes: Set<string>;
  routes: { [key: string]: Route };
  onToggleRoute: (routeId: string) => void;
  isLoading: boolean;
}

type CSSVarStyle = CSSProperties & Record<string, string>;

export default function InfoPanel({
  stopCount,
  routeCount,
  activeRoutes,
  routes,
  onToggleRoute,
  isLoading,
}: InfoPanelProps) {
  return (
    <aside className="info-panel">
      <header className="info-panel__header">
        <div className="info-panel__badge">CTA</div>
        <div>
          <h2 className="info-panel__title">Transit Overview</h2>
          <p className="info-panel__subtitle">Live GTFS snapshot</p>
        </div>
      </header>

      {isLoading ? (
        <div className="info-panel__loading">
          <span className="info-panel__spinner" aria-hidden="true" />
          <p>Loading CTA stop and route data…</p>
        </div>
      ) : (
        <>
          <div className="info-panel__metrics">
            <div className="info-panel__metric">
              <span className="info-panel__metric-label">Stops</span>
              <span className="info-panel__metric-value">{stopCount.toLocaleString()}</span>
            </div>
            <div className="info-panel__metric">
              <span className="info-panel__metric-label">Routes</span>
              <span className="info-panel__metric-value">{routeCount}</span>
            </div>
          </div>

          <section className="info-panel__section">
            <h3 className="info-panel__section-title">Getting Started</h3>
            <ul className="info-panel__list">
              <li>Click a stop marker to view service information.</li>
              <li>Select a route badge to draw its corridor.</li>
              <li>Activate multiple routes to compare coverage.</li>
              <li>Zoom in for block-level granularity.</li>
            </ul>
          </section>

          {activeRoutes.size > 0 && (
            <section className="info-panel__section info-panel__section--routes">
              <div className="info-panel__section-heading">
                <h3 className="info-panel__section-title">Active Routes</h3>
                <span className="info-panel__active-count">{activeRoutes.size}</span>
              </div>
              <div className="info-panel__route-grid">
                {Array.from(activeRoutes).map(routeId => {
                  const route = routes[routeId];
                  if (!route) return null;

                  const chipStyle: CSSVarStyle = {
                    '--chip-accent': `#${route.route_color || '99999C'}`,
                    '--chip-text': `#${route.route_text_color || 'ffffff'}`,
                  };

                  return (
                    <button
                      key={routeId}
                      type="button"
                      className="route-chip"
                      style={chipStyle}
                      onClick={() => onToggleRoute(routeId)}
                    >
                      <span className="route-chip__line">{route.route_short_name}</span>
                      <span className="route-chip__remove" aria-hidden="true">&times;</span>
                      <span className="route-chip__sr">Remove route {route.route_short_name}</span>
                    </button>
                  );
                })}
              </div>
            </section>
          )}
        </>
      )}
    </aside>
  );
}
