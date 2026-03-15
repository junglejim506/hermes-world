/**
 * world.js — Three.js scene engine for Hermes World.
 * Handles scene selection, character rendering, influence lines, animations.
 */

import * as THREE from 'https://unpkg.com/three@0.128.0/build/three.module.js';
import { buildCharacter, updateCharacterTarget, tickCharacters } from '/static/characters.js';
import { updateHUD } from '/static/hud.js';
import { connectWS } from '/static/ws-client.js';
import { buildScene as buildRaftScene } from '/static/scenes/raft.js';
import { buildScene as buildOfficeScene } from '/static/scenes/office.js';
import { buildScene as buildVillageScene } from '/static/scenes/village.js';
import { buildScene as buildSpaceScene } from '/static/scenes/space.js';
import { buildScene as buildCourtroomScene } from '/static/scenes/courtroom.js';
import { buildScene as buildPrisonScene } from '/static/scenes/prison.js';

// ── Renderer & Camera ─────────────────────────────────────────────────────────
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.getElementById('canvas-container').appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 200);
camera.position.set(0, 10, 14);
camera.lookAt(0, 0, 0);

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ── Scene ─────────────────────────────────────────────────────────────────────
let scene = new THREE.Scene();
const characterMeshes = {};  // agent_id → { group, body, head, legs, accDot, light, targetPos }
const influenceLines = [];
let currentSceneType = null;
let currentState = null;

const SCENE_BUILDERS = {
  raft: buildRaftScene,
  office: buildOfficeScene,
  village: buildVillageScene,
  space: buildSpaceScene,
  courtroom: buildCourtroomScene,
  prison: buildPrisonScene,
};

function initScene(sceneType) {
  // Teardown old scene
  while (scene.children.length > 0) scene.remove(scene.children[0]);
  Object.keys(characterMeshes).forEach(id => delete characterMeshes[id]);

  // Lighting
  const ambient = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambient);
  const sun = new THREE.DirectionalLight(0xffffff, 0.9);
  sun.position.set(5, 12, 8);
  sun.castShadow = true;
  sun.shadow.mapSize.set(1024, 1024);
  scene.add(sun);

  // Build scene environment
  const builder = SCENE_BUILDERS[sceneType] || SCENE_BUILDERS.raft;
  builder(scene, THREE);
  currentSceneType = sceneType;
}

// ── Stance colours ─────────────────────────────────────────────────────────────
const STANCE_COLOR = {
  utilitarian: 0x2dd4bf,
  deontological: 0xf87171,
  undecided: 0xfbbf24,
};

// ── State update ──────────────────────────────────────────────────────────────
function applyState(state) {
  currentState = state;

  if (state.scene_type && state.scene_type !== currentSceneType) {
    initScene(state.scene_type);
  }

  // Sync agents
  const agentIds = new Set((state.agents || []).map(a => a.id));

  // Remove departed agents
  Object.keys(characterMeshes).forEach(id => {
    if (!agentIds.has(id)) {
      scene.remove(characterMeshes[id].group);
      delete characterMeshes[id];
    }
  });

  // Add/update agents
  (state.agents || []).forEach(agent => {
    const color = STANCE_COLOR[agent.stance] || STANCE_COLOR.undecided;
    if (!characterMeshes[agent.id]) {
      const mesh = buildCharacter(THREE, agent.name, color);
      scene.add(mesh.group);
      characterMeshes[agent.id] = mesh;
    }
    const mesh = characterMeshes[agent.id];

    // Update stance colour
    mesh.body.material.color.setHex(color);
    mesh.accDot.material.color.setHex(color);
    mesh.accDot.material.emissive.setHex(color);

    // Target position from world state
    const tx = agent.position?.x ?? 0;
    const tz = agent.position?.z ?? 0;
    updateCharacterTarget(mesh, tx, tz);

    // Speaking animation trigger
    if (agent.last_action?.type === 'speak') {
      triggerSpeakAnim(mesh, state.agents);
    } else if (agent.last_action?.type === 'learn_skill') {
      triggerLearnAnim(mesh);
    }

    mesh._agentData = agent;
  });

  // Influence lines
  rebuildInfluenceLines(state.influence_graph || [], state.agents || []);

  // HUD
  updateHUD(state);
}

// ── Influence lines ───────────────────────────────────────────────────────────
const lineMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.4 });

function rebuildInfluenceLines(graph, agents) {
  influenceLines.forEach(l => scene.remove(l));
  influenceLines.length = 0;

  graph.forEach(edge => {
    const fromAgent = agents.find(a => a.id === edge.from);
    const toAgent   = agents.find(a => a.id === edge.to);
    if (!fromAgent || !toAgent) return;

    const color = STANCE_COLOR[fromAgent.stance] || 0xffffff;
    const mat = new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: 0.2 + edge.strength * 0.5,
      linewidth: 1,
    });

    const points = [
      new THREE.Vector3(fromAgent.position.x, 1.5, fromAgent.position.z),
      new THREE.Vector3(toAgent.position.x,   1.5, toAgent.position.z),
    ];
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const line = new THREE.Line(geo, mat);
    line._born = Date.now();
    line._ttl = 30000;
    scene.add(line);
    influenceLines.push(line);
  });
}

// ── Speak animation ───────────────────────────────────────────────────────────
function triggerSpeakAnim(mesh, allAgents) {
  mesh._speaking = true;
  mesh._speakTimer = 60;  // frames
  if (mesh.light) {
    mesh.light.intensity = 1.5;
  }
  // Other agents look at the speaker
  const speakerPos = mesh.group.position;
  Object.values(characterMeshes).forEach(m => {
    if (m !== mesh) {
      m.group.lookAt(speakerPos.x, m.group.position.y, speakerPos.z);
    }
  });
}

// ── Learn skill animation ─────────────────────────────────────────────────────
function triggerLearnAnim(mesh) {
  mesh._learning = true;
  mesh._learnTimer = 90;  // frames — crouch then rise
}

// ── Click to inspect ──────────────────────────────────────────────────────────
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

renderer.domElement.addEventListener('click', (e) => {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width)  * 2 - 1;
  mouse.y = -((e.clientY - rect.top)  / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);

  const meshList = Object.values(characterMeshes).flatMap(m => [m.body, m.head]);
  const hits = raycaster.intersectObjects(meshList);
  if (hits.length > 0) {
    // Walk up to find the group
    let obj = hits[0].object;
    while (obj.parent && !obj.parent._agentData) obj = obj.parent;
    const agent = obj.parent?._agentData || Object.values(characterMeshes).find(m => m.body === hits[0].object || m.head === hits[0].object)?._agentData;
    if (agent) openInspector(agent);
  }
});

function openInspector(agent) {
  document.getElementById('inspector').style.display = 'block';
  document.getElementById('inspector-name').textContent = agent.name;
  document.getElementById('inspector-role').textContent = agent.role;
  const sc = STANCE_COLOR[agent.stance] || 0xfbbf24;
  document.getElementById('inspector-stance').innerHTML = `Stance: <span style="color:#${sc.toString(16).padStart(6,'0')}">${agent.stance}</span>`;
  document.getElementById('inspector-skills').textContent = 'Skills: ' + (agent.skills || []).join(', ');
  const la = agent.last_action;
  document.getElementById('inspector-action').textContent = la ? `${la.type}: ${la.content?.slice(0,100) || '—'}` : 'No action yet.';
}

window.closeInspector = () => { document.getElementById('inspector').style.display = 'none'; };

// ── Orbit camera drag ─────────────────────────────────────────────────────────
let isDragging = false, lastX = 0, camTheta = 0, camPhi = 0.6, camR = 18;

renderer.domElement.addEventListener('mousedown', e => { if (e.button === 0) { isDragging = true; lastX = e.clientX; } });
renderer.domElement.addEventListener('mouseup', () => isDragging = false);
renderer.domElement.addEventListener('mousemove', e => {
  if (!isDragging) return;
  camTheta -= (e.clientX - lastX) * 0.005;
  lastX = e.clientX;
});
renderer.domElement.addEventListener('wheel', e => {
  camR = Math.max(6, Math.min(30, camR + e.deltaY * 0.02));
});

// ── Render loop ───────────────────────────────────────────────────────────────
const clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();

  // Orbit camera
  camera.position.x = camR * Math.sin(camTheta) * Math.cos(camPhi);
  camera.position.y = camR * Math.sin(camPhi) + 2;
  camera.position.z = camR * Math.cos(camTheta) * Math.cos(camPhi);
  camera.lookAt(0, 0.5, 0);

  // Tick characters (walking, speak pulse, learn crouch)
  tickCharacters(characterMeshes, dt);

  // Expire influence lines
  const now = Date.now();
  for (let i = influenceLines.length - 1; i >= 0; i--) {
    const l = influenceLines[i];
    const age = now - l._born;
    l.material.opacity = Math.max(0, 1 - age / l._ttl) * 0.6;
    if (age > l._ttl) {
      scene.remove(l);
      influenceLines.splice(i, 1);
    }
  }

  renderer.render(scene, camera);
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
connectWS(applyState);

// ── Intervene / Tick ──────────────────────────────────────────────────────────
window.sendIntervention = async () => {
  const input = document.getElementById('intervene-input');
  const cmd = input.value.trim();
  if (!cmd) return;
  await fetch('/api/intervene', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({command: cmd}) });
  input.value = '';
};

window.triggerTick = async () => {
  await fetch('/api/tick', { method: 'POST' });
};

document.getElementById('intervene-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') window.sendIntervention();
});

animate();
