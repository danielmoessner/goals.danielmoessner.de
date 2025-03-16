from config.form_addons import Addons, StayOnPageAddon


class FormClass:
    addons: Addons = {}

    # def __init__(
    #     self,
    #     user: CustomUser | AbstractBaseUser | AnonymousUser,
    #     opts: dict[str, Any],
    #     *args,
    #     **kwargs,
    # ): ...

    # def ok(self) -> int: ...

    # def is_valid(self) -> bool: ...

    def _has_addon(self, key: str) -> bool:
        return key in self.addons

    @property
    def stay_on_page(self) -> StayOnPageAddon | None:
        return self.addons.get("stay_on_page", None)
