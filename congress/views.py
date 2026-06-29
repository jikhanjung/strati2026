import datetime as dt
from zoneinfo import ZoneInfo

from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import ROOM_FLOOR, Abstract, Session, Talk

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
