from wsgic.thirdparty.airium import Airium

class Form(Airium):
    def __init__(self, *a, **kw):
        super().__init__()
        with self.form(*a, **kw):
            self.render()
    
    def render(self):
        pass

class CreateForm(Form):
    def render(self):
        with self.div(class_="col-md-6 col-12"):
            with self.div(class_="card"):
                with self.div(class_="card-header"):
                    with self.h4(class_="card-title"):
                        self("Create new {{ panel.name }} item")
                with self.div(class_="card-content"):
                    with self.div(class_="card-body"):
                        with self.form(class_="form form-horizontal", action="{{ route('admin_single_new', model=panel.name.lower()) }}", method="post"):
                            with self.div(class_="form-body"):
                                with self.div(class_="row"):
                                    self("{% for column in panel.columns %}")
                                    with self.div(class_="col-md-4"):
                                        with self.label():
                                            self("{{ column.replace("_", " ").title() }}")
                                    with self.div(class_="col-md-8 form-group"):
                                        self.input(type="{{ panel.sql_to_form(panel.columns[column]) }}", id="first-name", class_="form-control", name="{{ column }}", placeholder="{{ column.replace('_' ' ').title() }}")

                                    self("{% endfor %}")
                                    with self.div(class_="col-12 col-md-8 offset-md-4 form-group"):
                                        with self.div(class_='form-check'):
                                            with self.div(class_="checkbox"):
                                                with self.input type="checkbox" id="checkbox1"(class_='form-check-input', checked=''):
                                                with self.label(for_="checkbox1"):
                                                    self("Remember Me")
                                    with self.div(class_="col-sm-12 d-flex justify-content-end"):
                                        with self.button(type="submit", class_="btn btn-primary mr-1 mb-1"):
                                            self("Create")
                                        with self.button(type="reset", class_="btn btn-light-secondary mr-1 mb-1"):
                                            self("Reset")

