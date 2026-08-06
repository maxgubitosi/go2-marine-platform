/* ============================================================
   Motor de presentación · navegación por teclado, progreso por
   bloques, overview, autoplay de video por slide. Sin dependencias.
   ============================================================ */
(function () {
  "use strict";

  var deck = document.getElementById("deck");
  var slides = Array.prototype.slice.call(document.querySelectorAll(".slide"));
  var current = 0;

  // Bloques para la barra de progreso (5 segmentos).
  var BLOCKS = ["Introducción", "Problema", "Metodología", "Resultados", "Conclusiones"];

  /* ---------- Construir barra de progreso ---------- */
  var progress = document.getElementById("progress");
  BLOCKS.forEach(function () {
    var seg = document.createElement("div");
    seg.className = "seg";
    seg.innerHTML = '<div class="fill"></div>';
    progress.appendChild(seg);
  });
  var segs = Array.prototype.slice.call(progress.children);

  /* ---------- HUD ---------- */
  var blockName = document.querySelector("#hud .block-name");
  var curEl = document.querySelector("#hud .counter .cur");
  var totEl = document.querySelector("#hud .counter .tot");

  var wtxtEl = document.querySelector("#hud .within .wtxt");
  var dotsEl = document.querySelector("#hud .within .dots");
  var counterEl = document.querySelector("#hud .counter");

  // Contar slides principales (no backup) para el contador.
  var mainSlides = slides.filter(function (s) { return !s.hasAttribute("data-backup"); });
  totEl.textContent = mainSlides.length;

  // Agrupar slides principales por bloque para el progreso de sección.
  var blockGroups = {};
  mainSlides.forEach(function (s) {
    var b = s.getAttribute("data-block") || "0";
    (blockGroups[b] = blockGroups[b] || []).push(s);
  });
  function withinBlock(s) {
    var b = s.getAttribute("data-block") || "0";
    var g = blockGroups[b] || [s];
    return { idx: g.indexOf(s) + 1, total: g.length };
  }

  /* ---------- Overview ---------- */
  var overview = document.getElementById("overview");
  var ovGrid = document.getElementById("ov-grid");
  slides.forEach(function (s, i) {
    var item = document.createElement("div");
    item.className = "ov-item" + (s.hasAttribute("data-backup") ? " is-backup" : "");
    var label = s.getAttribute("data-title") || ("Slide " + (i + 1));
    var num = s.hasAttribute("data-backup") ? ("B" + s.getAttribute("data-backup")) : (mainSlides.indexOf(s) + 1);
    item.innerHTML = '<span class="n">' + num + '</span><span class="t">' + label + "</span>";
    item.addEventListener("click", function () { go(i); closeOverview(); });
    ovGrid.appendChild(item);
  });

  function openOverview() { overview.classList.add("open"); }
  function closeOverview() { overview.classList.remove("open"); }
  function toggleOverview() { overview.classList.toggle("open"); }

  /* ---------- Media por slide ---------- */
  function stopMedia(slide) {
    var vids = slide.querySelectorAll("video");
    vids.forEach(function (v) { try { v.pause(); v.currentTime = 0; } catch (e) {} });
    // Reiniciar animaciones marcadas con data-anim
    slide.querySelectorAll("[data-anim]").forEach(function (el) {
      el.classList.remove("run");
    });
  }
  function playMedia(slide) {
    var vids = slide.querySelectorAll("video[data-autoplay]");
    vids.forEach(function (v) {
      v.muted = true;
      var p = v.play();
      if (p && p.catch) p.catch(function () {});
    });
    // Disparar animaciones
    requestAnimationFrame(function () {
      slide.querySelectorAll("[data-anim]").forEach(function (el) {
        el.classList.add("run");
      });
    });
  }

  /* ---------- Ir a slide ---------- */
  function go(n) {
    n = Math.max(0, Math.min(slides.length - 1, n));
    if (n === current && slides[current].classList.contains("active")) return;
    var prevSlide = slides[current];
    if (prevSlide) { stopMedia(prevSlide); prevSlide.classList.remove("active"); }
    current = n;
    var s = slides[current];
    s.classList.add("active");
    playMedia(s);
    updateChrome();
    hideHint();
  }
  function next() { if (current < slides.length - 1) go(current + 1); }
  function prev() { if (current > 0) go(current - 1); }

  /* ---------- Actualizar chrome ---------- */
  function updateChrome() {
    var s = slides[current];
    var isBackup = s.hasAttribute("data-backup");
    var blockIdx = parseInt(s.getAttribute("data-block") || "0", 10); // 0..4, -1 portada
    var wb = withinBlock(s);
    // Progreso: segmento activo se llena proporcional al avance dentro del bloque
    segs.forEach(function (seg, i) {
      var fill = seg.querySelector(".fill");
      if (isBackup) { seg.classList.add("done"); fill.style.width = "100%"; return; }
      if (i < blockIdx) { seg.classList.add("done"); fill.style.width = "100%"; }
      else if (i === blockIdx) {
        seg.classList.remove("done");
        fill.style.width = Math.round((wb.idx / wb.total) * 100) + "%";
      }
      else { seg.classList.remove("done"); fill.style.width = "0%"; }
    });
    // HUD
    if (isBackup) {
      blockName.textContent = "Backup";
      wtxtEl.textContent = "";
      dotsEl.innerHTML = "";
      counterEl.textContent = "B" + s.getAttribute("data-backup");
    } else {
      blockName.textContent = blockIdx >= 0 ? BLOCKS[blockIdx] : "Portada";
      if (blockIdx >= 0) {
        wtxtEl.textContent = wb.idx + " / " + wb.total;
        // dots dentro de la sección
        var html = "";
        for (var k = 0; k < wb.total; k++) html += '<i class="' + (k < wb.idx ? "on" : "") + '"></i>';
        dotsEl.innerHTML = html;
      } else {
        wtxtEl.textContent = "";
        dotsEl.innerHTML = "";
      }
      counterEl.innerHTML = '<span class="cur">' + (mainSlides.indexOf(s) + 1) + '</span> / <span class="tot">' + mainSlides.length + '</span>';
    }
  }

  /* ---------- Hint ---------- */
  var hint = document.getElementById("hint");
  var hintTimer = setTimeout(hideHint, 5000);
  function hideHint() { if (hint) hint.classList.add("hide"); clearTimeout(hintTimer); }

  /* ---------- Teclado ---------- */
  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    switch (e.key) {
      case "ArrowRight": case " ": case "PageDown": case "ArrowDown":
        e.preventDefault(); next(); break;
      case "ArrowLeft": case "PageUp": case "ArrowUp":
        e.preventDefault(); prev(); break;
      case "Home": e.preventDefault(); go(0); break;
      case "End": e.preventDefault(); go(mainSlides.length - 1); break;
      case "o": case "O": e.preventDefault(); toggleOverview(); break;
      case "Escape": closeOverview(); break;
      case "b": case "B": {
        // Saltar al primer backup
        var firstBackup = slides.findIndex(function (s) { return s.hasAttribute("data-backup"); });
        if (firstBackup >= 0) go(firstBackup);
        break;
      }
      case "f": case "F":
        e.preventDefault();
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else document.exitFullscreen();
        break;
    }
    // Ir a slide por número (1-9)
    if (/^[1-9]$/.test(e.key) && !overview.classList.contains("open")) {
      var idx = parseInt(e.key, 10) - 1;
      if (mainSlides[idx]) go(slides.indexOf(mainSlides[idx]));
    }
  });

  /* ---------- Click / botones ---------- */
  document.getElementById("next").addEventListener("click", next);
  document.getElementById("prev").addEventListener("click", prev);

  // Click en mitad derecha/izquierda del deck avanza/retrocede
  deck.addEventListener("click", function (e) {
    if (e.target.closest("a, button, .navarrow, input, .no-nav, video")) return;
    var x = e.clientX / window.innerWidth;
    if (x > 0.62) next();
    else if (x < 0.20) prev();
  });

  // Swipe táctil
  var tx = 0;
  deck.addEventListener("touchstart", function (e) { tx = e.touches[0].clientX; }, { passive: true });
  deck.addEventListener("touchend", function (e) {
    var dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 60) { dx < 0 ? next() : prev(); }
  }, { passive: true });

  /* ---------- Hash deep-link ---------- */
  function fromHash() {
    var m = /slide=(\d+)/.exec(location.hash);
    if (m) { var i = parseInt(m[1], 10) - 1; if (slides[i]) current = i; }
  }
  fromHash();

  /* ---------- Init ---------- */
  slides[current].classList.add("active");
  playMedia(slides[current]);
  updateChrome();

  // Exponer para debug
  window.__deck = { go: go, next: next, prev: prev, total: slides.length };
})();
