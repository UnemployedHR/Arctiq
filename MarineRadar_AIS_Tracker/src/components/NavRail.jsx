import { useState, useRef } from 'react';
import {
  Map, BarChart2, Ship, Anchor, Lightbulb, Radio,
  Building2, Image, Newspaper, CreditCard, Bell, HelpCircle, User,
  ChevronRight,
} from 'lucide-react';

const PRIMARY_NAV = [
  { id: 'map',          icon: Map,        label: 'Live Map',              live: true  },
  { id: 'intelligence', icon: BarChart2,   label: 'Shipping Intelligence', live: true  },
  { id: 'vessels',      icon: Ship,        label: 'Vessels',              live: true  },
  { id: 'ports',        icon: Anchor,      label: 'Ports',                live: false },
  { id: 'lighthouses',  icon: Lightbulb,   label: 'Lighthouses',          live: false },
  { id: 'stations',     icon: Radio,       label: 'Stations',             live: false },
  { id: 'companies',    icon: Building2,   label: 'Companies',            live: false },
  { id: 'gallery',      icon: Image,       label: 'Photo Gallery',        live: false },
  { id: 'news',         icon: Newspaper,   label: 'Maritime News',        live: false },
];

const SECONDARY_NAV = [
  { id: 'plans',         icon: CreditCard,   label: 'Plans & Data'    },
  { id: 'notifications', icon: Bell,         label: 'Notifications'   },
  { id: 'support',       icon: HelpCircle,   label: 'Support'         },
];

export default function NavRail({ active, onChange }) {
  const [expanded, setExpanded] = useState(false);
  const leaveTimer = useRef(null);

  function handleMouseEnter() {
    clearTimeout(leaveTimer.current);
    setExpanded(true);
  }

  function handleMouseLeave() {
    leaveTimer.current = setTimeout(() => setExpanded(false), 180);
  }

  return (
    <nav
      className={`nav-rail ${expanded ? 'nav-rail--expanded' : ''}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Brand mark (icon-only when collapsed) */}
      <div className="nr-brand">
        <div className="nr-brand-icon">
          <Ship size={18} />
        </div>
        <span className="nr-brand-name">MarineRadar</span>
      </div>

      <div className="nr-divider" />

      {/* Primary nav */}
      <ul className="nr-list nr-list--primary">
        {PRIMARY_NAV.map(({ id, icon: Icon, label, live }) => (
          <li key={id}>
            <button
              className={`nr-item ${active === id ? 'nr-item--active' : ''}`}
              onClick={() => onChange(id)}
              title={!expanded ? label : undefined}
            >
              <span className="nr-item-icon"><Icon size={18} /></span>
              <span className="nr-item-label">{label}</span>
              {!live && expanded && (
                <span className="nr-item-badge">Soon</span>
              )}
            </button>
          </li>
        ))}
      </ul>

      <div className="nr-spacer" />
      <div className="nr-divider" />

      {/* Secondary nav */}
      <ul className="nr-list nr-list--secondary">
        {SECONDARY_NAV.map(({ id, icon: Icon, label }) => (
          <li key={id}>
            <button
              className={`nr-item nr-item--secondary ${active === id ? 'nr-item--active' : ''}`}
              onClick={() => onChange(id)}
              title={!expanded ? label : undefined}
            >
              <span className="nr-item-icon"><Icon size={16} /></span>
              <span className="nr-item-label">{label}</span>
            </button>
          </li>
        ))}
      </ul>

      <div className="nr-divider" />

      {/* Profile */}
      <button className="nr-profile" title={!expanded ? 'Profile' : undefined}>
        <div className="nr-avatar"><User size={15} /></div>
        <span className="nr-profile-label">Account</span>
        {expanded && <ChevronRight size={13} className="nr-profile-chevron" />}
      </button>
    </nav>
  );
}
