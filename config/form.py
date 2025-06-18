from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.actions import FORMS, NAVS, FormClass
from apps.utils.functional import list_map
from config.errors import GetFormError, InvalidUserError


def get_name(cls: type[object]):
    return cls.__name__


FORMS_DICT: dict[str, type[FormClass]] = {get_name(c): c for c in FORMS}


def get_form_class(form_name: str | None) -> type[FormClass]:
    if form_name is None:
        raise GetFormError("form needs to be supplied")
    form_class = FORMS_DICT.get(form_name, None)
    if form_class is None:
        raise GetFormError(f"form with name '{form_name}' not found")
    return form_class


def get_navs(form: FormClass) -> list[str]:
    return list_map(form.addons.get("navs", []), lambda n: NAVS.get(n, ""))


def set_request(form: FormClass, request: HttpRequest) -> None:
    if hasattr(form, "inject_request"):
        form.inject_request(request)  # type: ignore


def form_view(
    request: HttpRequest, form_name: str, template_name="form_view.html"
) -> HttpResponse:
    if request.method not in ["GET", "POST"]:
        return HttpResponse("only get and post allowed", 400)

    success_url = request.GET.get("success", request.get_full_path())
    assert isinstance(success_url, str)
    cancel_url = request.GET.get("cancel_url")

    try:
        form_class = get_form_class(form_name)
    except GetFormError as e:
        return HttpResponse(str(e), 400)

    data = None
    if request.method == "POST":
        data = {}
        for key in request.POST.keys():
            v = request.POST.getlist(key)
            if len(v) == 1:
                data[key] = v[0]
            else:
                data[key] = v

    files = request.FILES if request.method == "POST" else None

    try:
        form = form_class(request.user, opts=request.GET.dict(), data=data, files=files)
    except InvalidUserError:
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
    set_request(form, request)
    if request.method == "POST" and form.is_valid():
        ret = form.ok()
        if form._has_addon("stay_on_page"):
            return redirect(request.get_full_path())
        success = getattr(form, "success", None)
        if success:
            return redirect(success)
        success_url = success_url.replace("0", str(ret))
        return redirect(success_url)

    response = render(
        request,
        template_name,
        {"form": form, "cancel_url": cancel_url, "navs": get_navs(form)},
    )
    return response


def global_form_view(request: HttpRequest, form_name: str) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    return form_view(request, form_name, "global_form_view.html")
