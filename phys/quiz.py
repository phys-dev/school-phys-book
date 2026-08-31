"""Задания для самопроверки с мгновенной проверкой ответа.

Проверка идёт на JavaScript, поэтому задания работают и в тетради Jupyter,
и на собранном сайте. Ответ не подсказывается заранее: пояснение появляется
только после того, как ученик выбрал вариант или ввёл число.
"""

from __future__ import annotations

import json
from itertools import count

from IPython.display import HTML

_counter = count(1)

_CSS = """
<style>
.phys-quiz { border-left: 4px solid #3a8fb7; border-radius: 6px;
  padding: 12px 16px; margin: 14px 0; background: rgba(58, 143, 183, 0.07);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.phys-quiz .pq-q { font-weight: 600; margin-bottom: 10px; }
.phys-quiz .pq-opt { display: block; padding: 6px 10px; margin: 4px 0; cursor: pointer;
  border: 1px solid rgba(128, 140, 155, 0.35); border-radius: 6px;
  background: rgba(255, 255, 255, 0.45); transition: background 0.15s; }
.phys-quiz .pq-opt:hover { background: rgba(58, 143, 183, 0.16); }
.phys-quiz .pq-opt.ok { background: rgba(42, 157, 92, 0.22); border-color: #2a9d5c; }
.phys-quiz .pq-opt.no { background: rgba(209, 73, 91, 0.18); border-color: #d1495b; }
.phys-quiz .pq-num { font: inherit; width: 130px; padding: 5px 8px; border-radius: 6px;
  border: 1px solid rgba(128, 140, 155, 0.5); }
.phys-quiz button { font: inherit; padding: 5px 13px; border-radius: 6px; cursor: pointer;
  border: 1px solid rgba(128, 140, 155, 0.5); background: rgba(58, 143, 183, 0.14);
  margin-left: 8px; }
.phys-quiz .pq-fb { margin-top: 10px; font-size: 0.93em; display: none; }
.phys-quiz .pq-fb.show { display: block; }
.phys-quiz .pq-unit { opacity: 0.75; margin-left: 6px; }
</style>
"""


def _uid() -> str:
    return f"pq{next(_counter)}"


def choice(question: str, options: list[str], correct: int | list[int],
           explain: str = "") -> HTML:
    """Задание с выбором ответа.

    :param question: текст вопроса;
    :param options: варианты ответа;
    :param correct: номер правильного варианта (с нуля) или список номеров;
    :param explain: разбор, который появится после ответа.
    """
    uid = _uid()
    right = [correct] if isinstance(correct, int) else list(correct)
    opts = "".join(
        f'<label class="pq-opt" data-i="{i}">{text}</label>'
        for i, text in enumerate(options)
    )
    html = _CSS + f"""
<div class="phys-quiz" id="{uid}">
  <div class="pq-q">{question}</div>
  {opts}
  <div class="pq-fb" id="{uid}-fb"></div>
</div>
<script>
(function () {{
  const root = document.getElementById("{uid}");
  const right = {json.dumps(right)};
  const fb = document.getElementById("{uid}-fb");
  const explain = {json.dumps(explain, ensure_ascii=False)};
  let done = false;
  root.querySelectorAll(".pq-opt").forEach((opt) => {{
    opt.onclick = () => {{
      if (done) return;
      done = true;
      const i = +opt.dataset.i;
      const good = right.includes(i);
      opt.classList.add(good ? "ok" : "no");
      if (!good) root.querySelectorAll(".pq-opt").forEach((o) => {{
        if (right.includes(+o.dataset.i)) o.classList.add("ok");
      }});
      fb.innerHTML = (good ? "<b>Верно.</b> " : "<b>Пока нет.</b> ") + explain;
      fb.classList.add("show");
    }};
  }});
}})();
</script>
"""
    return HTML(html)


def numeric(question: str, answer: float, unit: str = "", tol: float = 0.05,
            explain: str = "") -> HTML:
    """Задание с числовым ответом.

    :param answer: правильное значение;
    :param unit: единица измерения, в которой ждём ответ;
    :param tol: допустимое относительное отклонение (0.05 — это 5 %).
    """
    uid = _uid()
    html = _CSS + f"""
<div class="phys-quiz" id="{uid}">
  <div class="pq-q">{question}</div>
  <div>
    <input class="pq-num" id="{uid}-in" placeholder="ответ"
           inputmode="decimal" autocomplete="off">
    <span class="pq-unit">{unit}</span>
    <button id="{uid}-btn">Проверить</button>
  </div>
  <div class="pq-fb" id="{uid}-fb"></div>
</div>
<script>
(function () {{
  const inp = document.getElementById("{uid}-in");
  const btn = document.getElementById("{uid}-btn");
  const fb = document.getElementById("{uid}-fb");
  const ans = {answer!r}, tol = {tol!r};
  const explain = {json.dumps(explain, ensure_ascii=False)};
  function check() {{
    const raw = inp.value.replace(",", ".").replace(/\\s/g, "")
      .replace(/·10\\^?/, "e").replace(/\\*10\\^?/, "e");
    const v = parseFloat(raw);
    if (isNaN(v)) {{
      fb.innerHTML = "Введите число. Степень можно записать так: 1.5e-10.";
      fb.classList.add("show"); return;
    }}
    const good = Math.abs(v - ans) <= Math.abs(ans) * tol + 1e-30;
    fb.innerHTML = (good
      ? "<b>Верно.</b> "
      : "<b>Не сходится.</b> Правильный ответ: " + ans.toPrecision(3) + ". ") + explain;
    fb.classList.add("show");
  }}
  btn.onclick = check;
  inp.onkeydown = (e) => {{ if (e.key === "Enter") check(); }};
}})();
</script>
"""
    return HTML(html)


def reveal(question: str, answer: str, button: str = "Показать разбор") -> HTML:
    """Качественный вопрос: сначала думаем сами, потом открываем разбор."""
    uid = _uid()
    html = _CSS + f"""
<div class="phys-quiz" id="{uid}">
  <div class="pq-q">{question}</div>
  <button id="{uid}-btn" style="margin-left:0">{button}</button>
  <div class="pq-fb" id="{uid}-fb">{answer}</div>
</div>
<script>
(function () {{
  const btn = document.getElementById("{uid}-btn");
  const fb = document.getElementById("{uid}-fb");
  btn.onclick = () => {{
    fb.classList.toggle("show");
    btn.textContent = fb.classList.contains("show") ? "Скрыть разбор" : "{button}";
  }};
}})();
</script>
"""
    return HTML(html)
