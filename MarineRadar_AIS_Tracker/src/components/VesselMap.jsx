import { useEffect, useRef, useState, memo } from 'react';
import { Map as MapLibreMap, NavigationControl as MapLibreNavControl } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Layers, Navigation as NavIcon } from 'lucide-react';

// ─── Tile Styles (public Carto GL styles — no API key required) ──────────────
const TILES = {
  dark: {
    url: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    label: 'Dark Nautical',
  },
  light: {
    url: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    label: 'Light',
  },
  voyager: {
    url: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
    label: 'Voyager',
  },
};

// ─── Ship icon: SVG arrow pointing UP (north = 0°), color-coded by type ──────
// MapLibre will rotate this according to `icon-rotate: heading`.
// The "nose" of the arrow is at the top (SVG y=0), so 0° = pointing up = North.
function buildShipSVG(color) {
  return `<svg viewBox="0 0 24 28" width="18" height="21" xmlns="http://www.w3.org/2000/svg">
  <path d="M12 1 L20 22 L12 18 L4 22 Z"
        fill="${color}" stroke="#ffffff" stroke-width="1.8" stroke-linejoin="round"/>
</svg>`;
}

// Cache ship HTMLImageElement objects by color
const shipImageCache = new Map();

function getShipImage(color) {
  if (shipImageCache.has(color)) return shipImageCache.get(color);
  const img = new Image(18, 21);
  img.src =
    'data:image/svg+xml;charset=utf-8,' +
    encodeURIComponent(buildShipSVG(color));
  shipImageCache.set(color, img);
  return img;
}

// ─── Layer / source name constants ───────────────────────────────────────────
const SRC_VESSELS = 'vessels';
const SRC_TRAIL = 'selected-trail';
const LYR_HIGHLIGHT = 'vessels-highlight';
const LYR_VESSELS = 'vessels-layer';
const LYR_TRAIL = 'trail-layer';
const LYR_OPENSEAMAP = 'openseamap-layer';
const SRC_OPENSEAMAP = 'openseamap';

// Known vessel type colors (must match server classifyShip)
const TYPE_COLORS = [
  '#1d4ed8', // Cargo
  '#b91c1c', // Tanker
  '#7c3aed', // Passenger / High Speed
  '#15803d', // Fishing
  '#b45309', // Tug/Dredger / Port Service
  '#dc2626', // SAR/Military
  '#0891b2', // Sailing/Leisure
  '#475569', // Other (fallback)
];

// ─── Layer control dropdown ───────────────────────────────────────────────────
const MapLayerControl = memo(function MapLayerControl({ style, onStyle }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="map-layer-ctrl">
      <button
        className={`mlc-toggle ${open ? 'open' : ''}`}
        onClick={() => setOpen((o) => !o)}
      >
        <Layers size={15} />
        <span>Layers</span>
      </button>
      {open && (
        <div className="mlc-dropdown">
          <div className="mlc-group-label">Base Map</div>
          <div className="mlc-tabs">
            {Object.keys(TILES).map((k) => (
              <button
                key={k}
                className={`mlc-tab ${style === k ? 'active' : ''}`}
                onClick={() => {
                  onStyle(k);
                  setOpen(false);
                }}
              >
                {TILES[k].label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

// ─── Main VesselMap ───────────────────────────────────────────────────────────
export default function VesselMap({ vessels, selected, onSelect }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layersReadyRef = useRef(false);
  const [mapStyle, setMapStyle] = useState('dark');
  // Keep latest props accessible inside stable map callbacks
  const vesselsRef = useRef(vessels);
  const onSelectRef = useRef(onSelect);
  vesselsRef.current = vessels;
  onSelectRef.current = onSelect;

  // ── 1. Initialize map once ─────────────────────────────────────────────────
  useEffect(() => {
    if (mapRef.current || !containerRef.current) return;

    const map = new MapLibreMap({
      container: containerRef.current,
      style: TILES.dark.url, // always start dark; style changes handled separately
      center: [15, 25],
      zoom: 3,
      minZoom: 2,
      attributionControl: true,
    });
    mapRef.current = map;

    map.addControl(
      new MapLibreNavControl({ showCompass: false }),
      'bottom-right'
    );

    // Pre-load all known ship images before the style finishes loading
    function preloadImages() {
      TYPE_COLORS.forEach((color) => {
        const imgId = `ship-${color}`;
        if (!map.hasImage(imgId)) {
          const img = getShipImage(color);
          if (img.complete) {
            map.addImage(imgId, img);
          } else {
            img.onload = () => {
              if (map && !map.removed && !map.hasImage(imgId)) {
                map.addImage(imgId, img);
              }
            };
          }
        }
      });
    }

    function addSourcesAndLayers() {
      if (layersReadyRef.current) return;

      preloadImages();

      // OpenSeaMap overlay (nautical marks, buoys, lighthouses)
      if (!map.getSource(SRC_OPENSEAMAP)) {
        map.addSource(SRC_OPENSEAMAP, {
          type: 'raster',
          tiles: ['https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png'],
          tileSize: 256,
          attribution: '© <a href="https://www.openseamap.org">OpenSeaMap</a>',
        });
      }
      if (!map.getLayer(LYR_OPENSEAMAP)) {
        map.addLayer({
          id: LYR_OPENSEAMAP,
          type: 'raster',
          source: SRC_OPENSEAMAP,
          minzoom: 6,
          paint: { 'raster-opacity': 0.85 },
        });
      }

      // Vessel trail (selected vessel's historical track as LineString)
      if (!map.getSource(SRC_TRAIL)) {
        map.addSource(SRC_TRAIL, {
          type: 'geojson',
          data: emptyLineString(),
        });
      }
      if (!map.getLayer(LYR_TRAIL)) {
        map.addLayer({
          id: LYR_TRAIL,
          type: 'line',
          source: SRC_TRAIL,
          layout: { 'line-join': 'round', 'line-cap': 'round' },
          paint: {
            'line-color': ['coalesce', ['get', 'color'], '#60a5fa'],
            'line-width': 2,
            'line-opacity': 0.55,
            'line-dasharray': [3, 3],
          },
        });
      }

      // Vessel positions GeoJSON source
      if (!map.getSource(SRC_VESSELS)) {
        map.addSource(SRC_VESSELS, {
          type: 'geojson',
          data: emptyCollection(),
        });
      }

      // Selection highlight ring (circle behind the selected icon)
      if (!map.getLayer(LYR_HIGHLIGHT)) {
        map.addLayer({
          id: LYR_HIGHLIGHT,
          type: 'circle',
          source: SRC_VESSELS,
          filter: ['==', ['get', 'isSelected'], true],
          paint: {
            'circle-radius': 14,
            'circle-color': 'rgba(255,255,255,0.18)',
            'circle-stroke-width': 2,
            'circle-stroke-color': ['coalesce', ['get', 'color'], '#60a5fa'],
          },
        });
      }

      // Ship symbol layer (icon-rotate uses true heading / CoG)
      if (!map.getLayer(LYR_VESSELS)) {
        map.addLayer({
          id: LYR_VESSELS,
          type: 'symbol',
          source: SRC_VESSELS,
          layout: {
            // icon-image references an image pre-loaded per color
            'icon-image': [
              'concat',
              'ship-',
              ['coalesce', ['get', 'color'], '#475569'],
            ],
            // heading is degrees clockwise from North — matches MapLibre convention
            'icon-rotate': ['coalesce', ['get', 'heading'], 0],
            'icon-rotation-alignment': 'map',
            'icon-allow-overlap': true,
            'icon-ignore-placement': true,
            'icon-size': [
              'case',
              ['==', ['get', 'isSelected'], true],
              1.3,
              0.9,
            ],
          },
        });
      }

      // Vessel click → selection
      map.on('click', LYR_VESSELS, (e) => {
        if (!e.features?.length) return;
        const props = e.features[0].properties;
        const mmsi = String(props.mmsi);
        const vessel = vesselsRef.current.find(
          (v) => String(v.mmsi) === mmsi
        );
        if (vessel) onSelectRef.current(vessel);
      });

      map.on('mouseenter', LYR_VESSELS, () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', LYR_VESSELS, () => {
        map.getCanvas().style.cursor = '';
      });

      layersReadyRef.current = true;
    }

    // MapLibre fires 'load' once on initial style load; fires 'styledata' on
    // subsequent style swaps.  We re-run addSourcesAndLayers on each full style
    // reload so our custom sources/layers are always present.
    map.on('load', () => {
      addSourcesAndLayers();
    });

    map.on('style.load', () => {
      layersReadyRef.current = false; // style was swapped — re-add everything
      addSourcesAndLayers();
    });

    return () => {
      // Clean up on component unmount
      map.remove();
      mapRef.current = null;
      layersReadyRef.current = false;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 2. Handle style switching ──────────────────────────────────────────────
  // We store the current style key in a ref so the effect can read it without
  // re-running initialization.
  const mapStyleRef = useRef(mapStyle);
  useEffect(() => {
    mapStyleRef.current = mapStyle;
    const map = mapRef.current;
    if (!map) return;
    map.setStyle(TILES[mapStyle].url);
    // layers will be re-added via the 'style.load' listener above
  }, [mapStyle]);

  // ── 3. Sync vessel data → GeoJSON source ──────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !layersReadyRef.current) return;

    const selMmsi = selected ? String(selected.mmsi) : null;

    const features = vessels
      .filter((v) => v.lat != null && v.lng != null)
      .map((v) => {
        const color = v.color || '#475569';

        // Ensure the ship image for this color exists in the map sprite
        const imgId = `ship-${color}`;
        if (!map.hasImage(imgId)) {
          const img = getShipImage(color);
          const add = () => {
            if (map && !map.removed && !map.hasImage(imgId)) {
              map.addImage(imgId, img);
            }
          };
          img.complete ? add() : (img.onload = add);
        }

        // Rotation: prefer true heading; fall back to CoG; default 0
        const heading =
          v.heading != null && v.heading !== 511
            ? v.heading
            : v.cog != null
            ? v.cog
            : 0;

        return {
          type: 'Feature',
          geometry: {
            type: 'Point',
            // GeoJSON convention: [longitude, latitude]
            coordinates: [v.lng, v.lat],
          },
          properties: {
            mmsi: v.mmsi,
            name: v.name || `MMSI ${v.mmsi}`,
            color,
            heading,
            isSelected: String(v.mmsi) === selMmsi,
          },
        };
      });

    const src = map.getSource(SRC_VESSELS);
    if (src) {
      src.setData({ type: 'FeatureCollection', features });
    }
  }, [vessels, selected]);

  // ── 4. Sync selected vessel trail → LineString source ─────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !layersReadyRef.current) return;

    const src = map.getSource(SRC_TRAIL);
    if (!src) return;

    if (selected?.history?.length > 1) {
      // history points are {lat, lng, timestamp} — GeoJSON needs [lng, lat]
      const coords = selected.history
        .filter((p) => p.lat != null && p.lng != null)
        .map((p) => [p.lng, p.lat]);

      // Append current position so trail connects to live location
      if (selected.lat != null && selected.lng != null) {
        coords.push([selected.lng, selected.lat]);
      }

      src.setData({
        type: 'Feature',
        geometry: { type: 'LineString', coordinates: coords },
        properties: { color: selected.color || '#60a5fa' },
      });
    } else {
      src.setData(emptyLineString());
    }
  }, [selected]);

  // ── 5. Fly to selected vessel when selection changes (not on every update) ─
  const prevSelectedMmsi = useRef(null);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selected?.lat || !selected?.lng) {
      prevSelectedMmsi.current = null;
      return;
    }
    const key = String(selected.mmsi);
    if (prevSelectedMmsi.current === key) return; // same vessel — no pan
    prevSelectedMmsi.current = key;

    const zoom = Math.max(map.getZoom(), 6);
    map.flyTo({
      center: [selected.lng, selected.lat],
      zoom,
      duration: 750,
    });
  }, [selected?.mmsi]); // eslint-disable-line react-hooks/exhaustive-deps

  const visibleCount = vessels.filter(
    (v) => v.lat != null && v.lng != null
  ).length;

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      {/* MapLibre renders into this div */}
      <div ref={containerRef} style={{ height: '100%', width: '100%' }} />

      {/* Layer switcher */}
      <MapLayerControl style={mapStyle} onStyle={setMapStyle} />

      {/* Vessel count badge */}
      <div className="map-vessel-count">
        <NavIcon size={11} />
        <span>{visibleCount} shown</span>
      </div>

      {/* Empty state overlay */}
      {vessels.length === 0 && (
        <div className="map-empty-state">
          <div className="mes-icon">🛰️</div>
          <div className="mes-title">Scanning for vessels…</div>
          <div className="mes-sub">Awaiting AIS data</div>
        </div>
      )}
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function emptyCollection() {
  return { type: 'FeatureCollection', features: [] };
}
function emptyLineString() {
  return {
    type: 'Feature',
    geometry: { type: 'LineString', coordinates: [] },
    properties: {},
  };
}
