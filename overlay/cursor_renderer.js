// ==============================================================================
//  Zoth Cursorz — 60 FPS Multi-Agent Virtual Cursor Renderer
//  Renders custom colored pointers, kinetic motion trails, click ripples & telemetry
// ==============================================================================

const canvas = document.getElementById('cursorCanvas');
const ctx = canvas.getContext('2d');

let W = (canvas.width = window.innerWidth);
let H = (canvas.height = window.innerHeight);

window.addEventListener('resize', () => {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
});

// Cursor animation tracking state
const activeCursors = new Map();
const ripples = [];

// Polling daemon state from shared memory /dev/shm or HTTP API
const fs = require('fs');
const SHARED_MEM_PATH = '/dev/shm/zoth_cursorz.json';

function pollCursors() {
  try {
    if (fs.existsSync(SHARED_MEM_PATH)) {
      const data = JSON.parse(fs.readFileSync(SHARED_MEM_PATH, 'utf8'));
      if (data && data.cursors) {
        updateCursorState(data.cursors);
      }
    }
  } catch (e) {
    // Fallback: silently retry next tick
  }
}

function updateCursorState(cursorList) {
  const currentIds = new Set();

  for (const c of cursorList) {
    currentIds.add(c.agent_id);
    let entry = activeCursors.get(c.agent_id);

    if (!entry) {
      entry = {
        agent_id: c.agent_id,
        name: c.name,
        color: c.color,
        symbol: c.symbol,
        icon: c.icon,
        x: c.x,
        y: c.y,
        currentX: c.x,
        currentY: c.y,
        state: c.state,
        action_text: c.action_text,
        last_click: c.last_click,
        trail: []
      };
      activeCursors.set(c.agent_id, entry);
    } else {
      entry.name = c.name;
      entry.color = c.color;
      entry.symbol = c.symbol;
      entry.icon = c.icon;
      entry.x = c.x;
      entry.y = c.y;
      entry.state = c.state;
      entry.action_text = c.action_text;

      // Check for new click event to spawn ripple
      if (c.last_click && c.last_click !== entry.last_click) {
        entry.last_click = c.last_click;
        ripples.push({
          x: c.x,
          y: c.y,
          color: c.color,
          radius: 4,
          maxRadius: 36,
          life: 1.0
        });
      }
    }
  }

  // Remove pruned cursors
  for (const id of activeCursors.keys()) {
    if (!currentIds.has(id)) {
      activeCursors.delete(id);
    }
  }
}

// 60 FPS Render Loop
function render() {
  ctx.clearRect(0, 0, W, H);
  const now = performance.now();

  // 1. Render Click Ripples
  for (let i = ripples.length - 1; i >= 0; i--) {
    const r = ripples[i];
    ctx.strokeStyle = r.color;
    ctx.globalAlpha = r.life;
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
    ctx.stroke();

    r.radius += 1.8;
    r.life -= 0.045;
    if (r.life <= 0) {
      ripples.splice(i, 1);
    }
  }
  ctx.globalAlpha = 1.0;

  // 2. Render Virtual Cursors
  for (const [id, c] of activeCursors) {
    // Smooth interpolating glide
    c.currentX += (c.x - c.currentX) * 0.28;
    c.currentY += (c.y - c.currentY) * 0.28;

    // Push into visual trail
    c.trail.push({ x: c.currentX, y: c.currentY, alpha: 0.65 });
    if (c.trail.length > 8) c.trail.shift();

    // Draw Motion Trail
    if (c.trail.length > 1) {
      for (let t = 0; t < c.trail.length - 1; t++) {
        const p1 = c.trail[t];
        const p2 = c.trail[t + 1];
        ctx.strokeStyle = c.color;
        ctx.globalAlpha = (t / c.trail.length) * 0.40;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1.0;

    // Draw Cursor Pointer by Icon Type
    ctx.save();
    ctx.translate(c.currentX, c.currentY);

    if (c.icon === 'reticle') {
      // 1nc0gn30 Cybernetic Reticle Cursor
      ctx.strokeStyle = c.color;
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.arc(0, 0, 10, 0, Math.PI * 2);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(-14, 0); ctx.lineTo(-4, 0);
      ctx.moveTo(4, 0); ctx.lineTo(14, 0);
      ctx.moveTo(0, -14); ctx.lineTo(0, -4);
      ctx.moveTo(0, 4); ctx.lineTo(0, 14);
      ctx.stroke();

      ctx.fillStyle = c.color;
      ctx.beginPath();
      ctx.arc(0, 0, 2.5, 0, Math.PI * 2);
      ctx.fill();
    } else if (c.icon === 'target') {
      // Sentinel Diamond Crosshair
      ctx.strokeStyle = c.color;
      ctx.lineWidth = 2.0;
      ctx.strokeRect(-8, -8, 16, 16);
      ctx.fillStyle = c.color;
      ctx.fillRect(-2, -2, 4, 4);
    } else {
      // Sovereign 24K Gold Arrow Cursor
      ctx.fillStyle = c.color;
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 1.5;

      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(0, 18);
      ctx.lineTo(4.5, 14);
      ctx.lineTo(9.5, 23);
      ctx.lineTo(12.5, 21.5);
      ctx.lineTo(7.5, 12.5);
      ctx.lineTo(13.5, 12.5);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // Telemetry Badge (Agent Name + Status)
    const badgeText = `${c.symbol} ${c.name}${c.action_text ? ' · ' + c.action_text : ''}`;
    ctx.font = 'bold 10px "JetBrains Mono", monospace';
    const textW = ctx.measureText(badgeText).width;

    ctx.fillStyle = 'rgba(10, 10, 15, 0.88)';
    ctx.strokeStyle = c.color;
    ctx.lineWidth = 1.0;

    const bx = 16;
    const by = 8;
    ctx.beginPath();
    ctx.roundRect(bx, by, textW + 16, 18, 9);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = c.color;
    ctx.textBaseline = 'middle';
    ctx.fillText(badgeText, bx + 8, by + 9);

    ctx.restore();
  }

  requestAnimationFrame(render);
}

// 60 Hz polling and render ticker
setInterval(pollCursors, 16);
render();
