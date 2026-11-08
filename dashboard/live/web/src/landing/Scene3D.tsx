import { Suspense, useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import type { Palette } from './palette';

const MODEL_URL = './models/orca-assets.glb';

// World layout. Earth top sits at y=0 under Chennai; the GEO arc is drawn about the Earth centre.
const EARTH_R = 30;
const EARTH_C = new THREE.Vector3(0, -EARTH_R, 0);
const ORBIT_R = 46;
const SAT_ANGLE = (98 * Math.PI) / 180;
const SAT_POS = new THREE.Vector3(
  EARTH_C.x + ORBIT_R * Math.cos(SAT_ANGLE), EARTH_C.y + ORBIT_R * Math.sin(SAT_ANGLE), 0,
);
const SAT_SCALE = 3;

type Site = { x: number; z: number; s: number; ry?: number };
const GATEWAY: Site = { x: -2.8, z: 0.8, s: 1.6, ry: 0.6 };
const TOWERS: Site[] = [{ x: 0.8, z: -1.5, s: 1.9 }, { x: 2.9, z: 0.5, s: 1.9 }, { x: -0.5, z: 2.3, s: 1.9 }];
const TERMINALS: Site[] = [
  { x: 1.3, z: 1.2, s: 0.55, ry: 0.4 }, { x: 3.5, z: 2.2, s: 0.55, ry: 1.2 }, { x: -1.3, z: -1.9, s: 0.55, ry: 2.1 },
  { x: 4.3, z: -1.1, s: 0.55, ry: 0.9 }, { x: 0.1, z: 0.3, s: 0.55, ry: 2.6 },
];

const easeInOutCubic = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const LEG = 1.0;       // seconds per camera leg
const HOLD = 0.25;     // seconds on the Earth view before the flight starts

type Waypoint = { p: THREE.Vector3; t: THREE.Vector3 };

/** Camera waypoints: Earth, satellite, gateway, Chennai. On wide screens the scene is shifted right of the text. */
function buildWaypoints(wide: boolean): Waypoint[] {
  const raw: Waypoint[] = [
    { p: new THREE.Vector3(-6, 10, 96), t: new THREE.Vector3(0, -9, 0) },
    { p: new THREE.Vector3(-1, 21, 14), t: SAT_POS.clone() },
    { p: new THREE.Vector3(1.5, 4, 9), t: new THREE.Vector3(GATEWAY.x, 0.8, GATEWAY.z) },
    { p: new THREE.Vector3(8.5, 5.5, 11.5), t: new THREE.Vector3(1.2, 2.6, 0) },
  ];
  if (!wide) return raw;
  return raw.map(({ p, t }) => {
    const dir = t.clone().sub(p);
    const right = new THREE.Vector3().crossVectors(dir, new THREE.Vector3(0, 1, 0)).setY(0).normalize();
    const shift = right.multiplyScalar(-0.17 * dir.length());
    return { p: p.clone().add(shift), t: t.clone().add(shift) };
  });
}

function Models({ pal }: { pal: Palette }) {
  const { scene, materials } = useGLTF(MODEL_URL) as unknown as {
    scene: THREE.Group; materials: Record<string, THREE.MeshStandardMaterial>;
  };
  const invalidate = useThree((s) => s.invalidate);

  // Recolour the shared GLB materials from tokens (dark: light-grey body, accent panels, warn trim, bg dark parts).
  useLayoutEffect(() => {
    const ink = new THREE.Color(pal.ink);
    const bg = new THREE.Color(pal.bg);
    const set = (name: string, c: THREE.Color) => {
      const m = materials[name];
      if (!m) return;
      m.color.copy(c);
      m.roughness = 0.85;
      m.metalness = 0;
      m.needsUpdate = true;
    };
    set('body', pal.light ? new THREE.Color(pal.surface2).lerp(ink, 0.14) : ink.clone().lerp(bg, 0.28));
    set('panel', new THREE.Color(pal.accent));
    set('accent', new THREE.Color(pal.warn));
    set('dark', pal.light ? bg.clone().lerp(ink, 0.82) : bg);
    invalidate();
  }, [materials, pal, invalidate]);

  const make = useMemo(() => (name: string) => {
    const src = scene.getObjectByName(name);
    return () => (src ? src.clone(true) : new THREE.Object3D());
  }, [scene]);
  const sat = useMemo(() => make('Satellite')(), [make]);
  const dish = useMemo(() => make('GatewayDish')(), [make]);
  const towers = useMemo(() => TOWERS.map(() => make('CellTower')()), [make]);
  const terms = useMemo(() => TERMINALS.map(() => make('UserTerminal')()), [make]);

  return (
    <>
      <primitive object={sat} position={SAT_POS} scale={SAT_SCALE} rotation={[0.25, 0.7, 0.1]} />
      <primitive object={dish} position={[GATEWAY.x, 0, GATEWAY.z]} scale={GATEWAY.s} rotation={[0, GATEWAY.ry ?? 0, 0]} />
      {towers.map((o, i) => <primitive key={`t${i}`} object={o} position={[TOWERS[i].x, 0, TOWERS[i].z]} scale={TOWERS[i].s} />)}
      {terms.map((o, i) => <primitive key={`u${i}`} object={o} position={[TERMINALS[i].x, 0, TERMINALS[i].z]} scale={TERMINALS[i].s} rotation={[0, TERMINALS[i].ry ?? 0, 0]} />)}
    </>
  );
}

function Earth({ pal }: { pal: Palette }) {
  const lines = useMemo(() => {
    const pts: number[] = [];
    const seg = 128;
    for (let lat = -75; lat <= 75; lat += 15) {
      const phi = (lat * Math.PI) / 180;
      const r = EARTH_R * 1.003 * Math.cos(phi);
      const y = EARTH_R * 1.003 * Math.sin(phi);
      for (let i = 0; i < seg; i++) {
        const a0 = (i / seg) * Math.PI * 2;
        const a1 = ((i + 1) / seg) * Math.PI * 2;
        pts.push(Math.cos(a0) * r, y, Math.sin(a0) * r, Math.cos(a1) * r, y, Math.sin(a1) * r);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
    return g;
  }, []);
  useEffect(() => () => lines.dispose(), [lines]);
  const surface = pal.light ? pal.surface2 : pal.surface;
  return (
    <group position={EARTH_C} rotation={[0.28, 0, 0.42]}>
      <mesh>
        <sphereGeometry args={[EARTH_R, 96, 64]} />
        <meshStandardMaterial color={surface} roughness={1} metalness={0} />
      </mesh>
      <lineSegments geometry={lines}>
        <lineBasicMaterial color={pal.border} transparent opacity={0.9} />
      </lineSegments>
    </group>
  );
}

function OrbitAndLinks({ pal }: { pal: Palette }) {
  const { orbit, links, tile } = useMemo(() => {
    const o: number[] = [];
    const n = 160;
    const a0 = (38 * Math.PI) / 180;
    const a1 = (142 * Math.PI) / 180;
    for (let i = 0; i < n; i++) {
      const u = a0 + ((a1 - a0) * i) / n;
      const v = a0 + ((a1 - a0) * (i + 1)) / n;
      o.push(EARTH_C.x + ORBIT_R * Math.cos(u), EARTH_C.y + ORBIT_R * Math.sin(u), 0,
        EARTH_C.x + ORBIT_R * Math.cos(v), EARTH_C.y + ORBIT_R * Math.sin(v), 0);
    }
    const l: number[] = [];
    const add = (s: Site, top: number) => l.push(s.x, top * s.s, s.z, SAT_POS.x, SAT_POS.y, SAT_POS.z);
    TOWERS.forEach((s) => add(s, 0.95));
    TERMINALS.forEach((s) => add(s, 0.9));
    const mk = (a: number[]) => {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(a, 3));
      return g;
    };
    const box = new THREE.BoxGeometry(12, 0.12, 8.5);
    return { orbit: mk(o), links: mk(l), tile: { box, edges: new THREE.EdgesGeometry(box) } };
  }, []);
  const feeder = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(
      [GATEWAY.x, 0.9 * GATEWAY.s, GATEWAY.z, SAT_POS.x, SAT_POS.y, SAT_POS.z], 3));
    return g;
  }, []);
  useEffect(() => () => { orbit.dispose(); links.dispose(); feeder.dispose(); tile.box.dispose(); tile.edges.dispose(); }, [orbit, links, feeder, tile]);

  return (
    <>
      <lineSegments geometry={orbit}><lineBasicMaterial color={pal.inkMuted} transparent opacity={0.5} /></lineSegments>
      <lineSegments geometry={links}><lineBasicMaterial color={pal.accent} transparent opacity={0.55} /></lineSegments>
      <lineSegments geometry={feeder}><lineBasicMaterial color={pal.accent} /></lineSegments>
      <mesh geometry={tile.box} position={[1, -0.06, 0.2]}>
        <meshStandardMaterial color={pal.light ? pal.surface : pal.surface2} roughness={1} metalness={0} />
      </mesh>
      <lineSegments geometry={tile.edges} position={[1, -0.06, 0.2]}>
        <lineBasicMaterial color={pal.border} />
      </lineSegments>
    </>
  );
}

function CameraRig({ reduced }: { reduced: boolean }) {
  const camera = useThree((s) => s.camera);
  const aspect = useThree((s) => s.size.width / Math.max(1, s.size.height));
  const invalidate = useThree((s) => s.invalidate);
  const wide = aspect > 1.2;
  const wps = useMemo(() => buildWaypoints(wide), [wide]);
  const t0 = useRef<number | null>(null);
  const look = useRef(new THREE.Vector3());
  const tmp = useRef(new THREE.Vector3());

  // Static framing (reduced motion) and initial pose before the first frame.
  useLayoutEffect(() => {
    const w = reduced ? wps[wps.length - 1] : wps[0];
    camera.position.copy(w.p);
    look.current.copy(w.t);
    camera.lookAt(w.t);
    invalidate();
  }, [camera, wps, reduced, invalidate]);

  useFrame((state) => {
    if (reduced) return;
    if (t0.current === null) t0.current = state.clock.elapsedTime;
    const el = state.clock.elapsedTime - t0.current - HOLD;
    const last = wps.length - 1;
    const p = camera.position;
    if (el < LEG * last) {
      const f = Math.max(0, el) / LEG;
      const leg = Math.min(last - 1, Math.floor(f));
      const k = easeInOutCubic(Math.min(1, f - leg));
      const a = wps[leg];
      const b = wps[leg + 1];
      p.lerpVectors(a.p, b.p, k);
      look.current.lerpVectors(a.t, b.t, k);
    } else {
      const d = el - LEG * last;
      const ramp = Math.min(1, d / 2.5);
      const m = ramp * ramp * (3 - 2 * ramp);
      const e = wps[last];
      p.set(
        e.p.x + Math.sin(d * 0.11) * 0.7 * m,
        e.p.y + Math.sin(d * 0.07 + 1) * 0.28 * m,
        e.p.z + Math.cos(d * 0.09) * 0.5 * m,
      );
      look.current.copy(tmp.current.copy(e.t));
    }
    camera.lookAt(look.current);
  });
  return null;
}

function Background({ color }: { color: string }) {
  const scene = useThree((s) => s.scene);
  const invalidate = useThree((s) => s.invalidate);
  useLayoutEffect(() => { scene.background = new THREE.Color(color); invalidate(); }, [scene, color, invalidate]);
  return null;
}

function Ready({ onReady }: { onReady: () => void }) {
  useEffect(() => { onReady(); }, [onReady]);
  return null;
}

export default function Scene3D({ pal, reduced, onReady }: { pal: Palette; reduced: boolean; onReady: () => void }) {
  return (
    <Canvas
      dpr={[1, 2]}
      frameloop={reduced ? 'demand' : 'always'}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      camera={{ fov: 35, near: 0.1, far: 400, position: [-6, 10, 96] }}
    >
      <Background color={pal.bg} />
      <ambientLight intensity={pal.light ? 1.5 : 0.9} />
      <directionalLight position={[18, 30, 22]} intensity={pal.light ? 1.7 : 2.3} />
      <directionalLight position={[-20, 6, -10]} intensity={0.35} />
      <Earth pal={pal} />
      <OrbitAndLinks pal={pal} />
      <Suspense fallback={null}>
        <Models pal={pal} />
        <Ready onReady={onReady} />
      </Suspense>
      <CameraRig reduced={reduced} />
    </Canvas>
  );
}

useGLTF.preload(MODEL_URL);
