from wsgic import WSGIApp
from wsgic.helpers import config
from wsgic.thirdparty.bottle import TEMPLATE_PATH

from .helpers import appdir

class AdminApp(WSGIApp):
	def __init__(self):
		super().__init__("wsgic_admin.urls:router", config)
	
	def setup(self):
		super().setup()
		TEMPLATE_PATH.append(appdir["template"].config["directory"].replace(".ext.", "_"))

__app__ = AdminApp()
