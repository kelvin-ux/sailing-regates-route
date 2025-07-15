import React, { useEffect, useRef, useState } from 'react';
import { Box, Spinner, Alert, AlertIcon } from '@chakra-ui/react';
import L from 'leaflet';
import { MapContainer, TileLayer, LayersControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

import { RouteResponse, WeatherData, Obstacle } from '../types';
import RouteLayer from './map/RouteLayer';
import WeatherLayer from './map/WeatherLayer';
import ObstacleLayer from './map/ObstacleLayer';
import MarkerLayer from './map/MarkerLayer';
import { useMapEvents } from '../hooks/useMapEvents';

// Poprawka ikon Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.divIcon({
  html: '<div class="custom-div-icon"></div>',
  iconSize: [30, 42],
  iconAnchor: [15, 42],
  popupAnchor: [0, -42],
  className: 'custom-div-icon'
});

L.Marker.prototype.options.icon = DefaultIcon;

interface MapPaneProps {
  routes: RouteResponse[];
  weatherData?: WeatherData;
  obstacles: Obstacle[];
  selectedRoute?: RouteResponse;
  onRouteSelect?: (route: RouteResponse) => void;
  onMapClick?: (latlng: L.LatLng) => void;
  isLoading?: boolean;
  error?: string;
  markers?: Array<{
    position: [number, number];
    type: 'start' | 'end' | 'waypoint';
    popup?: string;
  }>;
}

const MapPane: React.FC<MapPaneProps> = ({
  routes,
  weatherData,
  obstacles,
  selectedRoute,
  onRouteSelect,
  onMapClick,
  isLoading = false,
  error,
  markers = []
}) => {
  const mapRef = useRef<L.Map | null>(null);
  const [mapCenter] = useState<[number, number]>([54.52, 18.55]); // Zatoka Gdańska
  const [mapZoom] = useState(10);

  // Komponent do obsługi eventów mapy
  const MapEventHandler: React.FC = () => {
    const map = useMap();
    
    useMapEvents({
      click: (e) => {
        if (onMapClick) {
          onMapClick(e.latlng);
        }
      },
    });

    useEffect(() => {
      mapRef.current = map;
    }, [map]);

    return null;
  };

  // Automatyczne dopasowanie widoku do tras
  useEffect(() => {
    if (mapRef.current && routes.length > 0) {
      const group = new L.FeatureGroup();
      
      routes.forEach(route => {
        route.waypoints.forEach(waypoint => {
          const marker = L.marker([waypoint.point.lat, waypoint.point.lon]);
          group.addLayer(marker);
        });
      });

      if (group.getLayers().length > 0) {
        mapRef.current.fitBounds(group.getBounds(), {
          padding: [20, 20]
        });
      }
    }
  }, [routes]);

  if (error) {
    return (
      <Alert status="error" borderRadius="md">
        <AlertIcon />
        Błąd ładowania mapy: {error}
      </Alert>
    );
  }

  return (
    <Box position="relative" height="100%" width="100%">
      {isLoading && (
        <Box
          position="absolute"
          top="50%"
          left="50%"
          transform="translate(-50%, -50%)"
          zIndex={1000}
          bg="white"
          p={4}
          borderRadius="md"
          boxShadow="lg"
        >
          <Spinner size="lg" />
        </Box>
      )}
      
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <MapEventHandler />
        
        {/* Warstwy kafelków */}
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="OpenStreetMap">
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
          </LayersControl.BaseLayer>
          
          <LayersControl.BaseLayer name="Satellite">
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution="&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
            />
          </LayersControl.BaseLayer>
          
          <LayersControl.Overlay name="SeaMarks">
            <TileLayer
              url="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png"
              attribution="&copy; OpenSeaMap contributors"
              opacity={0.8}
            />
          </LayersControl.Overlay>
          
          {/* Warstwy danych */}
          <LayersControl.Overlay name="Trasy" checked>
            <RouteLayer
              routes={routes}
              selectedRoute={selectedRoute}
              onRouteSelect={onRouteSelect}
            />
          </LayersControl.Overlay>
          
          <LayersControl.Overlay name="Przeszkody">
            <ObstacleLayer obstacles={obstacles} />
          </LayersControl.Overlay>
          
          {weatherData && (
            <LayersControl.Overlay name="Pogoda">
              <WeatherLayer weatherData={weatherData} />
            </LayersControl.Overlay>
          )}
          
          {markers.length > 0 && (
            <LayersControl.Overlay name="Markery" checked>
              <MarkerLayer markers={markers} />
            </LayersControl.Overlay>
          )}
        </LayersControl>
      </MapContainer>
    </Box>
  );
};

export default MapPane;
