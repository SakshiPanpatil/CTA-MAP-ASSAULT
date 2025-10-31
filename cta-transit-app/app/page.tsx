'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import InfoPanel from '@/components/InfoPanel';
import { loadCTAData } from '@/utils/dataLoader';
import type { ProcessedData } from '@/types';

// Dynamically import MapComponent to avoid SSR issues with Leaflet
const MapComponent = dynamic(() => import('@/components/MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="map-loading-fallback">
      <div className="map-loading-fallback__spinner" />
      <p className="map-loading-fallback__text">Preparing interactive map...</p>
    </div>
  ),
});

const getThemeForCurrentTime = (): 'day' | 'night' => {
  const hour = new Date().getHours();
  return hour >= 6 && hour < 18 ? 'day' : 'night';
};

export default function Home() {
  const [data, setData] = useState<ProcessedData | null>(null);
  const [activeRoutes, setActiveRoutes] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasLaunched, setHasLaunched] = useState(false);
  const [theme, setTheme] = useState<'day' | 'night'>(getThemeForCurrentTime());

  useEffect(() => {
    loadCTAData()
      .then(loadedData => {
        setData(loadedData);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Error loading data:', err);
        setError(err.message);
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setTheme(getThemeForCurrentTime());
    }, 60000);
    return () => window.clearInterval(interval);
  }, []);

  const toggleRoute = (routeId: string) => {
    setActiveRoutes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(routeId)) {
        newSet.delete(routeId);
      } else {
        newSet.add(routeId);
      }
      return newSet;
    });
  };

  const isDataReady = Boolean(data);
  const showHero = !hasLaunched;

  const handleLaunch = () => {
    if (!isDataReady) return;
    setHasLaunched(true);
  };

  return (
    <div className={`app-shell app-shell--${theme}`}>
      <div className="sky-layer" aria-hidden="true">
        <div className="sky-layer__cloud sky-layer__cloud--one" />
        <div className="sky-layer__cloud sky-layer__cloud--two" />
        <div className="sky-layer__cloud sky-layer__cloud--three" />
      </div>

      {hasLaunched && data && (
        <div className="map-stage">
          <MapComponent
            stops={data.stops}
            routes={data.routes}
            stopToRoutes={data.stopToRoutes}
            routeShapes={data.routeShapes}
            activeRoutes={activeRoutes}
            onToggleRoute={toggleRoute}
            theme={theme}
          />
          <InfoPanel
            stopCount={data.stops.length}
            routeCount={Object.keys(data.routes).length}
            activeRoutes={activeRoutes}
            routes={data.routes}
            onToggleRoute={toggleRoute}
            isLoading={false}
          />
        </div>
      )}

      {showHero && (
        <div className="cta-hero">
          <div className="cta-hero__content">
            <img
              className="cta-hero__logo"
              src="https://www.transitchicago.com/assets/1/6/cta_logo.svg"
              alt="CTA logo"
            />
            <h1 className="cta-hero__title">Chicago Transit Explorer</h1>
            <p className="cta-hero__subtitle">
              Visualize current Chicago Transit Authority stops and routes in an immersive map experience.
            </p>

            {error ? (
              <div className="cta-hero__error">
                <p>{error}</p>
                <p className="cta-hero__error-hint">
                  Confirm that all GTFS files are present in <code>public/data</code>.
                </p>
              </div>
            ) : (
              <>
                <button
                  className="cta-hero__launch-button"
                  type="button"
                  onClick={handleLaunch}
                  disabled={!isDataReady}
                >
                  View CTA Stops &amp; Routes
                </button>
                <div className="cta-hero__status">
                  {isDataReady ? (
                    <span className="cta-hero__status-ready">Route data is ready.</span>
                  ) : (
                    <>
                      <span className="cta-hero__spinner" aria-hidden="true" />
                      <span>Loading CTA stop and route data…</span>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
