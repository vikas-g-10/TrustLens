const themes = {
  dark: {
    background: '#050505', card: '#101411', foreground: '#ebebeb', muted: '#8a918d', border: '#303633',
    primary: '#10b981', primaryForeground: '#03150f', success: '#34d399', warning: '#fbbf24', danger: '#f87171', info: '#67e8f9', track: '#1f2937',
  },
  light: {
    background: '#f5f7f6', card: '#ffffff', foreground: '#0a0f0d', muted: '#4a5550', border: '#d9dfdc',
    primary: '#047857', primaryForeground: '#ffffff', success: '#047857', warning: '#92400e', danger: '#b91c1c', info: '#0e7490', track: '#e3e8e6',
  },
};

const pairs = [
  ['foreground', 'background'], ['foreground', 'card'], ['muted', 'background'], ['muted', 'card'],
  ['primaryForeground', 'primary'], ['success', 'card'], ['warning', 'card'], ['danger', 'card'], ['info', 'card'],
  ['foreground', 'track'],
];

function luminance(hex) {
  const rgb = hex.match(/[a-f\d]{2}/gi).map((v) => parseInt(v, 16) / 255).map((v) => v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
}
function contrast(a, b) {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (light + .05) / (dark + .05);
}

let failed = false;
for (const [theme, values] of Object.entries(themes)) {
  console.log(`${theme}:`);
  for (const [text, background] of pairs) {
    const ratio = contrast(values[text], values[background]);
    const pass = ratio >= 4.5;
    failed ||= !pass;
    console.log(`  ${text} on ${background}: ${ratio.toFixed(2)}:1 ${pass ? 'PASS' : 'FAIL'}`);
  }
}
if (failed) process.exit(1);
