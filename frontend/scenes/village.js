/**
 * village.js — Village / resource crisis scene.
 */
export function buildScene(scene, THREE) {
  scene.background = new THREE.Color(0x2c1a0e);
  scene.fog = new THREE.FogExp2(0x2c1a0e, 0.025);

  // Dusty ground
  const groundGeo = new THREE.PlaneGeometry(40, 40);
  const groundMat = new THREE.MeshLambertMaterial({ color: 0x8b6914 });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  // Huts
  const hutPositions = [[-5, -3], [5, -3], [-5, 3], [5, 3], [0, -5]];
  hutPositions.forEach(([x, z]) => {
    const wallGeo = new THREE.BoxGeometry(1.5, 1.2, 1.5);
    const wallMat = new THREE.MeshLambertMaterial({ color: 0xc4a35a });
    const wall = new THREE.Mesh(wallGeo, wallMat);
    wall.position.set(x, 0.6, z);
    wall.castShadow = true;
    scene.add(wall);

    const roofGeo = new THREE.ConeGeometry(1.2, 1.0, 5);
    const roofMat = new THREE.MeshLambertMaterial({ color: 0x8b4513 });
    const roof = new THREE.Mesh(roofGeo, roofMat);
    roof.position.set(x, 1.7, z);
    roof.castShadow = true;
    scene.add(roof);
  });

  // Well in the center
  const wellGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.8, 8, 1, true);
  const wellMat = new THREE.MeshLambertMaterial({ color: 0x777777, side: THREE.DoubleSide });
  const well = new THREE.Mesh(wellGeo, wellMat);
  well.position.set(0, 0.4, 0);
  scene.add(well);

  // Dry cracked field patches
  for (let i = 0; i < 8; i++) {
    const patchGeo = new THREE.PlaneGeometry(2, 1.5);
    const patchMat = new THREE.MeshLambertMaterial({ color: 0x5c3d11, transparent: true, opacity: 0.7 });
    const patch = new THREE.Mesh(patchGeo, patchMat);
    patch.rotation.x = -Math.PI / 2;
    patch.position.set((Math.random() - 0.5) * 14, 0.01, (Math.random() - 0.5) * 14);
    scene.add(patch);
  }

  // Trees (dead)
  for (let i = 0; i < 5; i++) {
    const trunkGeo = new THREE.CylinderGeometry(0.1, 0.15, 2.5, 5);
    const trunkMat = new THREE.MeshLambertMaterial({ color: 0x4a3020 });
    const trunk = new THREE.Mesh(trunkGeo, trunkMat);
    const tx = (Math.random() - 0.5) * 16;
    const tz = (Math.random() - 0.5) * 16;
    trunk.position.set(tx, 1.25, tz);
    trunk.castShadow = true;
    scene.add(trunk);
  }
}
