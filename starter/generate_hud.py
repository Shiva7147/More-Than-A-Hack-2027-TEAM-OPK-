import json
import os

ROOT = r"d:\more-than-a-hack-2027"
json_path = os.path.join(ROOT, "viewer", "demo_data.json")
data_str = open(json_path, "r", encoding="utf-8").read()

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Barca Tactician HUD | Team OPK</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body {{ background: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    .pitch-bg {{
      background: radial-gradient(circle at center, #173821 0%, #0d2113 100%);
      box-shadow: 0 20px 50px rgba(0,0,0,0.8), inset 0 0 100px rgba(0,0,0,0.6);
    }}
    .glow-h {{ filter: drop-shadow(0 0 8px rgba(0, 102, 255, 0.9)); }}
    .glow-a {{ filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.9)); }}
    .glow-ball {{ filter: drop-shadow(0 0 12px rgba(250, 204, 21, 1)); }}
    .glass {{ background: rgba(18, 24, 38, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }}
    .timeline-scrub {{ cursor: pointer; }}
  </style>
</head>
<body class="text-slate-100 min-h-screen flex flex-col justify-between p-4 selection:bg-blue-600">

  <!-- Top Navigation & Live Match Telemetry -->
  <header class="glass rounded-2xl px-6 py-4 flex flex-wrap items-center justify-between gap-4 mb-4">
    <div class="flex items-center gap-4">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 to-red-600 flex items-center justify-center font-black text-xl shadow-lg shadow-blue-900/50">
        ⚽
      </div>
      <div>
        <h1 class="text-lg font-bold tracking-tight flex items-center gap-2">
          Barça Tactician HUD <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">TEAM OPK</span>
        </h1>
        <p class="text-xs text-slate-400">LaLiga EA Sports 2024-25 • FC Barcelona (H) vs Athletic Club (A)</p>
      </div>
    </div>

    <!-- Live Possession Badge -->
    <div class="flex items-center gap-6">
      <div class="flex flex-col items-center">
        <span class="text-[10px] uppercase font-bold tracking-wider text-slate-400">Match Clock</span>
        <span id="matchClock" class="font-mono text-xl font-bold text-slate-100">07:27</span>
      </div>
      <div class="h-8 w-px bg-slate-800"></div>
      <div class="flex flex-col items-center">
        <span class="text-[10px] uppercase font-bold tracking-wider text-slate-400">Controlled Possession</span>
        <span id="possessionBadge" class="text-xs font-black px-3 py-1 rounded-full bg-blue-600/30 text-blue-400 border border-blue-500/40 uppercase tracking-wide">
          FC Barcelona (H)
        </span>
      </div>
      <div class="h-8 w-px bg-slate-800"></div>
      <div class="flex flex-col items-center">
        <span class="text-[10px] uppercase font-bold tracking-wider text-slate-400">Possession Share</span>
        <div class="flex items-center gap-2 font-mono text-sm font-bold">
          <span class="text-blue-400">58% H</span>
          <span class="text-slate-600">:</span>
          <span class="text-red-400">42% A</span>
        </div>
      </div>
    </div>
  </header>

  <!-- Pitch Canvas & Tactical Radar -->
  <main class="flex-1 flex flex-col items-center justify-center relative my-2">
    <div class="relative w-full max-w-5xl aspect-[105.3/68] rounded-2xl overflow-hidden border border-emerald-900/40 pitch-bg">
      <canvas id="pitchCanvas" class="w-full h-full block"></canvas>
      
      <!-- Live Turnover Overlay Notification -->
      <div id="turnoverAlert" class="absolute top-4 left-1/2 -translate-x-1/2 glass px-4 py-1.5 rounded-full text-xs font-bold text-amber-400 border border-amber-500/40 flex items-center gap-2 shadow-2xl opacity-0 transition-opacity duration-300">
        <i class="fa-solid fa-arrows-rotate"></i>
        <span id="turnoverText">High-Press Turnover Detected</span>
      </div>
    </div>
  </main>

  <!-- Control Deck & Timeline -->
  <footer class="glass rounded-2xl p-5 space-y-4 max-w-5xl mx-auto w-full mt-4">
    <!-- Possession Ribbon -->
    <div class="space-y-1.5">
      <div class="flex justify-between items-center text-xs font-medium text-slate-400">
        <span>Timeline Ribbon (Continuous Spells)</span>
        <span id="frameCounter" class="font-mono text-slate-300">Frame: 11185 / 18685</span>
      </div>
      <div id="timelineContainer" class="w-full h-5 rounded-lg overflow-hidden relative timeline-scrub border border-slate-800">
        <canvas id="timelineCanvas" class="w-full h-full block"></canvas>
        <div id="timelinePlayhead" class="absolute top-0 bottom-0 w-1 bg-amber-400 shadow-[0_0_10px_#facc15] pointer-events-none" style="left: 0%;"></div>
      </div>
    </div>

    <!-- Playback & Fast Jumps -->
    <div class="flex flex-wrap items-center justify-between gap-4 pt-2">
      <!-- Media Buttons -->
      <div class="flex items-center gap-2">
        <button id="btnPlay" class="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center shadow-lg shadow-blue-600/30 transition">
          <i class="fa-solid fa-play"></i>
        </button>
        <button id="btnStepBack" class="w-9 h-9 rounded-xl glass hover:bg-slate-800 text-slate-300 flex items-center justify-center transition">
          <i class="fa-solid fa-backward-step"></i>
        </button>
        <button id="btnStepForward" class="w-9 h-9 rounded-xl glass hover:bg-slate-800 text-slate-300 flex items-center justify-center transition">
          <i class="fa-solid fa-forward-step"></i>
        </button>
        <div class="flex items-center glass rounded-xl px-2 py-1 gap-1 text-xs font-bold text-slate-400 ml-2">
          <span>Speed:</span>
          <button class="speed-btn px-2 py-0.5 rounded-lg bg-blue-600/40 text-blue-300" data-speed="1">1x</button>
          <button class="speed-btn px-2 py-0.5 rounded-lg hover:text-white" data-speed="2">2x</button>
          <button class="speed-btn px-2 py-0.5 rounded-lg hover:text-white" data-speed="4">4x</button>
        </div>
      </div>

      <!-- Quick 1-Click Jump to Critical Game Events -->
      <div class="flex items-center gap-2">
        <span class="text-xs text-slate-400 font-semibold flex items-center gap-1">
          <i class="fa-solid fa-bolt text-amber-400"></i> Event Jumps:
        </span>
        <button class="jump-btn px-2.5 py-1 rounded-lg text-xs font-semibold glass hover:border-blue-500/40 text-blue-300" data-frame="11351">
          Turnover #1 (Barça Win)
        </button>
        <button class="jump-btn px-2.5 py-1 rounded-lg text-xs font-semibold glass hover:border-red-500/40 text-red-300" data-frame="12665">
          Turnover #2 (Athletic Counter)
        </button>
        <button class="jump-btn px-2.5 py-1 rounded-lg text-xs font-semibold glass hover:border-slate-500/40 text-slate-300" data-frame="15889">
          Foul / Stoppage (Dead Ball)
        </button>
        <button class="jump-btn px-2.5 py-1 rounded-lg text-xs font-semibold glass hover:border-emerald-500/40 text-emerald-300" data-frame="18389">
          Barça Goal Kick Restart
        </button>
      </div>
    </div>
  </footer>

  <script>
    const matchData = {data_str};
    const frames = matchData.frames;
    const pitch = matchData.pitch;

    const canvas = document.getElementById("pitchCanvas");
    const ctx = canvas.getContext("2d");
    const timelineCanvas = document.getElementById("timelineCanvas");
    const tlCtx = timelineCanvas.getContext("2d");
    const playhead = document.getElementById("timelinePlayhead");

    let currentIdx = 0;
    let isPlaying = true;
    let playbackSpeed = 1;
    let lastTime = 0;
    const baseFps = 8.3;

    function resizeCanvas() {{
      canvas.width = canvas.clientWidth * window.devicePixelRatio;
      canvas.height = canvas.clientHeight * window.devicePixelRatio;
      timelineCanvas.width = timelineCanvas.clientWidth * window.devicePixelRatio;
      timelineCanvas.height = timelineCanvas.clientHeight * window.devicePixelRatio;
      drawTimeline();
    }}
    window.addEventListener("resize", resizeCanvas);

    // Draw Static Football Pitch Lines
    function drawPitch() {{
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
      ctx.lineWidth = 2 * window.devicePixelRatio;

      // Touchlines
      ctx.strokeRect(10, 10, w - 20, h - 20);

      // Halfway line & Center Circle
      ctx.beginPath();
      ctx.moveTo(w / 2, 10);
      ctx.lineTo(w / 2, h - 10);
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(w / 2, h / 2, h * 0.15, 0, Math.PI * 2);
      ctx.stroke();

      // Penalty Boxes
      const boxW = w * 0.16;
      const boxH = h * 0.55;
      ctx.strokeRect(10, (h - boxH) / 2, boxW, boxH);
      ctx.strokeRect(w - 10 - boxW, (h - boxH) / 2, boxW, boxH);
    }}

    // Draw Possession Ribbon
    function drawTimeline() {{
      const tw = timelineCanvas.width;
      const th = timelineCanvas.height;
      tlCtx.clearRect(0, 0, tw, th);

      const n = frames.length;
      for (let i = 0; i < n; i++) {{
        const x = (i / n) * tw;
        const w = (1 / n) * tw + 1;
        const lbl = frames[i].l;
        if (lbl === "H") tlCtx.fillStyle = "#2563eb"; // Blue (Barcelona)
        else if (lbl === "A") tlCtx.fillStyle = "#dc2626"; // Red (Athletic)
        else tlCtx.fillStyle = "#334155"; // Dark Slate (Dead Ball)
        tlCtx.fillRect(x, 0, w, th);
      }}
    }}

    function renderFrame(idx) {{
      drawPitch();
      const f = frames[idx];
      const w = canvas.width;
      const h = canvas.height;

      // Draw Players
      f.p.forEach(p => {{
        const px = (p.x / pitch.len) * (w - 20) + 10;
        const py = (p.y / pitch.wid) * (h - 20) + 10;
        const radius = 6 * window.devicePixelRatio;

        ctx.beginPath();
        ctx.arc(px, py, radius, 0, Math.PI * 2);
        if (p.t === "H") {{
          ctx.fillStyle = "#1d4ed8"; // Barça
          ctx.strokeStyle = "#ef4444";
          ctx.lineWidth = 2 * window.devicePixelRatio;
          ctx.stroke();
        }} else {{
          ctx.fillStyle = "#ef4444"; // Athletic
          ctx.strokeStyle = "#ffffff";
          ctx.lineWidth = 2 * window.devicePixelRatio;
          ctx.stroke();
        }}
        ctx.fill();
      }});

      // Draw Ball
      if (f.b) {{
        const bx = (f.b[0] / pitch.len) * (w - 20) + 10;
        const by = (f.b[1] / pitch.wid) * (h - 20) + 10;

        // Pressure Ring (2.0m control radius)
        const ringRadius = (2.0 / pitch.wid) * (h - 20);
        ctx.beginPath();
        ctx.arc(bx, by, ringRadius, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(250, 204, 21, 0.35)";
        ctx.lineWidth = 1.5 * window.devicePixelRatio;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Ball Marker
        ctx.beginPath();
        ctx.arc(bx, by, 5 * window.devicePixelRatio, 0, Math.PI * 2);
        ctx.fillStyle = "#facc15";
        ctx.shadowColor = "#facc15";
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
      }}

      // Update UI Telemetry
      const pct = (idx / frames.length) * 100;
      playhead.style.left = pct + "%";
      document.getElementById("frameCounter").innerText = `Frame: ${{f.f}} / 18685`;

      const secTotal = Math.floor(f.f / 25);
      const mins = Math.floor(secTotal / 60);
      const secs = secTotal % 60;
      document.getElementById("matchClock").innerText = `${{mins.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;

      const badge = document.getElementById("possessionBadge");
      if (f.l === "H") {{
        badge.innerText = "FC Barcelona (H)";
        badge.className = "text-xs font-black px-3 py-1 rounded-full bg-blue-600/30 text-blue-400 border border-blue-500/40 uppercase tracking-wide";
      }} else if (f.l === "A") {{
        badge.innerText = "Athletic Club (A)";
        badge.className = "text-xs font-black px-3 py-1 rounded-full bg-red-600/30 text-red-400 border border-red-500/40 uppercase tracking-wide";
      }} else {{
        badge.innerText = "Dead Ball / Stoppage (D)";
        badge.className = "text-xs font-black px-3 py-1 rounded-full bg-slate-700/40 text-slate-400 border border-slate-600/40 uppercase tracking-wide";
      }}
    }}

    function animate(time) {{
      if (isPlaying) {{
        if (time - lastTime > (1000 / (baseFps * playbackSpeed))) {{
          currentIdx = (currentIdx + 1) % frames.length;
          renderFrame(currentIdx);
          lastTime = time;
        }}
      }}
      requestAnimationFrame(animate);
    }}

    // Controls
    document.getElementById("btnPlay").onclick = () => {{
      isPlaying = !isPlaying;
      document.getElementById("btnPlay").innerHTML = isPlaying ? '<i class="fa-solid fa-pause"></i>' : '<i class="fa-solid fa-play"></i>';
    }};

    document.getElementById("btnStepForward").onclick = () => {{
      isPlaying = false;
      document.getElementById("btnPlay").innerHTML = '<i class="fa-solid fa-play"></i>';
      currentIdx = (currentIdx + 1) % frames.length;
      renderFrame(currentIdx);
    }};

    document.getElementById("btnStepBack").onclick = () => {{
      isPlaying = false;
      document.getElementById("btnPlay").innerHTML = '<i class="fa-solid fa-play"></i>';
      currentIdx = (currentIdx - 1 + frames.length) % frames.length;
      renderFrame(currentIdx);
    }};

    document.querySelectorAll(".speed-btn").forEach(btn => {{
      btn.onclick = () => {{
        document.querySelectorAll(".speed-btn").forEach(b => b.className = "speed-btn px-2 py-0.5 rounded-lg hover:text-white");
        btn.className = "speed-btn px-2 py-0.5 rounded-lg bg-blue-600/40 text-blue-300";
        playbackSpeed = parseFloat(btn.dataset.speed);
      }};
    }});

    document.querySelectorAll(".jump-btn").forEach(btn => {{
      btn.onclick = () => {{
        const targetFrame = parseInt(btn.dataset.frame);
        // Find closest index
        let closest = 0;
        let minDiff = 999999;
        frames.forEach((f, i) => {{
          const diff = Math.abs(f.f - targetFrame);
          if (diff < minDiff) {{
            minDiff = diff;
            closest = i;
          }}
        }});
        currentIdx = closest;
        renderFrame(currentIdx);
        // Alert
        const alert = document.getElementById("turnoverAlert");
        document.getElementById("turnoverText").innerText = btn.innerText;
        alert.style.opacity = "1";
        setTimeout(() => alert.style.opacity = "0", 2500);
      }};
    }});

    // Timeline Scrub
    document.getElementById("timelineContainer").onclick = (e) => {{
      const rect = e.currentTarget.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const ratio = Math.max(0, Math.min(1, clickX / rect.width));
      currentIdx = Math.floor(ratio * frames.length);
      renderFrame(currentIdx);
    }};

    setTimeout(() => {{
      resizeCanvas();
      renderFrame(0);
      requestAnimationFrame(animate);
    }}, 100);
  </script>
</body>
</html>"""

out_html = os.path.join(ROOT, "viewer", "index.html")
with open(out_html, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated standalone Hero Flow: {out_html} ({os.path.getsize(out_html)/(1024*1024):.2f} MB)")
