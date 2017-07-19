#!/opt/env/run-billing-admin-backend/bin/python3.6
#
# Ramode 2017
#


server_interface = "0.0.0.0"
server_port = 8031


# https://docs.python.org/2/howto/logging.html
import logging
logging.basicConfig(level=logging.DEBUG)

import asyncio
from aiohttp import web

# https://github.com/gnarlychicken/aiohttp_auth
from aiohttp_auth import auth

from models import *


async def login_view(request):
	params = await request.post()

	for q in params:
		print (q)

	username = params.get("username", None)
	password = params.get("password", None)

	print(username)
	print(password)
	
	try:
		user_obj = await objects.get(User, name=username, password=password)
	except:
		user_obj = None

	if user_obj:
		await auth.remember(request, username)
		return web.Response(body='OK'.encode('utf-8'))

	raise web.HTTPForbidden()



# One time execution my_function:
# loop = asyncio.get_event_loop()
# loop.run_until_complete( my_function() )
# loop.close()


def setup_routes(app):

	app.router.add_post("/api/v1/login", login_view)

	app.router.add_static("/", "/var/wwws/billing.eth0.pro/html")


app = web.Application()

# Прописывем роуты web-сервера:
setup_routes(app)

# Стартуем сервак!!
web.run_app(app, host=server_interface, port=server_port)
