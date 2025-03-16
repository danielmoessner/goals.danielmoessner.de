from typing import NotRequired, TypedDict


class StayOnPageAddon(TypedDict):
    submit: str


NAVS = {
    "create": "create_nav.html",
    "todos": "todos/nav.html",
    "achievements": "achievements/nav.html",
    "notes": "notes/nav.html",
    "story": "story/nav.html",
    "settings": "users/nav.html",
    "goals": "goals/nav.html",
}


class NavsAddon(TypedDict):
    navs: list[str]


class Addons(TypedDict):
    stay_on_page: NotRequired[StayOnPageAddon]
    navs: NotRequired[list[str]]
