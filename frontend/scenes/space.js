/**
 * space.js — Space colony / Mars scene.
 */
export function buildScene(scene, THREE) {
  scene.background = new THREE.Color(0x000008);
  scene.fog = new THREE.Fog(0x000008, 25, 60);

  // Red regolith floor
  const floorGeo = new THREE.PlaneGeometry(40, 40, 16, 16);
  const floorMat = new THREE.MeshLambertMaterial({ color: 0x7a2e1a });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  // Habitat dome
  const domeGeo = new THREE.SphereGeometry(4.5, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2);
  const domeMat = new THREE.MeshLambertMaterial({ color: 0xccddee, transparent: true, opacity: 0.25, side: THREE.DoubleSide });
  const dome = new THREE.Mesh(domeGeo, domeMat);
  dome.position.set(0, 0, 0);
  scene.add(dome);

  // Dome ring base
  const ringGeo = new THREE.TorusGeometry(4.5, 0.15, 6, 40);
  const ringMat = new THREE.MeshLambertMaterial({ color: 0x889aaa });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.rotation.x = Math.PI / 2;
  ring.position.y = 0.1;
  scene.add(ring);

  // Solar panels
  const panelMat = new THREE.MeshLambertMaterial({ color: 0x1a3a6c, emissive: new THREE.Color(0x001133), emissiveIntensity: 0.5 });
  [[-6, -4], [6, -4], [-6, 4], [6, 4]].forEach(([x, z]) => {
    const panGeo = new THREE.BoxGeometry(1.5, 0.05, 2.5);
    const pan = new THREE.Mesh(panGeo, panelMat);
    pan.position.set(x, 0.8, z);
    pan.rotation.x = -0.2;
    pan.castShadow = true;
    scene.add(pan);
    const postGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.8, 4);
    const postMat = new THREE.MeshLambertMaterial({ color: 0x888888 });
    const post = new THREE.Mesh(postGeo, postMat);
    post.position.set(x, 0.4, z);
    scene.add(post);
  });

  // Mars rocks
  for (let i = 0; i < 12; i++) {
    const rGeo = new THREE.DodecahedronGeometry(0.2 + Math.random() * 0.4, 0);
    const rMat = new THREE.MeshLambertMaterial({ color: 0x8b4513 });
    const rock = new THREE.Mesh(rGeo, rMat);
    rock.position.set((Math.random() - 0.5) * 18, 0.15, (Math.random() - 0.5) * 18);
    rock.rotation.set(Math.random(), Math.random(), Math.random());
    rock.castShadow = true;
    scene.add(rock);
  }

  // Stars
  const starGeo = new THREE.BufferGeometry();
  const sv = [];
  for (let i = 0; i < 500; i++) {
    sv.push((Math.random() - 0.5) * 120, 10 + Math.random() * 40, (Math.random() - 0.5) * 120);
  }
  starGeo.setAttribute('position', new THREE.Float32BufferAttribute(sv, 3));
  scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 0.1 })));

  // Distant reddish planet glow
  const glowLight = new THREE.PointLight(0xc0451a, 0.6, 60);
  glowLight.position.set(-20, 20, -20);
  scene.add(glowLight);
}
