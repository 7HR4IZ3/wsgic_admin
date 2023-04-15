
def setup_demo():
    from .views import authentication

    authentication.setup_demo()
    print("Done")