/**
 * T&L Digital — Theme Loader
 * ─────────────────────────────────────────────────────────────────────────────
 * Runs immediately in <head> before any styles are painted.
 * Reads user preferences from localStorage and stamps them as *inline*
 * CSS custom properties on <html> — inline styles beat every stylesheet rule,
 * so user preferences always win regardless of dashboard-specific CSS.
 *
 * Settings are written by docs/settings.html under the key "tl_theme".
 *
 * Shape of tl_theme (all fields optional):
 * {
 *   theme:       "light" | "dark",
 *   accent:      "#rrggbb",
 *   navy:        "#rrggbb",
 *   fontFamilyKey: "dm-sans" | "inter" | "system" | "georgia",
 *   fontFamily:  "<full CSS font-family string>",
 *   fontSize:    "14",          // px, stored as string
 *   radius:      "10",          // px, stored as string
 * }
 * ─────────────────────────────────────────────────────────────────────────────
 */
(function () {
  'use strict';

  /* ── Read saved preferences ── */
  var prefs = {};
  try {
    prefs = JSON.parse(localStorage.getItem('tl_theme') || '{}');
  } catch (e) { /* corrupt data — treat as defaults */ }

  var root = document.documentElement;

  /* Helper — only sets if value is truthy */
  function set(prop, value) {
    if (value) root.style.setProperty(prop, value);
  }

  /* ── 1. Theme (data-theme attribute) — applied first to prevent dark-mode FOUC */
  if (prefs.theme) {
    root.setAttribute('data-theme', prefs.theme);
  }

  /* ── 2. Accent colour — covers every alias name used across dashboards */
  if (prefs.accent) {
    set('--accent',       prefs.accent);
    set('--accent-hover', prefs.accent);
    /* CW survey uses --c-mobile for the primary chart/link colour */
    set('--c-mobile',     prefs.accent);
    /* SIR header accent */
    set('--accent-2',     prefs.accent);
  }

  /* ── 3. Navy / sidebar colour */
  if (prefs.navy) {
    set('--navy',       prefs.navy);
    set('--navy-light', prefs.navy);
    set('--header-bg',  prefs.navy);
  }

  /* ── 4. Border radius — covers every alias */
  if (prefs.radius) {
    var rPx  = prefs.radius + 'px';
    var rsPx = Math.max(2, Math.round(parseInt(prefs.radius, 10) * 0.6)) + 'px';
    set('--radius',    rPx);
    set('--r',         rPx);
    set('--radius-sm', rsPx);
    set('--r-sm',      rsPx);
  }

  /* ── 5. Font family — covers every alias */
  if (prefs.fontFamily) {
    set('--font-ui',  prefs.fontFamily);
    set('--font',     prefs.fontFamily);
  }

  /* ── 6. Base font size on <html> */
  if (prefs.fontSize) {
    root.style.fontSize = prefs.fontSize + 'px';
  }

}());
