from wsgic.routing import Router
from wsgic.helpers import config

from .views import *
from .helpers import appdir

router, routes = Router().get_routes()
routes.set("{", "}", "::")

routes.error([404, 403, 500], lambda e: render('admin/error.html', error=e))

with routes.use(AdminView()) as routes:
    routes.get("/", "index", name="admin_index"),
    
    routes.add("/manage/{url::path}/{id::int}", "single", method=["GET", 'POST'], name="admin_single_id")
    routes.add("/manage/{url::path}", "single", method=["GET", 'POST'], name="admin_single")
    routes.post("/manage/{url::path}/action", "action", name="admin_action")

    routes.post("generate", "generate", name="admin_new_token")
    routes.post("create_user", "create_user", name="admin_new_user"),
    routes.post("delete_user", "delete_user", name="admin_delete_user"),
    routes.post("create_role", "create_role", name="admin_new_role"),
    routes.post("delete_role", "delete_role", name="admin_delete_role")
    
    if config.DEBUG:
        routes.get("/test/{name}", lambda name: render(name))
        routes.get("/regen", "regen")

with routes.use(AuthenticationView()), routes.group('auth')  as routes:
    routes.add("login", "login", ["GET", "POST"], name="admin_login")
    routes.get("logout", "logout", name="admin_logout")
    routes.add("register", "register", ["GET", "POST"], name="admin_register")

    routes.get("validate/{code::int}", "validate", name="admin_validate")
    routes.add("reset_password", "send_password_reset_email", ["GET", "POST"], name="admin_password_reset")
    routes.get("change_password", "change_password", name="admin_change_pass")
    routes.get("change_password/{code::int}", "change_password_validate", name="admin_change_pass_validate")

# routes.static("/media", store, name="adminmedia")
routes.static("/assets", appdir["assets"], name="adminstatic")
