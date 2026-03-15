/**
 * courtroom.js — Courtroom / jury deliberation scene.
 */
export function buildScene(scene, THREE) {
  scene.background = new THREE.Color(0x0e0c08);
  scene.fog = new THREE.Fog(0x0e0c08, 20, 45);

  // Wood floor
  const floorGeo = new THREE.PlaneGeometry(18, 14);
  const floorMat = new THREE.MeshLambertMaterial({ color: 0x5c3d11 });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  // Floor planks
  for (let i = -6; i <= 6; i++) {
    const plankGeo = new THREE.BoxGeometry(0.9, 0.02, 14);
    const plankMat = new THREE.MeshLambertMaterial({ color: i % 2 === 0 ? 0x6b4c1e : 0x5c3d11 });
    const plank = new THREE.Mesh(plankGeo, plankMat);
    plank.position.set(i * 0.95, 0.01, 0);
    scene.add(plank);
  }

  // Jury table (long oval-ish)
  const tableGeo = new THREE.BoxGeometry(8, 0.12, 2.5);
  const tableMat = new THREE.MeshLambertMaterial({ color: 0x3d2b1f });
  const table = new THREE.Mesh(tableGeo, tableMat);
  table.position.set(0, 0.7, 0);
  table.castShadow = true;
  table.receiveShadow = true;
  scene.add(table);

  // Chairs around table
  const chairMat = new THREE.MeshLambertMaterial({ color: 0x2a1f15 });
  for (let side = -1; side <= 1; side += 2) {
    for (let i = -3; i <= 3; i++) {
      const chairGeo = new THREE.BoxGeometry(0.5, 0.8, 0.5);
      const chair = new THREE.Mesh(chairGeo, chairMat);
      chair.position.set(i * 1.1, 0.4, side * 1.8);
      chair.castShadow = true;
      scene.add(chair);
    }
  }

  // Judge's bench at far end
  const benchGeo = new THREE.BoxGeometry(4, 1.2, 1);
  const benchMat = new THREE.MeshLambertMaterial({ color: 0x3d2b1f });
  const bench = new THREE.Mesh(benchGeo, benchMat);
  bench.position.set(0, 0.6, -5.5);
  bench.castShadow = true;
  scene.add(bench);

  // Overhead lights (warm)
  [-3, 0, 3].forEach(x => {
    const bulbGeo = new THREE.SphereGeometry(0.12, 6, 6);
    const bulbMat = new THREE.MeshBasicMaterial({ color: 0xfff4cc });
    const bulb = new THREE.Mesh(bulbGeo, bulbMat);
    bulb.position.set(x, 4.5, 0);
    scene.add(bulb);
    const bulbLight = new THREE.PointLight(0xfff4cc, 0.6, 8);
    bulbLight.position.set(x, 4.5, 0);
    scene.add(bulbLight);
  });

  // Walls (dark panelling)
  const wallMat = new THREE.MeshLambertMaterial({ color: 0x2a1f10 });
  [
    [0, 2.5, -7, 18, 5, 0.2],
    [0, 2.5,  7, 18, 5, 0.2],
    [-9, 2.5, 0, 0.2, 5, 14],
    [ 9, 2.5, 0, 0.2, 5, 14],
  ].forEach(([x, y, z, w, h, d]) => {
    const wGeo = new THREE.BoxGeometry(w, h, d);
    const wall = new THREE.Mesh(wGeo, wallMat);
    wall.position.set(x, y, z);
    scene.add(wall);
  });
}
