import json
import os

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APPS_DIR = os.path.join(BASE_DIR, "apps")
TMP_DIR = os.path.join(BASE_DIR, "tmp")


with open(os.path.join(TMP_DIR, "secrets.json")) as f:
    secrets_json = json.loads(f.read())


def get_secret(setting, secrets=secrets_json):
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {} environment variable.".format(setting)
        raise ImproperlyConfigured(error_msg)


SECRET_KEY = get_secret("SECRET_KEY")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "filebrowser",
    "tinymce",
    "corsheaders",
    "apps.users.apps.UsersConfig",
    "apps.goals.apps.GoalsConfig",
    "apps.todos.apps.TodosConfig",
    "apps.notes.apps.NotesConfig",
    "apps.story.apps.StoryConfig",
    "apps.achievements.apps.AchievementsConfig",
    "apps.uploads.apps.UploadsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(TMP_DIR, "db.sqlite3"),
    }
}

LOGIN_URL = "/admin/login/"
AUTH_USER_MODEL = "users.CustomUser"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Berlin"

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(TMP_DIR, "static")

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static/dist")]

MEDIA_URL = "/media/"

MEDIA_ROOT = os.path.join(TMP_DIR, "media")

LOGIN_URL = "/global-form/Login/"
LOGIN_REDIRECT_URL = "/todos/todos/"
LOGOUT_REDIRECT_URL = "/global-form/Login/"

TINYMCE_DEFAULT_CONFIG = {
    "height": 360,
    "cleanup_on_startup": True,
    "custom_undo_redo_levels": 20,
    "selector": "textarea",
    "plugins": """
            save link image media preview codesample
            table code lists fullscreen  insertdatetime  nonbreaking
            directionality searchreplace wordcount visualblocks
            visualchars code fullscreen autolink lists  charmap print  hr
            anchor pagebreak
            """,
    "toolbar1": """
            fullscreen preview bold italic underline | fontselect,
            fontsizeselect  | forecolor backcolor | alignleft alignright |
            aligncenter alignjustify | indent outdent | bullist numlist table |
            | link image media | codesample |
            """,
    "toolbar2": """
            visualblocks visualchars |
            charmap hr pagebreak nonbreaking anchor |  code |
            """,
    "contextmenu": "formats | link image",
    "menubar": True,
    "statusbar": True,
    "relative_urls": False,
    "remove_script_host": False,
    "convert_urls": True,
}

FILEBROWSER_DIRECTORY = "user_content/"
DIRECTORY = ""

CORS_ALLOWED_ORIGINS = ["https://goals.danielmoessner.de", "http://localhost:3000"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CUSTOM_ALLOW_REGISTRATION = True

SESSION_COOKIE_AGE = 60 * 60 * 24 * 365  # 1 year
