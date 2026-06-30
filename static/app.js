/* STRATI 2026 — bookmarks + notes (localStorage), optional server sync via an
   anonymous device token. Photos stay device-local (IndexedDB), not synced. */
(function () {
  const SKEY = "strati_state";     // {bm:{id:{v,ts}}, notes:{id:{v,ts}}}
  const DKEY = "strati_device";    // 영구 디바이스 ID (페어링해도 안 바뀜)
  const TKEY = "strati_token";     // 싱크 토큰(공유 버킷 키; 페어링 시 상대 것으로 교체)

  function nowTs() { return Date.now(); }

  function loadState() {
    try {
      const s = JSON.parse(localStorage.getItem(SKEY));
      if (s && s.bm && s.notes) return s;
    } catch (e) { /* fall through */ }
    // 구버전 키(strati_bm / strati_notes)에서 1회 이관
    const st = { bm: {}, notes: {} };
    try { JSON.parse(localStorage.getItem("strati_bm") || "[]")
      .forEach(id => { st.bm[id] = { v: true, ts: 1 }; }); } catch (e) {}
    try { const o = JSON.parse(localStorage.getItem("strati_notes") || "{}");
      Object.keys(o).forEach(id => { st.notes[id] = { v: o[id], ts: 1 }; }); } catch (e) {}
    return st;
  }
  let STATE = loadState();
  function saveState() { localStorage.setItem(SKEY, JSON.stringify(STATE)); }

  function getBM() {
    return Object.keys(STATE.bm).filter(id => STATE.bm[id] && STATE.bm[id].v).map(Number);
  }
  function isBM(id) { const e = STATE.bm[id]; return !!(e && e.v); }
  function setBMv(id, on) { STATE.bm[id] = { v: on, ts: nowTs() }; saveState(); scheduleSync(); }
  function toggle(id) { const on = !isBM(id); setBMv(id, on); return on; }
  // 없으면 북마크 추가(있으면 그대로). 메모/사진 추가 시 자동 북마크용.
  function ensureBM(id) {
    if (isBM(id)) return false;
    setBMv(id, true);
    document.querySelectorAll('.bm[data-id="' + id + '"]').forEach(paint);
    document.dispatchEvent(new CustomEvent("bm:change", { detail: { id } }));
    return true;
  }

  function getNote(id) { const e = STATE.notes[id]; return (e && e.v) || ""; }
  function hasNote(id) { const e = STATE.notes[id]; return !!(e && e.v); }
  function setNote(id, text) {
    text = (text || "").trim();
    STATE.notes[id] = { v: text, ts: nowTs() };   // "" = 삭제(동기화용 tombstone)
    saveState(); scheduleSync();
    if (text) ensureBM(id);                        // 메모를 남기면 자동 북마크
  }

  // ── 동기화 (영구 디바이스 ID + 공유 싱크 토큰) ────────────────────────
  function randId() {
    return (window.crypto && crypto.randomUUID)
      ? crypto.randomUUID()
      : "d" + Math.random().toString(36).slice(2) + nowTs().toString(36);
  }
  function deviceId() {            // 이 브라우저 고유·영구
    let t = localStorage.getItem(DKEY);
    if (!t || t.length < 8) { t = randId(); localStorage.setItem(DKEY, t); }
    return t;
  }
  function deviceToken() {         // 공유 버킷 키(기본=디바이스 ID, 페어링 시 교체)
    let t = localStorage.getItem(TKEY);
    if (!t || t.length < 8) { t = deviceId(); localStorage.setItem(TKEY, t); }
    return t;
  }
  // 서버 응답(merged)을 현재 STATE에 항목별 ts 큰 쪽으로 병합(진행 중 로컬편집 보존)
  function mergeInto(server) {
    ["bm", "notes"].forEach(sec => {
      const out = {};
      [STATE[sec] || {}, (server && server[sec]) || {}].forEach(src => {
        Object.keys(src).forEach(k => {
          const e = src[k]; if (!e) return;
          const ts = e.ts || 0;
          if (!out[k] || ts > (out[k].ts || 0)) out[k] = { v: e.v, ts: ts };
        });
      });
      STATE[sec] = out;
    });
    saveState();
  }
  let syncT, syncing = false, syncAgain = false;
  function scheduleSync() { clearTimeout(syncT); syncT = setTimeout(syncNow, 800); }
  async function syncNow() {
    if (syncing) { syncAgain = true; return; }
    syncing = true;
    try {
      const res = await fetch("/api/sync/", {
        method: "POST",
        headers: { "X-Device": deviceToken(), "X-Device-Id": deviceId(),
                   "Content-Type": "application/json" },
        body: JSON.stringify(STATE),
      });
      if (res.ok) {
        const merged = await res.json();
        mergeInto(merged);
        if (merged.paired) localStorage.setItem("strati_linked", "1");
        if (typeof merged.devices === "number") localStorage.setItem("strati_devices", String(merged.devices));
        refresh();
        document.dispatchEvent(new CustomEvent("sync:applied"));
      }
    } catch (e) { /* 오프라인 등은 조용히 무시 */ }
    finally {
      syncing = false;
      if (syncAgain) { syncAgain = false; scheduleSync(); }
    }
  }
  // 첫 동기화 완료(또는 3초 경과)까지 기다릴 수 있는 promise
  let firstDone;
  const firstSync = new Promise(r => { firstDone = r; });
  function initSync() {
    const cap = setTimeout(firstDone, 3000);
    syncNow().finally(() => { clearTimeout(cap); firstDone(); });
  }

  async function pairNew() {           // 이 기기 토큰을 가리키는 6자리 코드 발급
    const res = await fetch("/api/pair/new/", {
      method: "POST", headers: { "X-Device": deviceToken() } });
    if (!res.ok) throw new Error("failed");
    return res.json();                 // {code, expires_in}
  }
  async function pairClaim(code) {     // 코드로 상대 토큰 채택 후 데이터 합치기
    const res = await fetch("/api/pair/claim/", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: String(code || "").trim() }) });
    if (!res.ok) throw new Error(res.status === 410 ? "expired" : "invalid");
    const data = await res.json();
    localStorage.setItem(TKEY, data.token);   // 싱크 토큰만 교체(디바이스 ID는 유지)
    localStorage.setItem("strati_linked", "1");
    await syncNow();                           // 내 로컬을 공유 버킷에 병합 + 병합본 수신
    return true;
  }
  function isLinked() { return localStorage.getItem("strati_linked") === "1"; }
  function linkedCount() { return parseInt(localStorage.getItem("strati_devices") || "0", 10) || 0; }

  async function listDevices() {       // {devices:[{id,seen}], current}
    const res = await fetch("/api/devices/", {
      headers: { "X-Device": deviceToken(), "X-Device-Id": deviceId() } });
    if (!res.ok) throw new Error("failed");
    return res.json();
  }
  async function forgetDevice(id) {    // 버킷 목록에서 특정 기기 제거
    const res = await fetch("/api/device/forget/", {
      method: "POST", headers: { "X-Device": deviceToken(), "Content-Type": "application/json" },
      body: JSON.stringify({ id }) });
    if (!res.ok) throw new Error("failed");
    const d = await res.json();
    if (typeof d.devices === "number") localStorage.setItem("strati_devices", String(d.devices));
    return d;
  }
  async function unlinkThisDevice() {  // 이 기기를 공유 버킷에서 분리(새 솔로 토큰)
    try { await forgetDevice(deviceId()); } catch (e) { /* best-effort */ }
    localStorage.setItem(TKEY, randId());
    localStorage.removeItem("strati_linked");
    localStorage.removeItem("strati_devices");
    await syncNow();                   // 내 데이터는 유지한 채 새 버킷으로 업로드
  }

  // ── 사진 (IndexedDB, 기기 로컬 — 동기화 안 함) ───────────────────────
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

  // ── UI helpers ───────────────────────────────────────────────────────
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

  document.addEventListener("DOMContentLoaded", function () { refresh(); initSync(); });

  window.STRATI = {
    getBM, isBM, toggle, esc, refresh, getNote, hasNote, setNote,
    hasPhoto, getPhotos, addPhotoFile, deletePhoto,
    syncNow, firstSync, deviceToken, deviceId, pairNew, pairClaim,
    isLinked, linkedCount, listDevices, forgetDevice, unlinkThisDevice,
  };
})();
