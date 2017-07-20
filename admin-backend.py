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
import aiohttp_auth
import aiohttp_session 
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from os import urandom
from aiohttp_auth.permissions import Group, Permission

# DB defination:
from models import *


async def login_view(request):
	params = await request.json()
	login = params.get("username", None)
	password = params.get("password", None)

	try:
		# Вываливает трейсбек, если запись не найдена
		user_obj = await objects.get(User, login=login, password=password)
	except:
		user_obj = None

	if user_obj:
		await aiohttp_auth.auth.remember(request, login)
		return web.Response(body='OK'.encode('utf-8'))

	raise web.HTTPForbidden()


async def acl_group_callback(login):
	# The user_id could be None if the user is not authenticated, but in
	# our example, we allow unauthenticated users access to some things, so
	# we return an empty tuple.
	# return group_map.get(user_id, tuple())
	try:
		user_obj = await objects.get(User, login=login)
		group_obj = await objects.get_related(user_obj, "group")
		res = (group_obj.name, )

	except:
		res = None

	return res


async def check_role(request):

	params = await request.json()
	role = params.get("role")

	groups = await aiohttp_auth.acl.get_user_groups(request)

	if groups:
		if role in groups:
			return web.Response(body='OK'.encode('utf-8'))

	raise web.HTTPNoContent()


async def create_subscriber(request):

	params = await request.json()
	print(params)

	user_id = await aiohttp_auth.auth.get_auth(request)
	print(user_id)

	user_obj = await objects.get(User, login=user_id)
	isp = await objects.get_related(user_obj, "isp")
	print(isp)

	subscriber_obj = await objects.create(Subscriber, name=params["name"], birthdate=params["birthdayDate"], phone=params["phone"], email=params["email"], passport=params["passport"], address=params["address"], isp_id=isp.id)

	# try:
	# 	subscriber_obj = objects.create(Subscriber, params)
	# 	return web.Response(body='OK'.encode('utf-8'))

	# except:
	# 	raise web.HTTPUnprocessableEntity()
	
	if subscriber_obj:
		return web.Response(body='OK'.encode('utf-8'))

	raise web.HTTPUnprocessableEntity()

	







# One time execution my_function:
# loop = asyncio.get_event_loop()
# loop.run_until_complete( my_function() )
# loop.close()


def setup_routes(app):

	app.router.add_post("/api/v1/login", login_view)
	app.router.add_post("/api/v1/check_role", check_role)
	app.router.add_post("/api/v1/subscribers/new", create_subscriber)

	app.router.add_static("/", "/var/wwws/billing.eth0.pro/html")


# Create a auth ticket mechanism that expires after 1 minute (60
# seconds), and has a randomly generated secret. Also includes the
# optional inclusion of the users IP address in the hash
# 1209600 sec - 2 week
# auth_policy = aiohttp_auth.auth.CookieTktAuthentication(urandom(32), 60, include_ip=True)
auth_policy = aiohttp_auth.auth.SessionTktAuthentication(urandom(32), 1209600, include_ip=True)

middlewares = [
aiohttp_session.session_middleware(EncryptedCookieStorage(urandom(32))),
aiohttp_auth.auth.auth_middleware(auth_policy),
aiohttp_auth.acl.acl_middleware(acl_group_callback),
]

app = web.Application(middlewares=middlewares)

# See context: https://github.com/gnarlychicken/aiohttp_auth
# It's a good convention to name roles with UPPER_CASE, so roles like ACCOUNTANT or ADMIN
# are easier to distinguish from permissions.
permissions = [
# (Permission.Allow, Group.Everyone, ('view',)),
# (Permission.Allow, Group.AuthenticatedUser, ('view', 'view_extra')),
(Permission.Allow, 'SUBSCRIBER',	('see_statistic')),
(Permission.Allow, 'KASSIR',		('see_statistic', 'create_subscriber')),
(Permission.Allow, 'ADMIN',			('see_statistic', 'create_subscriber', 'create_kassir', 'create_subscriber')),
(Permission.Allow, 'SUPER ADMIN',	('see_statistic', 'create_subscriber', 'create_kassir', 'create_subscriber', 'create_admin')),
]

# Прописывем роуты web-сервера:
setup_routes(app)

# Стартуем сервак!!
web.run_app(app, host=server_interface, port=server_port)
