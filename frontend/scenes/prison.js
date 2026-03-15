// Prison Scene — Cell block with exercise yard
export function buildScene(scene, THREE) {
  // Floor — concrete gray
  const floorGeo = new THREE.PlaneGeometry(20, 20);
  const floorMat = new THREE.MeshStandardMaterial({ 
    color: 0x3a3a3a,
    roughness: 0.9 
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.5;
  scene.add(floor);
  
  // Cell walls — dark blocks
  const wallMat = new THREE.MeshStandardMaterial({ color: 0x2a2a3a, roughness: 0.7 });
  for (let i = -2; i <= 2; i++) {
    const wall = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3, 4), wallMat);
    wall.position.set(i * 4, 1, -8);
    scene.add(wall);
  }
  
  // Bars — vertical lines
  const barMat = new THREE.MeshStandardMaterial({ color: 0x666680, metalness: 0.8 });
  for (let i = -3; i <= 3; i++) {
    const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 3), barMat);
    bar.position.set(i * 1.2, 1, -6);
    scene.add(bar);
  }
  
  // Harsh overhead lighting
  const dirLight = new THREE.DirectionalLight(0xffeedd, 0.6);
  dirLight.position.set(0, 15, 5);
  scene.add(dirLight);
  
  const ambient = new THREE.AmbientLight(0x303040, 0.4);
  scene.add(ambient);
  
  // Spotlight effect
  const spot = new THREE.SpotLight(0xffffee, 0.5);
  spot.position.set(0, 10, 0);
  spot.angle = Math.PI / 6;
  scene.add(spot);
  
  // Dark atmosphere
  scene.background = new THREE.Color(0x0a0a15);
  scene.fog = new THREE.Fog(0x0a0a15, 8, 25);
}
