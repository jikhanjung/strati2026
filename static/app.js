/* STRATI 2026 — client-side bookmarks + notes (localStorage, no login). */
(function () {
  const KEY = "strati_bm";
  const NKEY = "strati_notes";

  function getBM() {
    try { return JSON.parse(localStorage.getItem(KEY) || "[]"); }
    catch (e) { return []; }
  }
  function setBM(arr) { localStorage.setItem(KEY, JSON.stringify(arr)); }
  function isBM(id) { return getBM().includes(id); }

  // 메모: { talkId: text } 형태로 저장
  function getNotes() {
    try { return JSON.parse(localStorage.getItem(NKEY) || "{}"); }
    catch (e) { return {}; }
  }
  function getNote(id) { return getNotes()[id] || ""; }
  function hasNote(id) { return !!getNotes()[id]; }
  function setNote(id, text) {
    const n = getNotes();
    text = (text || "").trim();
    if (text) n[id] = text; else delete n[id];
    localStorage.setItem(NKEY, JSON.stringify(n));
    if (text) ensureBM(id);   // 메모를 남기면 자동 북마크
  }

  // 사진: blob은 IndexedDB, "어떤 talk에 사진이 있는지" 빠른 조회는 localStorage 인덱스
  const PKEY = "strati_photo_ids";
  function getPhotoIds() {
    try { return JSON.parse(localStorage.getItem(PKEY) || "[]"); }
    catch (e) { return []; }
  }
  function hasPhoto(id) { return getPhotoIds().includes(id); }
  function setPhotoId(id, on) {
    let a = getPhotoIds();
    if (on) { if (!a.includes(id)) a.push(id); } else { a = a.filter(x => x !== id); }
    localStorage.setItem(PKEY, JSON.stringify(a));
  }

  let _db;
  function db() {
    return _db || (_db = new Promise((res, rej) => {
      const r = indexedDB.open("strati", 1);
      r.onupgradeneeded = () => {
        const d = r.result;
        if (!d.objectStoreNames.contains("photos")) {
          const os = d.createObjectStore("photos", { keyPath: "id", autoIncrement: true });
          os.createIndex("talkId", "talkId", { unique: false });
        }
      };
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    }));
  }
  async function getPhotos(talkId) {
    const d = await db();
    return new Promise((res, rej) => {
      const out = [];
      const req = d.transaction("photos").objectStore("photos")
        .index("talkId").openCursor(IDBKeyRange.only(talkId));
      req.onsuccess = () => {
        const c = req.result;
        if (c) { out.push({ id: c.value.id, blob: c.value.blob }); c.continue(); }
        else res(out);
      };
      req.onerror = () => rej(req.error);
    });
  }
  // 저장 전 축소(최대변 1280px, JPEG 0.8)로 용량 절약
  function downscale(file, maxDim, quality) {
    return new Promise((res, rej) => {
      const img = new Image();
      img.onload = () => {
        let w = img.naturalWidth, h = img.naturalHeight;
        const scale = Math.min(1, maxDim / Math.max(w, h));
        w = Math.round(w * scale); h = Math.round(h * scale);
        const cv = document.createElement("canvas");
        cv.width = w; cv.height = h;
        cv.getContext("2d").drawImage(img, 0, 0, w, h);
        URL.revokeObjectURL(img.src);
        cv.toBlob(b => b ? res(b) : rej(new Error("encode failed")), "image/jpeg", quality);
      };
      img.onerror = () => { URL.revokeObjectURL(img.src); rej(new Error("unsupported image")); };
      img.src = URL.createObjectURL(file);
    });
  }
  async function addPhotoFile(talkId, file) {
    const blob = await downscale(file, 1280, 0.8);
    const d = await db();
    await new Promise((res, rej) => {
      const tx = d.transaction("photos", "readwrite");
      tx.objectStore("photos").add({ talkId, blob, ts: Date.now() });
      tx.oncomplete = res; tx.onerror = () => rej(tx.error);
    });
    setPhotoId(talkId, true);
    ensureBM(talkId);         // 사진을 추가하면 자동 북마크
  }
  async function deletePhoto(photoId, talkId) {
    const d = await db();
    await new Promise((res, rej) => {
      const tx = d.transaction("photos", "readwrite");
      tx.objectStore("photos").delete(photoId);
      tx.oncomplete = res; tx.onerror = () => rej(tx.error);
    });
    const rest = await getPhotos(talkId);
    if (!rest.length) setPhotoId(talkId, false);
  }
  function toggle(id) {
    const a = getBM();
    const i = a.indexOf(id);
    if (i >= 0) a.splice(i, 1); else a.push(id);
    setBM(a);
    return i < 0; // true if now bookmarked
  }
  // 없으면 북마크 추가(이미 있으면 그대로). 메모/사진 추가 시 자동 북마크용.
  function ensureBM(id) {
    const a = getBM();
    if (a.includes(id)) return false;
    a.push(id); setBM(a);
    document.querySelectorAll('.bm[data-id="' + id + '"]').forEach(paint);
    document.dispatchEvent(new CustomEvent("bm:change", { detail: { id } }));
    return true;
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
  function refresh() {
    document.querySelectorAll(".bm").forEach(paint);
    // 메모/사진 있는 카드 표시(제목 옆 📝/📷)
    document.querySelectorAll(".talk[data-id]").forEach(el => {
      const id = parseInt(el.dataset.id, 10);
      el.classList.toggle("has-note", hasNote(id));
      el.classList.toggle("has-photo", hasPhoto(id));
    });
  }

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

  window.STRATI = { getBM, isBM, toggle, esc, refresh, getNote, hasNote, setNote,
    hasPhoto, getPhotos, addPhotoFile, deletePhoto };
})();
