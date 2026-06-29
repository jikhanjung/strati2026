from django.db import models


class Session(models.Model):
    """학술 세션 (G1..G18, S1..S14)."""
    code = models.CharField(max_length=8, primary_key=True)
    category = models.CharField(max_length=1)          # G | S
    title = models.CharField(max_length=400, blank=True)
    poster_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["category", "code"]

    def __str__(self):
        return f"{self.code}. {self.title}"


class Abstract(models.Model):
    """초록집의 개별 초록."""
    session = models.ForeignKey(Session, null=True, on_delete=models.SET_NULL,
                                related_name="abstracts")
    page = models.IntegerField(null=True)
    title = models.CharField(max_length=600)
    abstract_text = models.TextField(blank=True)
    keywords = models.JSONField(default=list)          # ["kw1", ...]
    authors = models.JSONField(default=list)           # [{name, corresponding, affil_refs}]
    affiliations = models.JSONField(default=list)       # ["raw affil", ...]

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title

    @property
    def author_line(self):
        return ", ".join(a.get("name", "") for a in self.authors)

    @property
    def corresponding(self):
        return [a["name"] for a in self.authors if a.get("corresponding")]


class Talk(models.Model):
    """학술 프로그램의 발표(구두/기조). 시간·장소 + 초록 연결."""
    date = models.DateField()
    day_label = models.CharField(max_length=20)        # "June 29"
    room = models.CharField(max_length=60, blank=True)
    session = models.ForeignKey(Session, null=True, on_delete=models.SET_NULL,
                                related_name="talks")
    time_start = models.TimeField()
    time_end = models.TimeField(null=True)
    title = models.CharField(max_length=600)
    first_author = models.CharField(max_length=200, blank=True)
    kind = models.CharField(max_length=16, default="talk")   # talk | plenary
    abstract = models.ForeignKey(Abstract, null=True, on_delete=models.SET_NULL,
                                 related_name="talks")
    page = models.IntegerField(null=True)

    class Meta:
        ordering = ["date", "time_start", "room"]

    def __str__(self):
        return f"[{self.day_label} {self.time_start:%H:%M}] {self.title}"
