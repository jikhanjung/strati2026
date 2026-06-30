from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("program/", views.program, name="program"),
    path("sessions/", views.sessions, name="sessions"),
    path("session/<str:code>/", views.session_detail, name="session_detail"),
    path("talk/<int:pk>/", views.talk_detail, name="talk_detail"),
    path("abstract/<int:pk>/", views.abstract_detail, name="abstract_detail"),
    path("search/", views.search, name="search"),
    path("timetable/", views.timetable, name="timetable"),
    path("calendar.ics", views.calendar_ics, name="calendar_ics"),
    path("api/talks/", views.api_talks, name="api_talks"),
    path("api/sync/", views.api_sync, name="api_sync"),
    path("api/pair/new/", views.pair_new, name="pair_new"),
    path("api/pair/claim/", views.pair_claim, name="pair_claim"),
    path("api/devices/", views.api_devices, name="api_devices"),
    path("api/device/forget/", views.device_forget, name="device_forget"),
]
