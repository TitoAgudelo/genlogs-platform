"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { GoogleMap, DirectionsRenderer } from "@react-google-maps/api";

interface RouteMapProps {
  origin: string;
  destination: string;
}

const MAP_CONTAINER_STYLE = {
  width: "100%",
  height: "400px",
  borderRadius: "8px",
};

const MAP_OPTIONS: google.maps.MapOptions = {
  zoomControl: true,
  streetViewControl: false,
  mapTypeControl: false,
  fullscreenControl: true,
  styles: [
    { elementType: "geometry", stylers: [{ color: "#1d2c4d" }] },
    { elementType: "labels.text.stroke", stylers: [{ color: "#1a3646" }] },
    { elementType: "labels.text.fill", stylers: [{ color: "#8ec3b9" }] },
    {
      featureType: "water",
      elementType: "geometry.fill",
      stylers: [{ color: "#0e1626" }],
    },
    {
      featureType: "road",
      elementType: "geometry",
      stylers: [{ color: "#304a7d" }],
    },
    {
      featureType: "road",
      elementType: "geometry.stroke",
      stylers: [{ color: "#255763" }],
    },
  ],
};

const ROUTE_COLORS = ["#3b82f6", "#10b981", "#f59e0b"];

export default function RouteMap({ origin, destination }: RouteMapProps) {
  const [directions, setDirections] = useState<google.maps.DirectionsResult[]>(
    [],
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isGoogleLoaded, setIsGoogleLoaded] = useState(false);
  const mapRef = useRef<google.maps.Map | null>(null);

  useEffect(() => {
    const checkGoogle = () => {
      if (typeof google !== "undefined" && google.maps) {
        setIsGoogleLoaded(true);
      }
    };
    checkGoogle();
    const timer = setTimeout(checkGoogle, 1000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isGoogleLoaded || !origin || !destination) return;

    setLoading(true);
    setError("");
    setDirections([]);

    const directionsService = new google.maps.DirectionsService();

    // Request 3 alternative routes
    directionsService.route(
      {
        origin: `${origin}, USA`,
        destination: `${destination}, USA`,
        travelMode: google.maps.TravelMode.DRIVING,
        provideRouteAlternatives: true,
      },
      (result, status) => {
        if (status === google.maps.DirectionsStatus.OK && result) {
          // Take up to 3 routes
          const routes = result.routes.slice(0, 3);
          // Create separate DirectionsResult for each route to render with different colors
          const multipleResults = routes.map((route, index) => {
            const dirResult = { ...result } as google.maps.DirectionsResult;
            return {
              ...dirResult,
              routes: [route],
            } as google.maps.DirectionsResult;
          });
          setDirections(multipleResults);
        } else {
          setError("Could not calculate routes. Try different cities.");
        }
        setLoading(false);
      },
    );
  }, [isGoogleLoaded, origin, destination]);

  const onMapLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
  }, []);

  if (!isGoogleLoaded) {
    return (
      <div className="map-placeholder">
        <p>Google Maps requires an API key. Add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY to your .env file.</p>
      </div>
    );
  }

  return (
    <div className="map-container">
      <div className="map-header">
        <h3>Route Map</h3>
        <div className="map-legend">
          {directions.map((_, i) => (
            <span key={i} className="legend-item">
              <span
                className="legend-color"
                style={{ backgroundColor: ROUTE_COLORS[i] }}
              />
              Route {i + 1}
            </span>
          ))}
        </div>
      </div>

      {loading && (
        <div className="loading" style={{ justifyContent: "center", padding: "40px 0" }}>
          <div className="spinner" />
          <span>Calculating routes...</span>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <GoogleMap
        mapContainerStyle={MAP_CONTAINER_STYLE}
        options={MAP_OPTIONS}
        zoom={6}
        center={{ lat: 39.8283, lng: -98.5795 }}
        onLoad={onMapLoad}
      >
        {directions.map((dir, index) => (
          <DirectionsRenderer
            key={index}
            directions={dir}
            options={{
              polylineOptions: {
                strokeColor: ROUTE_COLORS[index],
                strokeWeight: index === 0 ? 5 : 3,
                strokeOpacity: index === 0 ? 1 : 0.6,
              },
              suppressMarkers: index > 0,
              preserveViewport: index > 0,
            }}
          />
        ))}
      </GoogleMap>

      {directions.length > 0 && (
        <div className="route-details">
          {directions.map((dir, index) => {
            const leg = dir.routes[0]?.legs[0];
            if (!leg) return null;
            return (
              <div key={index} className="route-detail-card">
                <span
                  className="legend-color"
                  style={{ backgroundColor: ROUTE_COLORS[index] }}
                />
                <div>
                  <strong>Route {index + 1}</strong>
                  <span className="route-detail-meta">
                    {leg.distance?.text} &middot; {leg.duration?.text}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
