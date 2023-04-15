import json
from datetime import datetime
from wsgic.http import redirect
from wsgic.session import sessions
from wsgic.database.helpers import BaseValidator
from wsgic.database.columns import ColumnFilters
from wsgic.services import service
from types import FunctionType, LambdaType

from .helpers import Dict
from .models import *

authentication = service("authentication")

class AdminPanel:
    model = None
    list_columns = None
    create_columns = None
    edit_columns = None
    delete_columns = None

    name = None
    skip = None
    group = "ungrouped"
    url = None
    template = "admin/layouts/model_template.html"
    single_template = "admin/layouts/single_template.html"

    edit_action = remove_action = None

    def __init__(self):
        assert self.model

        if self.list_columns:
            c = {}
            for x in self.list_columns:
                try:
                    c[x] = self.model.__columns__[x]
                except LookupError:
                    try:
                        c[x] = getattr(self, x)
                        c[x].name = x
                    except AttributeError:
                        raise Exception("Undefined column "+x)
        else:
            c = self.model.__columns__.copy()
        
        if self.create_columns:
            fc = {}
            for x in self.create_columns:
                try:
                    fc[x] = self.model.__columns__[x]
                except LookupError:
                    try:
                        fc[x] = getattr(self, x)
                        fc[x].name = x
                    except AttributeError:
                        raise Exception("Undefined column "+x)
        else:
            fc = self.model.__columns__.copy()
            fc.pop("id", "")
        self.create_columns = fc
        
        if self.edit_columns:
            fc = {}
            for x in self.edit_columns:
                try:
                    fc[x] = self.model.__columns__[x]
                except LookupError:
                    try:
                        fc[x] = getattr(self, x)
                        fc[x].name = x
                    except AttributeError:
                        raise Exception("Undefined column "+x)
        else:
            fc = self.model.__columns__.copy()
            fc.pop("id", "")
        self.edit_columns = fc
        
        if self.delete_columns:
            fc = {}
            for x in self.delete_columns:
                try:
                    fc[x] = self.model.__columns__[x]
                except LookupError:
                    try:
                        fc[x] = getattr(self, x)
                        fc[x].name = x
                    except AttributeError:
                        raise Exception("Undefined column "+x)
        else:
            fc = {"id": self.model.__columns__["id"]}
        self.delete_columns = fc
        
        # print(self.name, self.create_columns, self.edit_columns, self.delete_columns)

        if self.skip:
            for item in self.skip:
                c.pop(item, None)
                self.create_columns.pop(item, None)
                self.edit_columns.pop(item, None)
                self.delete_columns.pop(item, None)

        self.columns = c
        self.name = self.name or self.model.__name__
        self.url = str(self.url or str(self.group or '').lower() + '/' + self.model.__name__).lower()
        self.model.admin_url = self.url

        # print(self.model, self.model.__validation_rules__(), self.model.__validation_context__())
        # print()

        self.validator = service("validation", rules=self.model.__validation_rules__(), context=self.model.__validation_context__(), filterclass=ColumnFilters)

    def apply_data(self, column, value):
        return value[column]
    
    def apply_value(self, column, value):
        return value

    def apply_title(self, column):
        return str(column).replace("_", " ").title()

    def create(self, data):
        if self.validator.validate(data):
            return self.model.objects.create(**data)
        return redirect().back().with_inputs().error(*self.validator.errors_list())

    def update(self, data, id):
        if self.validator.validate(data):
            return self.model.objects.update(data, id=id)
        return redirect().back().with_inputs().error(*self.validator.errors_list())
    
    def delete(self, data):
        return self.model.objects.delete(**data)

    def get_actions(self):
        actions = {
            z.replace("_action", ''): getattr(self, z) for z in dir(self) if z.endswith("_action") and isinstance(getattr(self, z), (FunctionType, LambdaType))
        }
        return actions

panels = Dict()

def register(*a):
    for panel in a:
        if panel:
            if hasattr(panel, "template"):
                lpanel = panel()
            else:
                lpanel = AdminPanel
                lpanel.model = panel
                lpanel = lpanel()
            panels.set(lpanel.url, lpanel, lpanel.group)


class PasswordValidator(BaseValidator):
    def __init__(self, min_length=8, max_length=30):
        self.minl = min_length
        self.maxl = max_length
    
    def setup(self, column):
        self.column = column
        column.helper_texts.append("Password must be more than %d but less than %d"%(self.minl, self.maxl))
    
    def apply(self, data):
        if self.maxl < len(data) > self.minl:
            self.column.add_error("Password length invalid")
        if data == str(data).lower():
            self.column.add_error("Password must contain uppercase")
        return data

class ActivityCategoryPanel(AdminPanel):
    model = ActivityCategory
    group = "Auth"
    name = "Activity Category"

class ActivityPanel(AdminPanel):
    model = Activity
    group = "Auth"

class UserPanel(AdminPanel):
    model = User
    list_columns=["id", "username", "email_addr", "desc"]
    create_columns = ["username", "desc", "email_addr", "password"]
    delete_columns = ["username"]
    skip = ["hash"]
    group = "Auth"
    template = "admin/layouts/model_template_simple.html"

    password = Column(html_type="password", null=False, validators=[PasswordValidator()])
    password.setup(model.db, model)

    def apply_data(self, column, instance):
        return instance[column]
    
    def apply_value(self, column, data):
        if column == "hash":
            return data.decode("utf-8").lstrip("b").strip("'")
        return data

    def create(self, data):
        try:
            data = {x: self.create_columns[x].save(data[x]) for x in data}

            authentication.create_user(data['username'], data['group'], data['password'], data.get('email_addr'), data.get('desc'))
            return dict(ok=True, msg='')
        except Exception as e:
            return dict(ok=False, msg="An error occured")

    def delete(self, data):
        try:
            authentication.delete_user(data.get('username'))
            return dict(ok=True, msg='')
        except Exception as e:
            print(repr(e))
            return dict(ok=False, msg="An error occured")

class GroupPanel(AdminPanel):
    model = Groups
    list_columns = ['id', 'group', 'level']
    create_columns = ['group', 'level']
    delete_columns = ["group"]
    group = "Auth"
    template = 'admin/layouts/model_template_group.html'
    single_template = 'admin/layouts/single_template_group.html'
    
    def create(self, data):
        try:
            authentication.create_group(data.get('group'), data.get('level'))
            return dict(ok=True, msg='')
        except Exception as e:
            return dict(ok=False, msg="An error occured")

    def delete(self, data):
        try:
            authentication.delete_group(data.get('group'))
            return dict(ok=True, msg='')
        except Exception as e:
            return dict(ok=False, msg="An error occured")


class TokenPanel(AdminPanel):
    model = Token
    group = "Auth"

class PendingRegPanel(AdminPanel):
    model = PendingReg
    group = "Auth"
    name = "Pending Registrations"

class SessionPanel(AdminPanel):
    model = getattr(sessions.store, 'sessions', None)
    name = "Sessions"
    group = "Auth"
    
    def apply_data(self, column, instance):
        if isinstance(instance[column], datetime):
            return instance[column].ctime()
        if column == "data":
            value = instance[column]
            value.pop("__wsgic_vars", None)
            return value
        return instance[column]
    
    def delete(self, id):
        for id in id.split(','):
            id = int(id.strip())
            super().delete(id=id)
        return True

register(UserPanel, PendingRegPanel, TokenPanel, SessionPanel if SessionPanel.model != None else None, ActivityPanel, ActivityCategoryPanel)
