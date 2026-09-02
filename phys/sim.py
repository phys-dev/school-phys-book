"""Интерактивные модели молекулярных явлений.

Каждая модель — это самостоятельный HTML-блок с расчётом на JavaScript.
Он одинаково работает в Jupyter и на собранном сайте, где ядра Python нет,
поэтому модели остаются живыми и в электронном пособии, и на уроке у доски.

Расчёт ведётся честно: частицы сталкиваются упруго, а в модели агрегатных
состояний используется потенциал Леннард-Джонса. Поэтому кристалл, жидкость
и газ получаются сами собой — из одного и того же взаимодействия молекул,
как и объясняет молекулярно-кинетическая теория.
"""

from __future__ import annotations

import json
from itertools import count

from IPython.display import HTML, display

_counter = count(1)

_CSS = """
<style>
.phys-sim {
  border: 1px solid rgba(128, 140, 155, 0.35);
  border-radius: 10px;
  padding: 12px 14px 10px;
  margin: 14px 0;
  background: rgba(127, 140, 155, 0.06);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
.phys-sim canvas { width: 100%; height: auto; display: block; border-radius: 6px;
  background: #fbfcfd; border: 1px solid rgba(128, 140, 155, 0.25); }
.phys-sim .ps-title { font-weight: 600; margin-bottom: 8px; font-size: 0.98em; }
.phys-sim .ps-row { display: flex; flex-wrap: wrap; gap: 12px 18px;
  align-items: center; margin-top: 10px; font-size: 0.9em; }
.phys-sim label { display: flex; align-items: center; gap: 8px; }
.phys-sim input[type=range] { width: 150px; accent-color: #3a8fb7; }
.phys-sim button { font: inherit; padding: 5px 13px; border-radius: 6px; cursor: pointer;
  border: 1px solid rgba(128, 140, 155, 0.5); background: rgba(58, 143, 183, 0.12); }
.phys-sim button:hover { background: rgba(58, 143, 183, 0.25); }
.phys-sim .ps-readout { margin-top: 8px; font-size: 0.88em; opacity: 0.85;
  font-variant-numeric: tabular-nums; }
.phys-sim .ps-hint { margin-top: 6px; font-size: 0.85em; opacity: 0.7; font-style: italic; }
</style>
"""

_SHELL = """
<div class="phys-sim" id="__ID__">
  <div class="ps-title">__TITLE__</div>
  <canvas id="__ID__-c" width="__W__" height="__H__"></canvas>
  __CONTROLS__
  <div class="ps-readout" id="__ID__-out"></div>
  __HINT__
</div>
<script>
(function () {
  const root = document.getElementById("__ID__");
  const cv = document.getElementById("__ID__-c");
  const ctx = cv.getContext("2d");
  const out = document.getElementById("__ID__-out");
  const P = __PARAMS__;
  const el = (n) => root.querySelector('[data-name="' + n + '"]');
  let running = true, visible = true;
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((e) => { visible = e[0].isIntersecting; })
      .observe(root);
  }
__BODY__
  function loop() {
    if (running && visible) { step(); draw(); }
    requestAnimationFrame(loop);
  }
  const play = el("play");
  if (play) play.onclick = () => {
    running = !running;
    play.textContent = running ? "⏸ Пауза" : "▶ Пуск";
  };
  const reset = el("reset");
  if (reset) reset.onclick = () => { init(); draw(); };
  // ползунки перерисовывают модель сразу, не дожидаясь следующего кадра:
  // так отклик мгновенный даже у моделей без анимации
  root.querySelectorAll('input[type=range]').forEach((inp) => {
    inp.addEventListener("input", () => draw());
  });
  init();
  draw();
  loop();
})();
</script>
"""


def _build(title, body, params, controls="", hint="", width=760, height=380):
    """Собрать HTML-блок модели: холст, органы управления и расчёт на JS."""
    uid = f"ps{next(_counter)}"
    hint_html = f'<div class="ps-hint">{hint}</div>' if hint else ""
    html = _CSS + (
        _SHELL.replace("__ID__", uid)
        .replace("__TITLE__", title)
        .replace("__W__", str(width))
        .replace("__H__", str(height))
        .replace("__CONTROLS__", controls)
        .replace("__HINT__", hint_html)
        .replace("__PARAMS__", json.dumps(params, ensure_ascii=False))
        .replace("__BODY__", body)
    )
    return HTML(html)


def _slider(name, label, lo, hi, value, step=1, suffix=""):
    return (
        f'<label>{label}'
        f'<input type="range" data-name="{name}" min="{lo}" max="{hi}" '
        f'step="{step}" value="{value}">'
        f'<span data-name="{name}-v">{value}{suffix}</span></label>'
    )


def _buttons(play="⏸ Пауза", reset="⟲ Заново"):
    return (
        f'<button data-name="play">{play}</button>'
        f'<button data-name="reset">{reset}</button>'
    )


_BROWNIAN = """
  let mol = [], big, trail = [], t0 = 0;
  const R = P.R, rm = P.rm, M = P.M;
  function temp() { return +el("T").value; }
  function speed() { return P.v0 * Math.sqrt(temp() / 300); }
  function init() {
    t0 = 0; trail = [];
    big = { x: cv.width / 2, y: cv.height / 2, vx: 0, vy: 0 };
    mol = [];
    const n = +el("N").value;
    for (let i = 0; i < n; i++) {
      const a = Math.random() * 2 * Math.PI, v = speed() * (0.6 + 0.8 * Math.random());
      let x, y, tries = 0;
      do {
        x = rm + Math.random() * (cv.width - 2 * rm);
        y = rm + Math.random() * (cv.height - 2 * rm);
        tries++;
      } while (Math.hypot(x - big.x, y - big.y) < R + rm + 2 && tries < 50);
      mol.push({ x: x, y: y, vx: v * Math.cos(a), vy: v * Math.sin(a) });
    }
  }
  function step() {
    t0++;
    // скорость молекул поддерживаем соответствующей выбранной температуре
    const target = speed();
    for (const m of mol) {
      const v = Math.hypot(m.vx, m.vy) || 1;
      const k = 1 + 0.02 * (target * 1.0 / v - 1);   // мягкий термостат
      m.vx *= k; m.vy *= k;
      m.x += m.vx; m.y += m.vy;
      if (m.x < rm) { m.x = rm; m.vx = Math.abs(m.vx); }
      if (m.x > cv.width - rm) { m.x = cv.width - rm; m.vx = -Math.abs(m.vx); }
      if (m.y < rm) { m.y = rm; m.vy = Math.abs(m.vy); }
      if (m.y > cv.height - rm) { m.y = cv.height - rm; m.vy = -Math.abs(m.vy); }
      // упругий удар молекулы о броуновскую частицу
      const dx = m.x - big.x, dy = m.y - big.y, d = Math.hypot(dx, dy);
      if (d < R + rm && d > 0) {
        const nx = dx / d, ny = dy / d;
        const dvx = m.vx - big.vx, dvy = m.vy - big.vy;
        const vn = dvx * nx + dvy * ny;
        if (vn < 0) {
          const j = 2 * vn / (1 / 1 + 1 / M);       // масса молекулы принята за 1
          m.vx -= j * nx / 1;      m.vy -= j * ny / 1;
          big.vx += j * nx / M;    big.vy += j * ny / M;
        }
        const push = R + rm - d + 0.5;
        m.x += nx * push; m.y += ny * push;
      }
    }
    big.x += big.vx; big.y += big.vy;
    if (big.x < R) { big.x = R; big.vx = Math.abs(big.vx); }
    if (big.x > cv.width - R) { big.x = cv.width - R; big.vx = -Math.abs(big.vx); }
    if (big.y < R) { big.y = R; big.vy = Math.abs(big.vy); }
    if (big.y > cv.height - R) { big.y = cv.height - R; big.vy = -Math.abs(big.vy); }
    if (t0 % 6 === 0) {
      trail.push([big.x, big.y]);
      if (trail.length > 220) trail.shift();
    }
  }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "rgba(90, 105, 120, 0.55)";
    for (const m of mol) {
      ctx.beginPath(); ctx.arc(m.x, m.y, rm, 0, 7); ctx.fill();
    }
    if (trail.length > 1) {
      ctx.strokeStyle = "#d1495b"; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.moveTo(trail[0][0], trail[0][1]);
      for (const p of trail) ctx.lineTo(p[0], p[1]);
      ctx.stroke();
    }
    ctx.beginPath(); ctx.arc(big.x, big.y, R, 0, 7);
    ctx.fillStyle = "#e07a5f"; ctx.fill();
    ctx.strokeStyle = "#8c3b2a"; ctx.lineWidth = 2; ctx.stroke();
    el("T-v").textContent = temp() + " К";
    el("N-v").textContent = el("N").value;
    const v = Math.hypot(big.vx, big.vy);
    out.textContent = "Молекул: " + mol.length
      + "   ·   скорость молекул при этой температуре: в "
      + (speed() / P.v0).toFixed(2) + " раза больше, чем при 300 К"
      + "   ·   скорость броуновской частицы: " + v.toFixed(2) + " (усл. ед.)";
  }
"""


def brownian(n=90, temperature=300, big_radius=16, big_mass=60):
    """Броуновское движение: тяжёлая частица под ударами молекул.

    Молекулы упруго сталкиваются с крупной частицей, и та начинает
    двигаться по ломаной — ровно так, как Ж. Перрен зарисовывал движение
    частиц гуммигута под микроскопом. Ползунок температуры меняет скорость
    молекул: чем горячее, тем чаще и сильнее удары.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("T", "Температура:", 100, 900, temperature, 25, " К")
        + _slider("N", "Число молекул:", 20, 200, n, 10)
        + _buttons()
        + "</div>"
    )
    return _build(
        "Модель броуновского движения",
        _BROWNIAN,
        {"R": big_radius, "rm": 3.0, "M": big_mass, "v0": 1.5},
        controls,
        hint="Красная линия — след броуновской частицы: положение отмечается "
             "через равные промежутки времени, как в опыте Перрена.",
    )


_DIFFUSION = """
  const BOX_H = P.boxH, GR_H = cv.height - P.boxH;
  let a = [], b = [], wall = true, hist = [], frame = 0;
  const r = P.r;
  function speed() { return P.v0 * Math.sqrt(+el("T").value / 300); }
  function make(list, x0, x1) {
    const n = P.n;
    for (let i = 0; i < n; i++) {
      const ang = Math.random() * 2 * Math.PI, v = speed() * (0.7 + 0.6 * Math.random());
      list.push({
        x: x0 + r + Math.random() * (x1 - x0 - 2 * r),
        y: r + Math.random() * (BOX_H - 2 * r),
        vx: v * Math.cos(ang), vy: v * Math.sin(ang),
      });
    }
  }
  function init() {
    a = []; b = []; hist = []; frame = 0; wall = true;
    const mid = cv.width / 2;
    make(a, 0, mid - 3);
    make(b, mid + 3, cv.width);
    const w = el("wall");
    if (w) w.textContent = "Убрать перегородку";
  }
  function walls(p) {
    if (p.x < r) { p.x = r; p.vx = Math.abs(p.vx); }
    if (p.x > cv.width - r) { p.x = cv.width - r; p.vx = -Math.abs(p.vx); }
    if (p.y < r) { p.y = r; p.vy = Math.abs(p.vy); }
    if (p.y > BOX_H - r) { p.y = BOX_H - r; p.vy = -Math.abs(p.vy); }
    if (wall) {
      const mid = cv.width / 2;
      if (p.x > mid - r && p.x < mid) { p.x = mid - r; p.vx = -Math.abs(p.vx); }
      if (p.x < mid + r && p.x >= mid) { p.x = mid + r; p.vx = Math.abs(p.vx); }
    }
  }
  function collide(p, q) {
    const dx = q.x - p.x, dy = q.y - p.y;
    const d2 = dx * dx + dy * dy;
    if (d2 > 4 * r * r || d2 === 0) return;
    const d = Math.sqrt(d2), nx = dx / d, ny = dy / d;
    const vn = (q.vx - p.vx) * nx + (q.vy - p.vy) * ny;
    if (vn > 0) return;                     // уже разлетаются
    p.vx += vn * nx; p.vy += vn * ny;       // равные массы: обмен нормальными
    q.vx -= vn * nx; q.vy -= vn * ny;       // составляющими скорости
    const push = (2 * r - d) / 2 + 0.1;
    p.x -= nx * push; p.y -= ny * push;
    q.x += nx * push; q.y += ny * push;
  }
  function step() {
    frame++;
    const all = a.concat(b);
    const target = speed();
    for (const p of all) {
      const v = Math.hypot(p.vx, p.vy) || 1;
      const k = 1 + 0.02 * (target / v - 1);
      p.vx *= k; p.vy *= k;
      p.x += p.vx; p.y += p.vy;
      walls(p);
    }
    for (let i = 0; i < all.length; i++)
      for (let j = i + 1; j < all.length; j++) collide(all[i], all[j]);
    if (frame % 3 === 0) {
      const mid = cv.width / 2;
      const left = a.filter((p) => p.x < mid).length / a.length;
      hist.push(left);
      if (hist.length > 260) hist.shift();
    }
  }
  function dots(list, color) {
    ctx.fillStyle = color;
    for (const p of list) { ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, 7); ctx.fill(); }
  }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, cv.width, BOX_H);
    dots(a, "#3a8fb7"); dots(b, "#d1495b");
    if (wall) {
      ctx.fillStyle = "#5b6570";
      ctx.fillRect(cv.width / 2 - 2.5, 0, 5, BOX_H);
    }
    // график: какая доля синих молекул осталась в левой половине
    const y0 = BOX_H + 8, h = GR_H - 22;
    ctx.strokeStyle = "#c9ced6"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(34, y0); ctx.lineTo(cv.width - 6, y0);
    ctx.moveTo(34, y0 + h); ctx.lineTo(cv.width - 6, y0 + h); ctx.stroke();
    ctx.setLineDash([4, 4]); ctx.beginPath();
    ctx.moveTo(34, y0 + h / 2); ctx.lineTo(cv.width - 6, y0 + h / 2);
    ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = "#5b6570"; ctx.font = "11px system-ui";
    ctx.fillText("100%", 2, y0 + 4); ctx.fillText("50%", 8, y0 + h / 2 + 4);
    ctx.fillText("0", 22, y0 + h + 4);
    if (hist.length > 1) {
      ctx.strokeStyle = "#3a8fb7"; ctx.lineWidth = 1.8; ctx.beginPath();
      hist.forEach((val, i) => {
        const x = 34 + i / 260 * (cv.width - 40);
        const y = y0 + h * (1 - val);
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      });
      ctx.stroke();
    }
    ctx.fillStyle = "#5b6570";
    ctx.fillText("доля синих молекул в левой половине", 40, cv.height - 4);
    el("T-v").textContent = el("T").value + " К";
    const mid = cv.width / 2;
    const left = a.filter((p) => p.x < mid).length / a.length;
    const right = b.filter((p) => p.x > mid).length / b.length;
    out.textContent = wall
      ? "Перегородка на месте: газы разделены. Слева синих 100 %, справа красных 100 %."
      : "Слева синих: " + (100 * left).toFixed(0) + " %"
        + "   ·   справа красных: " + (100 * right).toFixed(0) + " %"
        + "   ·   перемешивание идёт само собой и назад не поворачивает";
  }
  const wbtn = el("wall");
  if (wbtn) wbtn.onclick = () => {
    wall = !wall;
    wbtn.textContent = wall ? "Убрать перегородку" : "Вернуть перегородку";
  };
"""


def diffusion(n=70, temperature=300):
    """Диффузия двух газов: перегородка, а после её удаления — перемешивание.

    Молекулы сталкиваются друг с другом упруго, поэтому перемешивание идёт
    постепенно, а не мгновенно. График внизу показывает, как выравниваются
    концентрации, и что сам собой обратный процесс не идёт.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("T", "Температура:", 100, 900, temperature, 25, " К")
        + '<button data-name="wall">Убрать перегородку</button>'
        + _buttons()
        + "</div>"
    )
    return _build(
        "Модель диффузии газов",
        _DIFFUSION,
        {"n": n, "r": 4.0, "v0": 1.4, "boxH": 250},
        controls,
        hint="Повысьте температуру — и посмотрите, как изменится время "
             "перемешивания. Это тот же опыт, что с медным купоросом и водой, "
             "только за секунды.",
        height=340,
    )


_STATES = """
  // Молекулы притягиваются на больших расстояниях и отталкиваются на малых
  // (потенциал Леннард-Джонса). Ничего, кроме этого закона и температуры,
  // в модель не заложено: кристалл, жидкость и газ получаются сами.
  const SIG = P.sigma, EPS = P.eps, RC = 2.5 * SIG, RC2 = RC * RC;
  const DT = P.dt, SUB = P.sub, G = P.g, N = P.n;
  let p = [], neigh = [];
  function temp() { return +el("T").value / 100; }
  function init() {
    p = [];
    const step = 1.12 * SIG;                        // равновесное расстояние
    const cols = Math.floor(Math.sqrt(N * 1.6));
    const rows = Math.ceil(N / cols);
    const x0 = (cv.width - (cols - 0.5) * step) / 2;
    const y0 = cv.height - 12 - rows * step * 0.87;
    for (let i = 0; i < N; i++) {
      const r = Math.floor(i / cols), c = i % cols;
      p.push({
        x: x0 + c * step + (r % 2) * step / 2,
        y: y0 + r * step * 0.87,
        vx: (Math.random() - 0.5), vy: (Math.random() - 0.5),
        fx: 0, fy: 0,
      });
    }
    neigh = new Array(N).fill(0);
    forces();
  }
  function forces() {
    for (const q of p) { q.fx = 0; q.fy = G; }
    neigh = new Array(p.length).fill(0);
    for (let i = 0; i < p.length; i++) {
      for (let j = i + 1; j < p.length; j++) {
        let dx = p[j].x - p[i].x, dy = p[j].y - p[i].y;
        const r2 = dx * dx + dy * dy;
        if (r2 > RC2 || r2 === 0) continue;
        const s2 = SIG * SIG / r2, s6 = s2 * s2 * s2;
        // F = 24ε(2(σ/r)¹² − (σ/r)⁶)/r² · вектор
        let f = 24 * EPS * (2 * s6 * s6 - s6) / r2;
        f = Math.max(-P.fmax, Math.min(P.fmax, f));  // страховка от «взрыва»
        p[i].fx -= f * dx; p[i].fy -= f * dy;
        p[j].fx += f * dx; p[j].fy += f * dy;
        if (r2 < 1.55 * SIG * SIG) { neigh[i]++; neigh[j]++; }
      }
    }
  }
  function bounce(q) {
    const m = 4;
    if (q.x < m) { q.x = m; q.vx = Math.abs(q.vx); }
    if (q.x > cv.width - m) { q.x = cv.width - m; q.vx = -Math.abs(q.vx); }
    if (q.y < m) { q.y = m; q.vy = Math.abs(q.vy); }
    if (q.y > cv.height - m) { q.y = cv.height - m; q.vy = -Math.abs(q.vy); }
  }
  function step() {
    for (let s = 0; s < SUB; s++) {
      for (const q of p) {                       // скоростной алгоритм Верле
        q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT;
        q.x += q.vx * DT; q.y += q.vy * DT;
      }
      forces();
      for (const q of p) {
        q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT;
        bounce(q);
      }
    }
    // термостат: подгоняем среднюю кинетическую энергию под заданную температуру
    let ke = 0;
    for (const q of p) ke += 0.5 * (q.vx * q.vx + q.vy * q.vy);
    const cur = ke / p.length, want = temp();
    const k = Math.sqrt(1 + 0.06 * (want / Math.max(cur, 1e-6) - 1));
    for (const q of p) { q.vx *= k; q.vy *= k; }
  }
  function state() {
    const avg = neigh.reduce((s, v) => s + v, 0) / neigh.length;
    if (avg > 4.4) return ["твёрдое (кристалл)", "#2f6690"];
    if (avg > 2.2) return ["жидкое", "#3a8fb7"];
    return ["газообразное", "#d1495b"];
  }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, cv.width, cv.height);
    const [name, color] = state();
    // связи между близкими молекулами — видно решётку
    ctx.strokeStyle = "rgba(90, 105, 120, 0.28)"; ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < p.length; i++)
      for (let j = i + 1; j < p.length; j++) {
        const dx = p[j].x - p[i].x, dy = p[j].y - p[i].y;
        if (dx * dx + dy * dy < 1.45 * SIG * SIG) {
          ctx.moveTo(p[i].x, p[i].y); ctx.lineTo(p[j].x, p[j].y);
        }
      }
    ctx.stroke();
    ctx.fillStyle = color;
    for (const q of p) { ctx.beginPath(); ctx.arc(q.x, q.y, SIG * 0.42, 0, 7); ctx.fill(); }
    ctx.fillStyle = color; ctx.font = "600 14px system-ui";
    ctx.fillText("состояние: " + name, 12, 22);
    el("T-v").textContent = el("T").value;
    const avg = neigh.reduce((s, v) => s + v, 0) / neigh.length;
    out.textContent = "Условная температура: " + el("T").value
      + "   ·   в среднем соседей у молекулы: " + avg.toFixed(1)
      + "   ·   чем сильнее движение, тем меньше молекул удерживается рядом";
  }
"""


def states(n=120, temperature=15):
    """Три агрегатных состояния как результат борьбы притяжения и движения.

    Молекулы взаимодействуют по одному и тому же закону при любой температуре.
    Меняется только скорость их движения — и вещество само переходит из
    кристалла в жидкость, а затем в газ. Слабая «тяжесть» прижимает вещество
    ко дну сосуда, поэтому у жидкости видна свободная поверхность.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("T", "Температура (усл. ед.):", 2, 120, temperature, 1)
        + _buttons()
        + "</div>"
    )
    return _build(
        "Модель трёх агрегатных состояний вещества",
        _STATES,
        {"n": n, "sigma": 13.0, "eps": 1.0, "dt": 0.06, "sub": 3,
         "g": 0.03, "fmax": 6.0},
        controls,
        hint="Ведите ползунок медленно от 2 до 120 и обратно: кристалл плавится, "
             "жидкость испаряется, а при охлаждении газ снова собирается в каплю "
             "и застывает.",
        height=330,
    )


_PAIR = """
  const W = cv.width, H = cv.height;
  const R0 = P.r0;                       // равновесное расстояние, пиксели
  let phase = 0;
  function dist() { return +el("r").value; }
  function force(r) {                    // Леннард-Джонс, нормирован на максимум
    const s = R0 / 1.122, x = s / r, x6 = Math.pow(x, 6);
    return 24 * (2 * x6 * x6 - x6) / r * P.fscale;
  }
  function energy(r) {
    const s = R0 / 1.122, x = s / r, x6 = Math.pow(x, 6);
    return 4 * (x6 * x6 - x6) * P.escale;
  }
  function init() { phase = 0; }
  function step() { phase += 0.08; }
  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, W, H);
    const r = dist();
    const cx = W * 0.27, cy = 78;
    const wob = 1.5 * Math.sin(phase);
    // две молекулы
    const x1 = cx - r / 2 - wob, x2 = cx + r / 2 + wob;
    ctx.strokeStyle = "#c9ced6"; ctx.setLineDash([3, 4]);
    ctx.beginPath(); ctx.moveTo(x1, cy); ctx.lineTo(x2, cy); ctx.stroke();
    ctx.setLineDash([]);
    for (const [x, col] of [[x1, "#2f6690"], [x2, "#3a8fb7"]]) {
      ctx.beginPath(); ctx.arc(x, cy, P.rad, 0, 7);
      ctx.fillStyle = col; ctx.fill();
    }
    // стрелки сил, действующих на молекулы
    const f = force(r);
    const len = Math.max(-60, Math.min(60, f * 240));
    ctx.strokeStyle = f > 0 ? "#d1495b" : "#2a9d5c";
    ctx.fillStyle = ctx.strokeStyle; ctx.lineWidth = 2.5;
    for (const [x, sgn] of [[x1, -1], [x2, 1]]) {
      const tip = x + sgn * len;
      ctx.beginPath(); ctx.moveTo(x, cy); ctx.lineTo(tip, cy); ctx.stroke();
      const d = Math.sign(len) * sgn;
      ctx.beginPath();
      ctx.moveTo(tip, cy); ctx.lineTo(tip - d * 8, cy - 5);
      ctx.lineTo(tip - d * 8, cy + 5); ctx.closePath(); ctx.fill();
    }
    ctx.font = "13px system-ui"; ctx.fillStyle = "#333";
    const label = Math.abs(f) < 0.004 ? "силы уравновешены"
                : (f > 0 ? "преобладает отталкивание" : "преобладает притяжение");
    ctx.fillText(label, 12, 22);
    ctx.fillText("r = " + (r / R0).toFixed(2) + " r₀", 12, 42);
    // график силы
    const gx = W * 0.52, gy = 30, gw = W - gx - 24, gh = H - 62;
    ctx.strokeStyle = "#c9ced6"; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(gx, gy + gh / 2); ctx.lineTo(gx + gw, gy + gh / 2);
    ctx.moveTo(gx, gy); ctx.lineTo(gx, gy + gh); ctx.stroke();
    ctx.fillStyle = "#5b6570"; ctx.font = "11px system-ui";
    ctx.fillText("F", gx + 4, gy + 9);
    ctx.fillText("r", gx + gw - 8, gy + gh / 2 + 14);
    ctx.fillText("отталкивание", gx + 6, gy + 22);
    ctx.fillText("притяжение", gx + 6, gy + gh - 6);
    const rmin = 0.85 * R0, rmax = 3.0 * R0;
    ctx.strokeStyle = "#2f6690"; ctx.lineWidth = 2; ctx.beginPath();
    for (let i = 0; i <= 200; i++) {
      const rr = rmin + (rmax - rmin) * i / 200;
      const val = Math.max(-1, Math.min(1, force(rr) * 34));
      const X = gx + gw * (rr - rmin) / (rmax - rmin);
      const Y = gy + gh / 2 - val * gh * 0.45;
      i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y);
    }
    ctx.stroke();
    // текущая точка на графике
    const X = gx + gw * (r - rmin) / (rmax - rmin);
    const val = Math.max(-1, Math.min(1, f * 34));
    const Y = gy + gh / 2 - val * gh * 0.45;
    ctx.beginPath(); ctx.arc(X, Y, 5, 0, 7);
    ctx.fillStyle = "#e07a5f"; ctx.fill();
    ctx.strokeStyle = "#e07a5f"; ctx.setLineDash([2, 3]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(X, gy + gh / 2); ctx.lineTo(X, Y); ctx.stroke();
    ctx.setLineDash([]);
    // отметка равновесного расстояния
    const Xe = gx + gw * (R0 - rmin) / (rmax - rmin);
    ctx.strokeStyle = "#5b6570"; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(Xe, gy); ctx.lineTo(Xe, gy + gh); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#5b6570"; ctx.fillText("r₀", Xe - 5, gy + gh + 12);
    el("r-v").textContent = (r / R0).toFixed(2) + " r₀";
    out.textContent = "Потенциальная энергия взаимодействия: "
      + energy(r).toFixed(2) + " (усл. ед.)   ·   на расстоянии r₀ сила равна нулю — "
      + "это положение равновесия, около которого молекулы и колеблются";
  }
"""


def molecule_pair(r0=70):
    """Притяжение и отталкивание двух молекул в зависимости от расстояния.

    Аналог опыта с двумя тележками (магниты — притяжение, пружины —
    отталкивание) из § 2 учебника, но здесь сразу видно и график силы.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("r", "Расстояние между молекулами:", 60, 210, 78, 1)
        + "</div>"
    )
    return _build(
        "Взаимодействие двух молекул",
        _PAIR,
        {"r0": r0, "rad": 17, "fscale": 0.02, "escale": 1.0},
        controls,
        hint="Сдвиньте молекулы ближе r₀ — они начнут отталкиваться; разведите "
             "дальше — притягиваться. На расстоянии в несколько размеров молекулы "
             "взаимодействие практически исчезает.",
        height=200,
    )


_LADDER = """
  const W = cv.width, H = cv.height, OBJ = P.objects;
  const LO = P.lo, HI = P.hi;
  function pos() { return +el("k").value / 10; }     // показатель степени
  function init() {}
  function step() {}
  function nearest(e) {
    let best = OBJ[0];
    for (const o of OBJ) if (Math.abs(o.e - e) < Math.abs(best.e - e)) best = o;
    return best;
  }
  function xOf(e) { return 46 + (W - 92) * (e - LO) / (HI - LO); }
  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, W, H);
    const e = pos(), y = H - 54;
    ctx.strokeStyle = "#5b6570"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(40, y); ctx.lineTo(W - 40, y); ctx.stroke();
    ctx.font = "10px system-ui"; ctx.textAlign = "center";
    for (let k = LO; k <= HI; k += 2) {
      const X = xOf(k);
      ctx.strokeStyle = "#c9ced6"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(X, y - 5); ctx.lineTo(X, y + 5); ctx.stroke();
      ctx.fillStyle = "#5b6570";
      ctx.fillText("10" + String(k).replace(/-/g, "⁻")
        .replace(/0/g, "⁰").replace(/1/g, "¹").replace(/2/g, "²")
        .replace(/3/g, "³").replace(/4/g, "⁴").replace(/5/g, "⁵")
        .replace(/6/g, "⁶").replace(/7/g, "⁷").replace(/8/g, "⁸")
        .replace(/9/g, "⁹"), X, y + 20);
    }
    ctx.fillStyle = "#5b6570"; ctx.fillText("метры", W - 20, y + 20);
    for (const o of OBJ) {
      const X = xOf(o.e);
      ctx.beginPath(); ctx.arc(X, y, 3.5, 0, 7);
      ctx.fillStyle = Math.abs(o.e - e) < 0.6 ? "#e07a5f" : "#9aa4b0"; ctx.fill();
    }
    const X = xOf(e);
    ctx.strokeStyle = "#e07a5f"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(X, y - 22); ctx.lineTo(X, y + 8); ctx.stroke();
    const o = nearest(e);
    ctx.textAlign = "left";
    ctx.font = "600 17px system-ui"; ctx.fillStyle = "#2f6690";
    ctx.fillText(o.name, 42, 34);
    ctx.font = "13px system-ui"; ctx.fillStyle = "#444";
    ctx.fillText(o.size, 42, 56);
    ctx.fillText(o.note, 42, 78);
    // во сколько раз больше атома
    const times = Math.pow(10, o.e + 10);
    let cmp;
    if (o.e < -10) cmp = "меньше атома в " + (1 / times).toExponential(0)
      .replace("e+", " · 10^") + " раз";
    else cmp = "больше атома примерно в 10" + ("" + Math.round(o.e + 10))
      .replace(/-/g, "⁻").replace(/0/g, "⁰").replace(/1/g, "¹")
      .replace(/2/g, "²").replace(/3/g, "³").replace(/4/g, "⁴")
      .replace(/5/g, "⁵").replace(/6/g, "⁶").replace(/7/g, "⁷")
      .replace(/8/g, "⁸").replace(/9/g, "⁹") + " раз";
    ctx.fillStyle = "#8a5a44"; ctx.fillText(cmp, 42, 100);
    el("k-v").textContent = "10^" + e.toFixed(1) + " м";
    out.textContent = "Атом (10⁻¹⁰ м) стоит ровно посередине между размером "
      + "атомного ядра и размером человека — и настолько же человек мал "
      + "по сравнению с расстоянием до ближайших звёзд.";
  }
"""


def scale_ladder():
    """Шкала размеров от атомного ядра до наблюдаемой Вселенной.

    Помогает почувствовать, насколько мал атом: расстояние по порядкам
    величины от ядра до атома примерно такое же, как от атома до песчинки.
    """
    objects = [
        {"e": -15, "name": "Атомное ядро", "size": "≈ 10⁻¹⁵ м = 1 фм",
         "note": "в 100 000 раз меньше самого атома"},
        {"e": -10, "name": "Атом", "size": "≈ 10⁻¹⁰ м = 0,1 нм",
         "note": "размер, о котором говорит § 1 учебника"},
        {"e": -9, "name": "Молекула воды", "size": "≈ 3 · 10⁻¹⁰ м",
         "note": "чуть больше атома: три атома вместе"},
        {"e": -8, "name": "Молекула ДНК (толщина)", "size": "≈ 2 · 10⁻⁹ м",
         "note": "сложные молекулы бывают гораздо крупнее простых"},
        {"e": -7, "name": "Вирус", "size": "≈ 10⁻⁷ м",
         "note": "состоит уже из миллионов атомов"},
        {"e": -5, "name": "Клетка крови", "size": "≈ 10⁻⁵ м",
         "note": "видна в школьный микроскоп"},
        {"e": -4, "name": "Толщина волоса", "size": "≈ 10⁻⁴ м = 0,1 мм",
         "note": "предел того, что различает глаз"},
        {"e": -3, "name": "Пылинка, капля тумана", "size": "≈ 10⁻³ м",
         "note": "в такой пылинке уже 10¹⁶ молекул"},
        {"e": 0, "name": "Человек", "size": "≈ 1,7 м",
         "note": "в человеке около 10²⁷ атомов"},
        {"e": 4, "name": "Гора Эверест", "size": "≈ 9 · 10³ м", "note": "8848 м над уровнем моря"},
        {"e": 7, "name": "Земля", "size": "≈ 1,3 · 10⁷ м", "note": "диаметр планеты"},
        {"e": 9, "name": "Солнце", "size": "≈ 1,4 · 10⁹ м", "note": "в 109 раз шире Земли"},
        {"e": 11, "name": "Орбита Земли", "size": "≈ 3 · 10¹¹ м",
         "note": "1 астрономическая единица ≈ 1,5 · 10¹¹ м"},
        {"e": 13, "name": "Орбита Нептуна", "size": "≈ 9 · 10¹² м", "note": "край планетной системы"},
        {"e": 16, "name": "До ближайшей звезды", "size": "≈ 4 · 10¹⁶ м",
         "note": "Проксима Центавра, 4,2 светового года"},
        {"e": 21, "name": "Наша Галактика", "size": "≈ 10²¹ м",
         "note": "Млечный Путь, около 100 000 световых лет"},
        {"e": 26, "name": "Наблюдаемая Вселенная", "size": "≈ 8,8 · 10²⁶ м",
         "note": "самый большой известный масштаб"},
    ]
    controls = (
        '<div class="ps-row">'
        + _slider("k", "Размер:", -150, 260, -100, 1)
        + "</div>"
    )
    return _build(
        "Шкала размеров: от атомного ядра до Вселенной",
        _LADDER,
        {"objects": objects, "lo": -15, "hi": 26},
        controls,
        hint="Каждый шаг вправо — это увеличение размера в 10 раз. "
             "Атом мал настолько же, насколько велика Галактика.",
        height=180,
    )


_CRYSTAL = """
  // Расплав охлаждается с той скоростью, которую вы задали. Медленное охлаждение
  // даёт кристалл, быстрое — аморфное тело (стекло). Больше ничего не меняется.
  const SIG = P.sigma, EPS = P.eps, RC = 2.5 * SIG, RC2 = RC * RC;
  const DT = P.dt, SUB = P.sub, N = P.n;
  let p = [], neigh = [], T = P.tHot, cooling = false, steps = 0;
  function init() {
    p = []; T = P.tHot; cooling = false; steps = 0;
    for (let i = 0; i < N; i++) {
      p.push({ x: 20 + Math.random() * (cv.width - 40),
               y: 20 + Math.random() * (cv.height - 40),
               vx: (Math.random() - 0.5) * 4, vy: (Math.random() - 0.5) * 4,
               fx: 0, fy: 0 });
    }
    neigh = new Array(N).fill(0);
    forces();
    const b = el("cool");
    if (b) b.textContent = "Охладить расплав";
  }
  function forces() {
    for (const q of p) { q.fx = 0; q.fy = P.g; }
    neigh = new Array(p.length).fill(0);
    for (let i = 0; i < p.length; i++)
      for (let j = i + 1; j < p.length; j++) {
        const dx = p[j].x - p[i].x, dy = p[j].y - p[i].y;
        const r2 = dx * dx + dy * dy;
        if (r2 > RC2 || r2 === 0) continue;
        const s2 = SIG * SIG / r2, s6 = s2 * s2 * s2;
        let f = 24 * EPS * (2 * s6 * s6 - s6) / r2;
        f = Math.max(-P.fmax, Math.min(P.fmax, f));
        p[i].fx -= f * dx; p[i].fy -= f * dy;
        p[j].fx += f * dx; p[j].fy += f * dy;
        if (r2 < 1.5 * SIG * SIG) { neigh[i]++; neigh[j]++; }
      }
  }
  function wall(q) {
    const m = 5;
    if (q.x < m) { q.x = m; q.vx = Math.abs(q.vx); }
    if (q.x > cv.width - m) { q.x = cv.width - m; q.vx = -Math.abs(q.vx); }
    if (q.y < m) { q.y = m; q.vy = Math.abs(q.vy); }
    if (q.y > cv.height - m) { q.y = cv.height - m; q.vy = -Math.abs(q.vy); }
  }
  function step() {
    steps++;
    for (let s = 0; s < SUB; s++) {
      for (const q of p) {
        q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT;
        q.x += q.vx * DT; q.y += q.vy * DT;
      }
      forces();
      for (const q of p) {
        q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT;
        wall(q);
      }
    }
    if (cooling && T > P.tCold) {
      T -= +el("rate").value * 2e-4;      // скорость охлаждения задаёт ползунок
      if (T < P.tCold) T = P.tCold;
    }
    let ke = 0;
    for (const q of p) ke += 0.5 * (q.vx * q.vx + q.vy * q.vy);
    const cur = ke / p.length;
    const k = Math.sqrt(1 + 0.05 * (T / Math.max(cur, 1e-6) - 1));
    for (const q of p) { q.vx *= k; q.vy *= k; }
  }
  function order() {
    // доля частиц, у которых ровно 6 соседей — в плоскости это признак
    // правильной треугольной упаковки, то есть кристалла
    let good = 0;
    for (const n of neigh) if (n >= 5 && n <= 7) good++;
    return good / neigh.length;
  }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, cv.width, cv.height);
    const ord = order();
    ctx.strokeStyle = "rgba(90, 105, 120, 0.3)"; ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < p.length; i++)
      for (let j = i + 1; j < p.length; j++) {
        const dx = p[j].x - p[i].x, dy = p[j].y - p[i].y;
        if (dx * dx + dy * dy < 1.4 * SIG * SIG) {
          ctx.moveTo(p[i].x, p[i].y); ctx.lineTo(p[j].x, p[j].y);
        }
      }
    ctx.stroke();
    for (let i = 0; i < p.length; i++) {
      // частицы с правильным окружением — синие, с нарушенным — оранжевые
      const ok = neigh[i] >= 5 && neigh[i] <= 7;
      ctx.beginPath(); ctx.arc(p[i].x, p[i].y, SIG * 0.4, 0, 7);
      ctx.fillStyle = ok ? "#2f6690" : "#e07a5f"; ctx.fill();
    }
    let name, color;
    if (T > P.tMelt) { name = "расплав (жидкость)"; color = "#d1495b"; }
    else if (ord > P.ordCrystal) { name = "кристалл — порядок дальний"; color = "#2f6690"; }
    else { name = "аморфное тело (стекло) — порядок только ближний"; color = "#e07a5f"; }
    ctx.fillStyle = color; ctx.font = "600 14px system-ui";
    ctx.fillText(name, 12, 22);
    el("rate-v").textContent = (+el("rate").value / 10).toFixed(1);
    out.textContent = "Температура: " + (T * 100).toFixed(0)
      + "   ·   доля частиц с правильным окружением: " + (100 * ord).toFixed(0) + " %"
      + (cooling ? "   ·   идёт охлаждение" : "   ·   нажмите «Охладить расплав»");
  }
  const cbtn = el("cool");
  if (cbtn) cbtn.onclick = () => {
    cooling = !cooling;
    cbtn.textContent = cooling ? "Пауза охлаждения" : "Охладить расплав";
  };
"""


def crystallization(n=220, rate=6):
    """Кристалл или стекло — зависит от того, как быстро охлаждать расплав.

    Модель начинается с горячей жидкости. Медленное охлаждение даёт молекулам
    время занять места в решётке, и вырастает кристалл. При быстром охлаждении
    молекулы застывают там, где их застигло, — получается аморфное тело.
    """
    controls = (
        '<div class="ps-row">'
        + '<button data-name="cool">Охладить расплав</button>'
        + _slider("rate", "Скорость охлаждения:", 1, 40, rate, 1)
        + _buttons()
        + "</div>"
    )
    return _build(
        "От расплава к кристаллу или к стеклу",
        _CRYSTAL,
        {"n": n, "sigma": 13.0, "eps": 1.0, "dt": 0.05, "sub": 3, "fmax": 6.0,
         "g": 0.08, "tHot": 0.4, "tCold": 0.02, "tMelt": 0.25, "ordCrystal": 0.35},
        controls,
        hint="Сначала охладите расплав медленно (ползунок влево) — вырастет решётка. "
             "Потом нажмите «Заново» и охладите быстро: получится стекло. "
             "Синие частицы стоят правильно, оранжевые — с нарушением порядка.",
        height=330,
    )


_WETTING = """
  // Капля жидкости на поверхности. Молекулы притягиваются друг к другу (как всегда),
  // а ползунок задаёт, насколько сильно они притягиваются к самой поверхности.
  // Из соотношения этих двух притяжений и получается смачивание или несмачивание.
  const SIG = P.sigma, EPS = P.eps, RC = 2.5 * SIG, RC2 = RC * RC;
  const DT = P.dt, SUB = P.sub, N = P.n, FLOOR = cv.height - 26;
  let p = [];
  function wallPull() { return +el("w").value / 20; }
  function init() {
    p = [];
    const cols = Math.ceil(Math.sqrt(N)), step = 1.1 * SIG;
    const x0 = cv.width / 2 - cols * step / 2;
    for (let i = 0; i < N; i++) {
      p.push({ x: x0 + (i % cols) * step + Math.random(),
               y: FLOOR - 10 - Math.floor(i / cols) * step,
               vx: 0, vy: 0, fx: 0, fy: 0 });
    }
    forces();
  }
  function forces() {
    const W = wallPull();
    for (const q of p) {
      q.fx = 0; q.fy = P.g;
      const d = FLOOR - q.y;                       // расстояние до поверхности
      if (d < 2.5 * SIG) q.fy += W * (1 - d / (2.5 * SIG));   // притяжение к стенке
    }
    for (let i = 0; i < p.length; i++)
      for (let j = i + 1; j < p.length; j++) {
        const dx = p[j].x - p[i].x, dy = p[j].y - p[i].y;
        const r2 = dx * dx + dy * dy;
        if (r2 > RC2 || r2 === 0) continue;
        const s2 = SIG * SIG / r2, s6 = s2 * s2 * s2;
        let f = 24 * EPS * (2 * s6 * s6 - s6) / r2;
        f = Math.max(-P.fmax, Math.min(P.fmax, f));
        p[i].fx -= f * dx; p[i].fy -= f * dy;
        p[j].fx += f * dx; p[j].fy += f * dy;
      }
  }
  function step() {
    for (let s = 0; s < SUB; s++) {
      for (const q of p) {
        q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT;
        q.x += q.vx * DT; q.y += q.vy * DT;
      }
      forces();
      for (const q of p) {
        q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT;
        if (q.x < 6) { q.x = 6; q.vx = Math.abs(q.vx); }
        if (q.x > cv.width - 6) { q.x = cv.width - 6; q.vx = -Math.abs(q.vx); }
        if (q.y > FLOOR - 3) { q.y = FLOOR - 3; q.vy = -Math.abs(q.vy) * 0.5; }
        if (q.y < 6) { q.y = 6; q.vy = Math.abs(q.vy); }
      }
    }
    let ke = 0;
    for (const q of p) ke += 0.5 * (q.vx * q.vx + q.vy * q.vy);
    const k = Math.sqrt(1 + 0.05 * (P.temp / Math.max(ke / p.length, 1e-6) - 1));
    for (const q of p) { q.vx *= k; q.vy *= k; }
  }
  function shape() {
    const xs = p.map((q) => q.x), ys = p.map((q) => q.y);
    const shirina = Math.max(...xs) - Math.min(...xs);
    const vysota = FLOOR - Math.min(...ys);
    return { shirina, vysota, otnoshenie: vysota / Math.max(shirina, 1) };
  }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#5b6570";
    ctx.fillRect(0, FLOOR, cv.width, cv.height - FLOOR);   // поверхность
    ctx.fillStyle = "#3a8fb7";
    for (const q of p) { ctx.beginPath(); ctx.arc(q.x, q.y, SIG * 0.42, 0, 7); ctx.fill(); }
    const s = shape();
    const smachivaet = s.otnoshenie < P.porog;
    ctx.fillStyle = smachivaet ? "#2a9d5c" : "#d1495b";
    ctx.font = "600 14px system-ui";
    ctx.fillText(smachivaet ? "жидкость смачивает поверхность — растекается"
                            : "жидкость не смачивает — собирается в каплю", 12, 22);
    el("w-v").textContent = wallPull().toFixed(1);
    out.textContent = "Ширина капли: " + s.shirina.toFixed(0)
      + "   ·   высота: " + s.vysota.toFixed(0)
      + "   ·   отношение высоты к ширине: " + s.otnoshenie.toFixed(2)
      + (smachivaet ? "   ·   притяжение к поверхности пересиливает"
                    : "   ·   молекулы сильнее держатся друг за друга");
  }
"""


def wetting(n=90, wall_pull=4):
    """Смачивание и несмачивание: капля растекается или собирается в шарик.

    Ползунок задаёт притяжение молекул жидкости к поверхности. Если оно больше
    притяжения молекул друг к другу — жидкость растекается (смачивает), если
    меньше — собирается в каплю (не смачивает). Ровно так это объясняет § 3.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("w", "Притяжение к поверхности:", 0, 24, wall_pull, 1)
        + _buttons()
        + "</div>"
    )
    return _build(
        "Смачивание: капля на поверхности",
        _WETTING,
        {"n": n, "sigma": 12.0, "eps": 1.0, "dt": 0.05, "sub": 6, "fmax": 6.0,
         "g": 0.02, "temp": 0.12, "porog": 0.45},
        controls,
        hint="Слева ползунка — поверхность вроде жирной или воскованной: капля стоит "
             "шариком. Справа — чистое стекло: вода растекается плёнкой.",
        height=300,
    )


_CAPILLARY = """
  // Подъём смачивающей жидкости в трубках разного радиуса.
  // Высота считается по формуле h = 2σ cos θ / (ρ g r): чем тоньше трубка,
  // тем выше поднимается жидкость.
  const RHO = P.rho, G = P.g, SIGMA = P.sigma;
  let t = 0;
  const tubes = P.tubes;               // радиусы трубок в миллиметрах
  function theta() { return +el("th").value; }     // краевой угол, градусы
  function height(rmm) {
    const r = rmm / 1000;
    return 2 * SIGMA * Math.cos(theta() * Math.PI / 180) / (RHO * G * r);  // м
  }
  function init() { t = 0; }
  function step() { t += 0.02; }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, cv.width, cv.height);
    const base = cv.height - 60, mash = P.mash;   // пикселей на метр подъёма
    // сосуд с жидкостью
    ctx.fillStyle = "rgba(58, 143, 183, 0.35)";
    ctx.fillRect(0, base, cv.width, 60);
    ctx.strokeStyle = "#5b6570"; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(0, base); ctx.lineTo(cv.width, base); ctx.stroke();
    const smachivaet = theta() < 90;
    tubes.forEach((rmm, i) => {
      const x = 90 + i * ((cv.width - 150) / (tubes.length - 1));
      const w = Math.max(7, rmm * P.pxmm);          // ширина трубки на рисунке
      let h = height(rmm) * mash;
      h = Math.max(-base + 30, Math.min(base - 30, h));
      // стенки трубки
      ctx.strokeStyle = "#5b6570"; ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x - w / 2, 24); ctx.lineTo(x - w / 2, base + 45);
      ctx.moveTo(x + w / 2, 24); ctx.lineTo(x + w / 2, base + 45);
      ctx.stroke();
      // столбик жидкости
      ctx.fillStyle = "rgba(58, 143, 183, 0.75)";
      const top = base - h;
      ctx.fillRect(x - w / 2 + 1, Math.min(top, base), w - 2, Math.abs(h) + (h > 0 ? 0 : 0));
      // мениск: вогнутый при смачивании, выпуклый при несмачивании
      ctx.beginPath();
      ctx.moveTo(x - w / 2 + 1, top);
      ctx.quadraticCurveTo(x, top + (smachivaet ? w * 0.5 : -w * 0.5), x + w / 2 - 1, top);
      ctx.lineTo(x + w / 2 - 1, top + 4); ctx.lineTo(x - w / 2 + 1, top + 4);
      ctx.closePath();
      ctx.fillStyle = smachivaet ? "#fbfcfd" : "rgba(58, 143, 183, 0.75)";
      ctx.fill();
      // подписи
      ctx.fillStyle = "#5b6570"; ctx.font = "11px system-ui"; ctx.textAlign = "center";
      ctx.fillText("r = " + rmm + " мм", x, base + 58);
      ctx.fillStyle = "#2f6690"; ctx.font = "600 12px system-ui";
      const hmm = height(rmm) * 1000;
      ctx.fillText((hmm >= 0 ? "+" : "") + hmm.toFixed(0) + " мм", x, Math.min(top, base) - 8);
    });
    ctx.textAlign = "left";
    ctx.fillStyle = smachivaet ? "#2a9d5c" : "#d1495b";
    ctx.font = "600 14px system-ui";
    ctx.fillText(smachivaet ? "жидкость смачивает стенки — поднимается"
                            : "жидкость не смачивает — опускается", 12, 18);
    el("th-v").textContent = theta() + "°";
    const h1 = height(tubes[0]) * 1000, h2 = height(tubes[tubes.length - 1]) * 1000;
    out.textContent = "Высота подъёма обратно пропорциональна радиусу: "
      + "в трубке " + tubes[0] + " мм — " + h1.toFixed(0) + " мм, "
      + "в трубке " + tubes[tubes.length - 1] + " мм — " + h2.toFixed(0) + " мм. "
      + "Радиус больше в " + (tubes[tubes.length - 1] / tubes[0]).toFixed(0)
      + " раз — подъём во столько же раз меньше.";
  }
"""


def capillary(theta=20):
    """Капиллярные явления: чем тоньше трубка, тем выше поднимается жидкость.

    Высота считается по формуле $h = 2\\sigma\\cos\\theta/(\\rho g r)$ для воды.
    Ползунок меняет краевой угол: до 90° жидкость смачивает стенки и поднимается,
    больше 90° — не смачивает и опускается, как ртуть в стеклянной трубке.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("th", "Краевой угол:", 0, 140, theta, 5, "°")
        + "</div>"
    )
    return _build(
        "Жидкость в капиллярах разного радиуса",
        _CAPILLARY,
        {"tubes": [0.1, 0.2, 0.5, 1.0, 2.0], "rho": 1000, "g": 9.8,
         "sigma": 0.073, "mash": 900, "pxmm": 26},
        controls,
        hint="Поверхностное натяжение воды 0,073 Н/м. Обратите внимание на форму "
             "поверхности: у смачивающей жидкости она вогнутая, у несмачивающей — выпуклая.",
        height=330,
    )


_EXPANSION = """
  // Почему тела расширяются при нагревании. Молекула колеблется в «яме»
  // потенциальной энергии. Яма несимметрична: влево стенка круче, чем вправо.
  // Поэтому с ростом энергии середина размаха уезжает вправо — среднее
  // расстояние между молекулами растёт. Это и есть тепловое расширение.
  const SIG = P.sigma, R0 = Math.pow(2, 1 / 6) * SIG;
  let phase = 0;
  function energy() { return -1 + +el("T").value / 100; }   // от -1 (дно ямы) вверх
  function U(r) {
    const x = SIG / r, x6 = Math.pow(x, 6);
    return 4 * (x6 * x6 - x6);          // в единицах глубины ямы
  }
  function roots() {
    // границы колебаний: там, где потенциальная энергия равна полной
    const E = energy();
    let a = R0, b = R0;
    for (let r = R0; r > 0.8 * SIG; r -= 0.0005 * SIG) { if (U(r) >= E) { a = r; break; } }
    for (let r = R0; r < 6 * SIG; r += 0.0005 * SIG) { if (U(r) >= E) { b = r; break; } }
    return { a, b, sred: (a + b) / 2 };
  }
  function init() { phase = 0; }
  function step() { phase += 0.06; }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, cv.width, cv.height);
    const { a, b, sred } = roots();
    const E = energy();
    const gx = 60, gy = 26, gw = cv.width - 100, gh = cv.height - 96;
    const rmin = 0.95 * SIG, rmax = 3.2 * SIG;
    const X = (r) => gx + gw * (r - rmin) / (rmax - rmin);
    const Y = (u) => gy + gh * (u + 1.15) / 1.55;      // энергия от -1.15 до 0.4
    // оси
    ctx.strokeStyle = "#c9ced6"; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(gx, Y(0)); ctx.lineTo(gx + gw, Y(0));
    ctx.moveTo(gx, gy); ctx.lineTo(gx, gy + gh); ctx.stroke();
    ctx.fillStyle = "#5b6570"; ctx.font = "11px system-ui";
    ctx.fillText("энергия", 6, gy + 8);
    ctx.fillText("расстояние между молекулами", gx + gw - 190, Y(0) + 16);
    // кривая потенциальной энергии
    ctx.strokeStyle = "#2f6690"; ctx.lineWidth = 2.2; ctx.beginPath();
    for (let i = 0; i <= 400; i++) {
      const r = rmin + (rmax - rmin) * i / 400;
      const u = Math.max(-1.15, Math.min(0.4, U(r)));
      i ? ctx.lineTo(X(r), Y(u)) : ctx.moveTo(X(r), Y(u));
    }
    ctx.stroke();
    // уровень полной энергии — «потолок» колебаний
    ctx.strokeStyle = "#d1495b"; ctx.lineWidth = 1.6; ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.moveTo(X(a), Y(E)); ctx.lineTo(X(b), Y(E)); ctx.stroke();
    ctx.setLineDash([]);
    // положение равновесия и среднее положение
    ctx.strokeStyle = "#9aa4b0"; ctx.setLineDash([3, 3]); ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(X(R0), gy); ctx.lineTo(X(R0), gy + gh); ctx.stroke();
    ctx.strokeStyle = "#e07a5f"; ctx.beginPath();
    ctx.moveTo(X(sred), gy); ctx.lineTo(X(sred), gy + gh); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#9aa4b0"; ctx.fillText("r₀", X(R0) - 6, gy + gh + 14);
    ctx.fillStyle = "#e07a5f"; ctx.fillText("среднее", X(sred) - 20, gy + gh + 28);
    // колеблющаяся молекула
    const r = sred + (b - a) / 2 * Math.cos(phase);
    ctx.beginPath(); ctx.arc(X(r), Y(Math.min(U(r), E)), 6, 0, 7);
    ctx.fillStyle = "#d1495b"; ctx.fill();
    // две молекулы внизу: левая закреплена, правая колеблется
    const yb = cv.height - 34;
    ctx.beginPath(); ctx.arc(40, yb, 11, 0, 7); ctx.fillStyle = "#2f6690"; ctx.fill();
    const scale = (cv.width - 150) / (3.2 * SIG);
    ctx.beginPath(); ctx.arc(40 + r * scale, yb, 11, 0, 7);
    ctx.fillStyle = "#3a8fb7"; ctx.fill();
    ctx.strokeStyle = "#c9ced6"; ctx.setLineDash([2, 3]);
    ctx.beginPath(); ctx.moveTo(40, yb); ctx.lineTo(40 + r * scale, yb); ctx.stroke();
    ctx.setLineDash([]);
    const rost = (sred / R0 - 1) * 100;
    el("T-v").textContent = el("T").value;
    out.textContent = "Ближняя граница колебаний: " + (a / R0).toFixed(3) + " r₀"
      + "   ·   дальняя: " + (b / R0).toFixed(3) + " r₀"
      + "   ·   среднее расстояние: " + (sred / R0).toFixed(3) + " r₀"
      + "   ·   тело расширилось на " + rost.toFixed(1) + " %";
  }
"""


def thermal_expansion(temperature=30):
    """Тепловое расширение как следствие несимметричной «ямы» взаимодействия.

    Если бы яма была симметричной, средний размах колебаний не смещался бы
    и тело не расширялось. Но влево от положения равновесия отталкивание растёт
    быстрее, чем притяжение вправо, — поэтому середина размаха с ростом
    температуры уходит вправо. Это объяснение из § 4 учебника, рис. 8.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("T", "Температура (усл. ед.):", 2, 95, temperature, 1)
        + _buttons()
        + "</div>"
    )
    return _build(
        "Почему тела расширяются при нагревании",
        _EXPANSION,
        {"sigma": 40.0},
        controls,
        hint="Сравните расстояния от r₀ до левой и правой границ колебаний: "
             "влево молекула отходит меньше, чем вправо. Именно из-за этого "
             "среднее расстояние растёт, а тело расширяется.",
        height=340,
    )


_CONTACT = """
  // Два газа в одном сосуде разделены стенкой из атомов твёрдого тела. Атомы стенки
  // привязаны к своим местам пружинами, но колеблются и передают энергию от молекул
  // слева молекулам справа. Никакого термостата нет: система замкнута.
  const W = cv.width, BOX_H = P.boxH, GR_H = cv.height - P.boxH;
  const rg = P.rg, rw = P.rw, mid = W / 2;
  let gas = [], wall = [], hist = [], frame = 0, ke0 = 1;
  function make(n, x0, x1, v) {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * 2 * Math.PI, s = v * (0.7 + 0.6 * Math.random());
      gas.push({ x: x0 + Math.random() * (x1 - x0), y: rg + Math.random() * (BOX_H - 2 * rg),
                 vx: s * Math.cos(a), vy: s * Math.sin(a) });
    }
  }
  function init() {
    gas = []; wall = []; hist = []; frame = 0;
    make(P.n, rg + 2, mid - rw - rg - 2, P.vHot);
    make(P.n, mid + rw + rg + 2, W - rg - 2, P.vCold);
    const nW = Math.ceil(BOX_H / P.wallStep);
    for (let i = 0; i < nW; i++) {
      const y = P.wallStep / 2 + i * P.wallStep;
      wall.push({ x: mid, y: y, hx: mid, hy: y, vx: 0, vy: 0 });
    }
    ke0 = sideKE(true);
    E0 = totalE();
  }
  function collide(p, q, r1, r2, m1, m2) {
    const dx = q.x - p.x, dy = q.y - p.y, d2 = dx * dx + dy * dy, R = r1 + r2;
    if (d2 >= R * R || d2 === 0) return;
    const d = Math.sqrt(d2), nx = dx / d, ny = dy / d;
    const vn = (p.vx - q.vx) * nx + (p.vy - q.vy) * ny;   // > 0 — сближаются
    if (vn <= 0) return;
    const J = 2 * vn / (1 / m1 + 1 / m2);                  // упругий удар разных масс
    p.vx -= J / m1 * nx; p.vy -= J / m1 * ny;
    q.vx += J / m2 * nx; q.vy += J / m2 * ny;
    const push = (R - d) / 2 + P.eps;
    p.x -= nx * push * m2 / (m1 + m2) * 2; p.y -= ny * push * m2 / (m1 + m2) * 2;
    q.x += nx * push * m1 / (m1 + m2) * 2; q.y += ny * push * m1 / (m1 + m2) * 2;
  }
  let E0 = 1;
  function totalE() {
    let e = 0;
    for (const p of gas) e += 0.5 * (p.vx * p.vx + p.vy * p.vy);
    for (const w of wall) e += 0.5 * P.mw * (w.vx * w.vx + w.vy * w.vy)
                             + 0.5 * P.mw * P.kt * ((w.x - w.hx) ** 2 + (w.y - w.hy) ** 2);
    return e;
  }
  function conserve() {
    // система замкнута: численная погрешность не должна менять полную энергию
    let pe = 0;
    for (const w of wall) pe += 0.5 * P.mw * P.kt * ((w.x - w.hx) ** 2 + (w.y - w.hy) ** 2);
    const keNow = totalE() - pe, keWant = E0 - pe;
    if (keNow > 0 && keWant > 0) {
      const k = Math.sqrt(keWant / keNow);
      for (const p of gas) { p.vx *= k; p.vy *= k; }
      for (const w of wall) { w.vx *= k; w.vy *= k; }
    }
  }
  function sideKE(left) {
    let s = 0, n = 0;
    for (const p of gas) if ((p.x < mid) === left) { s += 0.5 * (p.vx * p.vx + p.vy * p.vy); n++; }
    return n ? s / n : 0;
  }
  function step() {
    frame++;
    for (let s = 0; s < P.sub; s++) substep();
    conserve();
    if (frame % 4 === 0) {
      hist.push([sideKE(true) / ke0, sideKE(false) / ke0]);
      if (hist.length > 240) hist.shift();
    }
  }
  function substep() {
    for (const p of gas) {
      p.x += p.vx; p.y += p.vy;
      if (p.x < rg) { p.x = rg; p.vx = Math.abs(p.vx); }
      if (p.x > W - rg) { p.x = W - rg; p.vx = -Math.abs(p.vx); }
      if (p.y < rg) { p.y = rg; p.vy = Math.abs(p.vy); }
      if (p.y > BOX_H - rg) { p.y = BOX_H - rg; p.vy = -Math.abs(p.vy); }
      // страховка: сквозь стенку молекулы не проходят
      if (p.x > mid - rg && p.x < mid) { p.x = mid - rg; p.vx = -Math.abs(p.vx); }
      if (p.x < mid + rg && p.x >= mid) { p.x = mid + rg; p.vx = Math.abs(p.vx); }
    }
    for (const w of wall) {                    // атомы стенки на пружинах
      w.vx += -P.kt * (w.x - w.hx); w.vy += -P.kt * (w.y - w.hy);
      w.x += w.vx; w.y += w.vy;
    }
    for (let i = 0; i < gas.length; i++) {
      for (let j = i + 1; j < gas.length; j++) collide(gas[i], gas[j], rg, rg, 1, 1);
      for (const w of wall) collide(gas[i], w, rg, rw, 1, P.mw);
    }
  }
  function draw() {
    ctx.clearRect(0, 0, W, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, W, BOX_H);
    for (const w of wall) { ctx.beginPath(); ctx.arc(w.x, w.y, rw, 0, 7); ctx.fillStyle = "#5b6570"; ctx.fill(); }
    for (const p of gas) {
      const s = Math.hypot(p.vx, p.vy) / P.vHot;                   // цвет по скорости
      const t = Math.max(0, Math.min(1, s));
      ctx.fillStyle = "rgb(" + Math.round(60 + 170 * t) + "," + Math.round(120 - 60 * t) + "," + Math.round(200 - 150 * t) + ")";
      ctx.beginPath(); ctx.arc(p.x, p.y, rg, 0, 7); ctx.fill();
    }
    const y0 = BOX_H + 8, h = GR_H - 22;
    ctx.strokeStyle = "#c9ced6"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(34, y0); ctx.lineTo(W - 6, y0); ctx.moveTo(34, y0 + h); ctx.lineTo(W - 6, y0 + h); ctx.stroke();
    ctx.fillStyle = "#5b6570"; ctx.font = "11px system-ui";
    ctx.fillText("T", 12, y0 + 10); ctx.fillText("время →", W - 60, y0 + h + 14);
    const colors = ["#d1495b", "#2f6690"];
    for (let k = 0; k < 2; k++) {
      ctx.strokeStyle = colors[k]; ctx.lineWidth = 1.8; ctx.beginPath();
      hist.forEach((v, i) => {
        const X = 34 + i / 240 * (W - 40), Y = y0 + h * (1 - Math.min(1, v[k] / 1.05));
        i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y);
      });
      ctx.stroke();
    }
    const L = sideKE(true) / ke0, R = sideKE(false) / ke0;
    ctx.fillStyle = "#d1495b"; ctx.fillText("горячий газ", 40, y0 + 12);
    ctx.fillStyle = "#2f6690"; ctx.fillText("холодный газ", 40, y0 + 24);
    out.textContent = "Средняя кинетическая энергия молекул (усл. ед.):  слева " + L.toFixed(2)
      + "   ·   справа " + R.toFixed(2)
      + (Math.abs(L - R) < 0.12 ? "   ·   тепловое равновесие установилось" : "   ·   энергия переходит через стенку");
  }
"""


def thermal_contact(n=55):
    """Тепловое равновесие: горячий и холодный газ, разделённые твёрдой стенкой.

    Атомы стенки колеблются около своих мест и передают энергию от быстрых молекул
    слева медленным молекулам справа. Средние кинетические энергии двух газов
    выравниваются — это и есть установление теплового равновесия (§ 4 учебника).
    Молекулы через стенку не проходят: переходит только энергия.
    """
    controls = '<div class="ps-row">' + _buttons() + "</div>"
    return _build(
        "Два газа за стенкой: как устанавливается тепловое равновесие",
        _CONTACT,
        {"n": n, "rg": 4.0, "rw": 6.0, "mw": 3.0, "kt": 0.06, "wallStep": 13,
         "vHot": 2.2, "vCold": 0.8, "boxH": 250, "sub": 2, "eps": 0.02},
        controls,
        hint="Цвет молекулы показывает её скорость. Следите за графиком: красная и синяя "
             "линии сходятся к одному уровню и дальше лишь колеблются около него.",
        height=340,
    )


_PISTON = """
  // Газ под поршнем. Поршень движется — молекулы, отскакивая от него, меняют скорость:
  // при сжатии ускоряются, при расширении замедляются. Это изменение внутренней
  // энергии совершением работы. Дно можно сделать горячим или холодным — тогда
  // энергия меняется теплопередачей.
  const W = cv.width, BOX_H = P.boxH, GR_H = cv.height - P.boxH, r = P.r;
  const X0 = 60, X1 = W - 60;                          // стенки цилиндра
  let gas = [], piston = 16, target = 16, hist = [], frame = 0, dno = 0, ke0 = 1;
  function pistonY(vol) { return BOX_H - vol / 100 * (BOX_H - 16); }
  function avgKE() { let s = 0; for (const p of gas) s += 0.5 * (p.vx * p.vx + p.vy * p.vy); return s / gas.length; }
  function init() {
    gas = []; hist = []; frame = 0; dno = 0;
    el("vol").value = 100; piston = target = pistonY(100);
    for (let i = 0; i < P.n; i++) {
      const a = Math.random() * 2 * Math.PI, s = P.v0 * (0.7 + 0.6 * Math.random());
      gas.push({ x: X0 + r + Math.random() * (X1 - X0 - 2 * r), y: piston + r + Math.random() * (BOX_H - piston - 2 * r),
                 vx: s * Math.cos(a), vy: s * Math.sin(a) });
    }
    ke0 = avgKE();
    const b = el("dno"); if (b) b.textContent = "Нагреть дно";
  }
  function collide(p, q) {
    const dx = q.x - p.x, dy = q.y - p.y, d2 = dx * dx + dy * dy;
    if (d2 >= 4 * r * r || d2 === 0) return;
    const d = Math.sqrt(d2), nx = dx / d, ny = dy / d;
    const vn = (p.vx - q.vx) * nx + (p.vy - q.vy) * ny;
    if (vn <= 0) return;
    p.vx -= vn * nx; p.vy -= vn * ny; q.vx += vn * nx; q.vy += vn * ny;
    const push = (2 * r - d) / 2 + 0.1;
    p.x -= nx * push; p.y -= ny * push; q.x += nx * push; q.y += ny * push;
  }
  function step() {
    frame++;
    target = pistonY(+el("vol").value);
    const u = Math.sign(target - piston) * Math.min(P.u, Math.abs(target - piston));
    piston += u;
    for (const p of gas) {
      p.x += p.vx; p.y += p.vy;
      if (p.x < X0 + r) { p.x = X0 + r; p.vx = Math.abs(p.vx); }
      if (p.x > X1 - r) { p.x = X1 - r; p.vx = -Math.abs(p.vx); }
      if (p.y > BOX_H - r) {                          // дно
        p.y = BOX_H - r; p.vy = -Math.abs(p.vy);
        if (dno !== 0) {                              // горячее или холодное дно
          const s = Math.hypot(p.vx, p.vy) || 1e-6;
          const want = dno > 0 ? P.vHot : P.vCold;
          const k = 1 + 0.9 * (want / s - 1);
          p.vx *= k; p.vy *= k;
        }
      }
      if (p.y < piston + r && p.vy - u < 0) {         // удар о движущийся поршень
        p.y = piston + r;
        p.vy = 2 * u - p.vy;
      }
    }
    for (let i = 0; i < gas.length; i++) for (let j = i + 1; j < gas.length; j++) collide(gas[i], gas[j]);
    if (frame % 3 === 0) { hist.push(avgKE() / ke0); if (hist.length > 250) hist.shift(); }
  }
  function draw() {
    ctx.clearRect(0, 0, W, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, W, BOX_H);
    // цилиндр
    ctx.strokeStyle = "#5b6570"; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(X0, 4); ctx.lineTo(X0, BOX_H); ctx.lineTo(X1, BOX_H); ctx.lineTo(X1, 4); ctx.stroke();
    if (dno !== 0) { ctx.strokeStyle = dno > 0 ? "#d1495b" : "#3a8fb7"; ctx.lineWidth = 5;
      ctx.beginPath(); ctx.moveTo(X0, BOX_H); ctx.lineTo(X1, BOX_H); ctx.stroke(); }
    // поршень
    ctx.fillStyle = "#8a94a0"; ctx.fillRect(X0 + 1, piston - 10, X1 - X0 - 2, 10);
    ctx.fillRect(W / 2 - 5, 0, 10, piston - 10);
    for (const p of gas) {
      const t = Math.max(0, Math.min(1, Math.hypot(p.vx, p.vy) / (P.v0 * 2.2)));
      ctx.fillStyle = "rgb(" + Math.round(60 + 170 * t) + "," + Math.round(120 - 60 * t) + "," + Math.round(200 - 150 * t) + ")";
      ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, 7); ctx.fill();
    }
    const y0 = BOX_H + 8, h = GR_H - 22;
    ctx.strokeStyle = "#c9ced6"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(34, y0); ctx.lineTo(W - 6, y0); ctx.moveTo(34, y0 + h); ctx.lineTo(W - 6, y0 + h); ctx.stroke();
    ctx.fillStyle = "#5b6570"; ctx.font = "11px system-ui";
    ctx.fillText("внутренняя энергия газа (усл. ед.)", 40, y0 + 12); ctx.fillText("время →", W - 60, y0 + h + 14);
    ctx.strokeStyle = "#d1495b"; ctx.lineWidth = 1.8; ctx.beginPath();
    hist.forEach((v, i) => { const X = 34 + i / 250 * (W - 40), Y = y0 + h * (1 - Math.min(1, v / 3)); i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); });
    ctx.stroke();
    el("vol-v").textContent = el("vol").value + " %";
    const ke = avgKE() / ke0;
    out.textContent = "Объём газа: " + el("vol").value + " %   ·   средняя кинетическая энергия молекул: "
      + ke.toFixed(2) + " от начальной"
      + (Math.abs(u_last()) > 0.01 ? "   ·   поршень движется — над газом совершается работа" : (dno ? "   ·   идёт теплопередача через дно" : ""));
  }
  function u_last() { return target - piston; }
  const db = el("dno");
  if (db) db.onclick = () => {
    dno = dno === 0 ? 1 : (dno === 1 ? -1 : 0);
    db.textContent = dno === 0 ? "Нагреть дно" : (dno === 1 ? "Охладить дно" : "Убрать нагрев");
  };
"""


def piston(n=80):
    """Два способа изменить внутреннюю энергию газа: работа и теплопередача.

    Ползунок двигает поршень. При сжатии молекулы, отскакивая от движущегося
    навстречу поршня, ускоряются — газ нагревается, хотя тепло ему никто не передавал.
    При расширении замедляются. Кнопка делает дно горячим или холодным — тогда
    энергия меняется теплопередачей, без всякой работы. Это два способа из § 6.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("vol", "Объём газа:", 30, 100, 100, 1, " %")
        + '<button data-name="dno">Нагреть дно</button>'
        + _buttons()
        + "</div>"
    )
    return _build(
        "Газ под поршнем: работа и теплопередача",
        _PISTON,
        {"n": n, "r": 4.0, "v0": 1.4, "u": 1.2, "vHot": 3.2, "vCold": 0.6, "boxH": 250},
        controls,
        hint="Сожмите газ быстро и посмотрите на график. Потом верните поршень. "
             "Затем оставьте поршень на месте и нагрейте дно — энергия растёт и без работы.",
        height=340,
    )


_CONDUCTION = """
  // Два стержня из атомов, связанных пружинами. Левый край каждого стержня греется,
  // правый — охлаждается. Энергия колебаний передаётся от атома к атому — это и есть
  // теплопроводность. В верхнем стержне связи жёсткие (металл), в нижнем — слабые.
  const W = cv.width, COLS = P.cols, ROWS = P.rows, A = P.a, DT = P.dt;
  let rods = [];
  function kWeak() { return +el("k2").value / 100; }
  function makeRod(y0, k) {
    const nodes = [];
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
      const x = P.x0 + c * A, y = y0 + r * A;
      nodes.push({ x: x, y: y, hx: x, hy: y, vx: 0, vy: 0, m: 0.7 + 0.6 * Math.random(), T: 0, c: c });
    }
    return { nodes: nodes, k: k, y0: y0 };
  }
  function init() {
    rods = [makeRod(P.y1, P.kStrong), makeRod(P.y2, kWeak())];
  }
  function force(rod) {
    const n = rod.nodes, k = rod.k;
    for (const q of n) { q.fx = -P.kh * (q.x - q.hx); q.fy = -P.kh * (q.y - q.hy); }
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
      const i = r * COLS + c, p = n[i];
      for (const j of [c + 1 < COLS ? i + 1 : -1, r + 1 < ROWS ? i + COLS : -1]) {
        if (j < 0) continue;
        const q = n[j], dx = q.x - p.x, dy = q.y - p.y, d = Math.hypot(dx, dy) || 1e-6;
        const f = k * (d - A);
        p.fx += f * dx / d; p.fy += f * dy / d; q.fx -= f * dx / d; q.fy -= f * dy / d;
      }
    }
  }
  function gauss() { return (Math.random() + Math.random() + Math.random() - 1.5) * 1.63; }
  function step() {
    rods[1].k = kWeak();
    for (let s = 0; s < P.sub; s++) for (const rod of rods) {
      force(rod);
      for (const q of rod.nodes) {
        if (q.c === 0) {                                  // горячий край: атомы дрожат около мест
          q.x = q.hx + gauss() * P.ampHot; q.y = q.hy + gauss() * P.ampHot;
          q.vx = q.vy = 0; q.T = 0.5 * P.vHot * P.vHot; continue;
        }
        q.vx += q.fx / q.m * DT; q.vy += q.fy / q.m * DT;
        if (q.c >= COLS - 3) { q.vx *= P.cool; q.vy *= P.cool; }   // холодный край забирает энергию
        q.x += q.vx * DT; q.y += q.vy * DT;
        q.T = 0.97 * q.T + 0.03 * 0.5 * q.m * (q.vx * q.vx + q.vy * q.vy);
      }
    }
  }
  function tempAt(rod, c) {
    let s = 0; for (let r = 0; r < ROWS; r++) s += rod.nodes[r * COLS + c].T; return s / ROWS;
  }
  function draw() {
    ctx.clearRect(0, 0, W, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, W, cv.height);
    const Tref = P.vHot * P.vHot;                  // масштаб для цвета
    rods.forEach((rod, idx) => {
      for (const q of rod.nodes) {
        const t = Math.max(0, Math.min(1, q.T / Tref));
        ctx.fillStyle = "rgb(" + Math.round(50 + 200 * t) + "," + Math.round(90 + 40 * (1 - t) - 60 * t) + "," + Math.round(210 - 190 * t) + ")";
        ctx.beginPath(); ctx.arc(q.x, q.y, A * 0.36, 0, 7); ctx.fill();
      }
      ctx.fillStyle = "#5b6570"; ctx.font = "12px system-ui";
      ctx.fillText(idx === 0 ? "жёсткие связи (металл)" : "слабые связи (дерево, пластик)", P.x0, rod.y0 - 10);
      ctx.fillText("нагрев", 8, rod.y0 + A * (ROWS - 1) / 2 + 4);
      ctx.fillText("холод", W - 46, rod.y0 + A * (ROWS - 1) / 2 + 4);
    });
    el("k2-v").textContent = kWeak().toFixed(2);
    const c = Math.floor(COLS * 0.75);
    out.textContent = "Нагрев на ¾ длины стержня (усл. ед.):  металл " + (tempAt(rods[0], c) / Tref).toFixed(2)
      + "   ·   слабые связи " + (tempAt(rods[1], c) / Tref).toFixed(2)
      + "   ·   чем жёстче связь между атомами, тем быстрее передаётся энергия колебаний";
  }
"""


def conduction(cols=44, rows=5):
    """Теплопроводность: колебания атомов передаются по цепочке связей.

    Атомы двух стержней связаны пружинами. Левые концы греются, правые
    охлаждаются. В стержне с жёсткими связями (металл) энергия колебаний бежит
    к дальнему концу быстро, со слабыми связями — медленно. Это механизм
    теплопроводности из § 7 учебника: сами атомы остаются на местах, переносится
    только энергия.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("k2", "Жёсткость связей в нижнем стержне:", 4, 100, 14, 1)
        + _buttons()
        + "</div>"
    )
    return _build(
        "Теплопроводность двух стержней",
        _CONDUCTION,
        {"cols": cols, "rows": rows, "a": 14.0, "x0": 60, "y1": 30, "y2": 30 + rows * 14 + 34,
         "dt": 0.25, "kStrong": 1.0, "kh": 0.01, "vHot": 1.6, "ampHot": 1.3, "cool": 0.90, "sub": 2},
        controls,
        hint="Красный — горячо, синий — холодно. Нагрев доходит до дальнего конца "
             "верхнего стержня, пока нижний ещё холодный. Увеличьте жёсткость связей "
             "в нижнем — он станет «металлом».",
        height=230,
    )


_CALORIMETER = """
  // Нагретый металлический цилиндр опускают в воду. Энергия переходит от горячего тела
  // к холодному тем быстрее, чем больше разность температур; температуры сходятся
  // к общему значению. Его заранее даёт уравнение теплового баланса — модель это проверяет.
  const W = cv.width, H = cv.height;
  const MATERIALS = [[140, "свинец"], [230, "олово"], [250, "серебро"], [400, "медь"],
                     [460, "железо"], [500, "сталь"], [920, "алюминий"]];
  let t1 = 0, t2 = 0, time = 0, hist = [], key = "";
  function params() {
    return { m1: +el("m1").value / 1000, c1: +el("c1").value, T1: +el("T1").value,
             m2: +el("m2").value / 1000, c2: 4200, T2: 20, loss: +el("loss").value / 100 };
  }
  function balance(p) { return (p.c1 * p.m1 * p.T1 + p.c2 * p.m2 * p.T2) / (p.c1 * p.m1 + p.c2 * p.m2); }
  function material(c) {
    let best = MATERIALS[0];
    for (const m of MATERIALS) if (Math.abs(m[0] - c) < Math.abs(best[0] - c)) best = m;
    return Math.abs(best[0] - c) <= 25 ? best[1] : "";
  }
  function init() {
    const p = params(); key = JSON.stringify(p);
    t1 = p.T1; t2 = p.T2; time = 0; hist = [[0, t1, t2]];
  }
  function step() {
    const p = params();
    if (JSON.stringify(p) !== key) { init(); return; }      // сдвинули ползунок — опыт с начала
    for (let s = 0; s < P.sub; s++) {
      const q = P.k * (t1 - t2) * P.dt;                     // теплообмен металл → вода
      t1 -= q / (p.c1 * p.m1);
      t2 += q / (p.c2 * p.m2);
      const ql = p.loss * P.kl * (t2 - p.T2) * P.dt;        // потери в комнату
      t2 -= ql / (p.c2 * p.m2);
      time += P.dt;
    }
    if (time - hist[hist.length - 1][0] >= P.every) hist.push([time, t1, t2]);
    if (hist.length > 600) hist.shift();
  }
  function draw() {
    const p = params(), tb = balance(p);
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, W, H);
    const gx = 56, gy = 22, gw = W - 80, gh = H - 64;
    const Tmax = Math.max(100, p.T1 + 5), tmax = Math.max(60, hist[hist.length - 1][0] + 1);
    const X = (t) => gx + gw * t / tmax, Y = (T) => gy + gh * (1 - T / Tmax);
    ctx.strokeStyle = "#c9ced6"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(gx, gy + gh); ctx.lineTo(gx + gw, gy + gh); ctx.stroke();
    ctx.fillStyle = "#5b6570"; ctx.font = "11px system-ui";
    for (let T = 0; T <= Tmax; T += 20) { ctx.fillText(T + "°", 22, Y(T) + 4);
      ctx.beginPath(); ctx.moveTo(gx - 3, Y(T)); ctx.lineTo(gx, Y(T)); ctx.stroke(); }
    ctx.fillText("время, с", gx + gw - 52, gy + gh + 16);
    // расчётная температура равновесия — пунктиром
    ctx.strokeStyle = "#2a9d5c"; ctx.setLineDash([6, 4]); ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(gx, Y(tb)); ctx.lineTo(gx + gw, Y(tb)); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = "#2a9d5c"; ctx.fillText("по уравнению баланса: " + tb.toFixed(1) + " °C", gx + 8, Y(tb) - 6);
    for (const [idx, color, label] of [[1, "#d1495b", "металл"], [2, "#2f6690", "вода"]]) {
      ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath();
      hist.forEach((h, i) => { i ? ctx.lineTo(X(h[0]), Y(h[idx])) : ctx.moveTo(X(h[0]), Y(h[idx])); });
      ctx.stroke();
      ctx.fillStyle = color; ctx.fillText(label, X(hist[hist.length - 1][0]) + 6, Y(hist[hist.length - 1][idx]) + 4);
    }
    const mat = material(p.c1);
    el("m1-v").textContent = el("m1").value + " г"; el("m2-v").textContent = el("m2").value + " г";
    el("T1-v").textContent = el("T1").value + " °C"; el("loss-v").textContent = el("loss").value + " %";
    el("c1-v").textContent = el("c1").value + " Дж/(кг·°C)" + (mat ? " — " + mat : "");
    const gap = Math.abs(t1 - t2);
    out.textContent = "Сейчас: металл " + t1.toFixed(1) + " °C, вода " + t2.toFixed(1) + " °C"
      + (gap < 0.3 ? "   ·   равновесие: " + t2.toFixed(1) + " °C" + (p.loss > 0 ? " — ниже расчётного из-за потерь" : " — как и предсказывает уравнение")
                   : "   ·   теплообмен идёт, разность " + gap.toFixed(1) + " °C");
  }
"""


def calorimeter():
    """Калориметр: нагретый металл в воде, температуры сходятся к общей.

    Скорость передачи энергии пропорциональна разности температур, поэтому кривые
    сближаются сначала быстро, потом всё медленнее. Пунктир — температура, которую
    заранее даёт уравнение теплового баланса; модель с ним сходится. Ползунок потерь
    показывает, почему в реальной лабораторной результат выходит чуть ниже расчёта.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("c1", "Теплоёмкость металла:", 140, 920, 400, 10)
        + _slider("m1", "Масса металла:", 50, 500, 200, 10)
        + _slider("T1", "Его температура:", 40, 100, 90, 1)
        + "</div><div class=\"ps-row\">"
        + _slider("m2", "Масса воды (20 °C):", 100, 500, 200, 10)
        + _slider("loss", "Потери в комнату:", 0, 100, 0, 5)
        + _buttons()
        + "</div>"
    )
    return _build(
        "Калориметр: металл в воде",
        _CALORIMETER,
        {"k": 8.0, "kl": 1.5, "dt": 0.02, "sub": 4, "every": 0.25},
        controls,
        hint="Сначала предскажите температуру по уравнению баланса, потом запустите модель "
             "и сравните. Затем добавьте потери — так выглядит настоящая лабораторная работа.",
        height=300,
    )


_HEATING = """
  // Кусок льда греют нагревателем постоянной мощности. Пока лёд твёрдый, температура
  // растёт; при 0 °C она останавливается — вся энергия идёт на разрушение решётки;
  // когда весь лёд растаял, температура воды снова растёт. Ползунки меняют массу
  // и мощность, и видно, как от них зависят наклоны и длина «полки».
  const W = cv.width, H = cv.height;
  const C_ICE = 2100, C_WATER = 4200, LAMBDA = 3.4e5, L_VAPOR = 2.3e6, T0 = -40, T_END = 100;
  let time = 0, running_t = 0;
  function params() { return { m: +el("m").value / 1000, P: +el("P").value }; }
  function stages(p) {
    const q1 = C_ICE * p.m * (0 - T0), q2 = LAMBDA * p.m, q3 = C_WATER * p.m * T_END;
    const q4 = P.boil ? L_VAPOR * p.m : 0;
    return { t1: q1 / p.P, t2: q2 / p.P, t3: q3 / p.P, t4: q4 / p.P, q1, q2, q3, q4 };
  }
  function tempAt(p, s, tau) {
    if (tau <= s.t1) return T0 + (0 - T0) * tau / s.t1;
    if (tau <= s.t1 + s.t2) return 0;
    if (tau <= s.t1 + s.t2 + s.t3) return T_END * (tau - s.t1 - s.t2) / s.t3;
    return T_END;                                  // кипение: температура стоит на 100 °C
  }
  function init() { time = 0; }
  function step() { const p = params(), s = stages(p); const total = s.t1 + s.t2 + s.t3 + s.t4;
    time += total / P.frames; if (time > total * 1.08) time = total * 1.08; }
  function draw() {
    const p = params(), s = stages(p), total = s.t1 + s.t2 + s.t3 + s.t4;
    ctx.clearRect(0, 0, W, H); ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, W, H);
    const gx = 60, gy = 20, gw = W - 90, gh = H - 66;
    const X = (tau) => gx + gw * tau / (total * 1.08), Y = (T) => gy + gh * (1 - (T - T0) / (T_END - T0));
    ctx.strokeStyle = "#c9ced6"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(gx, gy + gh); ctx.lineTo(gx + gw, gy + gh); ctx.stroke();
    ctx.setLineDash([3, 4]); ctx.beginPath(); ctx.moveTo(gx, Y(0)); ctx.lineTo(gx + gw, Y(0)); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = "#5b6570"; ctx.font = "11px system-ui";
    for (const T of [-40, -20, 0, 20, 40, 60, 80, 100]) ctx.fillText(T + "°", 24, Y(T) + 4);
    ctx.fillText("время, мин", gx + gw - 60, gy + gh + 16);
    for (let mn = 0; mn <= total * 1.08 / 60; mn += Math.max(1, Math.round(total / 60 / 8))) {
      ctx.fillText(String(mn), X(mn * 60) - 4, gy + gh + 16);
    }
    // полный график бледно, пройденная часть — ярко
    const drawTo = (upto, color, width) => {
      ctx.strokeStyle = color; ctx.lineWidth = width; ctx.beginPath();
      for (let i = 0; i <= 300; i++) { const tau = upto * i / 300; const T = tempAt(p, s, tau);
        i ? ctx.lineTo(X(tau), Y(T)) : ctx.moveTo(X(tau), Y(T)); }
      ctx.stroke();
    };
    drawTo(total * 1.08, "rgba(120,130,140,0.35)", 1.5);
    drawTo(time, "#d1495b", 2.5);
    const Tn = tempAt(p, s, time);
    ctx.beginPath(); ctx.arc(X(time), Y(Tn), 5, 0, 7); ctx.fillStyle = "#d1495b"; ctx.fill();
    // подписи участков
    ctx.fillStyle = "#2f6690"; ctx.font = "12px system-ui";
    ctx.fillText("лёд нагревается", X(s.t1 * 0.05), Y(-22));
    ctx.fillText("лёд тает, t = 0 °C", X(s.t1 + s.t2 * 0.15), Y(0) - 8);
    ctx.fillText("вода нагревается", X(s.t1 + s.t2 + s.t3 * 0.35), Y(55));
    if (P.boil) ctx.fillText("вода кипит, t = 100 °C", X(s.t1 + s.t2 + s.t3 + s.t4 * 0.2), Y(100) - 8);
    el("m-v").textContent = el("m").value + " г"; el("P-v").textContent = el("P").value + " Вт";
    const t123 = s.t1 + s.t2 + s.t3;
    const faza = time <= s.t1 ? "лёд, " + Tn.toFixed(0) + " °C" : time <= s.t1 + s.t2
      ? "лёд + вода при 0 °C, растаяло " + Math.min(100, 100 * (time - s.t1) / s.t2).toFixed(0) + " %"
      : time <= t123 || !P.boil ? "вода, " + Tn.toFixed(0) + " °C"
      : "вода кипит при 100 °C, испарилось " + Math.min(100, 100 * (time - t123) / s.t4).toFixed(0) + " %";
    out.textContent = "Сейчас: " + faza + "   ·   нагрев льда до 0 °C: " + (s.t1 / 60).toFixed(1)
      + " мин (" + (s.q1 / 1000).toFixed(0) + " кДж)   ·   плавление: " + (s.t2 / 60).toFixed(1)
      + " мин (" + (s.q2 / 1000).toFixed(0) + " кДж)   ·   нагрев воды до 100 °C: " + (s.t3 / 60).toFixed(1)
      + " мин (" + (s.q3 / 1000).toFixed(0) + " кДж)"
      + (P.boil ? "   ·   кипение: " + (s.t4 / 60).toFixed(1) + " мин (" + (s.q4 / 1000).toFixed(0) + " кДж)" : "");
  }
"""


def heating_curve(boil=False):
    """График нагревания и плавления льда при постоянной мощности нагревателя.

    Три участка: нагрев льда (c = 2100), плавление при 0 °C (λ = 3,4·10⁵ Дж/кг)
    и нагрев воды (c = 4200). Длина «полки» пропорциональна массе и обратно
    пропорциональна мощности; наклоны участков различаются вдвое из-за разных
    теплоёмкостей льда и воды. Это график с рис. 31 учебника, но с ползунками.
    """
    controls = (
        '<div class="ps-row">'
        + _slider("m", "Масса льда:", 50, 500, 200, 10)
        + _slider("P", "Мощность нагревателя:", 100, 1000, 500, 50)
        + _buttons()
        + "</div>"
    )
    return _build(
        "График нагревания: от льда при −40 °C до " + ("полного выкипания воды" if boil else "воды при 100 °C"),
        _HEATING,
        {"frames": 900 if not boil else 1500, "boil": boil},
        controls,
        hint="Следите за подписью внизу: на «полке» энергия поступает, а температура стоит — "
             "она уходит на разрушение кристаллической решётки. Удвойте массу и посмотрите, "
             "что станет с длиной полки.",
        height=320,
    )


_EVAPORATION = """
  // Капля жидкости на дне сосуда. Молекулы притягиваются (Леннард-Джонс), и вырваться
  // с поверхности могут только самые быстрые. Уходя, они уносят избыток энергии —
  // жидкость остывает. Если пар над каплей всё время убирать («ветер»), испарение идёт
  // без остановки; если пар копится, молекулы возвращаются — наступает динамическое
  // равновесие, а число молекул пара перестаёт расти.
  const SIG = P.sigma, EPS = P.eps, RC = 2.5 * SIG, RC2 = RC * RC, DT = P.dt, SUB = P.sub, N = P.n;
  const SURF = cv.height * P.surf;               // условная граница «жидкость — пар»
  let p = [], ke0 = 1, ushlo = 0, frame = 0, key = "";
  function wind() { return +el("wind").value / 100; }
  function tstart() { return +el("T").value / 100; }
  function init() {
    p = []; ushlo = 0; frame = 0; key = el("T").value;
    const cols = Math.ceil(Math.sqrt(N * 2.2)), rows = Math.ceil(N / cols), step = 1.12 * SIG;
    const x0 = (cv.width - cols * step) / 2, y0 = cv.height - 12 - rows * step * 0.87;
    const v = Math.sqrt(2 * tstart());
    for (let i = 0; i < N; i++) {
      const r = Math.floor(i / cols), c = i % cols, a = Math.random() * 2 * Math.PI;
      p.push({ x: x0 + c * step + (r % 2) * step / 2, y: y0 + r * step * 0.87,
               vx: v * Math.cos(a) * (0.6 + 0.8 * Math.random()), vy: v * Math.sin(a) * (0.6 + 0.8 * Math.random()),
               fx: 0, fy: 0 });
    }
    forces();
    // прогрев капли до заданной температуры, чтобы опыт начинался с жидкости, а не с решётки
    for (let k = 0; k < P.warm; k++) {
      for (const q of p) { q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT; q.x += q.vx * DT; q.y += q.vy * DT; }
      forces();
      let s = 0;
      for (const q of p) { q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT;
        if (q.y > cv.height - 5) { q.y = cv.height - 5; q.vy = -Math.abs(q.vy); }
        s += 0.5 * (q.vx * q.vx + q.vy * q.vy); }
      const kk = Math.sqrt(tstart() / Math.max(s / p.length, 1e-6));
      for (const q of p) { q.vx *= kk; q.vy *= kk; }
    }
    ke0 = liquidKE() || 1;
  }
  function forces() {
    for (const q of p) { q.fx = 0; q.fy = P.g; }
    for (let i = 0; i < p.length; i++) for (let j = i + 1; j < p.length; j++) {
      const dx = p[j].x - p[i].x, dy = p[j].y - p[i].y, r2 = dx * dx + dy * dy;
      if (r2 > RC2 || r2 === 0) continue;
      const s2 = SIG * SIG / r2, s6 = s2 * s2 * s2;
      let f = 24 * EPS * (2 * s6 * s6 - s6) / r2; f = Math.max(-P.fmax, Math.min(P.fmax, f));
      p[i].fx -= f * dx; p[i].fy -= f * dy; p[j].fx += f * dx; p[j].fy += f * dy;
    }
  }
  function isLiquid(q) { return q.y > SURF; }
  function liquidKE() {
    let s = 0, n = 0;
    for (const q of p) if (isLiquid(q)) { s += 0.5 * (q.vx * q.vx + q.vy * q.vy); n++; }
    return n ? s / n : 0;
  }
  function step() {
    if (el("T").value !== key) { init(); return; }       // сменили начальную температуру — заново
    frame++;
    for (let s = 0; s < SUB; s++) {
      for (const q of p) { q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT; q.x += q.vx * DT; q.y += q.vy * DT; }
      forces();
      for (const q of p) {
        q.vx += 0.5 * q.fx * DT; q.vy += 0.5 * q.fy * DT;
        if (q.x < 5) { q.x = 5; q.vx = Math.abs(q.vx); }
        if (q.x > cv.width - 5) { q.x = cv.width - 5; q.vx = -Math.abs(q.vx); }
        if (q.y > cv.height - 5) { q.y = cv.height - 5; q.vy = -Math.abs(q.vy); }
        if (q.y < 5) { q.y = 5; q.vy = Math.abs(q.vy); }
      }
    }
    // ветер: каждую молекулу пара в верхней части сосуда уносит с заданной вероятностью
    if (wind() > 0) {
      const keep = [];
      for (const q of p) {
        if (q.y < SURF * 0.6 && Math.random() < wind() * P.windRate) ushlo++; else keep.push(q);
      }
      p = keep;
    }
  }
  function draw() {
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = "#fbfcfd"; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.strokeStyle = "#c9ced6"; ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(0, SURF); ctx.lineTo(cv.width, SURF); ctx.stroke(); ctx.setLineDash([]);
    for (const q of p) {
      ctx.fillStyle = isLiquid(q) ? "#3a8fb7" : "#d1495b";
      ctx.beginPath(); ctx.arc(q.x, q.y, SIG * 0.4, 0, 7); ctx.fill();
    }
    const nl = p.filter(isLiquid).length, nv = p.length - nl;
    el("wind-v").textContent = el("wind").value + " %"; el("T-v").textContent = el("T").value;
    ctx.fillStyle = "#5b6570"; ctx.font = "12px system-ui";
    ctx.fillText("молекул пара: " + nv, 12, 20);
    ctx.fillText("унесено ветром: " + ushlo, 12, 38);
    const ke = liquidKE() / ke0;
    out.textContent = "В жидкости " + nl + " молекул   ·   средняя кинетическая энергия молекул жидкости: "
      + ke.toFixed(2) + " от начальной"
      + (wind() > 0 ? "   ·   быстрые уходят безвозвратно — жидкость остывает"
                    : "   ·   пар копится и частично возвращается — динамическое равновесие");
  }
"""


def evaporation(n=110):
    """Испарение на уровне молекул: с поверхности жидкости уходят самые быстрые.

    Молекулы капли притягиваются друг к другу; вырваться наверх могут лишь те, чья
    скорость заметно выше средней. Улетая, они забирают избыток энергии, и средняя
    кинетическая энергия оставшихся молекул падает — жидкость остывает при испарении
    (§ 19). Ползунок «ветер» уносит пар из сосуда: испарение ускоряется. Без ветра пар
    копится, молекулы возвращаются — устанавливается динамическое равновесие (§ 18).
    """
    controls = (
        '<div class="ps-row">'
        + _slider("wind", "Ветер (уносит пар):", 0, 100, 0, 5)
        + _slider("T", "Начальная температура (усл.):", 50, 95, 75, 1)
        + _buttons()
        + "</div>"
    )
    return _build(
        "Испарение: почему жидкость остывает",
        _EVAPORATION,
        {"n": n, "sigma": 13.0, "eps": 1.0, "dt": 0.06, "sub": 3, "fmax": 6.0, "g": 0.004,
         "surf": 0.55, "windRate": 0.2, "warm": 250},
        controls,
        hint="Без ветра пар над каплей копится и часть молекул возвращается. Включите ветер — "
             "пар уносится, испарение не останавливается, а жидкость заметно остывает.",
        height=300,
    )
