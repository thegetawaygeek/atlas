import { useState, useRef, useEffect } from 'react'
import './App.css'
import sites from './data/sites'
import Map from './components/Map'

/* Format [lng, lat] coordinates as "27.3242° N, 68.1385° E" */
function formatCoords([lng, lat]) {
  const latDir = lat >= 0 ? 'N' : 'S'
  const lngDir = lng >= 0 ? 'E' : 'W'
  return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lng).toFixed(4)}° ${lngDir}`
}

/* Content panel takes up this fraction of the map width in site view.
   Used both for panel sizing and for the map's flyTo padding so the
   active site stays framed in the visible right portion. */
const PANEL_WIDTH = 0.55

function App() {
  const [view, setView] = useState('landing')
  const [activeSite, setActiveSite] = useState(null)
  /* displayedSite stays populated during the panel's slide-out animation
     so the panel can render while activeSite has already been cleared
     (which lets the persistent map start flying back to world view). */
  const [displayedSite, setDisplayedSite] = useState(null)
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [panelVisible, setPanelVisible] = useState(false)

  const handleEnterAtlas = () => {
    setView('map')
  }

  const handleSelectSite = (site) => {
    setActiveSite(site)
    setDisplayedSite(site)
    setView('site')
    setSearchOpen(false)
    setSearchQuery('')
    // Delay panel slide-in briefly so the map's flyTo begins first
    setTimeout(() => {
      setPanelVisible(true)
    }, 250)
  }

  const handleCloseSite = () => {
    // Trigger panel slide-out AND map fly-back simultaneously —
    // they animate in parallel for a seamless return to the globe.
    setPanelVisible(false)
    setActiveSite(null)
    setView('map')
    // Remove the panel from the DOM after its transition completes
    setTimeout(() => {
      setDisplayedSite(null)
    }, 550)
  }

  const handleGoHome = () => {
    if (view === 'site') {
      handleCloseSite()
    } else {
      setActiveSite(null)
      setSearchOpen(false)
      setSearchQuery('')
      setView('map')
    }
  }

  const filteredSites = searchQuery.trim()
    ? sites.filter(s =>
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : []

  return (
    <div className="h-full flex flex-col" style={{ backgroundColor: 'var(--color-cream)' }}>
      {/* Top Nav — hidden on landing */}
      {view !== 'landing' && (
        <TopNav
          activeSite={view === 'site' ? activeSite : null}
          searchOpen={searchOpen}
          searchQuery={searchQuery}
          filteredSites={filteredSites}
          onGoHome={handleGoHome}
          onSearchOpen={() => setSearchOpen(true)}
          onSearchClose={() => { setSearchOpen(false); setSearchQuery('') }}
          onSearchChange={setSearchQuery}
          onSelectSite={handleSelectSite}
        />
      )}

      {/* View rendering */}
      {view === 'landing' && (
        <LandingPage onEnter={handleEnterAtlas} />
      )}

      {/* Persistent map stage — one Map instance across map ↔ site so
         transitions are camera moves on the same canvas, never unmounts. */}
      {view !== 'landing' && (
        <div className="flex-1 relative min-h-0">
          <Map
            sites={sites}
            activeSite={view === 'site' ? activeSite : null}
            onSelectSite={handleSelectSite}
            leftInset={view === 'site' ? PANEL_WIDTH : 0}
          />

          {/* Site content panel — slides over the left side of the map */}
          {displayedSite && (
            <SitePanel
              site={displayedSite}
              visible={panelVisible}
              onClose={handleCloseSite}
            />
          )}
        </div>
      )}
    </div>
  )
}

/* ── Top Navigation Bar ── */
/* #6 — brand bolder, search darker + right-aligned, site name centered in site view */
function TopNav({ activeSite, searchOpen, searchQuery, filteredSites, onGoHome, onSearchOpen, onSearchClose, onSearchChange, onSelectSite }) {
  return (
    <nav className="flex items-center justify-between px-6 py-3 bg-white-card border-b border-gray-200 shrink-0 z-20 relative">
      {/* Left: Brand */}
      <button
        onClick={onGoHome}
        className="text-xs font-semibold uppercase tracking-[3px] text-text-dark cursor-pointer bg-transparent border-none shrink-0"
      >
        The Getaway Geek Atlas
      </button>

      {/* Center: site name when in site view */}
      <div className="flex-1 flex justify-center">
        {activeSite && (
          <span className="text-sm font-medium text-text-dark">
            {activeSite.name}
          </span>
        )}
      </div>

      {/* Right: Search */}
      <div className="relative shrink-0">
        {searchOpen ? (
          <SearchInput
            query={searchQuery}
            onChange={onSearchChange}
            results={filteredSites}
            onSelect={onSelectSite}
            onClose={onSearchClose}
          />
        ) : (
          <button
            onClick={onSearchOpen}
            className="flex items-center gap-2 text-text-body text-sm cursor-pointer bg-transparent border-none hover:text-text-dark transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Search
          </button>
        )}
      </div>
    </nav>
  )
}

/* ── Search Input ── */
function SearchInput({ query, onChange, results, onSelect, onClose }) {
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    const handleEsc = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  return (
    <div className="relative">
      <div className="flex items-center gap-2 bg-cream rounded-lg px-3 py-1.5 border border-gray-200">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-text-body shrink-0">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Search sites..."
          className="bg-transparent border-none outline-none text-sm text-text-dark w-48 placeholder:text-text-muted"
        />
        <button
          onClick={onClose}
          className="text-text-muted text-xs cursor-pointer bg-transparent border-none hover:text-text-dark"
        >
          &times;
        </button>
      </div>

      {results.length > 0 && (
        <div className="absolute top-full right-0 w-72 mt-1 bg-white-card rounded-lg shadow-lg border border-gray-200 overflow-hidden z-30">
          {results.map((site) => (
            <button
              key={site.id}
              onClick={() => onSelect(site)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left cursor-pointer bg-transparent border-none hover:bg-cream transition-colors"
            >
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: 'var(--color-gold)' }} />
              <div>
                <p className="text-sm font-medium text-text-dark">{site.name}</p>
                <p className="text-xs text-text-muted">{site.location}</p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Landing Page ── */
/* #5 — much larger fonts, removed "Start here." */
function LandingPage({ onEnter }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center relative overflow-hidden">
      <img
        src="/images/landing/hero.png"
        alt=""
        className="absolute inset-0 w-full h-full object-cover"
      />
      <div className="absolute inset-0 bg-black/40" />
      <div className="relative z-10 text-center px-6" style={{ textShadow: '0 3px 14px rgba(0,0,0,0.6)' }}>
        <p className="text-lg md:text-xl font-medium uppercase tracking-[6px] text-white/80 mb-6">
          The Getaway Geek
        </p>
        <h1 className="text-7xl md:text-9xl font-semibold text-white mb-8 max-w-3xl leading-none tracking-[4px]">
          ATLAS
        </h1>
        <p className="text-xl md:text-2xl text-white/90 mb-12 max-w-xl mx-auto font-light italic">
          The world is full of places that don't make sense.
        </p>
        <button
          onClick={onEnter}
          className="px-10 py-4 bg-white text-text-dark text-sm font-medium uppercase tracking-[1.5px] rounded cursor-pointer border-none hover:shadow-lg transition-shadow"
          style={{ textShadow: '0 1px 4px rgba(0,0,0,0.15)' }}
        >
          Explore the Atlas
        </button>
      </div>
    </div>
  )
}

/* ── Site Content Panel (Content State overlay) ──
   Absolutely positioned over the left 55% of the persistent map.
   Slides in/out via transform + opacity; the map camera moves
   independently underneath for a seamless transition. */
function SitePanel({ site, visible, onClose }) {
  const [expandedSections, setExpandedSections] = useState({ mystery: false, perspective: false, record: true })
  const [lightboxImage, setLightboxImage] = useState(null)
  const [copied, setCopied] = useState(false)

  const handleShare = () => {
    const url = `${window.location.origin}/#/site/${site.id}`
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  /* #9 — access badge style, three distinct levels */
  const accessStyles = {
    'Accessible': { color: 'var(--color-accessible)', backgroundColor: 'var(--color-accessible-bg)' },
    'Moderate Adventure': { color: 'var(--color-moderate)', backgroundColor: 'var(--color-moderate-bg)' },
    'Expedition-Level': { color: 'var(--color-expedition)', backgroundColor: 'var(--color-expedition-bg)' },
  }
  const accessStyle = accessStyles[site.access] || accessStyles['Accessible']

  return (
    <>
      {/* Content panel — absolute overlay on the left of the map */}
      <div
        className="absolute top-0 left-0 bottom-0 overflow-y-auto bg-white-card shadow-xl z-10 transition-all duration-500 ease-out"
        style={{
          width: `${PANEL_WIDTH * 100}%`,
          transform: visible ? 'translateX(0)' : 'translateX(-100%)',
          opacity: visible ? 1 : 0,
        }}
      >
        {/* Zero-height sticky container — sits at top: 16px as the panel scrolls,
            takes up no layout space so the hero image appears directly behind it.
            The button is absolutely positioned out of flow within this anchor. */}
        <div style={{ position: 'sticky', top: '16px', height: 0, zIndex: 20 }}>
          <button
            onClick={onClose}
            className="flex items-center justify-center cursor-pointer border-none text-text-dark text-lg hover:bg-white transition-colors"
            style={{
              position: 'absolute',
              top: 0,
              left: '16px',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              backgroundColor: 'rgba(255,255,255,0.92)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.22)',
            }}
          >
            &larr;
          </button>
        </div>

        {/* Hero image */}
        <div className="w-full h-72 relative overflow-hidden">
          <img
            src={site.heroImage}
            alt={site.name}
            className="absolute inset-0 w-full h-full object-cover"
          />
        </div>

        <div className="p-8">
          {/* Thematic tags */}
          <div className="flex flex-wrap gap-2 mb-3">
            {site.tags.map((tag) => (
              <span
                key={tag}
                className="text-[10px] uppercase tracking-[1.2px] px-3 py-1 rounded-full"
                style={{ color: 'var(--color-gold-text)', backgroundColor: 'var(--color-gold-light)' }}
              >
                {tag}
              </span>
            ))}
          </div>

          {/* Site name + share */}
          <div className="flex items-center gap-3 mb-1">
            <h2 className="text-2xl font-semibold text-text-dark">{site.name}</h2>
            <button
              onClick={handleShare}
              className="text-text-muted hover:text-text-dark cursor-pointer bg-transparent border-none transition-colors relative"
              title="Copy link"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                <polyline points="16 6 12 2 8 6" />
                <line x1="12" y1="2" x2="12" y2="15" />
              </svg>
              {copied && (
                <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] text-text-muted bg-cream px-2 py-0.5 rounded shadow-sm">
                  Link copied
                </span>
              )}
            </button>
          </div>

          {/* Location + Access badge (#9 — moved up, larger) */}
          <div className="flex items-center gap-3 mb-1">
            <p className="text-xs text-text-muted">{site.location}</p>
            <span
              className="inline-block text-[11px] font-semibold uppercase tracking-[1px] px-3 py-1 rounded-full"
              style={accessStyle}
            >
              {site.access}
            </span>
          </div>

          {/* Coordinates */}
          <p className="text-xs text-text-muted mb-5">{formatCoords(site.coordinates)}</p>

          {/* The Hook — its own moment, a pause in the card */}
          <div className="pt-9 pb-11 my-3 border-t border-b border-gray-200">
            <p className="text-[15px] italic text-text-hook" style={{ lineHeight: '1.9', fontWeight: 350 }}>
              {site.hook}
            </p>
          </div>

          {/* Photo gallery */}
          <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
            {site.galleryImages.map((src, i) => (
              <img
                key={i}
                src={src}
                alt={`${site.name} photo ${i + 1}`}
                onClick={() => setLightboxImage({ src, index: i })}
                className="w-32 h-22 rounded-lg shrink-0 object-cover cursor-pointer hover:opacity-80 transition-opacity"
              />
            ))}
          </div>

          {/* The Record */}
          {site.record && (
            <ExpandableSection
              title="The Record"
              expanded={expandedSections.record}
              onToggle={() => toggleSection('record')}
            >
              <ParagraphText text={site.record} />
            </ExpandableSection>
          )}

          {/* #8 — Mystery shows teaser by default */}
          <MysterySection
            text={site.mystery}
            expanded={expandedSections.mystery}
            onToggle={() => toggleSection('mystery')}
          />

          <ExpandableSection
            title="The Getaway Geek Perspective"
            expanded={expandedSections.perspective}
            onToggle={() => toggleSection('perspective')}
            goldBorder
          >
            <ParagraphText text={site.perspective} />
          </ExpandableSection>

          <ExpandableSection
            title="Travel Reality"
            expanded={expandedSections.travelReality}
            onToggle={() => toggleSection('travelReality')}
            maxHeight="3200px"
          >
            <TravelRealityContent text={site.travelReality} />
          </ExpandableSection>

          {/* Photo Credits — understated, bottom of card */}
          {site.photoCredits && (
            <div className="mt-6 pt-4 border-t border-gray-100">
              <p className="text-[11px] uppercase tracking-[1px] text-text-muted mb-2">Photo Credits</p>
              <p className="text-[11px] text-text-muted leading-relaxed">
                {site.photoCredits}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Lightbox overlay */}
      {lightboxImage && (
        <Lightbox
          src={lightboxImage.src}
          index={lightboxImage.index}
          onClose={() => setLightboxImage(null)}
        />
      )}
    </>
  )
}

/* ── Paragraph Text — splits \n-delimited content into spaced paragraphs ── */
function ParagraphText({ text }) {
  if (!text) return null
  return (
    <div className="space-y-3">
      {text.split('\n').filter(Boolean).map((para, i) => (
        <p key={i} className="text-sm text-text-body leading-relaxed">{para}</p>
      ))}
    </div>
  )
}

/* ── Mystery Section ── */
function MysterySection({ text, expanded, onToggle }) {
  return (
    <div className="mb-4">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-3 border-t border-gray-200 bg-transparent cursor-pointer text-left"
      >
        <span className="text-[13px] font-medium uppercase tracking-[1.2px] text-text-muted">
          The Mystery
        </span>
        <span className="text-[18px] font-medium" style={{ color: '#555555' }}>{expanded ? '−' : '+'}</span>
      </button>
      <div
        style={{
          maxHeight: expanded ? '1200px' : '0px',
          opacity: expanded ? 1 : 0,
          overflow: 'hidden',
          transition: 'max-height 0.3s ease, opacity 0.3s ease',
        }}
      >
        <div className="pb-4">
          <ParagraphText text={text} />
        </div>
      </div>
    </div>
  )
}

/* ── Expandable Section ── */
function ExpandableSection({ title, expanded, onToggle, goldBorder, maxHeight = '800px', children }) {
  return (
    <div className="mb-4">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-3 border-t border-gray-200 bg-transparent cursor-pointer text-left"
      >
        <span className="text-[13px] font-medium uppercase tracking-[1.2px] text-text-muted">
          {title}
        </span>
        <span className="text-[18px] font-medium" style={{ color: '#555555' }}>{expanded ? '−' : '+'}</span>
      </button>
      <div
        className="overflow-hidden transition-all duration-300 ease-in-out"
        style={{
          maxHeight: expanded ? maxHeight : '0px',
          opacity: expanded ? 1 : 0,
        }}
      >
        <div
          className={`pb-4 ${goldBorder ? 'border-l-2 pl-4' : ''}`}
          style={goldBorder ? { borderColor: 'var(--color-gold)' } : undefined}
        >
          {children}
        </div>
      </div>
    </div>
  )
}

/* ── Travel Reality Content ── */
/* Renders the structured 6-section travelReality field.
   Sections are stored as "HEADER\ncontent\n\nHEADER\ncontent" */
function TravelRealityContent({ text }) {
  if (!text) return null
  const blocks = text.split('\n\n').filter(Boolean)
  return (
    <div className="space-y-5">
      {blocks.map((block, i) => {
        const newlineIdx = block.indexOf('\n')
        if (newlineIdx === -1) return null
        const header = block.slice(0, newlineIdx).trim()
        const content = block.slice(newlineIdx + 1).trim()
        return (
          <div key={i}>
            <p className="text-[10px] font-semibold uppercase tracking-[1.4px] text-text-muted mb-1.5">
              {header}
            </p>
            <p className="text-sm text-text-body leading-relaxed">{content}</p>
          </div>
        )
      })}
    </div>
  )
}

/* ── Lightbox ── */
function Lightbox({ src, index, onClose }) {
  useEffect(() => {
    const handleEsc = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 cursor-pointer"
      onClick={onClose}
    >
      <img
        src={src}
        alt={`Photo ${index + 1}`}
        className="max-w-[85vw] max-h-[85vh] rounded-lg object-contain"
        onClick={(e) => e.stopPropagation()}
      />
      <button
        onClick={onClose}
        className="absolute top-6 right-6 text-white text-3xl cursor-pointer bg-transparent border-none hover:opacity-70 transition-opacity"
      >
        &times;
      </button>
    </div>
  )
}

export default App
