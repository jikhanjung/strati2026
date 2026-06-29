/* STRATI 2026 — client-side bookmarks (localStorage, no login). */
(function () {
  const KEY = "strati_bm";

  function getBM() {
    try { return JSON.parse(localStorage.getItem(KEY) || "[]"); }
    catch (e) { return []; }
  }
  function setBM(arr) { localStorage.setItem(KEY, JSON.stringify(arr)); }
  function isBM(id) { return getBM().includes(id); }
  function toggle(id) {
    const a = getBM();
    const i = a.indexOf(id);
    if (i >= 0) a.splice(i, 1); else a.push(id);
    setBM(a);
    return i < 0; // true if now bookmarked
  }
  function esc(s) {
    return (s || "").replace(/[&<>"']/g, c => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  function paint(btn) {
    const on = isBM(parseInt(btn.dataset.id, 10));
    btn.textContent = on ? "★" : "☆";
    btn.classList.toggle("on", on);
  }
  function refresh() { document.querySelectorAll(".bm").forEach(paint); }

  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".bm");
    if (!btn) return;
    e.preventDefault();
    const id = parseInt(btn.dataset.id, 10);
    toggle(id);
    document.querySelectorAll('.bm[data-id="' + id + '"]').forEach(paint);
    document.dispatchEvent(new CustomEvent("bm:change", { detail: { id } }));
  });

  document.addEventListener("DOMContentLoaded", refresh);

  window.STRATI = { getBM, isBM, toggle, esc, refresh };
})();
