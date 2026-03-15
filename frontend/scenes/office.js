/**
 * office.js — Startup / office scene.
 */
export function buildScene(scene, THREE) {
  scene.background = new THREE.Color(0x111118);
  scene.fog = new THREE.Fog(0x111118, 20, 50);

  // Floor
  const floorGeo = new THREE.PlaneGeometry(20, 20);
  const floorMat = new THREE.MeshLambertMaterial({ color: 0x1a1a2e });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  // Floor grid lines
  const gridHelper = new THREE.GridHelper(20, 20, 0x2a2a3e, 0x1e1e2e);
  gridHelper.position.y = 0.01;
  scene.add(gridHelper);

  // Desks
  const deskMat = new THREE.MeshLambertMaterial({ color: 0x2a2a4a });
  for (let i = -1; i <= 1; i++) {
    const deskGeo = new THREE.BoxGeometry(2, 0.08, 1);
    const desk = new THREE.Mesh(deskGeo, deskMat);
    desk.position.set(i * 3, 0.7, 0);
    desk.castShadow = true;
    desk.receiveShadow = true;
    scene.add(desk);

    // Monitor
    const monGeo = new THREE.BoxGeometry(0.8, 0.55, 0.05);
    const monMat = new THREE.MeshLambertMaterial({ color: 0x0a0a1a, emissive: new THREE.Color(0x1a3a5c), emissiveIntensity: 0.8 });
    const mon = new THREE.Mesh(monGeo, monMat);
    mon.position.set(i * 3, 1.1, -0.3);
    scene.add(mon);
  }

  // Whiteboard
  const wbGeo = new THREE.BoxGeometry(4, 2, 0.08);
  const wbMat = new THREE.MeshLambertMaterial({ color: 0xf0f0f0, emissive: new THREE.Color(0xffffff), emissiveIntensity: 0.1 });
  const wb = new THREE.Mesh(wbGeo, wbMat);
  wb.position.set(0, 1.5, -5);
  scene.add(wb);

  // Neon ceiling strip light
  const stripGeo = new THREE.BoxGeometry(8, 0.05, 0.2);
  const stripMat = new THREE.MeshBasicMaterial({ color: 0x7c6af7 });
  const strip = new THREE.Mesh(stripGeo, stripMat);
  strip.position.set(0, 4, 0);
  scene.add(strip);
  const stripLight = new THREE.RectAreaLight ? null : new THREE.PointLight(0x7c6af7, 0.5, 10);
  if (stripLight) { stripLight.position.set(0, 4, 0); scene.add(stripLight); }
}
