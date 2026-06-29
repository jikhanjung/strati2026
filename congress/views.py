import datetime as dt

from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import ROOM_FLOOR, Abstract, Session, Talk

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
    sel = next((d for d in days if d.isoformat() == day_param), days[0])
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
    talks = list(Talk.objects.select_related("session").all())
    data = [_talk_payload(t) for t in talks]

    # (날짜·룸)별 휴식/점심 도출 (표시 전용, 북마크 불가)
    from collections import defaultdict
    grouped = defaultdict(list)
    for t in talks:
        if t.room:
            grouped[(t.day_label, t.date.isoformat(), t.room)].append(t)
    breaks = []
    for (day, date, room), ts in grouped.items():
        for b in derive_breaks(ts):
            breaks.append({"day": day, "date": date, "room": room,
                           "start": b["start"].strftime("%H:%M"),
                           "end": b["end"].strftime("%H:%M"), "label": b["label"]})
    return JsonResponse({"talks": data, "breaks": breaks})


def home(request):
    return redirect("program")
