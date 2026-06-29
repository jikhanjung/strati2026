"""output/*.json → DB 적재.

  python manage.py import_json
"""
import datetime as dt
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from congress.models import Abstract, Session, Talk

MONTHS = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5,
          "June": 6, "July": 7, "August": 8, "September": 9, "October": 10,
          "November": 11, "December": 12}
YEAR = 2026


def parse_day(label):
    # "June 29" -> date(2026, 6, 29)
    m, d = label.split()
    return dt.date(YEAR, MONTHS[m], int(d))


def parse_time(s):
    if not s:
        return None
    h, m = s.split(":")
    return dt.time(int(h), int(m))


class Command(BaseCommand):
    help = "Load sessions/abstracts/program JSON into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--if-empty", action="store_true",
            help="이미 데이터가 있으면 건너뜀 (컨테이너 최초 기동용).")

    def load(self, name):
        path = settings.OUTPUT_DIR / name
        return json.loads(path.read_text(encoding="utf-8"))

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts.get("if_empty") and Talk.objects.exists():
            self.stdout.write("data already present, skip (--if-empty)")
            return
        # 기존 데이터 초기화 (재적재 가능하도록)
        Talk.objects.all().delete()
        Abstract.objects.all().delete()
        Session.objects.all().delete()

        # 1) sessions
        sess = self.load("sessions.json")["sessions"]
        Session.objects.bulk_create([
            Session(code=s["code"], category=s["category"],
                    title=s.get("title") or "", poster_count=s.get("poster_count", 0))
            for s in sess
        ])
        codes = set(Session.objects.values_list("code", flat=True))
        self.stdout.write(f"sessions: {len(sess)}")

        # 2) abstracts (원본 id 보존)
        absx = self.load("abstracts.json")["abstracts"]
        Abstract.objects.bulk_create([
            Abstract(
                id=a["id"],
                session_id=a["session"] if a["session"] in codes else None,
                page=a.get("page"),
                title=a["title"],
                abstract_text=a.get("abstract", ""),
                keywords=a.get("keywords", []),
                authors=a.get("authors", []),
                affiliations=a.get("affiliations_raw", []),
            )
            for a in absx
        ])
        self.stdout.write(f"abstracts: {len(absx)}")

        # 3) talks (program)
        talks = self.load("program.json")["talks"]
        objs = []
        for t in talks:
            if not t.get("date") or not t.get("time_start"):
                continue
            objs.append(Talk(
                id=t["id"],
                date=parse_day(t["date"]),
                day_label=t["date"],
                room=t.get("room") or "",
                session_id=t["session"] if t.get("session") in codes else None,
                time_start=parse_time(t["time_start"]),
                time_end=parse_time(t.get("time_end")),
                title=t["title"],
                first_author=t.get("first_author") or "",
                kind=t.get("kind", "talk"),
                abstract_id=t.get("abstract_id"),
                page=t.get("page"),
            ))
        Talk.objects.bulk_create(objs)
        self.stdout.write(f"talks: {len(objs)} (linked={sum(1 for o in objs if o.abstract_id)})")
        self.stdout.write(self.style.SUCCESS("import complete"))
