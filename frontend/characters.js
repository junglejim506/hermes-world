/**
 * characters.js — Low-poly humanoid mesh builder and animation system.
 */

export function buildCharacter(THREE, name, color = 0x2dd4bf) {
  const group = new THREE.Group();

  // Body
  const bodyGeo = new THREE.CylinderGeometry(0.22, 0.28, 0.9, 7);
  const bodyMat = new THREE.MeshLambertMaterial({ color });
  const body = new THREE.Mesh(bodyGeo, bodyMat);
  body.position.y = 0.55;
  body.castShadow = true;
  group.add(body);

  // Head
  const headGeo = new THREE.SphereGeometry(0.22, 7, 6);
  const headMat = new THREE.MeshLambertMaterial({ color: 0xf5d0a9 });
  const head = new THREE.Mesh(headGeo, headMat);
  head.position.y = 1.25;
  head.castShadow = true;
  group.add(head);

  // Legs
  const legGeo = new THREE.CylinderGeometry(0.08, 0.07, 0.55, 5);
  const legMat = new THREE.MeshLambertMaterial({ color: 0x444466 });
  const legL = new THREE.Mesh(legGeo, legMat); legL.position.set(-0.11, 0.05, 0); group.add(legL);
  const legR = new THREE.Mesh(legGeo, legMat); legR.position.set( 0.11, 0.05, 0); group.add(legR);

  // Arms
  const armGeo = new THREE.CylinderGeometry(0.06, 0.05, 0.5, 5);
  const armMat = new THREE.MeshLambertMaterial({ color });
  const armL = new THREE.Mesh(armGeo, armMat); armL.position.set(-0.32, 0.6, 0); armL.rotation.z =  0.3; group.add(armL);
  const armR = new THREE.Mesh(armGeo, armMat); armR.position.set( 0.32, 0.6, 0); armR.rotation.z = -0.3; group.add(armR);

  // Accent dot above head
  const dotGeo = new THREE.SphereGeometry(0.07, 6, 6);
  const dotMat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.9 });
  dotMat.emissive = new THREE.Color(color);
  const accDot = new THREE.Mesh(dotGeo, dotMat);
  accDot.position.y = 1.65;
  group.add(accDot);

  // Point light (dim by default, flares during speech)
  const light = new THREE.PointLight(color, 0, 3);
  light.position.y = 1.5;
  group.add(light);

  // Name label (sprite)
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 48;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = 'rgba(0,0,0,0)';
  ctx.fillRect(0, 0, 256, 48);
  ctx.font = 'bold 22px monospace';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.fillText(name, 128, 32);
  const texture = new THREE.CanvasTexture(canvas);
  const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true, opacity: 0.6 });
  const sprite = new THREE.Sprite(spriteMat);
  sprite.scale.set(1.4, 0.28, 1);
  sprite.position.y = 2.1;
  group.add(sprite);

  const mesh = { group, body, head, legL, legR, armL, armR, accDot, light };
  mesh._walkPhase = Math.random() * Math.PI * 2;
  mesh._targetX = 0;
  mesh._targetZ = 0;
  mesh._speaking = false;
  mesh._speakTimer = 0;
  mesh._learning = false;
  mesh._learnTimer = 0;
  group._agentData = null;

  return mesh;
}

export function updateCharacterTarget(mesh, tx, tz) {
  mesh._targetX = tx;
  mesh._targetZ = tz;
}

export function tickCharacters(characterMeshes, dt) {
  const t = performance.now() * 0.001;

  Object.values(characterMeshes).forEach(mesh => {
    const { group, legL, legR, armL, armR, accDot, light } = mesh;

    // Move toward target
    const dx = mesh._targetX - group.position.x;
    const dz = mesh._targetZ - group.position.z;
    const dist = Math.sqrt(dx * dx + dz * dz);
    const isMoving = dist > 0.05;

    if (isMoving) {
      const speed = Math.min(dist, 2.0 * dt);
      group.position.x += (dx / dist) * speed;
      group.position.z += (dz / dist) * speed;
      // Face direction of movement
      group.rotation.y = Math.atan2(dx, dz);
    }

    // Walking animation
    if (isMoving) {
      mesh._walkPhase += dt * 6;
      const swing = Math.sin(mesh._walkPhase) * 0.35;
      legL.rotation.x =  swing;
      legR.rotation.x = -swing;
      armL.rotation.x = -swing * 0.6;
      armR.rotation.x =  swing * 0.6;
      group.position.y = Math.abs(Math.sin(mesh._walkPhase * 2)) * 0.05;
    } else {
      legL.rotation.x = legR.rotation.x = armL.rotation.x = armR.rotation.x = 0;
      group.position.y = 0;
    }

    // Speaking animation — accent dot pulse + light flare
    if (mesh._speaking) {
      mesh._speakTimer--;
      const pulse = 0.9 + 0.2 * Math.sin(t * 12);
      accDot.scale.setScalar(pulse);
      light.intensity = 0.8 + 0.7 * Math.sin(t * 10);
      if (mesh._speakTimer <= 0) {
        mesh._speaking = false;
        accDot.scale.setScalar(1);
        light.intensity = 0;
      }
    } else {
      // Idle dot bob
      accDot.position.y = 1.65 + Math.sin(t * 1.5 + mesh._walkPhase) * 0.04;
    }

    // Learn skill animation — crouch + rise
    if (mesh._learning) {
      mesh._learnTimer--;
      const prog = mesh._learnTimer / 90;
      const crouch = prog < 0.5 ? (1 - prog * 2) * 0.3 : (prog * 2 - 1) * 0.3;
      group.scale.y = Math.max(0.7, 1 - crouch);
      accDot.material.opacity = 0.5 + 0.5 * Math.sin(t * 20);
      if (mesh._learnTimer <= 0) {
        mesh._learning = false;
        group.scale.y = 1;
        accDot.material.opacity = 0.9;
      }
    }
  });
}
