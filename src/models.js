import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// Hand-built landmark models, placed on their real map positions. Shapes are stylised, not surveyed.
const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.8, flatShading: true, ...o });
const add = (g, geo, mat, x = 0, y = 0, z = 0) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; g.add(m); return m; };
// rectangular hipped roof: a 4-sided frustum stretched to w × d
const hip = (w, d, h, top = 0.25) => new THREE.CylinderGeometry(top * Math.SQRT1_2, Math.SQRT1_2, h, 4, 1).rotateY(Math.PI / 4).scale(w, 1, d);

export const lampMat = new THREE.MeshStandardMaterial({ color: 0x332a18, emissive: 0xffd27a, emissiveIntensity: 0 });

function lighthouse() {
  const g = new THREE.Group(), white = M(0xf4f1ea), red = M(0xb5322a);
  add(g, new THREE.CylinderGeometry(3.2, 3.6, 1.2, 16), M(0xc9c2b4), 0, 0.6, 0);
  add(g, new THREE.CylinderGeometry(1.5, 2.2, 14, 16), white, 0, 8, 0);
  add(g, new THREE.CylinderGeometry(1.92, 2.02, 1.6, 16), red, 0, 4.2, 0);
  add(g, new THREE.CylinderGeometry(1.66, 1.76, 1.6, 16), red, 0, 10.6, 0);
  add(g, new THREE.CylinderGeometry(2.3, 2.3, 0.35, 16), M(0x3a3a3a), 0, 15.1, 0);
  add(g, new THREE.CylinderGeometry(1.15, 1.15, 2.2, 10), lampMat, 0, 16.4, 0);
  add(g, new THREE.ConeGeometry(1.5, 1.5, 10), red, 0, 18.2, 0);
  return g;
}

function mishkal() {
  const g = new THREE.Group(), wall = M(0xf2efe6), teal = M(0x3c9d96), tile = M(0x9a4a30), wood = M(0x5b3a26);
  add(g, new THREE.BoxGeometry(27, 0.8, 21), M(0xb9b0a0), 0, 0.4, 0);
  const tiers = [[24, 18, 4.4, wall], [19, 14, 3.4, teal], [14.5, 10.5, 3.2, teal], [10, 7, 3.0, teal]];
  let y = 0.8;
  for (const [w, d, h, m] of tiers) {
    add(g, new THREE.BoxGeometry(w, h, d), m, 0, y + h / 2, 0);
    // timber colonnade band
    add(g, new THREE.BoxGeometry(w + 0.3, 0.35, d + 0.3), wood, 0, y + h - 0.2, 0);
    add(g, hip(w + 4.2, d + 4.2, 1.9, 0.72), tile, 0, y + h + 0.95, 0);
    y += h + 1.3;
  }
  add(g, hip(11.5, 8.5, 2.6, 0.12), tile, 0, y + 1.0, 0);
  return g;
}

function tali() {
  const g = new THREE.Group(), lat = M(0xcdb89a), tile = M(0x8f452e), copper = M(0x7c5a36, { metalness: 0.4, roughness: 0.5 }), gold = M(0xd9a93a, { metalness: 0.7, roughness: 0.35 });
  // nalambalam: the walled cloister
  for (const [x, z, w, d] of [[0, -19, 42, 5], [0, 19, 42, 5], [-18.5, 0, 5, 33], [18.5, 0, 5, 33]]) {
    add(g, new THREE.BoxGeometry(w, 3.4, d), lat, x, 1.7, z);
    add(g, hip(w + 2, d + 2, 2.0, 0.4), tile, x, 4.4, z);
  }
  // sreekovil: two-tier sanctum
  add(g, new THREE.BoxGeometry(11, 4.2, 11), lat, 0, 2.1, 0);
  add(g, hip(15, 15, 2.6, 0.55), copper, 0, 5.5, 0);
  add(g, new THREE.BoxGeometry(7, 2.4, 7), lat, 0, 7.6, 0);
  add(g, hip(10.5, 10.5, 4.2, 0.04), copper, 0, 10.9, 0);
  add(g, new THREE.ConeGeometry(0.35, 1.8, 8), gold, 0, 13.8, 0);
  // gopuram + lamp pillar on the east side
  add(g, new THREE.BoxGeometry(6, 6, 7), lat, 23, 3, 0);
  add(g, hip(8.5, 9.5, 3.2, 0.3), tile, 23, 7.6, 0);
  add(g, new THREE.CylinderGeometry(0.28, 0.4, 8, 8), gold, 30, 4, 0);
  return g;
}

function pier(T, x0, z0, dirx, dirz) {
  const g = new THREE.Group(), iron = M(0x3b332e, { roughness: 0.95 });
  // walk seaward until the terrain turns to water, then plant two rows of broken piles
  let d = 0; while (d < 600 && T.heightAt(x0 + dirx * d, z0 + dirz * d) > 0.05) d += 5;
  const px = -dirz, pz = dirx;
  for (let i = 0; i < 16; i++) for (const s of [-1, 1]) {
    const k = (i * 7 + (s > 0 ? 3 : 0)) % 11, h = 3.5 + (k / 11) * 4.5 - i * 0.12;
    if (k === 5 && i > 3) continue;
    add(g, new THREE.CylinderGeometry(0.42, 0.5, h + 3, 6), iron, x0 + dirx * (d + 6 + i * 7.5) + px * s * 3.2, h / 2 - 1.5, z0 + dirz * (d + 6 + i * 7.5) + pz * s * 3.2);
  }
  return g;
}

function uru() {
  const g = new THREE.Group(), wood = M(0x7a4f2c), dark = M(0x4a301c), pale = M(0xc9a36d);
  const hull = add(g, new THREE.SphereGeometry(1, 14, 8, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2).scale(4.6, 5.2, 17), wood, 0, 7.2, 0);
  hull.material.side = THREE.DoubleSide;
  add(g, new THREE.BoxGeometry(8.4, 0.3, 30), pale, 0, 7.1, 0);
  add(g, new THREE.BoxGeometry(5, 2.6, 6), wood, 0, 8.5, 11);            // stern cabin
  add(g, new THREE.CylinderGeometry(0.22, 0.3, 15, 6), dark, 0, 14.5, -3); // mast
  for (let i = -3; i <= 3; i++) for (const s of [-1, 1]) add(g, new THREE.CylinderGeometry(0.16, 0.16, 6.5, 5), dark, s * (4.2 - Math.abs(i) * 0.25), 3.2, i * 4.2); // props
  for (let i = -2; i <= 2; i++) add(g, new THREE.BoxGeometry(7, 0.5, 0.7), dark, 0, 0.9, i * 5.5); // slipway timbers
  return g;
}

function stadium() {
  const g = new THREE.Group(), conc = M(0xb9b4a8), seat = M(0x3f6f9e), roof = M(0xd8d8d4), sx = 82, sz = 64;
  const pts = [[0.70, 0.6], [0.74, 1.4], [0.98, 11], [1.0, 11], [1.0, 0.6]].map(([r, y]) => new THREE.Vector2(r, y));
  const bowl = add(g, new THREE.LatheGeometry(pts, 56).scale(sx, 1, sz), conc); bowl.material.side = THREE.DoubleSide;
  const tiers = add(g, new THREE.LatheGeometry([new THREE.Vector2(0.745, 1.7), new THREE.Vector2(0.965, 10.6)], 56).scale(sx, 1, sz), seat, 0, 0.15, 0); tiers.material.side = THREE.DoubleSide;
  add(g, new THREE.LatheGeometry([new THREE.Vector2(0.86, 13.5), new THREE.Vector2(1.03, 12.2)], 28, Math.PI * 0.62, Math.PI * 0.76).scale(sx, 1, sz), roof).material.side = THREE.DoubleSide;
  add(g, new THREE.CylinderGeometry(1, 1, 0.3, 48).scale(sx * 0.7, 1, sz * 0.7), M(0x8a7a5e), 0, 0.55, 0);   // track
  add(g, new THREE.BoxGeometry(76, 0.3, 50), M(0x3e8a3c), 0, 0.75, 0);                                       // pitch
  for (const [x, z] of [[-0.78, -0.78], [0.78, -0.78], [-0.78, 0.78], [0.78, 0.78]]) {
    add(g, new THREE.CylinderGeometry(0.5, 0.8, 34, 6), M(0x8d9094), x * sx, 17, z * sz);
    add(g, new THREE.BoxGeometry(7, 4, 1.2), lampMat, x * sx, 35, z * sz).rotation.y = Math.atan2(x, z);
  }
  return g;
}

function planetarium() {
  const g = new THREE.Group(), cream = M(0xe6dfd0), dome = M(0xd9dde0, { roughness: 0.45, flatShading: false });
  add(g, new THREE.CylinderGeometry(13, 13.5, 6, 32), cream, 0, 3, 0);
  add(g, new THREE.SphereGeometry(11.5, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), dome, 0, 6, 0);
  add(g, new THREE.BoxGeometry(30, 7, 14), cream, 22, 3.5, 4);
  add(g, new THREE.BoxGeometry(31, 0.5, 15), M(0xb9b2a4), 22, 7.2, 4);
  return g;
}

// towers: 1 = single tower centred on the front, 2 = twin towers flanking the facade
function church(towers, wallC, trimC) {
  const g = new THREE.Group(), wall = M(wallC), tile = M(0x9a4a30), trim = M(trimC);
  add(g, new THREE.BoxGeometry(12, 9, 30), wall, 0, 4.5, 0);
  add(g, hip(13.5, 31.5, 5, 0.05), tile, 0, 11.5, 0).scale.x = 1;
  add(g, new THREE.BoxGeometry(20, 6, 8), wall, 0, 3, 6);                     // transept
  add(g, hip(21, 9.5, 3, 0.1), tile, 0, 7.5, 6);
  const tw = (x, h) => {
    add(g, new THREE.BoxGeometry(5, h, 5), wall, x, h / 2, -16.5);
    add(g, new THREE.BoxGeometry(5.5, 0.5, 5.5), trim, x, h * 0.62, -16.5);
    add(g, new THREE.BoxGeometry(5.5, 0.5, 5.5), trim, x, h, -16.5);
    add(g, new THREE.ConeGeometry(3.4, 6, 4).rotateY(Math.PI / 4), trim, x, h + 3.2, -16.5);
    add(g, new THREE.BoxGeometry(0.25, 2.2, 0.25), M(0xf2f2f2), x, h + 7.2, -16.5); add(g, new THREE.BoxGeometry(1.2, 0.25, 0.25), M(0xf2f2f2), x, h + 7.5, -16.5);
  };
  if (towers === 1) tw(0, 20); else { tw(-6.5, 19); tw(6.5, 19); add(g, new THREE.BoxGeometry(9, 13, 3), wall, 0, 6.5, -16); add(g, hip(9.5, 3.5, 3, 0.05), trim, 0, 14.5, -16); }
  return g;
}

export function buildLandmarks(T, placed = []) {
  const g = new THREE.Group(), skips = [];
  const place = (obj, lon, lat, rot = 0, clear = 0) => {
    const [x, z] = T.ll(lon, lat); obj.position.set(x, Math.max(T.heightAt(x, z), 0.4), z); obj.rotation.y = rot; g.add(obj);
    if (clear) skips.push([x, z, clear]);
    return obj;
  };
  place(lighthouse(), 75.76922, 11.25841, 0, 9);
  place(planetarium(), 75.78575, 11.2633, 0, 30);
  place(church(1, 0xf1ede2, 0x8c3b2e), 75.78029, 11.26264, Math.PI / 2, 20);
  place(church(2, 0xf3ead6, 0x9b5a3c), 75.77429, 11.25292, Math.PI / 2, 22);
  { const l = place(lighthouse(), 75.80589, 11.15824, 0, 10); l.scale.setScalar(1.7); }
  place(stadium(), 75.78585, 11.25650, 0.35, 78);
  { const [x, z] = T.ll(75.7712, 11.2548); g.add(pier(T, x, z, -0.94, 0.34)); }
  { const [x, z] = T.ll(75.7701, 11.2600); g.add(pier(T, x, z, -0.94, 0.34)); }
  { // uru on the Beypore shore: find the bank south of the yard
    let [x, z] = T.ll(75.8068, 11.1672), d = 0; while (d < 500 && T.heightAt(x, z + d) > 0.05) d += 5;
    const u = uru(); u.position.set(x, 0.6, z + d - 26); u.rotation.y = 0.5; g.add(u); skips.push([x, z + d - 26, 22]);
  }
  // buildings modelled in Blender from photo reference (pipeline/blender_models.py), set on their mapped footprints
  const loader = new GLTFLoader();
  for (const b of placed) {
    skips.push([b.x, -b.n, b.rx, b.rz]);
    if (!b.f) continue;
    loader.load(b.f, (gl) => {
      const o = gl.scene; o.position.set(b.x, (b.y ?? Math.max(T.heightAt(b.x, -b.n), 0.4)) + 0.05, -b.n); o.rotation.y = b.deg * Math.PI / 180;
      o.traverse((m) => { if (m.isMesh) { m.castShadow = m.receiveShadow = true; m.material.side = THREE.DoubleSide; } });
      if (b.drape) {   // long street-level scenes follow the ground instead of sitting on one flat plane
        o.position.y = 0;
        o.traverse((m) => {
          if (!m.isMesh) return; const p = m.geometry.attributes.position;
          for (let i = 0; i < p.count; i++) p.setY(i, p.getY(i) + Math.max(T.heightAt(p.getX(i) + b.x, p.getZ(i) - b.n), b.y - 1.5) + 0.05);
          p.needsUpdate = true; m.geometry.computeBoundingSphere(); m.geometry.computeBoundingBox();
        });
      }
      g.add(o);
    });
  }
  const skip = (x, z) => { for (const [sx, sz, r, r2] of skips) if (Math.abs(x - sx) < r && Math.abs(z - sz) < (r2 ?? r)) return true; return false; };
  const nearModel = (x, z) => { for (const [sx, sz, r, r2] of skips) if (Math.abs(x - sx) < r + 9 && Math.abs(z - sz) < (r2 ?? r) + 9) return true; return false; };
  return { group: g, skip, nearModel };
}
