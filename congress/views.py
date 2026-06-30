import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import (ROOM_FLOOR, Abstract, PairCode, Session, SyncDevice,
                     SyncPhoto, Talk)

CONGRESS_TZ = ZoneInfo("Asia/Shanghai")
ALARM_MIN = 5             # 발표 N분 전 캘린더 알림

ROOM_ORDER = [
    "International Room I", "International Room II", "International Room III",
    "Room 773", "Room 775", "Room 776",
]
MIN_BREAK_MIN = 10        # 이보다 짧은 간격은 휴식으로 보지 않음


def short_room(name):
    if name.startswith("International Room"):
        return "Int'l " + name.rsplit(" ", 1)[-1]
    if name.startswith("Room "):
        return name.split(" ", 1)[1]
    return name


def _gap_minutes(end, start):
    base = dt.date.min
    return (dt.datetime.combine(base, start) - dt.datetime.combine(base, end)).total_seconds() / 60


def _break_label(start, end):
    # 12:30 이전 시작 & 12:30 이후 종료로 점심시간대를 덮으면 Lunch
    if start <= dt.time(12, 30) and end >= dt.time(12, 30):
        return "Lunch"
    return "Break"


def derive_breaks(talks):
    """같은 (날짜·룸)의 연속 발표 사이 빈 시간 → 휴식/점심 entry(표시 전용)."""
    ts = sorted([t for t in talks if t.time_start and t.time_end],
                key=lambda t: t.time_start)
    out = []
    for a, b in zip(ts, ts[1:]):
        if b.time_start > a.time_end and _gap_minutes(a.time_end, b.time_start) >= MIN_BREAK_MIN:
            out.append({"start": a.time_end, "end": b.time_start,
                        "label": _break_label(a.time_end, b.time_start)})
    return out


def _days():
    return list(Talk.objects.order_by("date").values_list("date", flat=True).distinct())


def _talk_payload(t):
    return {
        "id": t.id,
        "day": t.day_label,
        "date": t.date.isoformat(),
        "room": t.room,
        "session": t.session_id,
        "floor": t.floor,
        "start": t.time_start.strftime("%H:%M") if t.time_start else "",
        "end": t.time_end.strftime("%H:%M") if t.time_end else "",
        "title": t.title,
        "author": t.first_author,
        "kind": t.kind,
        "abstract_id": t.abstract_id,
    }


def program(request):
    """일자별 프로그램. ?day=YYYY-MM-DD"""
    days = _days()
    if not days:
        return render(request, "congress/program.html", {"days": []})
    day_param = request.GET.get("day")
    if day_param:
        sel = next((d for d in days if d.isoformat() == day_param), days[0])
    else:
        # 명시적 선택이 없으면 오늘(쑤저우 시간)을, 일정에 없으면 첫째 날을 기본 선택
        today = timezone.now().astimezone(CONGRESS_TZ).date()
        sel = today if today in days else days[0]
    talks = list(Talk.objects.filter(date=sel).select_related("session", "abstract"))

    rooms = sorted({t.room for t in talks if t.room},
                   key=lambda r: ROOM_ORDER.index(r) if r in ROOM_ORDER else 99)
    by_room = {r: [] for r in rooms}
    plenary = []
    for t in talks:
        if t.room:
            by_room[t.room].append(t)
        else:
            plenary.append(t)
    columns = []
    for r in rooms:
        items = [("talk", t) for t in by_room[r]]
        items += [("break", b) for b in derive_breaks(by_room[r])]
        items.sort(key=lambda it: (it[1].time_start if it[0] == "talk" else it[1]["start"]))
        columns.append((r, short_room(r), ROOM_FLOOR.get(r, ""), items))

    return render(request, "congress/program.html", {
        "days": days, "selected": sel, "columns": columns, "plenary": plenary,
    })


def talk_detail(request, pk):
    t = get_object_or_404(Talk.objects.select_related("session", "abstract"), pk=pk)
    return render(request, "congress/talk_detail.html",
                  {"talk": t, "abstract": t.abstract, "session": t.session,
                   "obj_title": t.title})


def abstract_detail(request, pk):
    a = get_object_or_404(Abstract.objects.select_related("session"), pk=pk)
    return render(request, "congress/talk_detail.html",
                  {"talk": a.talks.first(), "abstract": a, "session": a.session,
                   "obj_title": a.title})


def sessions(request):
    items = Session.objects.annotate(
        n_talks=Count("talks", distinct=True),
        n_abs=Count("abstracts", distinct=True),
    )
    items = sorted(items, key=lambda s: (s.category, int(s.code[1:])))
    return render(request, "congress/sessions.html", {"sessions": items})


def session_detail(request, code):
    s = get_object_or_404(Session, code=code)
    talks = list(s.talks.select_related("abstract", "session").all())
    linked = {t.abstract_id for t in talks if t.abstract_id}
    extra = [a for a in s.abstracts.all() if a.id not in linked]   # 구두 미편성/포스터
    return render(request, "congress/session_detail.html",
                  {"session": s, "talks": talks, "extra": extra})


def search(request):
    q = (request.GET.get("q") or "").strip()
    talks = []
    if q:
        talks = list(Talk.objects.filter(
            Q(title__icontains=q) | Q(first_author__icontains=q) |
            Q(session__title__icontains=q)
        ).select_related("session")[:200])
    return render(request, "congress/search.html", {"q": q, "talks": talks})


def timetable(request):
    """북마크는 localStorage. 이 페이지는 JS가 /api/talks 로 렌더링."""
    return render(request, "congress/timetable.html", {})


def settings_page(request):
    """사용자 설정(동기화·사진 on/off 등). 값은 localStorage, JS로 처리."""
    return render(request, "congress/settings.html", {})


def api_talks(request):
    # ?ids=1,2,3 가 오면 그 발표들만 반환(My Plan 전용, 페이로드 최소화).
    # 휴식 도출은 전체 프로그램에서 해야 정확하므로 항상 전체를 조회.
    all_talks = list(Talk.objects.select_related("session").all())
    ids_param = request.GET.get("ids")
    if ids_param is not None:
        want = {int(x) for x in ids_param.split(",") if x.strip().isdigit()}
        sel = [t for t in all_talks if t.id in want]
    else:
        sel = all_talks
    data = [_talk_payload(t) for t in sel]

    # (날짜·룸)별 휴식/점심 도출 (표시 전용, 북마크 불가)
    from collections import defaultdict
    grouped = defaultdict(list)
    for t in all_talks:
        if t.room:
            grouped[(t.day_label, t.date.isoformat(), t.room)].append(t)
    # ids가 오면, 반환된 발표 직전의 휴식만 남겨 페이로드를 더 줄임
    keep = {(t.date.isoformat(), t.room, t.time_start.strftime("%H:%M"))
            for t in sel if t.room and t.time_start} if ids_param is not None else None
    breaks = []
    for (day, date, room), ts in grouped.items():
        for b in derive_breaks(ts):
            end = b["end"].strftime("%H:%M")
            if keep is not None and (date, room, end) not in keep:
                continue   # 북마크 발표로 이어지는 휴식이 아니면 제외
            breaks.append({"day": day, "date": date, "room": room,
                           "start": b["start"].strftime("%H:%M"),
                           "end": end, "label": b["label"]})
    resp = JsonResponse({"talks": data, "breaks": breaks})
    # 데이터는 배포 때만 바뀜 → 버전 쿼리(?v=)로 캐시 무효화하므로 장기 캐싱 가능
    resp["Cache-Control"] = "public, max-age=86400"
    return resp


def _ics_escape(s):
    return (s or "").replace("\\", "\\\\").replace(";", "\\;") \
        .replace(",", "\\,").replace("\n", "\\n")


def _ics_utc(date, t):
    local = dt.datetime.combine(date, t, tzinfo=CONGRESS_TZ)
    return local.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def calendar_ics(request):
    """북마크한 발표를 폰 캘린더에 추가(.ics). 각 일정에 N분 전 알림(VALARM)."""
    ids = [int(x) for x in request.GET.get("ids", "").split(",") if x.strip().isdigit()]
    talks = Talk.objects.filter(id__in=ids).select_related("session").order_by("date", "time_start")
    stamp = timezone.now().astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//strati2026//EN",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:STRATI 2026"]
    for t in talks:
        if not t.time_start:
            continue
        end_t = t.time_end or (dt.datetime.combine(dt.date.min, t.time_start)
                               + dt.timedelta(minutes=20)).time()
        loc = t.room + (f" ({t.floor})" if t.floor else "")
        desc = " · ".join(p for p in [t.session_id, t.first_author] if p)
        lines += [
            "BEGIN:VEVENT",
            f"UID:talk-{t.id}@strati2026",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{_ics_utc(t.date, t.time_start)}",
            f"DTEND:{_ics_utc(t.date, end_t)}",
            f"SUMMARY:{_ics_escape(t.title)}",
            f"LOCATION:{_ics_escape(loc)}",
            f"DESCRIPTION:{_ics_escape(desc)}",
            "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Reminder",
            f"TRIGGER:-PT{ALARM_MIN}M", "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines) + "\r\n"
    resp = HttpResponse(body, content_type="text/calendar; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="strati2026.ics"'
    return resp


def home(request):
    return redirect("program")


# ── 사진 동기화 (서버 저장 + 서명 URL) ────────────────────────────────────
PHOTO_URL_TTL = 30 * 24 * 3600   # 서명 URL 유효기간(초)


def _photo_sig(pid, exp):
    msg = f"{pid}:{exp}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()[:32]


def _photo_url(p):
    exp = int(timezone.now().timestamp()) + PHOTO_URL_TTL
    return f"/api/photos/file/{p.id}?exp={exp}&sig={_photo_sig(p.id, exp)}"


def _photo_meta(p):
    return {"id": p.id, "talk": p.talk_id, "size": p.size,
            "ts": p.created.isoformat(), "url": _photo_url(p)}


@csrf_exempt
@require_POST
def photo_upload(request):
    token = _device_token(request)
    if not token:
        return JsonResponse({"error": "missing device token"}, status=400)
    try:
        talk_id = int(request.POST.get("talk") or 0)
    except ValueError:
        talk_id = 0
    f = request.FILES.get("file")
    if not talk_id or not f:
        return JsonResponse({"error": "talk and file required"}, status=400)
    if f.size > settings.PHOTO_MAX_BYTES:
        return JsonResponse({"error": "file too large"}, status=413)
    # 쿼터: talk당 장수 · 토큰당 총 용량
    if SyncPhoto.objects.filter(token=token, talk_id=talk_id).count() >= settings.PHOTO_MAX_PER_TALK:
        return JsonResponse({"error": "per-talk limit reached"}, status=409)
    used = SyncPhoto.objects.filter(token=token).aggregate(s=Sum("size"))["s"] or 0
    if used + f.size > settings.PHOTO_MAX_PER_TOKEN:
        return JsonResponse({"error": "storage quota reached"}, status=409)

    sub = hashlib.sha256(token.encode()).hexdigest()[:16]
    folder = os.path.join(settings.MEDIA_ROOT, "photos", sub)
    os.makedirs(folder, exist_ok=True)
    p = SyncPhoto.objects.create(token=token, talk_id=talk_id, filename="", size=f.size)
    rel = os.path.join("photos", sub, f"{p.id}.jpg")
    with open(os.path.join(settings.MEDIA_ROOT, rel), "wb") as out:
        for chunk in f.chunks():
            out.write(chunk)
    p.filename = rel
    p.save(update_fields=["filename"])
    return JsonResponse(_photo_meta(p))


@csrf_exempt
@require_GET
def photo_list(request):
    token = _device_token(request)
    if not token:
        return JsonResponse({"error": "missing device token"}, status=400)
    qs = SyncPhoto.objects.filter(token=token)
    talk = request.GET.get("talk")
    if talk and talk.isdigit():
        qs = qs.filter(talk_id=int(talk))
    return JsonResponse({"photos": [_photo_meta(p) for p in qs]})


@csrf_exempt
@require_GET
def photo_talks(request):
    """이 토큰이 사진을 가진 talk id 목록(카드 📷 표시용)."""
    token = _device_token(request)
    if not token:
        return JsonResponse({"error": "missing device token"}, status=400)
    ids = list(SyncPhoto.objects.filter(token=token)
               .values_list("talk_id", flat=True).distinct())
    return JsonResponse({"talks": ids})


@require_GET
def photo_file(request, pid):
    """서명 URL로만 접근(헤더 인증 불가한 <img> 대응)."""
    try:
        exp = int(request.GET.get("exp") or 0)
    except ValueError:
        exp = 0
    sig = request.GET.get("sig") or ""
    if exp < timezone.now().timestamp() or not hmac.compare_digest(sig, _photo_sig(pid, exp)):
        return HttpResponse(status=403)
    p = SyncPhoto.objects.filter(id=pid).first()
    if not p or not p.filename:
        return HttpResponse(status=404)
    path = os.path.join(settings.MEDIA_ROOT, p.filename)
    if not os.path.exists(path):
        return HttpResponse(status=404)
    resp = FileResponse(open(path, "rb"), content_type="image/jpeg")
    resp["Cache-Control"] = "private, max-age=2592000"
    return resp


@csrf_exempt
@require_POST
def photo_delete(request, pid):
    token = _device_token(request)
    if not token:
        return JsonResponse({"error": "missing device token"}, status=400)
    p = SyncPhoto.objects.filter(id=pid, token=token).first()
    if not p:
        return JsonResponse({"error": "not found"}, status=404)
    if p.filename:
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, p.filename))
        except OSError:
            pass
    talk_id = p.talk_id
    p.delete()
    remaining = SyncPhoto.objects.filter(token=token, talk_id=talk_id).count()
    return JsonResponse({"deleted": True, "talk": talk_id, "remaining": remaining})


# ── 동기화 (익명 디바이스 토큰 + 페어링 코드) ─────────────────────────────
SYNC_SECTIONS = ("bm", "notes")
PAIR_TTL = dt.timedelta(minutes=5)


def _device_token(request):
    t = (request.headers.get("X-Device") or "").strip()
    return t if 8 <= len(t) <= 128 else ""


def _merge_state(a, b):
    """항목별 last-write-wins(ts 큰 쪽). a,b = {"bm":{id:{v,ts}}, "notes":{...}}."""
    out = {}
    for sec in SYNC_SECTIONS:
        m = {}
        for src in (a.get(sec) or {}), (b.get(sec) or {}):
            if not isinstance(src, dict):
                continue
            for k, e in src.items():
                if not isinstance(e, dict):
                    continue
                ts = e.get("ts") or 0
                if k not in m or ts > (m[k].get("ts") or 0):
                    m[k] = {"v": e.get("v"), "ts": ts}
        out[sec] = m
    return out


@csrf_exempt
@require_POST
def api_sync(request):
    """클라이언트 상태를 받아 서버 상태와 병합 후 병합본 반환(push+pull 일체)."""
    token = _device_token(request)
    if not token:
        return JsonResponse({"error": "missing device token"}, status=400)
    try:
        incoming = json.loads(request.body or "{}")
    except ValueError:
        return JsonResponse({"error": "bad json"}, status=400)
    if not isinstance(incoming, dict):
        incoming = {}
    device_id = (request.headers.get("X-Device-Id") or "").strip()[:128]
    with transaction.atomic():
        dev, _ = SyncDevice.objects.select_for_update().get_or_create(token=token)
        # 이 버킷에서 제거(차단)된 기기면 데이터 제공 없이 거부 → 클라가 새 토큰으로 분리
        if device_id and device_id in (dev.revoked or []):
            return JsonResponse({"revoked": True}, status=409)
        try:
            stored = json.loads(dev.state or "{}")
        except ValueError:
            stored = {}
        merged = _merge_state(stored, incoming)
        dev.state = json.dumps(merged, separators=(",", ":"))
        # 이 버킷을 쓴 디바이스 ID 기록(중복 방지) → 연결 기기 수 산출
        devices = dev.devices if isinstance(dev.devices, list) else []
        now_iso = timezone.now().isoformat()
        if device_id:
            entry = next((d for d in devices if isinstance(d, dict) and d.get("id") == device_id), None)
            if entry:
                entry["seen"] = now_iso
            else:
                devices.append({"id": device_id, "seen": now_iso})
        dev.devices = devices
        dev.save()
        count = len(devices)
        paired = dev.paired or count >= 2
    return JsonResponse({**merged, "paired": paired, "devices": count})


@csrf_exempt
def api_devices(request):
    """이 토큰(버킷)을 쓰는 디바이스 목록(최근 접속 순)."""
    token = _device_token(request)
    if not token:
        return JsonResponse({"error": "missing device token"}, status=400)
    dev = SyncDevice.objects.filter(token=token).first()
    raw = dev.devices if (dev and isinstance(dev.devices, list)) else []
    items = [{"id": d.get("id"), "seen": d.get("seen")}
             for d in raw if isinstance(d, dict) and d.get("id")]
    items.sort(key=lambda d: d.get("seen") or "", reverse=True)
    current = (request.headers.get("X-Device-Id") or "").strip()
    return JsonResponse({"devices": items, "current": current})


@csrf_exempt
@require_POST
def device_forget(request):
    """버킷에서 특정 디바이스 ID 제거(목록·카운트에서 빠짐)."""
    token = _device_token(request)
    if not token:
        return JsonResponse({"error": "missing device token"}, status=400)
    try:
        rid = str(json.loads(request.body or "{}").get("id", "")).strip()
    except ValueError:
        return JsonResponse({"error": "bad json"}, status=400)
    with transaction.atomic():
        dev = SyncDevice.objects.select_for_update().filter(token=token).first()
        count = 0
        if dev:
            devs = [d for d in (dev.devices or [])
                    if not (isinstance(d, dict) and d.get("id") == rid)]
            dev.devices = devs
            rev = dev.revoked or []
            if rid and rid not in rev:          # 차단 목록에 추가 → 재접속 시 거부
                rev.append(rid)
            dev.revoked = rev
            dev.save()
            count = len(devs)
    return JsonResponse({"devices": count})


@csrf_exempt
@require_POST
def pair_new(request):
    """현재 토큰을 가리키는 1회용 6자리 코드 발급(5분)."""
    token = _device_token(request)
    if not token:
        return JsonResponse({"error": "missing device token"}, status=400)
    PairCode.objects.filter(expires_at__lt=timezone.now()).delete()   # 만료분 청소
    for _ in range(10):
        code = f"{secrets.randbelow(1000000):06d}"
        if not PairCode.objects.filter(code=code).exists():
            PairCode.objects.create(code=code, token=token,
                                    expires_at=timezone.now() + PAIR_TTL)
            return JsonResponse({"code": code, "expires_in": int(PAIR_TTL.total_seconds())})
    return JsonResponse({"error": "try again"}, status=503)


@csrf_exempt
@require_POST
def pair_claim(request):
    """코드로 상대 기기의 토큰을 받아옴(1회용)."""
    try:
        code = str(json.loads(request.body or "{}").get("code", "")).strip()
    except ValueError:
        return JsonResponse({"error": "bad json"}, status=400)
    row = PairCode.objects.filter(code=code).first()
    if not row:
        return JsonResponse({"error": "invalid code"}, status=404)
    expired = row.expires_at < timezone.now()
    row.delete()
    if expired:
        return JsonResponse({"error": "expired code"}, status=410)
    # 양쪽(코드 생성 기기·청구 기기)이 공유하는 버킷을 "페어링됨"으로 표시.
    # 청구 기기가 이전에 제거(차단)됐었다면 재페어링이므로 차단 해제.
    claimer = (request.headers.get("X-Device-Id") or "").strip()[:128]
    with transaction.atomic():
        dev, _ = SyncDevice.objects.select_for_update().get_or_create(token=row.token)
        dev.paired = True
        if claimer:
            dev.revoked = [r for r in (dev.revoked or []) if r != claimer]
        dev.save()
    return JsonResponse({"token": row.token})
