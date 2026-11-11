// Postcard maker: grabs the current 3D view and composes a downloadable card on a 2D canvas.
const $ = (s) => document.querySelector(s);
const W = 1800, H = 1200;
let shot = null, style = 'classic', ctxApi = null;

function cover(ctx, img, x, y, w, h) {
  const s = Math.max(w / img.width, h / img.height), sw = w / s, sh = h / s;
  ctx.drawImage(img, (img.width - sw) / 2, (img.height - sh) / 2, sw, sh, x, y, w, h);
}
function spaced(ctx, text, x, y, gap, align = 'left') {
  const ws = [...text].map((c) => ctx.measureText(c).width), total = ws.reduce((a, b) => a + b, 0) + gap * (text.length - 1);
  let cx = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
  const ta = ctx.textAlign; ctx.textAlign = 'left';
  [...text].forEach((c, i) => { ctx.fillText(c, cx, y); cx += ws[i] + gap; });
  ctx.textAlign = ta; return total;
}
function stamp(ctx, x, y, s, ink, paper) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(0.05);
  ctx.fillStyle = paper; ctx.fillRect(0, 0, s, s * 1.22);
  ctx.globalCompositeOperation = 'destination-out';
  for (let i = 0; i <= 10; i++) for (const [px, py] of [[i * s / 10, 0], [i * s / 10, s * 1.22], [0, i * s * 1.22 / 10], [s, i * s * 1.22 / 10]]) { ctx.beginPath(); ctx.arc(px, py, s * 0.035, 0, 7); ctx.fill(); }
  ctx.globalCompositeOperation = 'source-over';
  ctx.strokeStyle = ink; ctx.lineWidth = s * 0.018; ctx.strokeRect(s * 0.1, s * 0.1, s * 0.8, s * 1.02);
  // a little uru on waves
  ctx.fillStyle = ink; ctx.beginPath(); ctx.moveTo(s * 0.22, s * 0.62); ctx.quadraticCurveTo(s * 0.5, s * 0.86, s * 0.8, s * 0.6); ctx.lineTo(s * 0.7, s * 0.74); ctx.quadraticCurveTo(s * 0.5, s * 0.8, s * 0.3, s * 0.74); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(s * 0.5, s * 0.24); ctx.lineTo(s * 0.5, s * 0.66); ctx.lineTo(s * 0.72, s * 0.58); ctx.closePath(); ctx.fill();
  ctx.lineWidth = s * 0.02; ctx.beginPath(); for (let i = 0; i < 4; i++) { ctx.moveTo(s * (0.2 + i * 0.16), s * 0.9); ctx.quadraticCurveTo(s * (0.24 + i * 0.16), s * 0.86, s * (0.28 + i * 0.16), s * 0.9); ctx.quadraticCurveTo(s * (0.32 + i * 0.16), s * 0.94, s * (0.36 + i * 0.16), s * 0.9); } ctx.stroke();
  ctx.font = `600 ${s * 0.1}px Jost, sans-serif`; ctx.textAlign = 'center'; ctx.fillText('CALICUT', s / 2, s * 1.07);
  ctx.restore();
}
const timeWord = (h) => (h < 6.3 ? 'before dawn' : h < 8 ? 'at sunrise' : h < 11 ? 'in the morning' : h < 15 ? 'at midday' : h < 17 ? 'in the afternoon' : h < 18.6 ? 'at golden hour' : h < 19.3 ? 'at dusk' : 'at night');

function draw() {
  const cv = $('#pcCanvas'), ctx = cv.getContext('2d'); if (!shot) return;
  const p = ctxApi.getPlace(), msg = $('#pcMsg').value.trim(), from = $('#pcFrom').value.trim();
  const coord = `${p.lat.toFixed(4)}° N  ${p.lon.toFixed(4)}° E`, caption = `${p.name} ${timeWord(ctxApi.getTime())}`;
  ctx.clearRect(0, 0, W, H); ctx.textBaseline = 'alphabetic';
  if (style === 'classic') {
    ctx.fillStyle = '#f3ebdb'; ctx.fillRect(0, 0, W, H);
    const m = 56, ph = 830; cover(ctx, shot, m, m, W - 2 * m, ph);
    ctx.strokeStyle = 'rgba(40,30,20,.25)'; ctx.lineWidth = 2; ctx.strokeRect(m, m, W - 2 * m, ph);
    stamp(ctx, W - m - 210, m + 34, 170, '#b5532f', '#f3ebdb');
    ctx.fillStyle = '#8a5a2c'; ctx.font = 'italic 500 58px "Playfair Display", Georgia, serif'; ctx.textAlign = 'left'; ctx.fillText('Greetings from', m + 4, ph + m + 96);
    ctx.fillStyle = '#1d2733'; ctx.font = '600 128px Jost, sans-serif'; const tw = spaced(ctx, 'KOZHIKODE', m, ph + m + 226, 22);
    ctx.fillStyle = '#c9772f'; ctx.font = '600 64px "Noto Sans Malayalam", sans-serif'; ctx.fillText('കോഴിക്കോട്', m + 440, ph + m + 98);
    ctx.textAlign = 'right'; ctx.fillStyle = '#1d2733'; ctx.font = '500 40px Jost, sans-serif'; ctx.fillText(caption, W - m, ph + m + 92);
    ctx.fillStyle = '#6b6457'; ctx.font = '400 30px "IBM Plex Mono", monospace'; ctx.fillText(coord, W - m, ph + m + 140);
    if (msg || from) { ctx.fillStyle = '#35507a'; ctx.font = '500 54px Caveat, cursive'; ctx.fillText((msg || '') + (from ? `  — ${from}` : ''), W - m, ph + m + 222, W - 2 * m - tw - 70); }
  } else {
    cover(ctx, shot, 0, 0, W, H);
    const g = ctx.createLinearGradient(0, H * 0.42, 0, H); g.addColorStop(0, 'rgba(6,10,20,0)'); g.addColorStop(1, 'rgba(6,10,20,.88)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.lineWidth = 3; ctx.strokeRect(40, 40, W - 80, H - 80);
    stamp(ctx, W - 270, 84, 170, '#b5532f', '#f3ebdb');
    ctx.textAlign = 'center'; ctx.fillStyle = '#ffc56b'; ctx.font = 'italic 500 70px "Playfair Display", Georgia, serif'; ctx.fillText('Greetings from', W / 2, H - 392);
    ctx.fillStyle = '#fff'; ctx.font = '700 216px Jost, sans-serif'; spaced(ctx, 'KOZHIKODE', W / 2, H - 196, 26, 'center');
    ctx.fillStyle = '#ffc56b'; ctx.font = '600 56px "Noto Sans Malayalam", sans-serif'; ctx.fillText('കോഴിക്കോട്', W / 2, H - 112);
    ctx.fillStyle = 'rgba(255,255,255,.82)'; ctx.font = '400 28px "IBM Plex Mono", monospace'; ctx.textAlign = 'left'; ctx.fillText(`${caption}  ·  ${coord}`, 76, H - 70);
    if (msg || from) { ctx.textAlign = 'right'; ctx.fillStyle = '#fff'; ctx.font = '500 50px Caveat, cursive'; ctx.fillText((msg || '') + (from ? `  — ${from}` : ''), W - 76, H - 66, 760); }
  }
}

export function initPostcard(api) {
  ctxApi = api;
  const cv = $('#pcCanvas'); cv.width = W; cv.height = H;
  $('#bCard').onclick = async () => {
    api.closePanels();
    api.composer.render();                                   // read the frame in the same task it was drawn
    const url = api.renderer.domElement.toDataURL('image/jpeg', 0.95);
    shot = new Image(); await new Promise((r) => { shot.onload = r; shot.src = url; });
    await Promise.all(['600 100px Jost', 'italic 500 60px "Playfair Display"', '500 50px Caveat', '600 60px "Noto Sans Malayalam"', '400 30px "IBM Plex Mono"'].map((f) => document.fonts.load(f, 'KOZHIKODE കോഴിക്കോട്'))).catch(() => {});
    draw(); $('#postcard').classList.add('open');
  };
  $('#pcMsg').oninput = draw; $('#pcFrom').oninput = draw;
  document.querySelectorAll('#pcStyles button').forEach((b) => (b.onclick = () => { style = b.dataset.s; document.querySelectorAll('#pcStyles button').forEach((x) => x.classList.toggle('on', x === b)); draw(); }));
  const blob = () => new Promise((r) => cv.toBlob(r, 'image/png'));
  $('#pcSave').onclick = async () => { const a = document.createElement('a'); a.href = URL.createObjectURL(await blob()); a.download = 'kozhikode-postcard.png'; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 4000); };
  const share = $('#pcShare');
  if (!navigator.canShare) share.hidden = true;
  share.onclick = async () => { const f = new File([await blob()], 'kozhikode-postcard.png', { type: 'image/png' }); if (navigator.canShare({ files: [f] })) navigator.share({ files: [f], title: 'Greetings from Kozhikode' }).catch(() => {}); };
  $('#pcLink').onclick = async (e) => { const b = e.currentTarget; try { await navigator.clipboard.writeText(api.getLink()); b.textContent = 'Link copied'; } catch { b.textContent = 'Copy from address bar'; } setTimeout(() => (b.textContent = 'Copy link to this view'), 2200); };
}
