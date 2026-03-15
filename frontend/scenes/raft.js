/**
 * raft.js — Survival (raft / ocean) scene.
 */
export function buildScene(scene, THREE) {
  scene.background = new THREE.Color(0x0d2137);
  scene.fog = new THREE.FogExp2(0x0d2137, 0.04);

  // Ocean floor plane
  const oceanGeo = new THREE.PlaneGeometry(80, 80, 12, 12);
  const oceanMat = new THREE.MeshLambertMaterial({ color: 0x0a3d5c, wireframe: false });
  const ocean = new THREE.Mesh(oceanGeo, oceanMat);
  ocean.rotation.x = -Math.PI / 2;
  ocean.position.y = -0.05;
  ocean.receiveShadow = true;
  scene.add(ocean);

  // Raft platform
  const raftGeo = new THREE.BoxGeometry(9, 0.25, 9);
  const raftMat = new THREE.MeshLambertMaterial({ color: 0x8b6914 });
  const raft = new THREE.Mesh(raftGeo, raftMat);
  raft.position.y = 0.0;
  raft.receiveShadow = true;
  raft.castShadow = true;
  scene.add(raft);

  // Plank lines on raft
  for (let i = -3; i <= 3; i++) {
    const plankGeo = new THREE.BoxGeometry(9, 0.05, 0.08);
    const plankMat = new THREE.MeshLambertMaterial({ color: 0x6b4f10 });
    const plank = new THREE.Mesh(plankGeo, plankMat);
    plank.position.set(0, 0.14, i * 1.3);
    scene.add(plank);
  }

  // Mast
  const mastGeo = new THREE.CylinderGeometry(0.06, 0.08, 5, 6);
  const mastMat = new THREE.MeshLambertMaterial({ color: 0x7c5c1e });
  const mast = new THREE.Mesh(mastGeo, mastMat);
  mast.position.set(-3, 2.6, -2);
  mast.castShadow = true;
  scene.add(mast);

  // Tattered sail
  const sailGeo = new THREE.PlaneGeometry(2.5, 3);
  const sailMat = new THREE.MeshLambertMaterial({ color: 0xd4c4a0, side: THREE.DoubleSide, transparent: true, opacity: 0.85 });
  const sail = new THREE.Mesh(sailGeo, sailMat);
  sail.position.set(-2, 3.2, -2);
  sail.rotation.y = 0.2;
  scene.add(sail);

  // Distant water waves (simple rings)
  for (let i = 0; i < 6; i++) {
    const r = 10 + i * 6;
    const waveGeo = new THREE.RingGeometry(r, r + 0.15, 40);
    const waveMat = new THREE.MeshBasicMaterial({ color: 0x1a5276, side: THREE.DoubleSide, transparent: true, opacity: 0.3 });
    const wave = new THREE.Mesh(waveGeo, waveMat);
    wave.rotation.x = -Math.PI / 2;
    wave.position.y = 0.01;
    scene.add(wave);
  }

  // Starry sky dots
  const starGeo = new THREE.BufferGeometry();
  const starVerts = [];
  for (let i = 0; i < 300; i++) {
    starVerts.push((Math.random() - 0.5) * 120, 15 + Math.random() * 30, (Math.random() - 0.5) * 120);
  }
  starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starVerts, 3));
  const starMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.12 });
  scene.add(new THREE.Points(starGeo, starMat));
}
