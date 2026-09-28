import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import VesselMap from './components/VesselMap';
import Sidebar from './components/Sidebar';
import NavRail from './components/NavRail';
import { fetchVessels, fetchStats, fetchVessel } from './api';
import { getVesselCountry } from './utils/country';
import {
  RotateCw, Compass, Radio, Anchor,
  Ship, Zap, TrendingUp, Clock, Search, X,
  Navigation, AlertCircle, Wifi, WifiOff,
} from 'lucide-react';
import './App.css';

// Poll interval: 20s is enough for vessel tracking; more frequent = more CPU
const REFRESH_MS = 20_000;
// Remove vessels unseen for more than 5 minutes
const STALE_CUTOFF_MS = 5 * 60 * 1000;
// Track last-known backend mode so we can flush stale sim data on transition
let lastKnownSimulated = null;

// Type colors matching server classification
const TYPE_META = {
  'Cargo':         { color: '#1d4ed8', icon: '📦' },
  'Tanker':        { color: '#b91c1c', icon: '🛢️' },
  'Passenger':     { color: '#7c3aed', icon: '🚢' },
  'Fishing':       { color: '#15803d', icon: '🎣' },
  'Tug/Dredger':   { color: '#b45309', icon: '⚓' },
  'SAR/Military':  { color: '#dc2626', icon: '🛡️' },
  'High Speed':    { color: '#6d28d9', icon: '⚡' },
  'Sailing/Leisure':{ color: '#0891b2', icon: '⛵' },
  'Port/Service':  { color: '#c2410c', icon: '🔧' },
  'Other':         { color: '#475569', icon: '🚤' },
};

function getTypeColor(label) {
  return TYPE_META[label]?.color || '#475569';
}

export default function App() {
  const vesselMapRef = useRef(new Map());
  const [vessels, setVessels] = useState([]);
  const [selectedMmsi, setSelectedMmsi] = useState(null);
  const [selectedVesselDetails, setSelectedVesselDetails] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [filter, setFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [activeSection, setActiveSection] = useState('map');
  const [mapCoords, setMapCoords] = useState(null);

  const detailFetchRef = useRef(null);

  // ── Selected vessel logic ──────────────────────────────────────────────────
  useEffect(() => {
    if (selectedMmsi === null) {
      setSelectedVesselDetails(null);
      detailFetchRef.current = null;
      return;
    }

    const basic = vesselMapRef.current.get(selectedMmsi);
    if (basic) setSelectedVesselDetails(basic);

    const token = Symbol();
    detailFetchRef.current = token;
    fetchVessel(selectedMmsi)
      .then((details) => {
        if (detailFetchRef.current !== token) return;
        if (details?.mmsi != null && !details.error) {
          setSelectedVesselDetails(details);
        }
      })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMmsi]);

  // Patch live position into selected detail on every poll cycle
  useEffect(() => {
    if (!selectedMmsi || !selectedVesselDetails) return;
    const fresh = vesselMapRef.current.get(selectedMmsi);
    if (!fresh) return;
    setSelectedVesselDetails((prev) => prev ? {
      ...prev,
      lat: fresh.lat, lng: fresh.lng,
      sog: fresh.sog, cog: fresh.cog,
      heading: fresh.heading, updatedAt: fresh.updatedAt,
    } : fresh);
  }, [vessels, selectedMmsi]);

  // ── Selection handler ──────────────────────────────────────────────────────
  const handleSelectVessel = useCallback((vessel) => {
    if (!vessel) {
      setSelectedMmsi(null);
      setSelectedVesselDetails(null);
      return;
    }
    // Navigate to map view when vessel is selected from Vessels section
    if (activeSection !== 'map') setActiveSection('map');
    setSelectedMmsi(String(vessel.mmsi));
  }, [activeSection]);

  // ── Data fetching — MERGE strategy ────────────────────────────────────────
  const loadVessels = useCallback(async () => {
    try {
      const [healthRes, data] = await Promise.all([
        fetch('http://localhost:3001/api/health').then((r) => r.json()).catch(() => null),
        fetchVessels(),
      ]);

      const incoming = data.vessels || [];
      const isNowSimulated = healthRes?.simulated ?? incoming.some((v) => v.isSimulated);

      if (lastKnownSimulated === true && isNowSimulated === false) {
        const map = vesselMapRef.current;
        for (const key of [...map.keys()]) {
          const v = map.get(key);
          if (v?.isSimulated || String(key).startsWith('990')) map.delete(key);
        }
      }
      lastKnownSimulated = isNowSimulated;

      const map = vesselMapRef.current;
      const now = Date.now();
      const seenMmsis = new Set();

      for (const v of incoming) {
        const key = String(v.mmsi);
        seenMmsis.add(key);
        const prev = map.get(key);
        map.set(key, prev ? { ...prev, ...v } : v);
      }

      for (const [key, v] of map) {
        if (!seenMmsis.has(key) && (now - (v.updatedAt || 0)) > STALE_CUTOFF_MS) {
          map.delete(key);
        }
      }

      const list = Array.from(map.values());
      setVessels(list);
      setLastUpdate(new Date());
      setConnectionStatus(
        healthRes
          ? (healthRes.simulated ? 'simulated' : healthRes.streaming ? 'live' : 'offline')
          : (incoming.length > 0 ? (isNowSimulated ? 'simulated' : 'live') : 'live')
      );
    } catch {
      setConnectionStatus('offline');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    try { setStats(await fetchStats()); } catch {}
  }, []);

  // Initial load + recurring poll — always-on, no pause
  useEffect(() => {
    let active = true;
    (async () => { if (active) await Promise.all([loadVessels(), loadStats()]); })();
    const iv = setInterval(() => { if (active) { loadVessels(); loadStats(); } }, REFRESH_MS);
    return () => { active = false; clearInterval(iv); };
  }, [loadVessels, loadStats]);

  // ── Filtering ──────────────────────────────────────────────────────────────
  const filteredVessels = useMemo(() => {
    const q = filter.toLowerCase();
    return vessels.filter((v) => {
      const matchName = !filter
        || (v.name || '').toLowerCase().includes(q)
        || (v.destination || '').toLowerCase().includes(q)
        || String(v.mmsi).includes(q);
      const matchType = typeFilter === 'All' || v.typeLabel === typeFilter;
      return matchName && matchType;
    });
  }, [vessels, filter, typeFilter]);

  const vesselTypes = useMemo(
    () => ['All', ...new Set(vessels.map((v) => v.typeLabel || 'Unknown').sort())],
    [vessels],
  );

  const statusLabel = {
    connecting: 'Connecting…',
    live: 'AIS Live',
    simulated: 'Simulator',
    offline: 'Offline',
  }[connectionStatus] || 'Unknown';

  const underway = vessels.filter(v => (v.sog || 0) > 0.5).length;

  return (
    <div className="app-layout">
      {/* ─── Collapsible Navigation Rail ─── */}
      <NavRail active={activeSection} onChange={setActiveSection} />

      <div className="app-main">
        {/* ══════════ TOP BAR ══════════ */}
        <header className="top-bar">
          {/* Center: Search */}
          <div className="tb-search-wrap">
            <Search size={14} className="tb-search-icon" />
            <input
              className="tb-search-input"
              placeholder="Search vessels, MMSI, IMO, callsign…"
              value={filter}
              onChange={e => setFilter(e.target.value)}
            />
            {filter && (
              <button className="tb-search-clear" onClick={() => setFilter('')}>
                <X size={12} />
              </button>
            )}
          </div>

          {/* Right: status + refresh */}
          <div className="tb-actions">
            <div className={`status-pill ${connectionStatus}`}>
              <span className="pill-dot" />
              <Radio size={10} />
              <span>{statusLabel}</span>
              {vessels.length > 0 && (
                <span className="pill-count">{vessels.length.toLocaleString()}</span>
              )}
            </div>
            <button
              className="action-pill"
              onClick={() => { loadVessels(); loadStats(); }}
              disabled={loading}
              title="Refresh data"
            >
              <RotateCw size={12} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </header>

        {/* ══════════ MAIN WORKSPACE ══════════ */}
        <div className="workspace">
          <div className="content-area">

            {/* ── Vessels section panel ── */}
            {activeSection === 'vessels' && (
              <div className="section-panel">
                <div className="sp-header">
                  <Ship size={16} />
                  <span>Vessels</span>
                  <span className="sp-count">{vessels.length}</span>
                </div>
                <Sidebar
                  vessels={filteredVessels}
                  allVessels={vessels}
                  selected={selectedVesselDetails}
                  onSelect={handleSelectVessel}
                  filter={filter}
                  onFilterChange={setFilter}
                  typeFilter={typeFilter}
                  onTypeFilterChange={setTypeFilter}
                  vesselTypes={vesselTypes}
                  loading={loading}
                  stats={stats}
                />
              </div>
            )}

            {/* ── Shipping Intelligence section ── */}
            {activeSection === 'intelligence' && (
              <div className="section-panel">
                <div className="sp-header">
                  <TrendingUp size={16} />
                  <span>Shipping Intelligence</span>
                </div>
                <div className="intel-grid">
                  <div className="intel-card intel-card--accent">
                    <div className="ic-val">{(stats?.total || vessels.length).toLocaleString()}</div>
                    <div className="ic-label">Total Vessels</div>
                    <div className="ic-sub">In AIS database</div>
                  </div>
                  <div className="intel-card">
                    <div className="ic-val ic-val--green">{underway}</div>
                    <div className="ic-label">Underway</div>
                    <div className="ic-sub">SOG {'>'} 0.5 kn</div>
                  </div>
                  <div className="intel-card">
                    <div className="ic-val">{vessels.length - underway}</div>
                    <div className="ic-label">At Rest</div>
                    <div className="ic-sub">Anchored / Moored</div>
                  </div>
                  <div className="intel-card">
                    <div className="ic-val">{Object.keys(stats?.byType || {}).length}</div>
                    <div className="ic-label">Vessel Types</div>
                    <div className="ic-sub">Classified by AIS</div>
                  </div>

                  <div className="intel-divider" />
                  <div className="intel-section-title">Live Feed Status</div>

                  <div className={`intel-status-card intel-status-card--${connectionStatus}`}>
                    <div className="isc-dot" />
                    <div className="isc-body">
                      <div className="isc-title">{statusLabel}</div>
                      <div className="isc-sub">
                        {connectionStatus === 'live'
                          ? 'AISStream WebSocket — receiving live AIS positions'
                          : connectionStatus === 'simulated'
                          ? 'Simulator mode — add AISSTREAM_API_KEY to go live'
                          : connectionStatus === 'offline'
                          ? 'Connection lost — retrying…'
                          : 'Establishing connection…'}
                      </div>
                    </div>
                  </div>

                  {Object.entries(stats?.byType || {}).length > 0 && (
                    <>
                      <div className="intel-section-title">By Type</div>
                      {Object.entries(stats.byType)
                        .sort((a, b) => b[1] - a[1])
                        .map(([type, count]) => (
                          <div key={type} className="intel-type-row">
                            <span className="itr-dot" style={{ background: getTypeColor(type) }} />
                            <span className="itr-name">{type}</span>
                            <span className="itr-count">{count}</span>
                            <div className="itr-bar-track">
                              <div
                                className="itr-bar-fill"
                                style={{
                                  width: `${(count / (stats.total || 1)) * 100}%`,
                                  background: getTypeColor(type),
                                }}
                              />
                            </div>
                          </div>
                        ))}
                    </>
                  )}

                  {lastUpdate && (
                    <div className="intel-footer">
                      <Clock size={11} />
                      <span>Updated {lastUpdate.toLocaleTimeString()}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ── Placeholder sections ── */}
            {['ports', 'lighthouses', 'stations', 'companies', 'gallery', 'news', 'plans', 'notifications', 'support'].includes(activeSection) && (
              <div className="section-panel">
                <PlaceholderSection section={activeSection} />
              </div>
            )}

            {/* MAP is always mounted and always visible in flex remaining space */}
            <div className="map-area">
              <VesselMap
                vessels={filteredVessels}
                selected={selectedVesselDetails}
                onSelect={handleSelectVessel}
                onCoords={setMapCoords}
              />

              {/* Right-side vessel detail panel */}
              {selectedVesselDetails && (
                <aside className="detail-panel">
                  <VesselDetailPanel
                    vessel={selectedVesselDetails}
                    onClose={() => handleSelectVessel(null)}
                  />
                </aside>
              )}

              {/* Coordinate bar */}
              {mapCoords && (
                <div className="coord-bar">
                  <span className="coord-item">
                    <span className="coord-lbl">LAT</span>
                    <span className="coord-val">{mapCoords.lat >= 0 ? `${mapCoords.lat.toFixed(5)}° N` : `${Math.abs(mapCoords.lat).toFixed(5)}° S`}</span>
                  </span>
                  <span className="coord-sep" />
                  <span className="coord-item">
                    <span className="coord-lbl">LON</span>
                    <span className="coord-val">{mapCoords.lng >= 0 ? `${mapCoords.lng.toFixed(5)}° E` : `${Math.abs(mapCoords.lng).toFixed(5)}° W`}</span>
                  </span>
                </div>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Placeholder Section ──────────────────────────────────────────────────────
const PLACEHOLDER_META = {
  ports:         { icon: '⚓', title: 'Ports',              sub: 'Port intelligence module' },
  lighthouses:   { icon: '🗼', title: 'Lighthouses',         sub: 'Lighthouse & AtoN registry' },
  stations:      { icon: '📡', title: 'AIS Stations',        sub: 'AIS receiver network' },
  companies:     { icon: '🏢', title: 'Companies',           sub: 'Vessel owner/operator database' },
  gallery:       { icon: '🖼️', title: 'Photo Gallery',       sub: 'Vessel photo submissions' },
  news:          { icon: '📰', title: 'Maritime News',       sub: 'Latest maritime intelligence' },
  plans:         { icon: '💳', title: 'Plans & Data',        sub: 'Data service tiers' },
  notifications: { icon: '🔔', title: 'Notifications',       sub: 'Alerts & vessel watches' },
  support:       { icon: '❓', title: 'Support',             sub: 'Help center & documentation' },
};

function PlaceholderSection({ section }) {
  const meta = PLACEHOLDER_META[section] || { icon: '🚧', title: section, sub: '' };
  return (
    <div className="placeholder-section">
      <div className="ph-icon">{meta.icon}</div>
      <div className="ph-title">{meta.title}</div>
      <div className="ph-sub">{meta.sub}</div>
      <div className="ph-badge">
        <AlertCircle size={12} />
        Data source not connected
      </div>
      <p className="ph-desc">
        This module is part of the MarineRadar frontend architecture.
        Connect a data source to activate it — no backend changes needed for the UI.
      </p>
    </div>
  );
}

// ─── Vessel Detail Panel ──────────────────────────────────────────────────────
function navStatusLabel(n) {
  return ({
    0: 'Underway (Engine)', 1: 'At Anchor', 2: 'Not Under Command',
    3: 'Restricted Maneuverability', 4: 'Constrained by Draught',
    5: 'Moored', 6: 'Aground', 7: 'Engaged in Fishing',
    8: 'Underway (Sailing)', 15: 'Undefined',
  })[n] ?? `Status ${n}`;
}

function VesselDetailPanel({ vessel, onClose }) {
  const length = vessel.dimA != null ? (vessel.dimA || 0) + (vessel.dimB || 0) : null;
  const beam   = vessel.dimC != null ? (vessel.dimC || 0) + (vessel.dimD || 0) : null;
  const speed  = vessel.sog != null ? Number(vessel.sog).toFixed(1) : null;
  const typeColor = getTypeColor(vessel.typeLabel);
  const country   = getVesselCountry(vessel.mmsi);
  const speedKph  = speed ? (parseFloat(speed) * 1.852).toFixed(1) : null;

  return (
    <div className="detail-panel-inner">
      {/* Header */}
      <div className="dp-header" style={{ borderLeft: `3px solid ${typeColor}` }}>
        <div className="dp-vessel-id">
          <div className="dp-type-badge" style={{ background: `${typeColor}18`, color: typeColor, borderColor: `${typeColor}30` }}>
            {vessel.typeLabel || 'Unknown'}
          </div>
          <h2 className="dp-name">{vessel.name || `MMSI ${vessel.mmsi}`}</h2>
          <div className="dp-sub-header">
            <span className="dp-flag">{country.flag}</span>
            <span className="dp-flag-name">{country.name}</span>
            {vessel.callsign && <span className="dp-sub-divider"> · {vessel.callsign}</span>}
          </div>
        </div>
        <button className="dp-close" onClick={onClose}>✕</button>
      </div>

      <div className="dp-content">
        {/* Live telemetry */}
        <section className="dp-section">
          <div className="dp-section-title"><Zap size={12} /> Live Telemetry</div>
          <div className="telem-grid">
            <div className="telem-card primary">
              <div className="tc-icon">🚢</div>
              <div className="tc-val">{speed ?? '—'} <span className="tc-unit">kn</span></div>
              <div className="tc-label">Speed</div>
              {speedKph && <div className="tc-sub">{speedKph} km/h</div>}
            </div>
            <div className="telem-card">
              <div className="tc-val">{vessel.cog != null ? `${Math.round(vessel.cog)}°` : '—'}</div>
              <div className="tc-label">Course</div>
            </div>
            <div className="telem-card">
              <div className="tc-val">{vessel.heading != null ? `${Math.round(vessel.heading)}°` : '—'}</div>
              <div className="tc-label">Heading</div>
            </div>
            <div className="telem-card">
              <div className="tc-val nav-status-val" style={{ color: typeColor }}>
                {vessel.navStatus != null ? navStatusLabel(vessel.navStatus).split(' ')[0] : 'Active'}
              </div>
              <div className="tc-label">Nav Status</div>
            </div>
          </div>
        </section>

        {/* Position */}
        <section className="dp-section">
          <div className="dp-section-title"><TrendingUp size={12} /> Position</div>
          <div className="pos-display">
            <div className="pos-row">
              <span className="pos-label">Latitude</span>
              <span className="pos-val">{vessel.lat != null ? `${vessel.lat.toFixed(5)}°` : '—'}</span>
            </div>
            <div className="pos-row">
              <span className="pos-label">Longitude</span>
              <span className="pos-val">{vessel.lng != null ? `${vessel.lng.toFixed(5)}°` : '—'}</span>
            </div>
          </div>
        </section>

        {/* Identifiers */}
        <section className="dp-section">
          <div className="dp-section-title"><Ship size={12} /> Identifiers</div>
          <div className="id-table">
            <div className="id-row"><span>Flag</span><span>{country.flag} &nbsp;{country.name}</span></div>
            <div className="id-row"><span>MMSI</span><span>{vessel.mmsi}</span></div>
            {vessel.imo && <div className="id-row"><span>IMO</span><span>{vessel.imo}</span></div>}
            {vessel.callsign && <div className="id-row"><span>Callsign</span><span>{vessel.callsign}</span></div>}
            {(length || beam) && (
              <div className="id-row">
                <span>Dimensions</span>
                <span>{length ? `${length}m` : '—'} × {beam ? `${beam}m` : '—'}</span>
              </div>
            )}
            {vessel.draught && <div className="id-row"><span>Draught</span><span>{vessel.draught} m</span></div>}
          </div>
        </section>

        {/* History */}
        {vessel.history && vessel.history.length > 1 && (
          <section className="dp-section">
            <div className="dp-section-title"><Clock size={12} /> Track History</div>
            <div className="history-preview">
              <div className="history-count">{vessel.history.length} position points recorded</div>
              <div className="history-bar">
                {vessel.history.slice(-20).map((_, i) => (
                  <div
                    key={i}
                    className="history-pip"
                    style={{
                      background: typeColor,
                      opacity: 0.3 + (i / vessel.history.length) * 0.7
                    }}
                  />
                ))}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
