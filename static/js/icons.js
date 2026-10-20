/**
 * VaaniAI SVG Icon Registry
 * Clean, lightweight, professional vector icons replacing all informal emojis.
 * Built with Lucide/Feather stroke geometry (24x24 viewBox, stroke-width: 2).
 */

const Icons = {
  svg(inner, cls = "ui-icon", extra = "") {
    return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ${extra}>${inner}</svg>`;
  },

  mic(cls = "ui-icon") {
    return this.svg(`<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>`, cls);
  },

  micRecord(cls = "ui-icon-record") {
    return this.svg(`<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>`, cls);
  },

  speaker(cls = "ui-icon") {
    return this.svg(`<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>`, cls);
  },

  trash(cls = "ui-icon") {
    return this.svg(`<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>`, cls);
  },

  search(cls = "ui-icon") {
    return this.svg(`<circle cx="11" cy="11" r="8"/><line x1="21" x2="21" y1="21" y2="16.65"/>`, cls);
  },

  report(cls = "ui-icon") {
    return this.svg(`<circle cx="11" cy="11" r="8"/><line x1="21" x2="21" y1="21" y2="16.65"/><path d="m11 8 .01 0"/><path d="M11 12v4"/>`, cls);
  },

  bolt(cls = "ui-icon") {
    return this.svg(`<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>`, cls);
  },

  book(cls = "ui-icon") {
    return this.svg(`<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>`, cls);
  },

  scroll(cls = "ui-icon") {
    return this.svg(`<path d="M8 2h8a2 2 0 0 1 2 2v14a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V6a4 4 0 0 1 4-4h2"/><path d="M18 18a2 2 0 0 0-2-2H4"/><line x1="8" x2="14" y1="7" y2="7"/><line x1="8" x2="14" y1="11" y2="11"/>`, cls);
  },

  alert(cls = "ui-icon") {
    return this.svg(`<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" x2="12" y1="9" y2="13"/><line x1="12" x2="12.01" y1="17" y2="17"/>`, cls);
  },

  check(cls = "ui-icon") {
    return this.svg(`<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>`, cls);
  },

  award(cls = "ui-icon") {
    return this.svg(`<circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>`, cls);
  },

  refresh(cls = "ui-icon") {
    return this.svg(`<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>`, cls);
  },

  target(cls = "ui-icon") {
    return this.svg(`<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>`, cls);
  },

  wind(cls = "ui-icon") {
    return this.svg(`<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>`, cls);
  },

  sparkles(cls = "ui-icon") {
    return this.svg(`<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/>`, cls);
  },

  arrowRight(cls = "ui-icon") {
    return this.svg(`<line x1="5" x2="19" y1="12" y2="12"/><polyline points="12 5 19 12 12 19"/>`, cls);
  },

  edit(cls = "ui-icon") {
    return this.svg(`<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>`, cls);
  },

  lightbulb(cls = "ui-icon") {
    return this.svg(`<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>`, cls);
  },

  fileText(cls = "ui-icon") {
    return this.svg(`<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/>`, cls);
  },

  ruler(cls = "ui-icon") {
    return this.svg(`<path d="m21.73 7.73-14-14a2.4 2.4 0 0 0-3.46 0l-2 2a2.4 2.4 0 0 0 0 3.46l14 14a2.4 2.4 0 0 0 3.46 0l2-2a2.4 2.4 0 0 0 0-3.46z"/><line x1="7.5" x2="9.5" y1="4.5" y2="6.5"/><line x1="10.5" x2="12.5" y1="7.5" y2="9.5"/><line x1="13.5" x2="15.5" y1="10.5" y2="12.5"/>`, cls);
  },

  lotus(cls = "ui-icon") {
    return this.svg(`<path d="M12 2C9 7 4 9 4 15a8 8 0 0 0 16 0c0-6-5-8-8-13Z"/><path d="M12 12c-2 2-3 4-3 6a3 3 0 0 0 6 0c0-2-1-4-3-6Z"/>`, cls);
  }
};

window.Icons = Icons;
