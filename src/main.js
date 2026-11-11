import * as THREE from 'three';
import { MapControls } from 'three/addons/controls/MapControls.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { Terrain, buildGround, buildingMaterial, buildChunk, buildTrees, buildLamps, buildRoads, buildWards, wardAt } from './city.js';
import { buildLandmarks, lampMat } from './models.js';
import { LANDMARKS, VIEWS, TOURS } from './places.js';
import { initPostcard } from './postcard.js';

const $ = (s) => document.querySelector(s);
const D2R = Math.PI / 180, clamp = (v, a, b) => Math.min(b, Math.max(a, v)), lerp = (a, b, t) => a + (b - a) * t;
const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const fmtIN = (n) => n.toLocaleString('en-IN');

// ------------------------------------------------------------------ renderer
const canvas = $('#scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0xc9d9e6, 0.000034);
const camera = new THREE.PerspectiveCamera(42, 1, 10, 400000);
const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(4, 4, { type: THREE.HalfFloatType, samples: 4 }));
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(4, 4), 0.2, 0.6, 1.0); composer.addPass(bloom);
composer.addPass(new OutputPass());

// radius / maxRadius: how far from the view centre buildings are kept in memory (metres)
const QUALITY = { low: { pr: 1, sh: 0, tree: 1300, bloom: false, radius: 1700, maxRadius: 3000, model: 2200 }, medium: { pr: 1.5, sh: 2048, tree: 2800, bloom: true, radius: 3200, maxRadius: 7500, model: 4500 }, high: { pr: 2, sh: 4096, tree: 5600, bloom: true, radius: 5500, maxRadius: 1e9, model: 1e9 } };
let Qn = 'high', Qs = QUALITY.high;
const autoQ = () => {
  const cores = navigator.hardwareConcurrency || 4, mem = navigator.deviceMemory || 8, phone = innerWidth < 820 || matchMedia('(pointer: coarse)').matches;
  if (mem <= 4 || cores < 4) return 'low';
  if (phone) return cores >= 8 && mem >= 8 ? 'medium' : 'low';
  return cores >= 8 ? 'high' : 'medium';
};

const sky = new Sky(); sky.scale.setScalar(300000); scene.add(sky);
const skyU = sky.material.uniforms; skyU.turbidity.value = 5; skyU.mieCoefficient.value = 0.004; skyU.mieDirectionalG.value = 0.82;
const sun = new THREE.DirectionalLight(0xffffff, 3); sun.castShadow = true; scene.add(sun, sun.target);
sun.shadow.bias = -0.0003;
const moon = new THREE.DirectionalLight(0x8fa6dc, 0); moon.position.set(-0.4, 0.8, 0.3); scene.add(moon);
const hemi = new THREE.HemisphereLight(0xbcd4f0, 0x5a5346, 1); scene.add(hemi);
{ // stars
  const p = []; for (let i = 0; i < 1800; i++) { const v = new THREE.Vector3().randomDirection(); if (v.y < 0.03) continue; p.push(v.x * 250000, v.y * 250000, v.z * 250000); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  var stars = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xdfe8ff, size: 1.6, sizeAttenuation: false, transparent: true, opacity: 0, fog: false, depthWrite: false }));
  stars.frustumCulled = false; scene.add(stars);
}

const U = { uMask: { value: null }, uMask2: { value: null }, uSea: { value: null }, uTime: { value: 0 }, uNight: { value: 0 }, uSkyCol: { value: new THREE.Color() }, uHalf: { value: new THREE.Vector2() } };

// ------------------------------------------------------------------ time of day (sun for Kozhikode, 15 January)
const LAT = 11.25 * D2R, DECL = -21.2 * D2R, NOON = 12.6;
const env = { time: 17.6, night: 0, sunDir: new THREE.Vector3() };
const C_NIGHT = new THREE.Color(0x0a1122), C_DUSK = new THREE.Color(0xe7a981), C_DAY = new THREE.Color(0xc4d6e6), tmpC = new THREE.Color();
function setTime(h) {
  env.time = h;
  const H = (h - NOON) * 15 * D2R;
  const sinAlt = Math.sin(LAT) * Math.sin(DECL) + Math.cos(LAT) * Math.cos(DECL) * Math.cos(H), alt = Math.asin(sinAlt);
  const az = Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(LAT) - Math.tan(DECL) * Math.cos(LAT)) + Math.PI;
  env.sunDir.set(Math.sin(az) * Math.cos(alt), sinAlt, -Math.cos(az) * Math.cos(alt));
  const day = sstep(-0.06, 0.1, sinAlt), high = sstep(0.02, 0.5, sinAlt), night = 1 - sstep(-0.13, 0.03, sinAlt);
  env.night = night;
  sun.intensity = 3.4 * sstep(-0.01, 0.16, sinAlt);
  sun.color.setRGB(1, lerp(0.56, 0.96, high), lerp(0.3, 0.88, high));
  sun.castShadow = Qs.sh > 0 && sun.intensity > 0.05;
  moon.intensity = 0.5 * night;
  hemi.intensity = lerp(0.2, lerp(1.5, 1.05, high), day);
  hemi.color.copy(tmpC.set(0x3c4d86)).lerp(new THREE.Color(0xbcd4f0), day);
  hemi.groundColor.set(0x1a1c26).lerp(new THREE.Color(0x7a6a58), day);
  skyU.sunPosition.value.copy(env.sunDir);
  skyU.rayleigh.value = lerp(3.2, 1.1, high);
  skyU.turbidity.value = lerp(7, 3.5, high);
  scene.fog.color.copy(C_NIGHT).lerp(tmpC.copy(C_DUSK).lerp(C_DAY, high), day);
  U.uSkyCol.value.setRGB(0.02, 0.03, 0.07).lerp(tmpC.setRGB(0.30, 0.52, 0.78).lerp(new THREE.Color(0.85, 0.5, 0.3), (1 - high) * 0.45), day);
  U.uNight.value = night;
  renderer.toneMappingExposure = lerp(0.7, lerp(0.82, 0.58, high), day);
  bloom.strength = lerp(0.1, 0.75, night); bloom.threshold = lerp(1.25, 0.55, night); bloom.radius = 0.55;
  stars.material.opacity = night * 0.9;
  if (lamps) { lamps.material.opacity = night * 0.9; lamps.visible = night > 0.02; }
  lampMat.emissiveIntensity = night * 6;
  const hh = Math.floor(h), mm = Math.floor((h - hh) * 60);
  $('#clock').textContent = `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')} IST`;
  $('#time').value = h;
  document.querySelectorAll('#presets button').forEach((b) => b.classList.toggle('on', Math.abs(+b.dataset.t - h) < 0.3));
}
let timeTween = null;
function tweenTime(to, dur = 2.2) { timeTween = { a: env.time, b: to, t: 0, dur }; }

// ------------------------------------------------------------------ camera
const controls = new MapControls(camera, canvas);
Object.assign(controls, { enableDamping: true, dampingFactor: 0.09, screenSpacePanning: false, maxPolarAngle: 85.5 * D2R, minDistance: 110, maxDistance: 52000, zoomToCursor: true, zoomSpeed: 1.3 });
let T = null, fly = null;
const cs = { x: 0, z: 0, d: 3000, h: 60, t: 68 };
function applyCam(s) {
  const y = T ? Math.max(T.heightAt(s.x, s.z), 0) : 0, h = s.h * D2R, t = s.t * D2R;
  controls.target.set(s.x, y, s.z);
  camera.position.set(s.x - Math.sin(h) * Math.sin(t) * s.d, y + Math.cos(t) * s.d, s.z + Math.cos(h) * Math.sin(t) * s.d);
  camera.lookAt(controls.target);
}
function readCam() {
  const dx = controls.target.x - camera.position.x, dy = camera.position.y - controls.target.y, dz = controls.target.z - camera.position.z;
  const d = Math.hypot(dx, dy, dz);
  return { x: controls.target.x, z: controls.target.z, d, h: (Math.atan2(dx, -dz) / D2R + 360) % 360, t: Math.acos(clamp(dy / d, -1, 1)) / D2R };
}
function flyTo(v, dur) {
  const a = readCam(), [x, z] = v.ll ? T.ll(...v.ll) : [v.x, v.z];
  const b = { x, z, d: v.d, h: v.h, t: v.t }, span = Math.hypot(b.x - a.x, b.z - a.z);
  b.h = a.h + ((((b.h - a.h) % 360) + 540) % 360 - 180);
  fly = { a, b, t: 0, dur: dur ?? clamp(1.6 + span / 3500, 1.8, 5), bump: Math.max(0, span * 0.55 - Math.max(a.d, b.d) * 0.5) };
}
controls.addEventListener('start', () => { fly = null; tour.auto && setAuto(false); $('#hint').classList.add('gone'); });
const keys = new Set();
addEventListener('keydown', (e) => { if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return; keys.add(e.key.toLowerCase()); if (e.key === 'Escape') closePanels(); });
addEventListener('keyup', (e) => keys.delete(e.key.toLowerCase()));

function resize() {
  const w = innerWidth, h = innerHeight, pr = Math.min(devicePixelRatio || 1, Qs.pr);
  renderer.setPixelRatio(pr); renderer.setSize(w, h, false); composer.setPixelRatio(pr); composer.setSize(w, h);
  camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener('resize', resize);

// ------------------------------------------------------------------ labels
const labelBox = $('#labels'), labels = [];
let showLabels = true, showWards = false, useMl = false;
function addLabel(o) {
  const el = document.createElement('div'); el.className = 'lb ' + o.cls;
  el.innerHTML = (o.dot ? '<i></i>' : '') + '<span></span>';
  if (o.onClick) { el.classList.add('click'); el.addEventListener('click', o.onClick); }
  labelBox.appendChild(el);
  const L = { ...o, el, w: 0, shown: false, y: (o.y ?? Math.max(T.heightAt(o.x, o.z), 0)) + (o.lift ?? 30) };
  labels.push(L); return L;
}
function relabel() { for (const L of labels) { L.el.lastChild.textContent = (useMl && L.ml) || L.n; L.w = 0; } }
const pv = new THREE.Vector3(), used = [];
function updateLabels() {
  const W = innerWidth, H = innerHeight; used.length = 0;
  for (const L of labels) {
    let vis = L.group === 'ward' ? showWards : L.group === 'tour' ? tour.id === L.tour : showLabels;
    if (vis) {
      const d = camera.position.distanceTo(pv.set(L.x, L.y, L.z));
      vis = d < L.maxD && d > (L.minD || 0);
      if (vis) { pv.project(camera); vis = pv.z < 1 && Math.abs(pv.x) < 1.05 && Math.abs(pv.y) < 1.05; }
    }
    if (vis) {
      if (!L.w) { L.el.style.display = 'flex'; L.w = L.el.offsetWidth || 60; L.shown = true; }
      const sx = (pv.x * 0.5 + 0.5) * W, sy = (-pv.y * 0.5 + 0.5) * H, x0 = L.dot ? sx - 8 : sx - L.w / 2, x1 = x0 + L.w, y0 = sy - 10, y1 = sy + 10;
      for (const r of used) if (x0 < r[2] && x1 > r[0] && y0 < r[3] && y1 > r[1]) { vis = false; break; }
      if (vis) { used.push([x0 - 6, y0 - 4, x1 + 6, y1 + 4]); L.el.style.transform = `translate(${x0.toFixed(1)}px,${(sy - 10).toFixed(1)}px)`; }
    }
    if (vis !== L.shown) { L.el.style.display = vis ? 'flex' : 'none'; L.shown = vis; }
  }
}

// ------------------------------------------------------------------ load
const bar = $('#bar i'), stage = $('#stage');
const prog = (f, txt) => { bar.style.width = (f * 100).toFixed(1) + '%'; if (txt) stage.textContent = txt; };
let man, lamps = null, wards = [], wardLines = null, localities = [];
const stream = { b: [], t: [], lm: null, bmat: null, bbuf: null, treeOf: null };
const texLoader = new THREE.TextureLoader();
const tex = async (url, srgb) => { const t = await texLoader.loadAsync(url); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.anisotropy = 8; return t; };
const bin = (url) => fetch(url).then((r) => r.arrayBuffer()), js = (url) => fetch(url).then((r) => r.json());
const tick = () => new Promise((r) => setTimeout(r, 0));

async function load() {
  resize();
  prog(0.03, 'Reading the map');
  man = await js('data/manifest.json');
  let done = 0; const N = 14, step = (p) => p.then((v) => { prog(0.05 + 0.4 * (++done / N), 'Laying out coast, rivers and hills'); return v; });
  const [hc, hb, satCore, satBack, mask, mask2, sea, bbuf, tbuf, roads, w, loc, , placed] = await Promise.all([
    step(bin('data/height_core.bin')), step(bin('data/height_back.bin')), step(tex('data/sat_core.jpg', true)), step(tex('data/sat_back.jpg', true)),
    step(tex('data/masks.jpg')), step(tex('data/masks2.jpg')), step(tex('data/sea_back.png')), step(bin('data/buildings.bin')), step(bin('data/trees.bin')),
    step(js('data/roads.json')), step(js('data/wards.json')), step(js('data/localities.json')), step(document.fonts.ready), step(js('models/manifest.json'))]);
  wards = w; localities = loc;
  T = new Terrain(man, hc, hb);
  U.uMask.value = mask; U.uMask2.value = mask2; U.uSea.value = sea; U.uHalf.value.set(T.HX, T.HY);
  scene.add(buildGround(T, { satCore, satBack }, U));
  const lm = buildLandmarks(T, placed); scene.add(lm.group);
  scene.add(buildRoads(roads, T, U));
  lamps = buildLamps(roads, T); scene.add(lamps);
  wardLines = buildWards(wards, T); scene.add(wardLines);
  setupLabels(); setupUI();
  const start = parseHash() || VIEWS.home;
  const [sx, sz] = T.ll(...start.ll);
  applyCam({ x: sx, z: sz, d: start.d * 2.6, h: start.h - 35, t: 40 }); setTime(start.time ?? 17.6);
  renderer.compile(scene, camera);

  // buildings, trees and landmark models stream in around the view instead of all loading up front
  applyQuality($('#quality').value);
  const C = man.chunk, centre = (ch) => [-T.HX + (ch.i + 0.5) * C, -(-T.HY + (ch.j + 0.5) * C)];
  stream.lm = lm; stream.bmat = buildingMaterial(U); stream.bbuf = bbuf; stream.treeOf = buildTrees(man, tbuf, T, lm.nearModel);
  stream.b = man.bChunks.map((ch) => ({ ch, c: centre(ch), mesh: null })); stream.t = man.tChunks.map((ch) => ({ ch, c: centre(ch), meshes: null }));
  const first = stream.b.filter((e) => Math.hypot(e.c[0] - sx, e.c[1] - sz) < Math.min(Qs.radius, 1600)).sort((a, b) => Math.hypot(a.c[0] - sx, a.c[1] - sz) - Math.hypot(b.c[0] - sx, b.c[1] - sz));
  let nb = 0;
  for (const e of first) { e.mesh = buildChunk(man, e.ch, bbuf, stream.bmat, lm.skip); scene.add(e.mesh); prog(0.45 + 0.5 * ++nb / first.length, `Raising buildings from their footprints · ${fmtIN(nb)} of ${first.length} blocks`); await tick(); }
  lm.loadNear(sx, sz, Qs.model);
  prog(1, 'Ready'); await tick();
  $('#count').textContent = fmtIN(man.buildings);
  document.body.classList.add('ready');
  flyTo(start, 4.5); setTimeout(() => $('#hint').classList.add('gone'), 9000);
  renderer.setAnimationLoop(frame);
  window.__k = { scene, camera, renderer, flyTo, setTime, env, T, controls };
}

function setupLabels() {
  for (const p of LANDMARKS) {
    const [x, z] = T.ll(...p.ll);
    addLabel({ n: p.n, ml: p.ml, x, z, cls: p.water ? 'water' : 'lm', dot: !p.water, maxD: p.water ? 60000 : p.chip ? 26000 : 9000, minD: p.water ? 2500 : 0, lift: p.water ? 5 : 45, onClick: p.water ? null : () => flyTo({ ll: p.ll, ...p.v }) });
  }
  for (const [id, tr] of Object.entries(TOURS)) tr.stops.forEach((s, i) => {
    const [x, z] = T.ll(...s.ll); s.x = x; s.z = z;
    addLabel({ n: `${i + 1} · ${s.n}`, x, z, cls: 'tourlb ' + id, group: 'tour', tour: id, dot: true, maxD: 40000, lift: 70, onClick: () => goStop(i) });
  });
  labels.sort((a, b) => (a.group === 'tour' ? -1 : 0) - (b.group === 'tour' ? -1 : 0));
  for (const l of localities) addLabel({ n: l.n, ml: l.ml, x: l.x, z: -l.y, cls: 'loc', maxD: l.t === 'locality' ? 9000 : 5500, lift: 25 });
  for (const w of wards) if (T.inCore(w.c[0], -w.c[1])) addLabel({ n: `${w.no} · ${w.name}`, x: w.c[0], z: -w.c[1], cls: 'ward', group: 'ward', maxD: 11000, lift: 30 });
  relabel();
}

// ------------------------------------------------------------------ tours
const tour = { id: null, i: 0, auto: false, timer: 0 };
const beacon = new THREE.Group();
{
  const m = new THREE.MeshBasicMaterial({ color: 0xffb347, transparent: true, opacity: 0.28, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide });
  beacon.add(new THREE.Mesh(new THREE.CylinderGeometry(2.5, 5, 320, 16, 1, true).translate(0, 160, 0), m));
  const ring = new THREE.Mesh(new THREE.RingGeometry(26, 32, 48).rotateX(-Math.PI / 2), m.clone()); ring.material.opacity = 0.7; ring.name = 'ring'; ring.position.y = 6; beacon.add(ring);
  beacon.visible = false; scene.add(beacon);
}
let routeLine = null;
function startTour(id) {
  closePanels(); tour.id = id; const tr = TOURS[id];
  document.body.dataset.tour = id; $('#tour').classList.add('open');
  $('#tourKind').textContent = tr.title;
  if (routeLine) { scene.remove(routeLine); routeLine.geometry.dispose(); }
  const pts = []; for (const s of tr.stops) pts.push(new THREE.Vector3(s.x, Math.max(T.heightAt(s.x, s.z), 0) + 40, s.z));
  routeLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.2).getPoints(240)),
    new THREE.LineDashedMaterial({ color: id === 'food' ? 0xff8a5c : 0xffc35c, dashSize: 60, gapSize: 40, transparent: true, opacity: 0.9, depthTest: false, fog: false }));
  routeLine.computeLineDistances(); routeLine.renderOrder = 6; scene.add(routeLine);
  $('#dots').innerHTML = tr.stops.map((_, i) => `<b data-i="${i}"></b>`).join('');
  goStop(0);
}
function goStop(i) {
  const tr = TOURS[tour.id]; if (!tr) return; tour.i = (i + tr.stops.length) % tr.stops.length; const s = tr.stops[tour.i];
  $('#tourStep').textContent = `Stop ${tour.i + 1} of ${tr.stops.length}`;
  $('#tourName').textContent = s.n; $('#tourNo').textContent = String(tour.i + 1).padStart(2, '0'); $('#tourSub').textContent = s.dish ? (s.dish === s.cat ? s.dish : `${s.cat} · ${s.dish}`) : s.ml || ''; $('#tourSub').className = s.dish ? 'dish' : 'ml';
  $('#tourText').textContent = s.text;
  document.querySelectorAll('#dots b').forEach((b, k) => b.classList.toggle('on', k === tour.i));
  beacon.position.set(s.x, Math.max(T.heightAt(s.x, s.z), 0), s.z); beacon.visible = true;
  flyTo({ ll: s.ll, ...s.v }); if (s.time) tweenTime(s.time, 3); tour.timer = 0;
}
function setAuto(on) { tour.auto = on; tour.timer = 0; $('#tourAuto').classList.toggle('on', on); $('#tourAuto').textContent = on ? 'Pause' : 'Autoplay'; }
function endTour() { tour.id = null; setAuto(false); delete document.body.dataset.tour; $('#tour').classList.remove('open'); beacon.visible = false; if (routeLine) { scene.remove(routeLine); routeLine = null; } }

// ------------------------------------------------------------------ UI
function closePanels() { $('#about').classList.remove('open'); $('#postcard').classList.remove('open'); }
function applyQuality(v) {
  Qn = v === 'auto' ? autoQ() : v; Qs = QUALITY[Qn];
  bloom.enabled = Qs.bloom; renderer.shadowMap.enabled = Qs.sh > 0;
  if (Qs.sh) { sun.shadow.mapSize.set(Qs.sh, Qs.sh); sun.shadow.map?.dispose(); sun.shadow.map = null; }
  $('#quality').options[0].textContent = `Auto · ${autoQ()[0].toUpperCase() + autoQ().slice(1)}`;
  resize(); setTime(env.time);
}
function setupUI() {
  const chips = $('#chips');
  for (const p of LANDMARKS.filter((p) => p.chip)) { const b = document.createElement('button'); b.textContent = p.chip; b.onclick = () => flyTo({ ll: p.ll, ...p.v }); chips.appendChild(b); }
  const all = document.createElement('button'); all.textContent = 'Whole city'; all.onclick = () => flyTo(VIEWS.city); chips.appendChild(all);
  $('#time').addEventListener('input', (e) => { timeTween = null; setTime(+e.target.value); });
  document.querySelectorAll('#presets button').forEach((b) => (b.onclick = () => tweenTime(+b.dataset.t)));
  const tog = (id, fn) => ($(id).onclick = (e) => { const on = e.currentTarget.classList.toggle('on'); fn(on); });
  tog('#tLabels', (on) => (showLabels = on)); tog('#tWards', (on) => { showWards = on; wardLines.visible = on; });
  tog('#tMl', (on) => { useMl = on; relabel(); });
  $('#quality').onchange = (e) => applyQuality(e.target.value);
  $('#addBtn').onclick = (e) => { const o = $('#addPlace').classList.toggle('open'); e.currentTarget.setAttribute('aria-expanded', o); };
  canvas.addEventListener('pointerdown', () => $('#addPlace').classList.remove('open'));
  $('#bAbout').onclick = () => { const o = !$('#about').classList.contains('open'); closePanels(); $('#about').classList.toggle('open', o); };
  document.querySelectorAll('[data-close]').forEach((b) => (b.onclick = closePanels));
  $('#compass').onclick = () => { const c = readCam(); flyTo({ x: c.x, z: c.z, d: c.d, h: 0, t: c.t }, 1.2); };
  $('#bTour').onclick = () => (tour.id === 'sights' ? endTour() : startTour('sights'));
  $('#bFood').onclick = () => (tour.id === 'food' ? endTour() : startTour('food'));
  $('#tourPrev').onclick = () => goStop(tour.i - 1); $('#tourNext').onclick = () => goStop(tour.i + 1);
  $('#tourAuto').onclick = () => setAuto(!tour.auto); $('#tourEnd').onclick = endTour;
  $('#dots').onclick = (e) => e.target.dataset.i && goStop(+e.target.dataset.i);
  const s = man.heightSrc, tot = s.mapped + s.est;
  $('#aCount').textContent = fmtIN(man.buildings); $('#aTrees').textContent = fmtIN(man.trees); $('#aWards').textContent = wards.length;
  $('#aMapped').textContent = (100 * s.mapped / tot).toFixed(1) + '%'; $('#aEst').textContent = (100 * s.est / tot).toFixed(1) + '%';
  $('#aMappedBar').style.width = Math.max(1, 100 * s.mapped / tot) + '%'; $('#aEstBar').style.width = 100 * s.est / tot + '%';
  $('#aMappedN').textContent = fmtIN(s.mapped);
  initPostcard({ renderer, composer, getPlace: () => place, getTime: () => env.time, getLink: () => { writeHash(); return location.href; }, closePanels });
}

// ------------------------------------------------------------------ shareable view
function parseHash() {
  const m = location.hash.match(/v=([-\d.,]+)/); if (!m) return null;
  const [lat, lon, d, h, t, time] = m[1].split(',').map(Number);
  if (![lat, lon, d, h, t].every(Number.isFinite)) return null;
  return { ll: [clamp(lon, 75.6, 76), clamp(lat, 11.05, 11.45)], d: clamp(d, 150, 50000), h, t: clamp(t, 0, 85), time: Number.isFinite(time) ? clamp(time, 5, 23) : undefined };
}
function writeHash() {
  const c = readCam(), [lon, lat] = T.toLL(c.x, c.z);
  history.replaceState(null, '', `#v=${lat.toFixed(5)},${lon.toFixed(5)},${c.d.toFixed(0)},${c.h.toFixed(0)},${c.t.toFixed(0)},${env.time.toFixed(2)}`);
}

// ------------------------------------------------------------------ frame
const place = { name: 'Kozhikode', ward: '', lat: 0, lon: 0 };
const clock = new THREE.Clock(); let fc = 0, shHalf = 0;
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
function frame() {
  const dt = Math.min(clock.getDelta(), 0.1); U.uTime.value += dt; fc++;
  if (timeTween) { timeTween.t += dt / timeTween.dur; const e = ease(Math.min(timeTween.t, 1)); setTime(lerp(timeTween.a, timeTween.b, e)); if (timeTween.t >= 1) timeTween = null; }
  if (fly) {
    fly.t += dt / fly.dur; const e = ease(Math.min(fly.t, 1)), { a, b } = fly;
    applyCam({ x: lerp(a.x, b.x, e), z: lerp(a.z, b.z, e), d: Math.exp(lerp(Math.log(a.d), Math.log(b.d), e)) + Math.sin(Math.PI * e) * fly.bump, h: lerp(a.h, b.h, e), t: lerp(a.t, b.t, e) });
    if (fly.t >= 1) { fly = null; writeHash(); }
  } else {
    if (keys.size) {
      const c = readCam(), sp = c.d * 0.9 * dt, h = c.h * D2R; let f = 0, r = 0;
      if (keys.has('w') || keys.has('arrowup')) f += 1; if (keys.has('s') || keys.has('arrowdown')) f -= 1; if (keys.has('d') || keys.has('arrowright')) r += 1; if (keys.has('a') || keys.has('arrowleft')) r -= 1;
      if (f || r) { const dx = (Math.sin(h) * f + Math.cos(h) * r) * sp, dz = (-Math.cos(h) * f + Math.sin(h) * r) * sp; controls.target.x += dx; controls.target.z += dz; camera.position.x += dx; camera.position.z += dz; }
    }
    controls.target.x = clamp(controls.target.x, -T.BX * 0.8, T.BX * 0.8); controls.target.z = clamp(controls.target.z, -T.BY * 0.8, T.BY * 0.8);
    controls.target.y = Math.max(T.heightAt(controls.target.x, controls.target.z), 0);
    controls.update();
    const g = Math.max(T.heightAt(camera.position.x, camera.position.z), 0) + 25; if (camera.position.y < g) camera.position.y = g;
  }
  if (tour.auto && !fly) { tour.timer += dt; if (tour.timer > (tour.id === 'food' ? 6 : 9)) goStop(tour.i + 1); }
  const c = readCam();
  camera.near = clamp(c.d * 0.02, 4, 120); camera.far = 400000; camera.updateProjectionMatrix();
  // sun shadow frustum follows the view
  if (sun.castShadow) {
    const half = clamp(c.d * 0.8, 350, 4500);
    if (Math.abs(half - shHalf) / half > 0.08) { shHalf = half; const sc = sun.shadow.camera; sc.left = sc.bottom = -half; sc.right = sc.top = half; sc.near = 100; sc.far = 16000; sc.updateProjectionMatrix(); sun.shadow.normalBias = half / Qs.sh * 3.5; }
    sun.target.position.copy(controls.target); sun.position.copy(controls.target).addScaledVector(env.sunDir, 8000);
  }
  if (fc % 6 === 0) {
    streamTick(c);
    const ring = beacon.getObjectByName('ring'); if (beacon.visible) { const s = 1 + 0.25 * Math.sin(U.uTime.value * 2.4) + c.d / 2500; ring.scale.set(s, 1, s); beacon.children[0].scale.set(1 + c.d / 1500, 1, 1 + c.d / 1500); }
    $('#needle').style.transform = `rotate(${-c.h}deg)`;
  }
  if (fc % 15 === 0) updateHud(c);
  updateLabels();
  composer.render();
}
// Build the nearest missing chunk, drop the far ones. One build per call keeps frames smooth on slow devices.
function streamTick(c) {
  const fx = controls.target.x, fz = controls.target.z, R = Math.max(Qs.radius, Math.min(c.d * 1.3, Qs.maxRadius));
  let best = null, bd = R, pendingB = 0, dropped = 0;
  for (const e of stream.b) {
    const d = Math.hypot(e.c[0] - fx, e.c[1] - fz);
    if (!e.mesh) { if (d < R) { pendingB++; if (d < bd) { bd = d; best = e; } } }
    else if (d > R * 1.5 + 700 && dropped < 2) { scene.remove(e.mesh); e.mesh.geometry.dispose(); e.mesh = null; dropped++; }
  }
  if (best && !fly) { best.mesh = buildChunk(man, best.ch, stream.bbuf, stream.bmat, stream.lm.skip); scene.add(best.mesh); }
  else if (best && fc % 18 === 0) { best.mesh = buildChunk(man, best.ch, stream.bbuf, stream.bmat, stream.lm.skip); scene.add(best.mesh); }
  const td = Qs.tree + c.d * 0.25, cx = lerp(fx, camera.position.x, 0.25), cz = lerp(fz, camera.position.z, 0.25), far = c.d > 14000;
  let tb = null, tbd = td;
  for (const e of stream.t) {
    const d = Math.hypot(e.c[0] - cx, e.c[1] - cz);
    if (e.meshes) {
      if (d > td * 1.6 + 500) { for (const m of e.meshes) { scene.remove(m); m.dispose(); } e.meshes = null; }
      else for (const m of e.meshes) m.visible = !far && d < td;
    } else if (!far && d < tbd) { tbd = d; tb = e; }
  }
  if (tb && !best) { tb.meshes = stream.treeOf(tb.ch); for (const m of tb.meshes) scene.add(m); }
  if (fc % 30 === 0) stream.lm.loadNear(fx, fz, Qs.model);
  document.body.classList.toggle('streaming', pendingB > 0);
}
function updateHud(c) {
  const [lon, lat] = T.toLL(c.x, c.z); let best = null, bd = 1e9;
  for (const l of localities) { const d = Math.hypot(l.x - c.x, -l.y - c.z); if (d < bd) { bd = d; best = l; } }
  const w = wardAt(wards, c.x, -c.z);
  place.name = bd < 2500 && best ? ((useMl && best.ml) || best.n) : w ? w.name : T.heightAt(c.x, c.z) <= 0.05 && c.x < 0 ? 'Arabian Sea' : 'Kozhikode district';
  place.ward = w ? `Ward ${w.no} · ${w.name}` : ''; place.lat = lat; place.lon = lon;
  $('#hudName').textContent = place.name + (w ? ` · Ward ${w.no}` : '');
  $('#hudPos').textContent = `${lat.toFixed(4)}° N ${lon.toFixed(4)}° E · eye ${fmtIN(Math.round(camera.position.y))} m`;
}

load().catch((e) => { console.error(e); stage.textContent = 'Could not load the city: ' + e.message; });
