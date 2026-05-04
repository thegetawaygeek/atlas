import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'

mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN

const WORLD_VIEW = { center: [20, 20], zoom: 2.2, pitch: 0, bearing: 0 }
const SITE_ZOOM = 9.5

// Classic map-pin red
const PIN_COLOR = '#E63946'
const PIN_COLOR_HOVER = '#F04858'

// Load a classic Google-Maps-style pin (round head + pointed bottom) as an HTMLImageElement
function loadPinImage(color, size) {
  return new Promise((resolve) => {
    // Device pixel ratio for crisp rendering at small sizes
    const dpr = Math.max(1, window.devicePixelRatio || 1)
    const pad = 4 // room for shadow + stroke
    const headR = size * 0.5
    const w = Math.round(size + pad * 2)
    const h = Math.round(size * 1.4 + pad * 2)

    const canvas = document.createElement('canvas')
    canvas.width = w * dpr
    canvas.height = h * dpr
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)

    const cx = w / 2
    const cy = pad + headR // center of head circle
    const tipY = h - pad   // bottom point

    // Pin silhouette: round head with tangent sides tapering to a point
    // Tangent points from external point (cx, tipY) to circle of radius headR at (cx, cy)
    const d = tipY - cy
    const sinA = headR / d
    const cosA = Math.sqrt(1 - sinA * sinA)
    // Tangent point on right side of circle
    const tx = cx + headR * cosA
    const ty = cy + headR * sinA
    // Left tangent is mirror
    const startAngle = Math.atan2(ty - cy, tx - cx) // right tangent angle
    const endAngle = Math.PI - startAngle           // left tangent angle

    ctx.beginPath()
    // Start at right tangent, sweep counter-clockwise over the top back to left tangent
    ctx.arc(cx, cy, headR, startAngle, endAngle, true)
    // Left tangent down to tip
    ctx.lineTo(cx, tipY)
    ctx.closePath()

    // Soft drop shadow beneath the pin
    ctx.shadowColor = 'rgba(0,0,0,0.35)'
    ctx.shadowBlur = 4
    ctx.shadowOffsetY = 1.5
    ctx.fillStyle = color
    ctx.fill()

    // White outline for contrast on any background
    ctx.shadowColor = 'transparent'
    ctx.strokeStyle = '#FFFFFF'
    ctx.lineWidth = 1.5
    ctx.stroke()

    // Inner white dot (classic pin hole)
    ctx.beginPath()
    ctx.arc(cx, cy, headR * 0.32, 0, Math.PI * 2)
    ctx.fillStyle = '#FFFFFF'
    ctx.fill()

    const img = new Image()
    img.onload = () => resolve(img)
    img.src = canvas.toDataURL()
  })
}

const REGIONAL_ZOOM = 4.5   // pull-back zoom after leaving a site

// ─── Tooltip configuration ─────────────────────────────────────────────────
//
// TOOLTIP_VERSION controls which visual variant shows on the 3 test sites.
//   'A' — light card: white/near-white background, subtle shadow
//   'B' — dark card:  near-black translucent background, minimal shadow
//
// Change this value to switch between versions, then reload.
const TOOLTIP_VERSION = 'B'

// Tooltip lines for all 30 sites, sourced verbatim from "Tooltips - First 30 Sites".
const TOOLTIP_LINES = {
  'poverty-point':  'No farmers. No explanation.',
  'teotihuacan':    'A city with no name.',
  'palenque':       'A sealed tomb with a voice.',
  'chichen-itza':   'The pyramid answers back.',
  'chavin':         'The walls are making the sound.',
  'nazca':          "Made for eyes that didn't exist.",
  'machupicchu':    'The stones move and return.',
  'saqsaywaman':    'None of them repeat.',
  'tiwanaku':       "These aren't stones. They're parts.",
  'skara-brae':     'The furniture is still there.',
  'rosslyn-chapel': "You'll recognize them.",
  'newgrange':      'Once a year, the light finds its way in.',
  'stonehenge':     'They wanted those stones.',
  'goseck':         'The sun still lines up.',
  'ggantija':       'Then it stopped.',
  'hal-saflieni':   'The chamber behaves differently.',
  'great-zimbabwe': 'A tower with no entrance.',
  'derinkuyu':      'Eighteen levels down. No way in from above.',
  'gobekli-tepe':   'They built it. Then they buried it.',
  'karahan-tepe':   'One site is an anomaly. This is not.',
  'petra':          "The water shouldn't be here.",
  'giza':           'Level to within two centimeters.',
  'dendera':        'Painted in the dark. No soot.',
  'karnak':         'Two thousand years. One direction.',
  'mohenjo-daro':   'The drains still run.',
  'ellora':         'They started at the top.',
  'hampi':          'Fifty-six pillars. Fifty-six tones.',
  'borobudur':      'You can see them. You cannot reach them.',
  'angkor-wat':     'Not invaded. Not destroyed. Just thirsty.',
  'longyou':        'No one wrote it down.',
}

const TOOLTIP_STYLES = {
  A: {
    background:  'rgba(255, 255, 255, 0.97)',
    boxShadow:   '0 2px 10px rgba(0,0,0,0.09)',
    nameColor:   'rgba(26, 26, 26, 0.87)',
    lineColor:   'rgba(26, 26, 26, 1.0)',
  },
  B: {
    background:  'rgba(14, 14, 18, 0.72)',
    boxShadow:   '0 2px 8px rgba(0,0,0,0.14)',
    nameColor:   'rgba(255, 255, 255, 0.50)',
    lineColor:   'rgba(255, 255, 255, 1.0)',
  },
}
// ──────────────────────────────────────────────────────────────────────────

export default function Map({ sites, activeSite, onSelectSite, leftInset = 0, interactive = true }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const onSelectRef = useRef(onSelectSite)
  const sitesRef = useRef(sites)
  const leftInsetRef = useRef(leftInset)
  const prevSiteRef = useRef(null)  // remembers the last-viewed site for the pull-back

  useEffect(() => { onSelectRef.current = onSelectSite }, [onSelectSite])
  useEffect(() => { sitesRef.current = sites }, [sites])
  useEffect(() => { leftInsetRef.current = leftInset }, [leftInset])

  useEffect(() => {
    if (mapRef.current) return

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      ...WORLD_VIEW,
      projection: 'globe',
      interactive,
      scrollZoom: true,
    })

    map.on('style.load', () => {
      map.setFog({
        color: 'rgb(186, 210, 235)',
        'high-color': 'rgb(36, 92, 223)',
        'horizon-blend': 0.02,
        'space-color': 'rgb(11, 11, 25)',
        'star-intensity': 0.6,
      })

      // Hide roads and navigation layers
      const style = map.getStyle()
      if (style && style.layers) {
        for (const layer of style.layers) {
          const id = layer.id.toLowerCase()
          if (
            id.includes('road') || id.includes('highway') ||
            id.includes('motorway') || id.includes('trunk') ||
            id.includes('street') || id.includes('bridge') ||
            id.includes('tunnel') || id.includes('path') ||
            id.includes('pedestrian') || id.includes('track') ||
            id.includes('rail') || id.includes('ferry') ||
            id.includes('aerialway') || id.includes('shield') ||
            id.includes('route') || id.includes('transit')
          ) {
            map.setLayoutProperty(layer.id, 'visibility', 'none')
          }
        }
      }

      map.addSource('mapbox-dem', {
        type: 'raster-dem',
        url: 'mapbox://mapbox.mapbox-terrain-dem-v1',
        tileSize: 512,
        maxzoom: 14,
      })
      map.setTerrain({ source: 'mapbox-dem', exaggeration: 1.5 })

      // Create pin images (normal + hover) then add layers
      const pinSize = 8
      const pinHoverSize = 10
      Promise.all([
        loadPinImage(PIN_COLOR, pinSize),
        loadPinImage(PIN_COLOR_HOVER, pinHoverSize),
      ]).then(([pinNormal, pinHover]) => {
        if (!map.hasImage('pin-normal')) map.addImage('pin-normal', pinNormal)
        if (!map.hasImage('pin-hover')) map.addImage('pin-hover', pinHover)
        addPinLayers(map)
      })
    })

    function addPinLayers(map) {
      // GeoJSON source — include first hook sentence for legacy tooltip fallback
      const geojson = {
        type: 'FeatureCollection',
        features: (sitesRef.current || []).map(site => {
          const firstSentence = site.hook?.match(/[^.!?]+[.!?]+/)?.[0]?.trim() || site.hook || ''
          return {
            type: 'Feature',
            geometry: { type: 'Point', coordinates: site.coordinates },
            properties: { id: site.id, name: site.name, hookSentence: firstSentence },
          }
        }),
      }

      map.addSource('atlas-sites', { type: 'geojson', data: geojson })

      // Pin layer — icon-offset compensates for the 4px bottom padding
      // baked into the pin image so the tip sits on the exact coordinate
      map.addLayer({
        id: 'site-pins',
        type: 'symbol',
        source: 'atlas-sites',
        layout: {
          'icon-image': 'pin-normal',
          'icon-anchor': 'bottom',
          'icon-offset': [0, 4],
          'icon-allow-overlap': true,
          'icon-ignore-placement': true,
        },
      })

      // ── Tooltip element ─────────────────────────────────────────────────
      // pointer-events:none so it never blocks map interaction.
      // Starts fully transparent/translated; shown by transitioning
      // opacity and transform rather than display toggling.
      const vs = TOOLTIP_STYLES[TOOLTIP_VERSION]

      const tooltip = document.createElement('div')
      tooltip.setAttribute('aria-hidden', 'true')
      Object.assign(tooltip.style, {
        position:      'absolute',
        pointerEvents: 'none',
        borderRadius:  '5px',
        padding:       '5px 9px',
        zIndex:        '10',
        opacity:       '0',
        transform:     'translateY(4px)',
        transition:    'opacity 175ms ease, transform 175ms ease',
      })
      containerRef.current.appendChild(tooltip)

      // ── HTML builders ───────────────────────────────────────────────────
      // New design: used for the 3 test sites (Giza, Göbekli Tepe, Petra)
      function buildNewTooltip(name, line) {
        return (
          `<div style="font-weight:400;font-size:9px;line-height:1.2;` +
          `margin-bottom:3px;color:${vs.nameColor};letter-spacing:0.05em">${name}</div>` +
          `<div style="font-weight:400;font-size:13px;line-height:1.4;` +
          `color:${vs.lineColor};letter-spacing:0.02em">${line}</div>`
        )
      }

      // Legacy design: unchanged for all other 27 sites
      function buildLegacyTooltip(name, hookSentence) {
        return (
          `<div style="font-weight:600;font-size:12px;margin-bottom:4px;color:#1A1A1A">${name}</div>` +
          `<div style="font-size:11px;color:#4A4A4A;font-style:italic">${hookSentence}</div>`
        )
      }

      // ── Positioning ─────────────────────────────────────────────────────
      // Sits above and to the right of the cursor — offset slightly so it
      // doesn't feel mechanically anchored to the pin.
      function positionTooltip(x, y) {
        const h = tooltip.offsetHeight || 48
        tooltip.style.left = (x + 20) + 'px'
        tooltip.style.top  = (y - h - 22) + 'px'
      }

      function fadeIn() {
        tooltip.style.transition = 'opacity 175ms ease, transform 175ms ease'
        tooltip.style.opacity    = '1'
        tooltip.style.transform  = 'translateY(0)'
      }

      function fadeOut() {
        tooltip.style.transition = 'opacity 100ms ease, transform 100ms ease'
        tooltip.style.opacity    = '0'
        tooltip.style.transform  = 'translateY(4px)'
      }

      // ── Hover state ─────────────────────────────────────────────────────
      let hoveredId       = null
      let hoverTimer      = null
      let pendingFeature  = null
      let lastX           = 0
      let lastY           = 0

      map.on('mouseenter', 'site-pins', (e) => {
        map.getCanvas().style.cursor = 'pointer'
        const feature = e.features?.[0]
        if (!feature) return

        hoveredId = feature.properties.id
        map.setLayoutProperty('site-pins', 'icon-image', [
          'case', ['==', ['get', 'id'], hoveredId], 'pin-hover', 'pin-normal',
        ])

        const tooltipLine = TOOLTIP_LINES[hoveredId]

        if (tooltipLine) {
          // ── New animated tooltip (test sites only) ──
          pendingFeature = feature
          clearTimeout(hoverTimer)
          hoverTimer = setTimeout(() => {
            if (!pendingFeature) return
            Object.assign(tooltip.style, {
              background: vs.background,
              boxShadow:  vs.boxShadow,
            })
            tooltip.innerHTML = buildNewTooltip(pendingFeature.properties.name, tooltipLine)
            positionTooltip(lastX, lastY)
            fadeIn()
          }, 200)
        } else {
          // ── Legacy tooltip (all other sites, unchanged behavior) ──
          const { name, hookSentence } = feature.properties
          Object.assign(tooltip.style, {
            background: '#FFFFFF',
            boxShadow:  '0 2px 10px rgba(0,0,0,0.13)',
          })
          tooltip.innerHTML = buildLegacyTooltip(name, hookSentence)
          positionTooltip(e.point.x, e.point.y)
          tooltip.style.transition = 'none'
          tooltip.style.opacity    = '1'
          tooltip.style.transform  = 'translateY(0)'
        }
      })

      map.on('mousemove', 'site-pins', (e) => {
        lastX = e.point.x
        lastY = e.point.y
        // Track position continuously; only reposition if tooltip is visible
        if (parseFloat(tooltip.style.opacity) > 0) {
          positionTooltip(lastX, lastY)
        }
      })

      map.on('mouseleave', 'site-pins', () => {
        clearTimeout(hoverTimer)
        pendingFeature = null
        map.getCanvas().style.cursor = ''
        hoveredId = null
        map.setLayoutProperty('site-pins', 'icon-image', 'pin-normal')
        fadeOut()
      })

      map.on('click', 'site-pins', (e) => {
        clearTimeout(hoverTimer)
        const feature = e.features?.[0]
        if (!feature || !onSelectRef.current) return
        const site = sitesRef.current?.find(s => s.id === feature.properties.id)
        if (site) {
          fadeOut()
          onSelectRef.current(site)
        }
      })
    }

    map.addControl(new mapboxgl.NavigationControl(), 'bottom-right')

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [interactive])

  // Fly to active site or back to world. The leftInset fraction shifts the
  // visual center right via mapbox padding so the site stays framed in the
  // visible portion of the map while the content panel overlays the left.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    const container = containerRef.current
    const insetPx = container ? container.clientWidth * leftInset : 0
    const padding = { left: insetPx, top: 0, right: 0, bottom: 0 }

    if (activeSite) {
      prevSiteRef.current = activeSite
      map.flyTo({
        center: activeSite.coordinates,
        zoom: SITE_ZOOM,
        pitch: 40,
        bearing: -15,
        duration: 2800,
        padding,
        essential: true,
      })
    } else if (prevSiteRef.current) {
      // Pull back to a regional view centered on the site the user just left —
      // far enough to show surrounding pins and geography, close enough to
      // feel like lifting off rather than teleporting.
      map.flyTo({
        center: prevSiteRef.current.coordinates,
        zoom: REGIONAL_ZOOM,
        pitch: 15,
        bearing: 0,
        duration: 2200,
        padding,
        essential: true,
      })
    } else {
      // First load — no site ever viewed — return to default globe
      map.flyTo({
        ...WORLD_VIEW,
        padding,
        duration: 2200,
        essential: true,
      })
    }
  }, [activeSite, leftInset])

  return (
    <div ref={containerRef} className="w-full h-full" />
  )
}
