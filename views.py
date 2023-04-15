from functools import partial
from wsgic.http import request, response, redirect, abort
from wsgic.views import BaseView, render
from wsgic.views.templates import Jinja2Template
from wsgic.helpers import config
from wsgic.session import sessions
from wsgic.services import service
from wsgic_auth.decorators import (login_required, check, authentication, authorization)
from wsgic.services.validation import Validator
# from wsgic_auth.core import JWTAuth

from .panels import *

render = partial(render, engine=Jinja2Template)

# jwtauth: JWTAuth = service("authentication.jwt")
validation: Validator = service("validation")

class AuthenticationView(BaseView):
    def login(self):
        """Authenticationenticate users"""
        validation_rules = {
            "username": {
                "required": "Username not specified."
            },
            "password": {
                "required": "Password cannot be empty.",
                # "min_length(8)": "Password must be greater than 8 characters.",
                # "max_length(32)": "Password must be less than 32 characters."
            }
        }
        if not request.user:
            if request.method == "GET":
                # messages.add("Login or create an account")
                # if authentication.logged_in():
                #     return redirect().route("admin_index")
                return render("admin/auth-login.html")
            else:

                validation.set_rules(validation_rules)
                username = request.POST.username
                password = request.POST.password
                remember = request.POST.get("remember", False)
                validation.validate(request.POST)

                #validation = request.validation.set_rules(validation_rules).validate()

                # trigger_activity("User Login", f"{authentication.current_user.username} signed in.", category="User")
                if not validation.is_valid():
                    errors = []
                    for error in validation.errors_dict().values():
                        for item in error:
                            errors.append(item)

                    return redirect().back().error(*errors)

                return redirect().route(request.next or "admin_index").message("Logged in successfully as {request.user.username}.") if authentication.login(username, password, remember) else redirect().route("admin_login").error("Log in failed.")
        else:
            # redirect(route("login")))
            return redirect().route(request.next or 'admin_index')
            # return render("admin/index.html")

    def logout(self):
        # trigger_activity("User Login", f"{request.user.username} signed out.", category="User")
        authentication.logout()
        return redirect().route(config.get("logout_redirect") or request.previous_url)
        # messages.add('Logged out successfully.')

    def register(self):
        """Send out registration email"""
        if request.method == 'GET':
            return render('admin/auth-register.html')
        authentication.register(request.POST.get('username'), request.POST.get('password'), request.POST.get('email_address'))
        return redirect().route(config.get('register_redirect', 'admin_login')).message('Check your email to complete registration.')

    def validate(self, code):
        """Validate registration, create user account"""
        authentication.validate_registration(code)
        return 'Thanks. <a href="%s">Go to login</a>' %route('admin_login')

    def send_password_reset_email(self):
        """Send out password reset email"""
        if request.method == 'GET':
            return render('admin/auth-forgot-password.html')
        authentication.send_password_reset_email(
            username=request.POST.get('username'),
            email_addr=request.POST.get('email')
        )
        return redirect().route(config.get('pass_reset_redirect', 'admin_login')).message('Please check your mailbox.')

    def change_password_validate(self, code):
        """Show password change form"""
        return dict(reset_code=code)

    def change_password(self):
        """Change password"""
        authentication.reset_password(request.POST.get('reset_code'), request.POST.get('password'))
        return 'Thanks. <a href="%s">Go to login</a>' %route('admin_login')

    def status(self):
        return f"Logged in as {request.user.username}" if request.user else f"Not logged in"

class AdminView(BaseView):
    decorators = [
        login_required(fail="admin_login", back=True),
        # check(lambda req: authentication.is_logged_in(), fail=partial(abort, 403, "You must be logged in.")),
        check(lambda request: authorization.in_group("admin", request.user.id) if request.user else False, fail=partial(abort, 403, "You must be an admin."))
    ]

    @property
    def sidebaritems(self):
        return [
            {
              "name": "Main Menu",
              "isTitle": True
            },
            {
                "name": "Hompage",
                "key": "home",
                "icon": "home",
                "url": route("admin_index")
            }
          ] + [
            {
              "name": group.title(),
              "key": group,
              "icon": "user",
              "submenu": [
                {
                  "name": panels.grouped[group][item].name,
                  "url": route("admin_single", url=panels.grouped[group][item].url)
                } for item in panels.grouped[group]
              ]
            } for group in panels.grouped
          ] + [
          {
            "name": "Authenticationentication",
            "key": "authenticationentication",
            "icon": "user",
            "submenu": [
              {
                "name": "Logout",
                "url": route("admin_logout")
              },
              {
                "name": "Forgot Password",
                "url": route("admin_forgot_password")
              }
            ]
          }
        ]

    def index(self):
        """Only admin users can see this"""
        return render('admin/index.html', dict(
            panels=panels,
            sidebarItems = self.sidebaritems,
            activities=Activity.objects.get()[::-1][:6],
            Activity=Activity
        ))
    
    def regen(self):
        print(sessions.session.sid)
        sessions.regenerate()
        return "Done"
    
    def single(self, url, id=None):
        panel = panels.get(url)
        if panel:
            try:
                if request.method == "GET":
                    recent_actions = Activity.objects.like(title="Modified Object", body=f"% {panel.name} object%")[:5:-1]
                    return render("admin/single.html", panel=panel, panels=panels, sidebarItems = self.sidebaritems, id=id, activities=Activity.objects.get()[::-1][:6], recent_actions=recent_actions)
    
                elif request.method == "POST":
                    action = request.POST.pop('__action', None)
    
                    if action == "create":
                        data = {x: request.POST[x] for x in request.POST if request.POST.get(x)}
                        r = panel.create(data)
                        trigger_activity("Modified Object", f"{request.user.username} created {panel.name} object")
    
                        if request.next:
                            return redirect().next()
                        return redirect().route("admin_single", url=url).message("%s object created"%panel.name.title())
    
                    elif action == "edit":
                        id = id or request.POST.id
                        data = {x: request.POST[x] for x in request.POST if request.POST.get(x)}
                        print({x: request.POST[x] for x in request.POST})
                        panel.update(data, id)
    
                        trigger_activity("Modified Object", f"{request.user.username} edited {panel.name} object")
    
                        if request.next:
                            return redirect().next()
                        return redirect().route("admin_single", url=url).message("%s object on id=%s edited"%(panel.name.title(), id))
    
                    elif action == "delete":
                        data = {x: request.POST[x] for x in request.POST if request.POST.get(x)}
                        panel.delete(data)
    
                        trigger_activity("Modified Object", f"{request.user.username} deleted {panel.name} object")
    
                        if request.next:
                            return redirect().next()
                        return redirect().route("admin_single", url=url).message("%s object deleted"%panel.name.title())
    
                    else:
                        if request.next:
                            return redirect().next()
                        return redirect().route("admin_index").error("Invalid action '%s'"%url)
            except (ValueError, AssertionError) as e:
                print(e)
                return redirect().back().with_inputs()
        return abort(404, "Not found '%s' "%request.path, error="No model named '%s'"%url)
    
    def action(self, url):
        panel = panels.get(url)
        if panel:
            action = request.POST.get("action")
            ids = (request.POST.get("id")).split(",")
            
            if hasattr(panel, action+"_action"):
                for id in ids:
                    func = getattr(panel, action+"_action")
                    func(panel.model.objects.get(id=id))

                if request.next:
                    return redirect().next()
                return redirect().route("admin_single", url=url).message("%s object deleted"%panel.name.title())
        else:
            return abort(404, "Not found '%s' "%request.path, error="No model named '%s'"%url)
    
    
    def generate(self):
        trigger_activity("Authentication Token", f"{request.user.username} generated authentication token.")
        # return str(jwtauth.generate(authentication.current_user))

    def create_user(self):
        try:
            authentication.create_user(request.POST.username, request.POST.role, request.POST.password)
            return dict(ok=True, msg='')
        except Exception as e:
            return dict(ok=False, msg="An error occured")


    def delete_user(self):
        try:
            authentication.delete_user(request.POST.get('username'))
            return dict(ok=True, msg='')
        except Exception as e:
            print(repr(e))
            return dict(ok=False, msg="An error occured")


    def create_role(self):
        try:
            authentication.create_role(request.POST.get('role'), request.POST.get('level'))
            return dict(ok=True, msg='')
        except Exception as e:
            return dict(ok=False, msg="An error occured")


    def delete_role(self):
        try:
            authentication.delete_role(request.POST.get('role'))
            return dict(ok=True, msg='')
        except Exception as e:
            return dict(ok=False, msg="An error occured")