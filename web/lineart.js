// Line-art look of the beetlebug.org explode viewer: flat matte fills, dark edge lines on top,
// an accent on the parts of the current step. The viewer (viewer.html) and the image renderer
// (bittle_pi_addon/iso/render.js) both use this file, so the site and the documents look the same.
import * as THREE from "three";

export const EDGE_DEG = 28;

// Fill colors by finish: printed, bought, dark (the robot), clear.
export const THEMES = {
  light: {
    print: "#f3f3ef", buy: "#c3c7ca", dark: "#4a4f55", clear: "#d9eef2",
    ink: "#16181a", inkOpacity: 0.55, accent: "#0a7f63", mix: 0.22,
    bg: "#fbfbf9", grid: "#ecece6", tagBg: "#fbfbf9",
  },
  dark: {
    print: "#3a4144", buy: "#5c6468", dark: "#22272a", clear: "#2c4a52",
    ink: "#eceeed", inkOpacity: 0.5, accent: "#3fd1a6", mix: 0.5,
    bg: "#0f1112", grid: "rgba(236,238,237,0.04)", tagBg: "#0f1112",
  },
};

/** Hemisphere light, and a key light that moves with the camera. */
export function addLights(scene, camera) {
  const hemi = new THREE.HemisphereLight(0xffffff, 0xb0b0b0, 2.6);
  // The site turns its Y-up models to Z-up and keeps the light at +Y. In this Y-up frame that is -Z (the head end).
  hemi.position.set(0, 0, -1);
  scene.add(hemi);
  const key = new THREE.DirectionalLight(0xffffff, 1.8);
  key.position.set(1, -2, 3);
  camera.add(key);
  scene.add(camera);
}

/** A mesh with its edge lines as a child. */
export function partMesh(geo) {
  const mat = new THREE.MeshStandardMaterial({
    roughness: 0.75, metalness: 0, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
  });
  const mesh = new THREE.Mesh(geo, mat);
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo, EDGE_DEG), new THREE.LineBasicMaterial({ transparent: true }));
  mesh.add(edges);
  return { mesh, edges };
}

/**
 * Set the look of one part.
 * finish: print | buy | dark | clear. focus: the part moves in this step (accent).
 * ghost: see-through, so that the parts inside show. fill: a color that replaces the finish color.
 * opacity: an upper limit for the fill opacity (the case opacity slider of the viewer).
 */
export function setLook(mesh, edges, theme, { finish = "print", focus = false, ghost = false, fill = null, edgesOn = true, opacity = 1 }) {
  const T = THEMES[theme];
  const mat = mesh.material, lm = edges.material;
  const c = new THREE.Color(fill || T[finish] || T.print);
  if (focus) c.lerp(new THREE.Color(T.accent), T.mix);
  mat.color.copy(c);
  mat.metalness = finish === "buy" ? 0.35 : 0;
  let op = finish === "clear" ? 0.55 : 1;
  let lop = focus ? 0.95 : T.inkOpacity;
  if (opacity < 1) { op = Math.min(op, opacity); lop *= Math.max(opacity, 0.3); }
  if (ghost) { op = Math.min(op, 0.1); lop = Math.min(lop, 0.16); }
  mat.opacity = op;
  mat.transparent = op < 1;
  mat.depthWrite = op >= 1;
  lm.color.set(focus ? T.accent : T.ink);
  lm.opacity = lop;
  edges.visible = edgesOn;
}

/** A dashed accent line from the home position of a part to where it is drawn. */
export function guideLine(theme) {
  const g = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
    new THREE.LineDashedMaterial({ dashSize: 3, gapSize: 2.5, transparent: true, opacity: 0.95, color: THEMES[theme].accent }),
  );
  g.renderOrder = 2;
  return g;
}

export function setGuide(g, a, b, theme) {
  g.geometry.setFromPoints([a, b]);
  g.computeLineDistances();
  g.material.color.set(THEMES[theme].accent);
}

/** Turn a part about the vertical axis (Y) through pivot, then move it by off: its matrix in the parent frame. */
export function placeMatrix(pivot, deg, off) {
  const q = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), THREE.MathUtils.degToRad(deg));
  const m = new THREE.Matrix4().makeTranslation(-pivot.x, -pivot.y, -pivot.z);
  m.premultiply(new THREE.Matrix4().makeRotationFromQuaternion(q));
  m.premultiply(new THREE.Matrix4().makeTranslation(pivot.x + off.x, pivot.y + off.y, pivot.z + off.z));
  return m;
}

/**
 * Tag boxes above parts, moved up where they overlap a tag below them (the same rule as the site).
 * tags: [{x, y, w, h}] with x, y the top-left corner. Returns the same list, moved.
 */
export function spreadTags(tags, gap = 3) {
  tags.sort((a, b) => b.y - a.y);
  const placed = [];
  for (const t of tags) {
    for (let k = 0; k < tags.length; k++) {
      const hit = placed.find((o) => t.x < o.x + o.w + gap + 1 && o.x < t.x + t.w + gap + 1 && t.y < o.y + o.h + gap && o.y < t.y + t.h + gap);
      if (!hit) break;
      t.y = hit.y - t.h - gap;
    }
    placed.push(t);
  }
  return tags;
}

/** The CSS of the background grid (the page behind a transparent canvas). */
export function gridCSS(theme) {
  const T = THEMES[theme];
  return `background-color:${T.bg};background-image:linear-gradient(${T.grid} 1px, transparent 1px),` +
    `linear-gradient(90deg, ${T.grid} 1px, transparent 1px);background-size:24px 24px;`;
}
