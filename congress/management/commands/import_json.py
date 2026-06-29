"""output/*.json → DB 적재.

  python manage.py import_json            # 전체 wipe 후 재적재(기본)
  python manage.py import_json --upsert   # PK 기준 update + 신규 insert (wipe 없음)
  python manage.py import_json --if-empty # 데이터 있으면 건너뜀

북마크는 클라이언트(localStorage)에 있어 DB엔 사용자 데이터가 없으므로,
--upsert 는 output/*.json 을 안전하게 DB에 반영(재배포 시 자동 갱신)한다.
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
            help="이미 데이터가 있으면 건너뜀.")
        parser.add_argument(
            "--upsert", action="store_true",
            help="wipe 없이 PK 기준 update + 신규 insert.")

    def load(self, name):
        path = settings.OUTPUT_DIR / name
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, model, objs, unique_fields, update_fields, upsert):
        if upsert:
            model.objects.bulk_create(
                objs, update_conflicts=True,
                unique_fields=unique_fields, update_fields=update_fields)
        else:
            model.objects.bulk_create(objs)

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts.get("if_empty") and Talk.objects.exists():
            self.stdout.write("data already present, skip (--if-empty)")
            return
        upsert = opts.get("upsert")
        if not upsert:
            Talk.objects.all().delete()
            Abstract.objects.all().delete()
            Session.objects.all().delete()

        # 1) sessions
        sess = self.load("sessions.json")["sessions"]
        self.save(Session, [
            Session(code=s["code"], category=s["category"],
                    title=s.get("title") or "", poster_count=s.get("poster_count", 0))
            for s in sess
        ], ["code"], ["category", "title", "poster_count"], upsert)
        codes = set(Session.objects.values_list("code", flat=True))
        self.stdout.write(f"sessions: {len(sess)}")

        # 2) abstracts (원본 id 보존)
        absx = self.load("abstracts.json")["abstracts"]
        self.save(Abstract, [
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
        ], ["id"], ["session", "page", "title", "abstract_text",
                    "keywords", "authors", "affiliations"], upsert)
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
        self.save(Talk, objs, ["id"],
                  ["date", "day_label", "room", "session", "time_start",
                   "time_end", "title", "first_author", "kind", "abstract", "page"],
                  upsert)
        self.stdout.write(f"talks: {len(objs)} (linked={sum(1 for o in objs if o.abstract_id)})")
        self.stdout.write(self.style.SUCCESS(
            "import complete" + (" (upsert)" if upsert else "")))
