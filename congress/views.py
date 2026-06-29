from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Abstract, Session, Talk

ROOM_ORDER = [
    "International Room I", "International Room II", "International Room III",
    "Room 773", "Room 775", "Room 776",
]


def _days():
    return list(Talk.objects.order_by("date").values_list("date", flat=True).distinct())


def _talk_payload(t):
    return {
        "id": t.id,
        "day": t.day_label,
        "date": t.date.isoformat(),
        "room": t.room,
        "session": t.session_id,
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
    columns = [(r, by_room[r]) for r in rooms]

    return render(request, "congress/program.html", {
        "days": days, "selected": sel, "columns": columns, "plenary": plenary,
    })


def talk_detail(request, pk):
    t = get_object_or_404(Talk.objects.select_related("session", "abstract"), pk=pk)
    return render(request, "congress/talk_detail.html",
                  {"talk": t, "abstract": t.abstract, "obj_title": t.title})


def abstract_detail(request, pk):
    a = get_object_or_404(Abstract.objects.select_related("session"), pk=pk)
    return render(request, "congress/talk_detail.html",
                  {"talk": a.talks.first(), "abstract": a, "obj_title": a.title})


def sessions(request):
    items = Session.objects.annotate(
        n_talks=Count("talks", distinct=True),
        n_abs=Count("abstracts", distinct=True),
    )
    items = sorted(items, key=lambda s: (s.category, int(s.code[1:])))
    return render(request, "congress/sessions.html", {"sessions": items})


def session_detail(request, code):
    s = get_object_or_404(Session, code=code)
    talks = list(s.talks.select_related("abstract").all())
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
    data = [_talk_payload(t) for t in Talk.objects.select_related("session").all()]
    return JsonResponse({"talks": data})


def home(request):
    return redirect("program")
