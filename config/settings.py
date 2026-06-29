"""Django settings for STRATI 2026 companion app."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(key, default=False):
    return os.environ.get(key, str(default)).lower() in ("1", "true", "yes", "on")


SECRET_KEY = os.environ.get(
    "STRATI_SECRET_KEY",
    "django-insecure-%ydgk0u_p1phr2%n%nq7r+cqxk%5shz^%_)%me8nqgkau-5(n0",
)

DEBUG = env_bool("STRATI_DEBUG", True)

ALLOWED_HOSTS = os.environ.get("STRATI_ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("STRATI_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "congress",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "congress.context_processors.version",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# DB: SQLite 단일 파일. production/이 서버 모두 /srv/strati2026 의 파일을 사용
# (Docker 에서는 호스트 /srv/strati2026 를 컨테이너에 mount).
STRATI_DB_PATH = os.environ.get("STRATI_DB_PATH", "/srv/strati2026/db.sqlite3")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": STRATI_DB_PATH,
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Shanghai"   # 학회 개최지(쑤저우) 기준
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# JSON 산출물 위치 (import_json 커맨드가 읽음)
OUTPUT_DIR = Path(os.environ.get("STRATI_OUTPUT_DIR", BASE_DIR / "output"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
