/**
 * Sthāna Diagram - Interactive Human Vocal Tract Cross-Section SVG
 * Visualizes the 5 Classical Places of Articulation (Pāṇinīya Śikṣā):
 * 1. Kaṇṭha (Throat / Velum)
 * 2. Tālu (Hard Palate)
 * 3. Mūrdhā (Roof / Dome of Palate)
 * 4. Danta (Upper Teeth)
 * 5. Oṣṭha (Lips)
 * plus Nāsikā (Nasal Cavity)
 */

const SthanaDiagram = (function() {
  let svgRoot = null;
  let activeHighlight = null;

  // Coordinates for the 5 Sthānas on a 500x380 SVG canvas
  const STHANA_COORDS = {
    kanthya: { x: 195, y: 265, name: "कण्ठ्य (Kaṇṭhya - Throat/Velum)", sutra: "अकुहविसर्जनीयानां कण्ठः" },
    talavya: { x: 260, y: 160, name: "तालव्य (Tālavya - Hard Palate)", sutra: "इचुयशानां तालु" },
    murdhanya: { x: 315, y: 148, name: "मूर्धन्य (Mūrdhanya - Palate Dome)", sutra: "ऋटुरषाणां मूर्धा" },
    dantya: { x: 375, y: 190, name: "दन्त्य (Dantya - Upper Teeth)", sutra: "ऌतुलसानां दन्ताः" },
    oshthya: { x: 420, y: 215, name: "ओष्ठ्य (Oṣṭhya - Lips)", sutra: "उपूपध्मानीयानामोष्ठौ" },
    nasikya: { x: 310, y: 95, name: "नासिक्य (Nāsikya - Nasal Cavity)", sutra: "ञमङणननां नासिका च" },
    dantoshthya: { x: 405, y: 225, name: "दन्तोष्ठ्य (Dantoṣṭhya - Teeth & Lips)", sutra: "वकारस्य दन्तोष्ठम्" }
  };

  // Tongue curve paths for each articulation posture
  const TONGUE_PATHS = {
    // Neutral tongue resting
    neutral: "M 180 290 Q 220 280 260 250 Q 300 230 330 225 Q 360 230 380 250 L 320 320 Q 240 330 180 290 Z",
    // Dantya: tip pressing against back of upper front teeth
    dantya: "M 180 290 Q 220 280 260 240 Q 310 210 368 194 Q 374 198 370 215 L 320 320 Q 240 330 180 290 Z",
    // Murdhanya: tip curled backward touching the high dome
    murdhanya: "M 180 290 Q 220 280 250 230 Q 280 180 310 155 Q 318 160 305 185 L 320 320 Q 240 330 180 290 Z",
    // Talavya: blade of tongue flattened against hard palate
    talavya: "M 180 290 Q 210 260 255 172 Q 280 170 320 195 Q 350 220 360 240 L 320 320 Q 240 330 180 290 Z",
    // Kanthya: base of tongue raised towards soft palate
    kanthya: "M 180 290 Q 200 230 215 210 Q 230 230 270 245 Q 320 240 350 250 L 320 320 Q 240 330 180 290 Z",
    // Oshthya: neutral tongue with closed/rounded lips
    oshthya: "M 180 290 Q 220 280 260 255 Q 310 245 350 240 Q 375 240 385 245 L 320 320 Q 240 330 180 290 Z"
  };

  function createSVG() {
    return `
      <svg id="vocal-tract-svg" viewBox="0 0 500 380" class="sthana-svg" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <!-- Gradients -->
          <linearGradient id="palateGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#EEDAC5" />
            <stop offset="100%" stop-color="#D7BBA0" />
          </linearGradient>
          <linearGradient id="tongueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#E57373" />
            <stop offset="100%" stop-color="#C62828" />
          </linearGradient>
          <filter id="glowGold" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <!-- Background grid hint -->
        <rect width="100%" height="100%" fill="transparent" />

        <!-- Outer Facial Profile & Throat Silhouette -->
        <path d="M 280 40 
                 Q 330 50 370 85 
                 Q 400 115 410 145 
                 Q 425 170 415 185 
                 Q 440 200 445 215
                 Q 440 225 425 228
                 Q 445 240 435 260
                 Q 415 285 390 295
                 Q 370 330 350 360
                 L 150 360
                 L 150 300
                 Q 160 240 180 200
                 Q 210 130 250 70
                 Z" 
              fill="#F8FAFC" stroke="#CBD5E1" stroke-width="2" />

        <!-- Nasal Cavity (Nāsikā) -->
        <path id="zone-nasikya" d="M 320 80 Q 370 85 385 130 Q 350 145 300 140 Q 280 110 320 80 Z" 
              fill="#F1F5F9" stroke="#CBD5E1" stroke-width="1.5" />
        <text x="325" y="115" font-family="'Eczar', serif" font-size="12" font-weight="700" fill="#64748B" text-anchor="middle">नासिक्य</text>

        <!-- Hard & Soft Palate Contour (Roof of Oral Cavity) -->
        <path d="M 175 285 
                 Q 185 240 210 200
                 Q 250 140 315 142
                 Q 360 145 380 180
                 L 380 200" 
              fill="none" stroke="#475569" stroke-width="3" stroke-linecap="round" />

        <!-- Upper Teeth (Danta) -->
        <path id="zone-dantya-teeth" d="M 374 180 L 378 198 L 386 198 L 383 180 Z" 
              fill="#FFFFFF" stroke="#0F172A" stroke-width="1.8" />

        <!-- Upper & Lower Lips (Oṣṭha) -->
        <path id="upper-lip" d="M 405 200 Q 435 208 425 218 L 398 215 Z" fill="#F87171" stroke="#DC2626" stroke-width="1.5" />
        <path id="lower-lip" d="M 400 230 Q 430 232 420 248 L 392 242 Z" fill="#F87171" stroke="#DC2626" stroke-width="1.5" />

        <!-- Pharynx and Vocal Cords / Throat Passage -->
        <path d="M 160 350 Q 175 300 180 260 Q 185 220 200 180" 
              fill="none" stroke="#E65100" stroke-width="2" stroke-dasharray="4,4" opacity="0.6" />
        <text x="145" y="315" font-family="'Plus Jakarta Sans', sans-serif" font-size="11" font-weight="700" fill="#E65100">स्वरतन्त्री (Glottis)</text>

        <!-- Dynamic Tongue (Jihvā) -->
        <path id="sthana-tongue" d="${TONGUE_PATHS.neutral}" 
              fill="url(#tongueGrad)" stroke="#DC2626" stroke-width="2.2" 
              style="transition: all 0.45s cubic-bezier(0.4, 0, 0.2, 1);" />

        <!-- Interactive Sthāna Anchor Points & Rings -->
        
        <!-- 1. Kaṇṭhya (Throat / Velum) -->
        <g id="marker-kanthya" class="sthana-marker" transform="translate(195, 255)">
          <circle class="ring-pulse" r="14" fill="#E65100" opacity="0.2" />
          <circle class="core-dot" r="7" fill="#E65100" stroke="#FFF" stroke-width="2" />
          <text x="-10" y="24" font-family="'Eczar', serif" font-size="13" font-weight="700" fill="#0F172A" text-anchor="end">१. कण्ठ्य</text>
        </g>

        <!-- 2. Tālavya (Hard Palate) -->
        <g id="marker-talavya" class="sthana-marker" transform="translate(260, 155)">
          <circle class="ring-pulse" r="14" fill="#E65100" opacity="0.2" />
          <circle class="core-dot" r="7" fill="#E65100" stroke="#FFF" stroke-width="2" />
          <text x="0" y="-12" font-family="'Eczar', serif" font-size="13" font-weight="700" fill="#0F172A" text-anchor="middle">२. तालव्य</text>
        </g>

        <!-- 3. Mūrdhanya (Roof / Retroflex) -->
        <g id="marker-murdhanya" class="sthana-marker" transform="translate(320, 145)">
          <circle class="ring-pulse" r="14" fill="#E65100" opacity="0.2" />
          <circle class="core-dot" r="7" fill="#E65100" stroke="#FFF" stroke-width="2" />
          <text x="5" y="-12" font-family="'Eczar', serif" font-size="13" font-weight="700" fill="#0F172A" text-anchor="middle">३. मूर्धन्य</text>
        </g>

        <!-- 4. Dantya (Upper Teeth) -->
        <g id="marker-dantya" class="sthana-marker" transform="translate(378, 190)">
          <circle class="ring-pulse" r="14" fill="#E65100" opacity="0.2" />
          <circle class="core-dot" r="7" fill="#E65100" stroke="#FFF" stroke-width="2" />
          <text x="20" y="14" font-family="'Eczar', serif" font-size="13" font-weight="700" fill="#0F172A">४. दन्त्य</text>
        </g>

        <!-- 5. Oṣṭhya (Lips) -->
        <g id="marker-oshthya" class="sthana-marker" transform="translate(425, 215)">
          <circle class="ring-pulse" r="14" fill="#E65100" opacity="0.2" />
          <circle class="core-dot" r="7" fill="#E65100" stroke="#FFF" stroke-width="2" />
          <text x="18" y="5" font-family="'Eczar', serif" font-size="13" font-weight="700" fill="#0F172A">५. ओष्ठ्य</text>
        </g>

        <!-- Comparison Arrow Container -->
        <g id="comparison-arrow-layer"></g>
      </svg>
    `;
  }

  function init(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = createSVG();
    svgRoot = document.getElementById("vocal-tract-svg");
  }

  function highlight(sthanaKey, customLabel) {
    if (!svgRoot) return;
    
    // Normalize key
    const key = (sthanaKey || "kanthya").toLowerCase();
    
    // Reset all markers
    const markers = svgRoot.querySelectorAll(".sthana-marker");
    markers.forEach(m => {
      const dot = m.querySelector(".core-dot");
      const pulse = m.querySelector(".ring-pulse");
      if (dot) dot.setAttribute("fill", "#E65100");
      if (pulse) {
        pulse.setAttribute("fill", "#E65100");
        pulse.setAttribute("opacity", "0.2");
        pulse.removeAttribute("filter");
      }
    });

    // Clear comparison arrows
    const arrowLayer = svgRoot.querySelector("#comparison-arrow-layer");
    if (arrowLayer) arrowLayer.innerHTML = "";

    // Highlight active marker
    const activeMarker = svgRoot.querySelector(`#marker-${key}`);
    if (activeMarker) {
      const dot = activeMarker.querySelector(".core-dot");
      const pulse = activeMarker.querySelector(".ring-pulse");
      if (dot) {
        dot.setAttribute("fill", "#EA580C");
        dot.setAttribute("r", "9");
      }
      if (pulse) {
        pulse.setAttribute("fill", "#EA580C");
        pulse.setAttribute("opacity", "0.6");
        pulse.setAttribute("filter", "url(#glowGold)");
      }
    }

    // Morph the tongue to the appropriate posture
    const tongue = svgRoot.querySelector("#sthana-tongue");
    if (tongue) {
      const targetPath = TONGUE_PATHS[key] || TONGUE_PATHS.neutral;
      tongue.setAttribute("d", targetPath);
    }

    // Update label banner if present
    const meta = STHANA_COORDS[key] || { name: key, sutra: "" };
    const bannerTitle = document.getElementById("sthana-banner-name");
    const bannerSutra = document.getElementById("sthana-banner-sutra");
    if (bannerTitle) bannerTitle.textContent = customLabel || meta.name;
    if (bannerSutra) bannerSutra.textContent = meta.sutra || "";
  }

  function compare(expectedSthana, heardSthana) {
    if (!svgRoot) return;
    
    const expKey = (expectedSthana || "").toLowerCase();
    const hrdKey = (heardSthana || "").toLowerCase();

    // Clear previous
    highlight(expKey);

    const expMarker = svgRoot.querySelector(`#marker-${expKey}`);
    const hrdMarker = svgRoot.querySelector(`#marker-${hrdKey}`);

    if (expMarker) {
      const dot = expMarker.querySelector(".core-dot");
      const pulse = expMarker.querySelector(".ring-pulse");
      if (dot) dot.setAttribute("fill", "#059669"); // Emerald for expected
      if (pulse) pulse.setAttribute("fill", "#059669");
    }

    if (hrdMarker && hrdKey !== expKey) {
      const dot = hrdMarker.querySelector(".core-dot");
      const pulse = hrdMarker.querySelector(".ring-pulse");
      if (dot) dot.setAttribute("fill", "#DC2626"); // Crimson for errant heard
      if (pulse) pulse.setAttribute("fill", "#DC2626");

      // Draw directional corrective arrow from Heard -> Expected
      const arrowLayer = svgRoot.querySelector("#comparison-arrow-layer");
      const start = STHANA_COORDS[hrdKey];
      const end = STHANA_COORDS[expKey];

      if (arrowLayer && start && end) {
        arrowLayer.innerHTML = `
          <defs>
            <marker id="arrowHead" markerWidth="8" markerHeight="8" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#059669" />
            </marker>
          </defs>
          <path d="M ${start.x} ${start.y} Q ${(start.x + end.x)/2} ${Math.min(start.y, end.y) - 25} ${end.x} ${end.y}"
                fill="none" stroke="#059669" stroke-width="3" stroke-dasharray="6,4"
                marker-end="url(#arrowHead)" />
          <text x="${(start.x + end.x)/2}" y="${Math.min(start.y, end.y) - 30}" 
                fill="#059669" font-family="'Plus Jakarta Sans', sans-serif" font-size="11" font-weight="800" text-anchor="middle">
            स्थानान्तरणम् (Shift Tongue Here)
          </text>
        `;
      }
    }
  }

  return {
    init,
    highlight,
    compare
  };
})();
