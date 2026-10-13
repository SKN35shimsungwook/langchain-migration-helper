// 안내서 v2 공용 스크립트: window.GUIDE = { quiz: [...], checks: [...], storeKey: "..." }
(function () {
  const G = window.GUIDE || {};
  function store(k, v) {
    try {
      if (v === undefined) return JSON.parse(localStorage.getItem(k));
      localStorage.setItem(k, JSON.stringify(v));
    } catch (e) { return null; }
  }

  const quizEl = document.getElementById("quiz"), scoreEl = document.getElementById("score");
  if (quizEl && G.quiz) {
    const answered = {};
    const renderScore = () => {
      const right = Object.values(answered).filter(Boolean).length;
      scoreEl.textContent = right + " / " + G.quiz.length + " 맞힘";
    };
    G.quiz.forEach((item, i) => {
      const box = document.createElement("div"); box.className = "q";
      const t = document.createElement("p"); t.innerHTML = "<b>Q" + (i + 1) + ".</b> "; t.append(item.q); box.append(t);
      const opts = document.createElement("div"); opts.className = "opts";
      const why = document.createElement("p"); why.className = "why"; why.hidden = true; why.textContent = "해설: " + item.why;
      item.opts.forEach((o, j) => {
        const b = document.createElement("button"); b.type = "button"; b.textContent = o;
        b.addEventListener("click", () => {
          opts.querySelectorAll("button").forEach(x => x.classList.remove("right", "wrong"));
          b.classList.add(j === item.a ? "right" : "wrong");
          if (j !== item.a) opts.children[item.a].classList.add("right");
          why.hidden = false;
          if (!(i in answered)) { answered[i] = j === item.a; renderScore(); }
        });
        opts.append(b);
      });
      box.append(opts, why); quizEl.append(box);
    });
    renderScore();
  }

  const checksEl = document.getElementById("checks"), progEl = document.getElementById("progress");
  if (checksEl && G.checks) {
    const saved = store(G.storeKey || "guide-v2-checks") || {};
    const renderProgress = () => {
      const n = Object.values(saved).filter(Boolean).length;
      progEl.textContent = n + " / " + G.checks.length + " 완료";
    };
    G.checks.forEach(([title, sub], i) => {
      const id = "chk-" + i;
      const l = document.createElement("label"); l.htmlFor = id;
      const c = document.createElement("input"); c.type = "checkbox"; c.id = id; c.checked = !!saved[i];
      c.addEventListener("change", () => { saved[i] = c.checked; store(G.storeKey || "guide-v2-checks", saved); renderProgress(); });
      const s = document.createElement("span"); s.textContent = title;
      const sm = document.createElement("small"); sm.textContent = sub; s.append(sm);
      l.append(c, s); checksEl.append(l);
    });
    renderProgress();
  }
})();
