/**
 * hud.js — Sidebar, feed, and stats overlay logic.
 */

let _lastRound = -1;

export function updateHUD(state) {
  if (!state) return;

  // Status badge
  const badge = document.getElementById('status-badge');
  badge.textContent = `● ${state.status || 'idle'}`;
  badge.className = state.status === 'running' ? 'running' : 'idle';

  // Header
  document.getElementById('hud-scenario').textContent = state.scenario?.slice(0, 120) || 'No simulation running.';
  document.getElementById('hud-round').textContent = `Round ${state.round ?? '—'} · ${(state.scene_type || '').toUpperCase()}`;

  // Countdown
  if (state.next_round_at) {
    _startCountdown(state.next_round_at);
  } else {
    document.getElementById('hud-countdown').textContent = '';
  }

  // Stance bars
  const agents = state.agents || [];
  const total = agents.length || 1;
  const counts = { utilitarian: 0, deontological: 0, undecided: 0 };
  agents.forEach(a => { counts[a.stance] = (counts[a.stance] || 0) + 1; });
  ['utilitarian', 'deontological', 'undecided'].forEach(s => {
    const pct = (counts[s] / total * 100).toFixed(0);
    document.getElementById(`bar-${s}`).style.width = pct + '%';
    document.getElementById(`cnt-${s}`).textContent = counts[s];
  });

  // World stats
  const statsEl = document.getElementById('world-stats');
  statsEl.innerHTML = '';
  const world = state.world || {};
  Object.entries(world).forEach(([k, v]) => {
    if (k === 'events') return;
    const row = document.createElement('div');
    row.className = 'stat-row';
    row.innerHTML = `<span class="stat-key">${k.replace(/_/g, ' ')}</span><span class="stat-val">${formatStatVal(v)}</span>`;
    statsEl.appendChild(row);
  });
  if ((world.events || []).length > 0) {
    const last = world.events[world.events.length - 1];
    const row = document.createElement('div');
    row.className = 'stat-row';
    row.innerHTML = `<span class="stat-key">latest event</span><span class="stat-val" style="color:#f87171">${last}</span>`;
    statsEl.appendChild(row);
  }

  // Feed — current round actions
  if (state.round !== _lastRound) {
    _lastRound = state.round;
    const feed = document.getElementById('feed');
    feed.innerHTML = '';
    const log = state.round_log || [];
    const currentEntries = log.filter(e => e.round === state.round);
    if (currentEntries.length === 0) {
      feed.innerHTML = '<span style="color:#444;font-size:11px">Waiting for round…</span>';
    } else {
      currentEntries.forEach(entry => {
        const el = document.createElement('div');
        el.className = `feed-entry ${entry.action?.type || 'idle'}`;
        const agentName = agents.find(a => a.id === entry.agent_id)?.name || entry.agent_id;
        const emoji = { speak: '💬', use_skill: '⚙️', learn_skill: '📚', idle: '·' }[entry.action?.type] || '•';
        el.innerHTML = `<span class="feed-agent">${emoji} ${agentName}</span><span class="feed-content">${entry.action?.content?.slice(0, 80) || '—'}</span>`;
        feed.appendChild(el);
      });
    }
  }

  // Skill registry
  const skillEl = document.getElementById('skill-list');
  const registry = state.skill_registry || {};
  const skills = Object.entries(registry);
  if (skills.length === 0) {
    skillEl.innerHTML = '<span style="color:#444;font-size:11px">No skills learned yet.</span>';
  } else {
    skillEl.innerHTML = '';
    skills.slice(-12).forEach(([name, info]) => {
      const el = document.createElement('div');
      el.className = 'skill-entry';
      el.innerHTML = `<span class="skill-name">${name}</span> <span class="skill-owner">← ${info.learned_by} (r${info.round})</span>`;
      skillEl.appendChild(el);
    });
  }
}

function formatStatVal(v) {
  if (typeof v === 'boolean') return v ? '✓' : '✗';
  if (typeof v === 'number') return v % 1 === 0 ? v : v.toFixed(1);
  return String(v);
}

let _countdownInterval = null;
function _startCountdown(nextRoundAt) {
  if (_countdownInterval) clearInterval(_countdownInterval);
  _countdownInterval = setInterval(() => {
    const ms = new Date(nextRoundAt) - Date.now();
    const el = document.getElementById('hud-countdown');
    if (ms <= 0) {
      el.textContent = 'Round advancing…';
      clearInterval(_countdownInterval);
    } else {
      const s = Math.floor(ms / 1000) % 60;
      const m = Math.floor(ms / 60000);
      el.textContent = `Next round in ${m}m ${String(s).padStart(2, '0')}s`;
    }
  }, 1000);
}
