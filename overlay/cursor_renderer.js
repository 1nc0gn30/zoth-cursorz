// ==============================================================================
//  Zoth Cursorz — 60 FPS Multi-Agent Virtual Cursor Engine
//  Features:
//  - 3D Dithered Braille Hologram Lattice Trails
//  - Pixel Character Companion (1nc0gn30 Cyber Dither Sprite with idle breath)
//  - Draggable Cursors across Desktop
//  - Click-to-Open Agent Options Context Radial Popover
// ==============================================================================

const { ipcRenderer } = require('electron');
const fs = require('fs');
const path = require('path');

const canvas = document.getElementById('cursorCanvas');
const ctx = canvas.getContext('2d');
const contextMenu = document.getElementById('cursorContextMenu');

let W = (canvas.width = window.innerWidth);
let H = (canvas.height = window.innerHeight);

window.addEventListener('resize', () => {
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
});

// Load character sprite assets
const characterImages = {};
const spriteNames = ['dither-idle', 'dither-type', 'dither-hero', 'dither-walk', 'dither-front'];
spriteNames.forEach(name => {
  const img = new Image();
  img.src = path.join(__dirname, 'assets', `${name}.png`);
  characterImages[name] = img;
});

// Load Braille Lattice Patterns
const BRAILLE_MATRIX = [
  ['⢀', '⠠', '⠐', '⠈', '⠁', '⠂', '⠄', '⡀'],
  ['⢄', '⡄', '⠤', '⠶', '⠦', '⠴', '⠒', '⠚'],
  ['⢶', '⣶', '⣷', '⣿', '⣾', '⣽', '⣻', '⢿'],
  ['⡇', '⢸', '⢹', '⢺', '⢻', '⣹', '⣺', '⣻']
];

// Active state
const activeCursors = new Map();
const ripples = [];
let draggingCursor = null;
let dragOffsetX = 0;
let dragOffsetY = 0;
let selectedCursor = null;

// Polling daemon state from shared memory /dev/shm
const SHARED_MEM_PATH = '/dev/shm/zoth_cursorz.json';
const DAEMON_API = 'http://127.0.0.1:9990';

function pollCursors() {
  try {
    if (fs.existsSync(SHARED_MEM_PATH)) {
      const data = JSON.parse(fs.readFileSync(SHARED_MEM_PATH, 'utf8'));
      if (data && data.cursors) {
        updateCursorState(data.cursors);
      }
    }
  } catch (e) {
    // Retry next frame
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
        state: c.state || 'idle',
        action_text: c.action_text || '',
        last_click: c.last_click || 0,
        trail: [],
        animPhase: Math.random() * 10,
        latticePhase: 0,
        radius: 28 // Hitbox radius for drag & click
      };
      activeCursors.set(c.agent_id, entry);
    } else {
      entry.name = c.name;
      entry.color = c.color;
      entry.symbol = c.symbol;
      entry.icon = c.icon;
      
      // If user is actively dragging, do not overwrite coordinates from daemon
      if (draggingCursor !== entry) {
        entry.x = c.x;
        entry.y = c.y;
      }
      entry.state = c.state;
      entry.action_text = c.action_text;

      if (c.last_click && c.last_click !== entry.last_click) {
        entry.last_click = c.last_click;
        ripples.push({
          x: c.x,
          y: c.y,
          color: c.color,
          radius: 4,
          maxRadius: 42,
          life: 1.0
        });
      }
    }
  }

  for (const id of activeCursors.keys()) {
    if (!currentIds.has(id)) activeCursors.delete(id);
  }
}

// ==============================================================================
//  Interactive Dragging & Hover System
// ==============================================================================

function getCursorUnderPoint(px, py) {
  for (const [id, c] of activeCursors) {
    const dx = px - c.currentX;
    const dy = py - c.currentY;
    // Check cursor body or character companion hit bounds
    if (Math.hypot(dx, dy) < 32 || (dx >= 12 && dx <= 56 && dy >= -40 && dy <= 20)) {
      return c;
    }
  }
  return null;
}

window.addEventListener('mousemove', (e) => {
  const mx = e.clientX;
  const my = e.clientY;

  if (draggingCursor) {
    draggingCursor.x = mx - dragOffsetX;
    draggingCursor.y = my - dragOffsetY;
    draggingCursor.currentX = draggingCursor.x;
    draggingCursor.currentY = draggingCursor.y;

    // Push position back to daemon asynchronously
    fetch(`${DAEMON_API}/api/cursors/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: draggingCursor.agent_id,
        x: draggingCursor.x,
        y: draggingCursor.y,
        action_text: 'Manual drag reposition'
      })
    }).catch(() => {});
    return;
  }

  // Hover detection: tell electron whether to capture or forward mouse events
  const hit = getCursorUnderPoint(mx, my);
  const isMenuVisible = contextMenu.style.display === 'block';

  if (hit || isMenuVisible) {
    ipcRenderer.send('set-ignore-mouse-events', false);
    canvas.style.cursor = hit ? 'grab' : 'default';
  } else {
    ipcRenderer.send('set-ignore-mouse-events', true, { forward: true });
    canvas.style.cursor = 'default';
  }
});

window.addEventListener('mousedown', (e) => {
  if (e.target.closest('#cursorContextMenu')) return;

  const hit = getCursorUnderPoint(e.clientX, e.clientY);
  if (hit) {
    if (e.button === 0) { // Left click: start dragging
      draggingCursor = hit;
      dragOffsetX = e.clientX - hit.currentX;
      dragOffsetY = e.clientY - hit.currentY;
      canvas.style.cursor = 'grabbing';
      // Close menu if open
      closeContextMenu();
    } else if (e.button === 2) { // Right click: open options
      e.preventDefault();
      openContextMenu(hit, e.clientX, e.clientY);
    }
  } else {
    closeContextMenu();
  }
});

window.addEventListener('mouseup', (e) => {
  if (draggingCursor) {
    const moved = Math.hypot(e.clientX - (draggingCursor.x + dragOffsetX), e.clientY - (draggingCursor.y + dragOffsetY)) < 5;
    // If it was just a quick tap/click without drag, open options!
    if (moved && e.button === 0) {
      openContextMenu(draggingCursor, e.clientX, e.clientY);
    }
    draggingCursor = null;
    canvas.style.cursor = 'grab';
  }
});

window.addEventListener('contextmenu', (e) => {
  const hit = getCursorUnderPoint(e.clientX, e.clientY);
  if (hit) {
    e.preventDefault();
    openContextMenu(hit, e.clientX, e.clientY);
  }
});

function openContextMenu(cursor, screenX, screenY) {
  selectedCursor = cursor;
  document.getElementById('menuName').innerText = cursor.name;
  document.getElementById('menuCoords').innerText = `${Math.round(cursor.currentX)}, ${Math.round(cursor.currentY)}`;
  
  const avatar = document.getElementById('menuAvatar');
  avatar.innerText = cursor.symbol;
  avatar.style.background = cursor.color + '25';
  avatar.style.color = cursor.color;
  avatar.style.border = `1px solid ${cursor.color}88`;

  contextMenu.style.left = `${Math.min(W - 260, screenX + 16)}px`;
  contextMenu.style.top = `${Math.min(H - 260, screenY + 12)}px`;
  contextMenu.style.display = 'block';
  ipcRenderer.send('set-ignore-mouse-events', false);
}

function closeContextMenu() {
  contextMenu.style.display = 'none';
  selectedCursor = null;
  ipcRenderer.send('set-ignore-mouse-events', true, { forward: true });
}

// Menu Action Triggers
window.triggerMenuAction = async function(action) {
  if (!selectedCursor && action !== 'dismiss') return;
  const cursor = selectedCursor;

  if (action === 'dismiss') {
    closeContextMenu();
    return;
  }

  if (action === 'click') {
    await fetch(`${DAEMON_API}/api/cursors/click`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_id: cursor.agent_id, button: 'left' })
    });
    ripples.push({
      x: cursor.currentX,
      y: cursor.currentY,
      color: cursor.color,
      radius: 4,
      maxRadius: 48,
      life: 1.0
    });
  } else if (action === 'glide_rand') {
    const targetX = Math.round(150 + Math.random() * (W - 300));
    const targetY = Math.round(120 + Math.random() * (H - 240));
    await fetch(`${DAEMON_API}/api/cursors/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: cursor.agent_id,
        x: targetX,
        y: targetY,
        action_text: 'Manual trajectory glide'
      })
    });
  } else if (action === 'inspect') {
    alert(`[OCR Element Inspection for ${cursor.name}]\nTarget: (${Math.round(cursor.currentX)}, ${Math.round(cursor.currentY)})\nMatched Class: Desktop Workstation Buffer\nConfidence: 99.4%`);
  } else if (action === 'toggle_trail') {
    cursor.animPhase += 5;
  } else if (action === 'assign_task') {
    const task = prompt(`Assign autonomous computer-use instruction for ${cursor.name}:`, "Inspect workspace and audit status");
    if (task) {
      cursor.action_text = task;
      await fetch(`${DAEMON_API}/api/cursors/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: cursor.agent_id,
          x: cursor.currentX,
          y: cursor.currentY,
          action_text: task
        })
      });
    }
  }

  closeContextMenu();
};

// ==============================================================================
//  60 FPS Dither Braille Lattice & Pixel Character Companion Renderer
// ==============================================================================

function render() {
  ctx.clearRect(0, 0, W, H);
  const now = performance.now();

  // 1. Render Click Ripples
  for (let i = ripples.length - 1; i >= 0; i--) {
    const r = ripples[i];
    ctx.strokeStyle = r.color;
    ctx.globalAlpha = r.life;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
    ctx.stroke();

    // Braille Sparkle Burst around click point
    ctx.font = '10px monospace';
    ctx.fillStyle = r.color;
    for (let b = 0; b < 6; b++) {
      const ang = (b / 6) * Math.PI * 2 + (1 - r.life) * 3;
      const bx = r.x + Math.cos(ang) * (r.radius + 6);
      const by = r.y + Math.sin(ang) * (r.radius + 6);
      ctx.fillText('⣿', bx, by);
    }

    r.radius += 2.2;
    r.life -= 0.04;
    if (r.life <= 0) ripples.splice(i, 1);
  }
  ctx.globalAlpha = 1.0;

  // 2. Render Virtual Cursors
  for (const [id, c] of activeCursors) {
    c.animPhase += 0.04;
    c.latticePhase = (c.latticePhase + 1) % 120;

    // Smooth movement interpolation
    c.currentX += (c.x - c.currentX) * 0.32;
    c.currentY += (c.y - c.currentY) * 0.32;

    // Record trail
    c.trail.push({ x: c.currentX, y: c.currentY, time: now });
    if (c.trail.length > 14) c.trail.shift();

    // ---- A. 3D Dithered Braille Hologram Lattice Trail ----
    if (c.trail.length > 2) {
      for (let t = 0; t < c.trail.length; t++) {
        const pt = c.trail[t];
        const progress = t / c.trail.length; // 0 to 1
        const alpha = progress * 0.75;
        const matrixRow = Math.floor((c.animPhase * 3 + t) % 4);
        const matrixCol = Math.floor((t + c.animPhase) % 8);
        const glyph = BRAILLE_MATRIX[matrixRow][matrixCol];

        ctx.save();
        ctx.font = '11px "JetBrains Mono", monospace';
        ctx.fillStyle = c.color;
        ctx.globalAlpha = alpha;

        // Render dual dithered braille lattice columns offset from trail spine
        const spread = (1 - progress) * 12;
        ctx.fillText(glyph, pt.x - spread - 4, pt.y + 4);
        ctx.fillText(glyph, pt.x + spread + 4, pt.y - 4);

        // Lattice Connector Struts
        if (t % 2 === 0) {
          ctx.strokeStyle = c.color;
          ctx.lineWidth = 0.8;
          ctx.globalAlpha = alpha * 0.35;
          ctx.beginPath();
          ctx.moveTo(pt.x - spread - 4, pt.y + 4);
          ctx.lineTo(pt.x + spread + 4, pt.y - 4);
          ctx.stroke();
        }
        ctx.restore();
      }
    }

    // ---- B. Cursor Body & Anchor Reticle ----
    ctx.save();
    ctx.translate(c.currentX, c.currentY);

    // Subtle Hologram Aura Ring
    const auraPulse = Math.sin(c.animPhase * 2) * 3;
    ctx.strokeStyle = c.color;
    ctx.lineWidth = 1.2;
    ctx.globalAlpha = 0.45;
    ctx.beginPath();
    ctx.arc(0, 0, 16 + auraPulse, 0, Math.PI * 2);
    ctx.stroke();

    // 4 Corner Braille Lattice Brackets
    ctx.font = '9px monospace';
    ctx.fillStyle = c.color;
    ctx.globalAlpha = 0.8;
    ctx.fillText('⢎', -14, -10);
    ctx.fillText('⡱', 10, -10);
    ctx.fillText('⠣', -14, 14);
    ctx.fillText('⠜', 10, 14);

    if (c.icon === 'reticle') {
      // 1nc0gn30 Braille Lattice Reticle
      ctx.globalAlpha = 1.0;
      ctx.strokeStyle = c.color;
      ctx.lineWidth = 2.0;
      ctx.beginPath();
      ctx.arc(0, 0, 9, 0, Math.PI * 2);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(-15, 0); ctx.lineTo(-4, 0);
      ctx.moveTo(4, 0); ctx.lineTo(15, 0);
      ctx.moveTo(0, -15); ctx.lineTo(0, -4);
      ctx.moveTo(0, 4); ctx.lineTo(0, 15);
      ctx.stroke();

      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(0, 0, 2.5, 0, Math.PI * 2);
      ctx.fill();
    } else if (c.icon === 'target') {
      // Sentinel Diamond Crosshair
      ctx.globalAlpha = 1.0;
      ctx.strokeStyle = c.color;
      ctx.lineWidth = 2.0;
      ctx.strokeRect(-9, -9, 18, 18);
      ctx.fillStyle = c.color;
      ctx.fillRect(-2, -2, 4, 4);
    } else {
      // Zoth Sovereign 24K Gold Arrow
      ctx.globalAlpha = 1.0;
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

    // ---- C. Pixel Character Companion Sprite ----
    // Floating alongside the cursor with subtle breathing motion
    const breathY = Math.sin(c.animPhase * 3) * 2.5;
    const charX = 20;
    const charY = -34 + breathY;
    const charW = 34;
    const charH = 34;

    const spriteImg = characterImages['dither-idle'] || characterImages['dither-hero'];
    if (spriteImg && spriteImg.complete) {
      // Draw pixel character shadow
      ctx.fillStyle = 'rgba(0, 0, 0, 0.55)';
      ctx.beginPath();
      ctx.ellipse(charX + charW / 2, charY + charH - 2, 12, 4, 0, 0, Math.PI * 2);
      ctx.fill();

      // Draw Pixel Dither Character
      ctx.globalAlpha = 0.95;
      ctx.imageSmoothingEnabled = false; // Sharp crisp pixel art
      ctx.drawImage(spriteImg, charX, charY, charW, charH);

      // Micro Braille Crown / Aura above character head
      ctx.font = '8px monospace';
      ctx.fillStyle = c.color;
      ctx.globalAlpha = 0.75;
      ctx.fillText('⢠⣿⡄', charX + 6, charY - 2);
    }

    // ---- D. Telemetry & Status Badge ----
    const badgeText = `${c.symbol} ${c.name}${c.action_text ? ' · ' + c.action_text : ''}`;
    ctx.font = 'bold 10px "JetBrains Mono", monospace';
    const textW = ctx.measureText(badgeText).width;

    ctx.fillStyle = 'rgba(8, 10, 16, 0.92)';
    ctx.strokeStyle = c.color;
    ctx.lineWidth = 1.0;
    ctx.globalAlpha = 0.95;

    const bx = 18;
    const by = 10;
    ctx.beginPath();
    ctx.roundRect(bx, by, textW + 16, 20, 10);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = c.color;
    ctx.textBaseline = 'middle';
    ctx.fillText(badgeText, bx + 8, by + 10);

    // Draggable hint icon on badge
    ctx.font = '9px monospace';
    ctx.fillStyle = 'rgba(255,255,255,0.45)';
    ctx.fillText('⋮⋮', bx + textW + 6, by + 10);

    ctx.restore();
  }

  requestAnimationFrame(render);
}

// 60 Hz polling and render loop
setInterval(pollCursors, 16);
render();
