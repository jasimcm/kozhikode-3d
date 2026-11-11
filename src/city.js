import * as THREE from 'three';

const srgb = (v) => Math.round(Math.pow(v / 255, 2.2) * 255);

// ------------------------------------------------------------------ terrain
export class Terrain {
  constructor(man, core, back) {
    this.m = man; this.HX = man.halfX; this.HY = man.halfY;
    this.core = new Uint16Array(core); this.back = new Uint16Array(back);
    [this.gw, this.gh] = man.grid; [this.bw, this.bh] = man.gridBack;
    this.BX = man.back[2]; this.BY = man.back[3];
  }
  _s(g, w, h, u, v) {
    u = Math.min(Math.max(u, 0), w - 1.001); v = Math.min(Math.max(v, 0), h - 1.001);
    const i = u | 0, j = v | 0, fx = u - i, fy = v - j, k = j * w + i;
    return ((g[k] * (1 - fx) + g[k + 1] * fx) * (1 - fy) + (g[k + w] * (1 - fx) + g[k + w + 1] * fx) * fy) / 10 - 100;
  }
  inCore(x, z) { return Math.abs(x) < this.HX && Math.abs(z) < this.HY; }
  heightAt(x, z) {
    if (this.inCore(x, z)) return this._s(this.core, this.gw, this.gh, (x + this.HX) / (2 * this.HX) * (this.gw - 1), (z + this.HY) / (2 * this.HY) * (this.gh - 1));
    return this._s(this.back, this.bw, this.bh, (x + this.BX) / (2 * this.BX) * (this.bw - 1), (z + this.BY) / (2 * this.BY) * (this.bh - 1));
  }
  ll(lon, lat) { return [(lon - this.m.center[0]) * this.m.mx, -(lat - this.m.center[1]) * this.m.my]; }
  toLL(x, z) { return [this.m.center[0] + x / this.m.mx, this.m.center[1] - z / this.m.my]; }
}

function groundMaterial(U, sat, isBack) {
  const mat = new THREE.MeshStandardMaterial({ map: sat, roughness: 0.96, metalness: 0 });
  mat.onBeforeCompile = (s) => {
    Object.assign(s.uniforms, U, { uIsBack: { value: isBack ? 1 : 0 } });
    s.vertexShader = s.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec2 vGUv; varying vec3 vWPos;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvGUv = uv; vWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    s.fragmentShader = s.fragmentShader
      .replace('#include <common>', `#include <common>
        varying vec2 vGUv; varying vec3 vWPos;
        uniform sampler2D uMask, uMask2, uSea; uniform float uTime, uNight, uIsBack; uniform vec3 uSkyCol; uniform vec2 uHalf;
        float gWater; float gRoad;`)
      .replace('#include <map_fragment>', `#include <map_fragment>
        if (uIsBack > 0.5 && abs(vWPos.x) < uHalf.x && abs(vWPos.z) < uHalf.y) discard;
        vec3 gm = uIsBack > 0.5 ? vec3(0.0) : texture2D(uMask, vGUv).rgb;
        vec3 gm2 = uIsBack > 0.5 ? vec3(0.0) : texture2D(uMask2, vGUv).rgb;
        float sea = uIsBack > 0.5 ? texture2D(uSea, vGUv).r : 0.0;
        gWater = smoothstep(0.35, 0.65, max(gm.g, sea));
        gRoad = gm.r * (1.0 - gWater);
        vec3 gb = diffuseColor.rgb;
        float gl = dot(gb, vec3(0.3, 0.6, 0.1));
        gb = mix(vec3(gl), gb, 1.25) * 1.9 + 0.012;
        gb *= 1.0 - 0.38 * gm2.g;
        gb = mix(gb, vec3(0.2, 0.19, 0.17), gRoad * 0.45);
        gb = mix(gb, vec3(0.2, 0.17, 0.15), gm2.r * 0.4 * (1.0 - gWater));
        vec3 wc = mix(vec3(0.010, 0.085, 0.105), diffuseColor.rgb * 1.6, 0.22);
        gb = mix(gb, wc, gWater);
        diffuseColor.rgb = gb;`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.2, gWater);')
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        if (gWater > 0.01) {
          vec2 p = vWPos.xz; float t = uTime;
          float fd = 1.0 / (1.0 + length(vViewPosition) * 0.0009);
          vec2 w = vec2(0.0);
          w += 0.030 * vec2(0.8, 0.6) * cos(dot(p, vec2(0.8, 0.6)) * 0.071 + t * 0.9);
          w += 0.026 * vec2(0.35, -0.94) * cos(dot(p, vec2(0.35, -0.94)) * 0.163 + t * 1.1);
          w += 0.034 * vec2(-0.5, 0.86) * cos(dot(p, vec2(-0.5, 0.86)) * 0.11 + t * 1.3);
          w += 0.04 * vec2(0.95, -0.3) * cos(dot(p, vec2(0.95, -0.3)) * 0.23 + t * 1.9);
          w += 0.045 * vec2(0.2, 0.98) * cos(dot(p, vec2(0.2, 0.98)) * 0.47 + t * 2.6);
          vec3 wn = normalize(vec3(w.x * fd * 1.6, 1.0, w.y * fd * 1.6));
          normal = normalize(mix(normal, normalize((viewMatrix * vec4(wn, 0.0)).xyz), gWater));
        }`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        float fres = pow(1.0 - clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0), 3.0);
        totalEmissiveRadiance += gWater * uSkyCol * (0.06 + 0.62 * fres);
        totalEmissiveRadiance += gRoad * vec3(1.0, 0.58, 0.24) * uNight * 0.12;`);
  };
  return mat;
}

export function buildGround(T, tex, U) {
  const g = new THREE.Group();
  const mk = (w, h, gw, gh, grid, sat, isBack) => {
    const geo = new THREE.PlaneGeometry(w, h, gw - 1, gh - 1); geo.rotateX(-Math.PI / 2);
    const p = geo.attributes.position;
    for (let k = 0; k < p.count; k++) p.setY(k, grid[k] / 10 - 100);
    geo.computeVertexNormals();
    const mesh = new THREE.Mesh(geo, groundMaterial(U, sat, isBack));
    mesh.receiveShadow = !isBack; return mesh;
  };
  g.add(mk(2 * T.HX, 2 * T.HY, T.gw, T.gh, T.core, tex.satCore, false));
  g.add(mk(2 * T.BX, 2 * T.BY, T.bw, T.bh, T.back, tex.satBack, true));
  // open sea beyond the backdrop
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(400000, 500000).rotateX(-Math.PI / 2),
    new THREE.MeshStandardMaterial({ color: 0x083642, roughness: 0.3 }));
  sea.position.set(-T.BX - 200000 + 50, -0.5, 0); g.add(sea);
  return g;
}

// ------------------------------------------------------------------ buildings
const WALLS = [0xd9d2c4, 0xcfc6b4, 0xe2d8bd, 0xc9b8a0, 0xbfc8ba, 0xb9c6cc, 0xd8c4bb, 0xc4beb4, 0xe6e0d4, 0xcbb391, 0xaab2b6, 0xbfa08a, 0xddd3c0, 0xb8ad9c]
  .map((c) => [srgb(c >> 16), srgb((c >> 8) & 255), srgb(c & 255)]);

export function buildingMaterial(U) {
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, flatShading: true, roughness: 0.88, metalness: 0, side: THREE.DoubleSide });
  mat.onBeforeCompile = (s) => {
    Object.assign(s.uniforms, U);
    s.vertexShader = s.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec2 aBU; varying vec2 vBU;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvBU = aBU;');
    s.fragmentShader = s.fragmentShader
      .replace('#include <common>', `#include <common>
        varying vec2 vBU; uniform float uNight; float bWin; float bGlow;
        float bh(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
        float isWall = step(vBU.x, 60000.0);
        float hasWin = step(vBU.x, 29999.0);
        vec2 wuv = vec2(vBU.x * 0.1 / 3.4, vBU.y * 0.1 / 2.9);
        vec2 wc = floor(wuv), wf = fract(wuv);
        float lod = 1.0 - smoothstep(0.22, 0.6, fwidth(wuv.x) + fwidth(wuv.y));
        float sd0 = dot(vColor.rgb, vec3(37.1, 91.7, 53.3));
        float sd = bh(wc + sd0);
        float win = step(0.28, wf.x) * step(wf.x, 0.72) * step(0.38, wf.y) * step(wf.y, 0.76) * hasWin * step(0.22, bh(wc.yx * 1.7 + sd0));
        bWin = win * lod;
        bGlow = isWall * mix(0.05, mix(0.2 * 0.3, win * step(sd, 0.34) * (0.6 + 0.6 * bh(wc.yx + sd)), lod), hasWin);
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.06, 0.075, 0.09), bWin * 0.6);
        // weathering: darker toward the ground, faint vertical streaks
        diffuseColor.rgb *= isWall > 0.5 ? 0.9 + 0.1 * bh(vec2(floor(vBU.x * 0.02), sd0)) : 1.0;
        diffuseColor.rgb *= isWall > 0.5 ? mix(0.82, 1.0, smoothstep(0.0, 4.0, vBU.y * 0.1)) : 1.0;`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.18, bWin);')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += bGlow * uNight * vec3(1.0, 0.7, 0.36) * 2.2;');
  };
  return mat;
}

const _v2 = [];
export function buildChunk(man, ch, buf, mat, skip) {
  const N = ch.n, V = ch.v, o = ch.o, Q = man.q, C = man.chunk;
  const cnt = new Uint8Array(buf, o, N), hts = new Uint8Array(buf, o + N, N), flg = new Uint8Array(buf, o + 2 * N, N), col = new Uint8Array(buf, o + 3 * N, 3 * N);
  const base = new Int16Array(buf.slice(o + 6 * N, o + 8 * N)), vr = new Int16Array(buf.slice(o + 8 * N, o + 8 * N + 4 * V));
  const ox = -man.halfX + (ch.i + 0.5) * C, oy = -man.halfY + (ch.j + 0.5) * C;
  let tv = 0, ti = 0;
  for (let b = 0; b < N; b++) { const n = cnt[b], pit = (flg[b] & 7) === 1; tv += (n + 1) * 2 + n + (pit ? (n === 4 ? 2 : n) : 0); ti += n * 6 + (pit ? (n === 4 ? 18 : n * 6 + (n - 2) * 3) : (n - 2) * 3); }
  const pos = new Float32Array(tv * 3), cl = new Uint8Array(tv * 3), bu = new Uint16Array(tv * 2), idx = new Uint32Array(ti);
  let v = 0, k = 0, r = 0, maxH = 0;
  for (let b = 0; b < N; b++) {
    const n = cnt[b], h = hts[b] * 0.5, f = flg[b], style = f & 7, seed = f >> 3, y0 = base[b] / 10, r0 = r; r += n;
    if (skip) { let sx = 0, sy = 0; for (let i = 0; i < n; i++) { sx += vr[(r0 + i) * 2]; sy += vr[(r0 + i) * 2 + 1]; } if (skip(ox + sx / n * Q, -(oy + sy / n * Q))) continue; }
    let wc = WALLS[seed % WALLS.length];
    if (h > 24) wc = [srgb(150 + seed * 2), srgb(165 + seed * 2), srgb(178 + seed * 2)];
    else if (style === 2) wc = [srgb(170), srgb(172), srgb(170)];
    const yb = y0 - 4, yt = y0 + h; if (yt > maxH) maxH = yt;
    // walls
    let u = 0; const w0 = v;
    for (let i = 0; i <= n; i++) {
      const a = r0 + (i % n), x = vr[a * 2] * Q, z = -vr[a * 2 + 1] * Q;
      if (i > 0) { const p = r0 + i - 1; u += Math.hypot(x - vr[p * 2] * Q, z + vr[p * 2 + 1] * Q); }
      const uu = Math.min(Math.round(u * 10), 29000) + (h < 7.5 ? 30000 : 0);
      pos.set([x, yb, z, x, yt, z], v * 3); cl.set(wc, v * 3); cl.set(wc, v * 3 + 3);
      bu[v * 2] = uu; bu[v * 2 + 1] = 0; bu[v * 2 + 2] = uu; bu[v * 2 + 3] = Math.round((h + 4) * 10);
      // v coordinate counts from 4 m below ground so floors line up at ground level
      bu[v * 2 + 1] = 0; v += 2;
    }
    for (let i = 0; i < n; i++) { const a = w0 + i * 2; idx.set([a, a + 1, a + 2, a + 1, a + 3, a + 2], k); k += 6; }
    // roof
    const rc = [srgb(col[b * 3]), srgb(col[b * 3 + 1]), srgb(col[b * 3 + 2])], t0 = v;
    for (let i = 0; i < n; i++) { const a = r0 + i; pos.set([vr[a * 2] * Q, yt, -vr[a * 2 + 1] * Q], v * 3); cl.set(rc, v * 3); bu[v * 2] = 65535; v++; }
    if (style === 1 && n === 4) {
      const P = (i) => [pos[(t0 + i) * 3], pos[(t0 + i) * 3 + 2]];
      const [a, b1, c, d] = [P(0), P(1), P(2), P(3)];
      const l0 = Math.hypot(b1[0] - a[0], b1[1] - a[1]), l1 = Math.hypot(c[0] - b1[0], c[1] - b1[1]);
      const sh = l0 >= l1 ? 0 : 1; // sh=0: long edges are 0-1 and 2-3
      const q = [0, 1, 2, 3].map((i) => (i + sh) % 4), S = Math.min(l0, l1), ry = yt + Math.min(S * 0.32, 2.8);
      const mid = (i, j) => { const A = P(q[i]), B = P(q[j]); return [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2]; };
      const mA = mid(1, 2), mB = mid(3, 0), ins = 0.22;
      const rA = [mA[0] + (mB[0] - mA[0]) * ins, mA[1] + (mB[1] - mA[1]) * ins], rB = [mB[0] + (mA[0] - mB[0]) * ins, mB[1] + (mA[1] - mB[1]) * ins];
      pos.set([rA[0], ry, rA[1], rB[0], ry, rB[1]], v * 3); cl.set(rc, v * 3); cl.set(rc, v * 3 + 3); bu[v * 2] = 65535; bu[v * 2 + 2] = 65535;
      const A = v, B = v + 1, p = q.map((i) => t0 + i); v += 2;
      idx.set([p[0], p[1], A, p[0], A, B, p[2], p[3], B, p[2], B, A, p[1], p[2], A, p[3], p[0], B], k); k += 18;
    } else if (style === 1) {
      // hipped roof for any footprint: an inner ring pulled toward the centroid and raised
      let cx = 0, cz = 0; for (let i = 0; i < n; i++) { cx += pos[(t0 + i) * 3]; cz += pos[(t0 + i) * 3 + 2]; } cx /= n; cz /= n;
      let rm = 0; for (let i = 0; i < n; i++) rm += Math.hypot(pos[(t0 + i) * 3] - cx, pos[(t0 + i) * 3 + 2] - cz); rm /= n;
      const ry = yt + Math.min(rm * 0.42, 2.9), i0 = v;
      for (let i = 0; i < n; i++) { pos.set([cx + (pos[(t0 + i) * 3] - cx) * 0.3, ry, cz + (pos[(t0 + i) * 3 + 2] - cz) * 0.3], v * 3); cl.set(rc, v * 3); bu[v * 2] = 65535; v++; }
      for (let i = 0; i < n; i++) { const j = (i + 1) % n; idx.set([t0 + i, t0 + j, i0 + j, t0 + i, i0 + j, i0 + i], k); k += 6; }
      if (n === 3) { idx.set([i0, i0 + 1, i0 + 2], k); k += 3; }
      else { _v2.length = 0; for (let i = 0; i < n; i++) _v2.push(new THREE.Vector2(vr[(r0 + i) * 2], vr[(r0 + i) * 2 + 1])); for (const t of THREE.ShapeUtils.triangulateShape(_v2, [])) { idx[k++] = i0 + t[0]; idx[k++] = i0 + t[1]; idx[k++] = i0 + t[2]; } }
    } else if (n === 3) { idx.set([t0, t0 + 1, t0 + 2], k); k += 3; }
    else {
      _v2.length = 0; for (let i = 0; i < n; i++) _v2.push(new THREE.Vector2(vr[(r0 + i) * 2], vr[(r0 + i) * 2 + 1]));
      const tris = THREE.ShapeUtils.triangulateShape(_v2, []);
      for (const t of tris) { idx[k++] = t0 + t[0]; idx[k++] = t0 + t[1]; idx[k++] = t0 + t[2]; }
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos.subarray(0, v * 3), 3));
  geo.setAttribute('color', new THREE.BufferAttribute(cl.subarray(0, v * 3), 3, true));
  geo.setAttribute('aBU', new THREE.BufferAttribute(bu.subarray(0, v * 2), 2));
  geo.setIndex(new THREE.BufferAttribute(idx.subarray(0, k), 1));
  geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, maxH / 2, 0), C * 0.95 + maxH);
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(ox, 0, -oy); mesh.castShadow = mesh.receiveShadow = true; mesh.matrixAutoUpdate = false; mesh.updateMatrix();
  return mesh;
}

// ------------------------------------------------------------------ trees
function merged(parts) {
  parts = parts.map(([g, c]) => [g.index ? g.toNonIndexed() : g, c]);
  let n = 0; for (const [g] of parts) n += g.attributes.position.count;
  const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), col = new Float32Array(n * 3); let o = 0;
  for (const [g, c] of parts) {
    g.computeVertexNormals();
    pos.set(g.attributes.position.array, o * 3); nor.set(g.attributes.normal.array, o * 3);
    const cc = new THREE.Color(c); for (let i = 0; i < g.attributes.position.count; i++) col.set([cc.r, cc.g, cc.b], (o + i) * 3);
    o += g.attributes.position.count;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); out.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return out;
}
function treeGeos() {
  const blob = merged([
    [new THREE.IcosahedronGeometry(1, 0).scale(1, 0.78, 1).translate(0, 1.55, 0), 0x2f6230],
    [new THREE.IcosahedronGeometry(0.62, 0).scale(1, 0.8, 1).rotateY(1).translate(0.55, 1.15, 0.3), 0x285728],
    [new THREE.CylinderGeometry(0.09, 0.13, 1.0, 4).translate(0, 0.5, 0), 0x4a3828],
  ]);
  const parts = [[new THREE.CylinderGeometry(0.14, 0.24, 9, 4).translate(0, 4.5, 0), 0x6e5a44]];
  for (let i = 0; i < 7; i++) {
    const a = (i / 7) * Math.PI * 2 + (i % 2) * 0.2, w = 0.75, drop = 1.2 + (i % 3) * 0.5;
    const f = new THREE.BufferGeometry();
    f.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
      0, 9, -0.15, 0, 9, 0.15, 2.6, 9.5, w, 0, 9, -0.15, 2.6, 9.5, w, 2.6, 9.5, -w,
      2.6, 9.5, -w, 2.6, 9.5, w, 4.8, 9.4 - drop, 0]), 3));
    parts.push([f.rotateY(a), i % 2 ? 0x4d8a3a : 0x437c35]);
  }
  return [blob, merged(parts)];
}

export function buildTrees(man, T, clear) {
  const [gBlob, gPalm] = treeGeos(), Q = man.q, C = man.chunk;
  const mat = new THREE.MeshLambertMaterial({ vertexColors: true, side: THREE.DoubleSide });
  const m4 = new THREE.Matrix4(), qt = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), sc = new THREE.Vector3(), ps = new THREE.Vector3(), c = new THREE.Color();
  // returns a builder so tree chunks can be created (and thrown away) on demand as the camera moves
  return (ch, buf) => {
    const out = [];
    const n = ch.n, xy = new Int16Array(buf.slice(ch.o, ch.o + 4 * n)), sz = new Uint8Array(buf, ch.o + 4 * n, n), kd = new Uint8Array(buf, ch.o + 5 * n, n);
    const ox = -man.halfX + (ch.i + 0.5) * C, oz = -(-man.halfY + (ch.j + 0.5) * C);
    let np = 0; for (let i = 0; i < n; i++) np += kd[i];
    const meshes = [new THREE.InstancedMesh(gBlob, mat, n - np), new THREE.InstancedMesh(gPalm, mat, np)], ct = [0, 0];
    for (let i = 0; i < n; i++) {
      const x = ox + xy[i * 2] * Q, z = oz - xy[i * 2 + 1] * Q, s = sz[i] / 255, k = kd[i];
      const scl = k ? 0.75 + s * 0.55 : 3.4 + s * 4.6;
      ps.set(x, T.heightAt(x, z) - 0.2, z); qt.setFromAxisAngle(up, s * 40); sc.set(scl, scl * (0.9 + ((i * 7) % 10) / 40), scl);
      if (clear && clear(x, z)) sc.set(0, 0, 0);
      meshes[k].setMatrixAt(ct[k], m4.compose(ps, qt, sc));
      const t = 0.78 + ((i * 13) % 17) / 40; meshes[k].setColorAt(ct[k], c.setRGB(t, t * (0.95 + s * 0.12), t * 0.9)); ct[k]++;
    }
    for (const m of meshes) {
      if (!m.count) continue;
      m.instanceMatrix.needsUpdate = true; m.computeBoundingSphere(); m.matrixAutoUpdate = false; m.frustumCulled = true;
      m.userData.c = new THREE.Vector2(ox, oz); out.push(m);
    }
    return out;
  };
}

// ------------------------------------------------------------------ roads (crisp ribbons draped on the terrain)
const ROAD_COL = { 0: 0x6e7278, 1: 0x74777b, 2: 0x7c7e79, 3: 0x82837c, 4: 0x8b8a83, 5: 0xa39a88, 9: 0x5a524b };
// Elevated stretches the map data does not flag as bridges: centre (east, north), flat radius, ramp length, deck height (m)
const FLYOVERS = [{ x: 4300, n: 2715, r: 290, ramp: 150, h: 7.5 }];
function flyH(x, z) {
  let e = 0;
  for (const f of FLYOVERS) { const t = Math.min(Math.max(1 - (Math.hypot(x - f.x, z + f.n) - f.r) / f.ramp, 0), 1); e = Math.max(e, f.h * t * t * (3 - 2 * t)); }
  return e;
}
export function buildRoads(roads, T, U) {
  const pos = [], col = [], uv = [], idx = [], c = new THREE.Color(), fp = [], fi = [];
  const quad = (a, b, c2, d) => { const k = fp.length / 3; fp.push(...a, ...b, ...c2, ...d); fi.push(k, k + 1, k + 2, k, k + 2, k + 3); };
  for (const r of roads) {
    // subdivide so the ribbon follows the ground
    const P = []; const p = r.p;
    for (let i = 0; i + 1 < p.length; i += 2) {
      const x = p[i], z = -p[i + 1];
      if (P.length) { const [px, pz] = P[P.length - 1], L = Math.hypot(x - px, z - pz), n = Math.ceil(L / 22); for (let k = 1; k < n; k++) P.push([px + (x - px) * k / n, pz + (z - pz) * k / n]); }
      P.push([x, z]);
    }
    if (P.length < 2) continue;
    c.set(ROAD_COL[r.c] ?? 0x6d6c66);
    const hw = r.w / 2, lift = r.c === 9 ? 1.25 : 1.1 - r.c * 0.06, base = pos.length / 3, major = r.c <= 1 ? 1 : r.c === 9 ? 2 : 0; let run = 0;
    const prevEdge = { '-1': null, 1: null }; let prevRun = 0;
    for (let i = 0; i < P.length; i++) {
      const a = P[Math.max(i - 1, 0)], b = P[Math.min(i + 1, P.length - 1)], q = P[i];
      let dx = b[0] - a[0], dz = b[1] - a[1]; const L = Math.hypot(dx, dz) || 1; dx /= L; dz /= L;
      if (i) run += Math.hypot(q[0] - P[i - 1][0], q[1] - P[i - 1][1]);
      const el = r.c === 0 ? flyH(q[0], q[1]) : 0, gy = Math.max(T.heightAt(q[0], q[1]), 0.2);
      for (const s of [-1, 1]) {
        const x = q[0] - dz * hw * s, z = q[1] + dx * hw * s;
        const y = el > 0.3 ? gy + lift + el : Math.max(T.heightAt(x, z), gy) + lift;
        pos.push(x, y, z); col.push(c.r, c.g, c.b); uv.push(s > 0 ? 1 : 0, run, major);
        if (el > 0.3) {   // deck edge: parapet above, girder face below
          const pv = prevEdge[s]; if (pv) quad([pv[0], pv[1] + 1.0, pv[2]], [x, y + 1.0, z], [x, y - 1.4, z], [pv[0], pv[1] - 1.4, pv[2]]);
          prevEdge[s] = [x, y, z];
        } else prevEdge[s] = null;
      }
      if (el > 0.3 && i) {   // deck underside, and a pier every ~30 m where the deck is high enough
        const k = pos.length / 3; quad([pos[(k - 4) * 3], pos[(k - 4) * 3 + 1] - 1.4, pos[(k - 4) * 3 + 2]], [pos[(k - 3) * 3], pos[(k - 3) * 3 + 1] - 1.4, pos[(k - 3) * 3 + 2]], [pos[(k - 1) * 3], pos[(k - 1) * 3 + 1] - 1.4, pos[(k - 1) * 3 + 2]], [pos[(k - 2) * 3], pos[(k - 2) * 3 + 1] - 1.4, pos[(k - 2) * 3 + 2]]);
        if (el > 3 && Math.floor(run / 30) !== Math.floor(prevRun / 30)) {
          const w = 1.3, y0 = gy - 1, y1 = gy + lift + el - 1.4, X = q[0], Z = q[1];
          for (const [ax, az, bx, bz] of [[-w, -w, w, -w], [w, -w, w, w], [w, w, -w, w], [-w, w, -w, -w]]) quad([X + ax, y1, Z + az], [X + bx, y1, Z + bz], [X + bx, y0, Z + bz], [X + ax, y0, Z + az]);
          quad([X - 3.4, y1, Z - 3.4], [X + 3.4, y1, Z - 3.4], [X + 3.4, y1 - 0.01, Z + 3.4], [X - 3.4, y1 - 0.01, Z + 3.4]);
        }
      }
      prevRun = run;
      if (i) { const k = base + (i - 1) * 2; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); }
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.setAttribute('aRU', new THREE.Float32BufferAttribute(uv, 3));
  g.setIndex(idx);
  const nrm = new Float32Array(pos.length); for (let i = 1; i < nrm.length; i += 3) nrm[i] = 1; g.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9, side: THREE.FrontSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  mat.onBeforeCompile = (s) => {
    Object.assign(s.uniforms, U);
    s.vertexShader = s.vertexShader.replace('#include <common>', '#include <common>\nattribute vec3 aRU; varying vec3 vRU;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvRU = aRU;');
    s.fragmentShader = s.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vRU; uniform float uNight;')
      .replace('#include <color_fragment>', `#include <color_fragment>
        float aa = fwidth(vRU.x) * 1.5;
        float edge = smoothstep(0.0, aa, vRU.x) * smoothstep(0.0, aa, 1.0 - vRU.x);
        diffuseColor.rgb *= mix(0.72, 1.0, edge);
        float fade = 1.0 - smoothstep(0.02, 0.07, fwidth(vRU.y) / 12.0 + fwidth(vRU.x));
        float dash = step(abs(vRU.x - 0.5), 0.022) * step(fract(vRU.y / 12.0), 0.5) * step(abs(vRU.z - 1.0), 0.1);
        float sideLine = (step(abs(vRU.x - 0.07), 0.012) + step(abs(vRU.x - 0.93), 0.012)) * step(abs(vRU.z - 1.0), 0.1);
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.78, 0.76, 0.68), (dash + sideLine * 0.6) * fade);
        float ties = step(fract(vRU.y / 1.4), 0.4) * step(abs(vRU.z - 2.0), 0.1) * fade;
        float rails = (step(abs(vRU.x - 0.3), 0.04) + step(abs(vRU.x - 0.7), 0.04)) * step(abs(vRU.z - 2.0), 0.1) * fade;
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.2, 0.17, 0.15), ties * 0.5);
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.55, 0.56, 0.58), rails);`)
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += vec3(1.0, 0.58, 0.24) * uNight * (vRU.z > 1.5 ? 0.02 : 0.5) * diffuseColor.rgb * 4.0;');
  };
  const m = new THREE.Mesh(g, mat); m.receiveShadow = true; m.frustumCulled = false; m.renderOrder = 1;
  const fg = new THREE.BufferGeometry(); fg.setAttribute('position', new THREE.Float32BufferAttribute(fp, 3)); fg.setIndex(fi);
  const fm = new THREE.Mesh(fg, new THREE.MeshStandardMaterial({ color: 0xb4b1a9, roughness: 0.9, flatShading: true, side: THREE.DoubleSide }));
  fm.castShadow = fm.receiveShadow = true; fm.frustumCulled = false;
  const grp = new THREE.Group(); grp.add(m, fm); return grp;
}

// ------------------------------------------------------------------ street lamps
export function buildLamps(roads, T) {
  const pts = [];
  for (const r of roads) {
    if (r.c > 2) continue; const p = r.p; let carry = 0; const step = r.c === 2 ? 60 : 42;
    for (let i = 0; i + 3 < p.length; i += 2) {
      const ax = p[i], ay = p[i + 1], bx = p[i + 2], by = p[i + 3], L = Math.hypot(bx - ax, by - ay);
      for (let d = carry; d < L; d += step) { const x = ax + (bx - ax) * d / L, z = -(ay + (by - ay) * d / L); if (T.inCore(x, z)) pts.push(x, T.heightAt(x, z) + 9, z); }
      carry = (carry - L) % step; if (carry < 0) carry += step;
    }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  const m = new THREE.PointsMaterial({ color: 0xffb060, size: 26, sizeAttenuation: true, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending });
  const o = new THREE.Points(g, m); o.frustumCulled = false; o.visible = false; return o;
}

// ------------------------------------------------------------------ wards
export function buildWards(wards, T) {
  const pts = [];
  for (const w of wards) for (const r of w.r) for (let i = 0; i + 3 < r.length; i += 2) {
    const ax = r[i], az = -r[i + 1], bx = r[i + 2], bz = -r[i + 3], L = Math.hypot(bx - ax, bz - az), n = Math.max(1, Math.ceil(L / 60));
    for (let s = 0; s < n; s++) {
      const x0 = ax + (bx - ax) * s / n, z0 = az + (bz - az) * s / n, x1 = ax + (bx - ax) * (s + 1) / n, z1 = az + (bz - az) * (s + 1) / n;
      pts.push(x0, Math.max(T.heightAt(x0, z0), 0) + 14, z0, x1, Math.max(T.heightAt(x1, z1), 0) + 14, z1);
    }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  const o = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xffb347, transparent: true, opacity: 0.85, depthTest: false }));
  o.renderOrder = 5; o.visible = false; o.frustumCulled = false; return o;
}
export function wardAt(wards, x, y) {
  for (const w of wards) for (const r of w.r) {
    let inside = false;
    for (let i = 0, j = r.length - 2; i < r.length; j = i, i += 2)
      if ((r[i + 1] > y) !== (r[j + 1] > y) && x < (r[j] - r[i]) * (y - r[i + 1]) / (r[j + 1] - r[i + 1]) + r[i]) inside = !inside;
    if (inside) return w;
  }
  return null;
}
