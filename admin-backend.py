#!/opt/env/run-billing-admin-backend/bin/python3.6
#
# Ramode 2017
#

# import ipdb; ipdb.set_trace()

server_interface = "0.0.0.0"
server_port = 8031


# https://docs.python.org/2/howto/logging.html
# https://stackoverflow.com/questions/10973362/python-logging-function-name-file-name-line-number-using-a-single-file
import logging
logger = logging.getLogger('root')
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)


import json
from os import urandom


import asyncio
from aiohttp import web

# https://github.com/gnarlychicken/aiohttp_auth
# import aiohttp_auth
# import aiohttp_session 
# from aiohttp_session.cookie_storage import EncryptedCookieStorage
# from os import urandom
# from aiohttp_auth.permissions import Group, Permission


# NEW: https://github.com/ilex/aiohttp_auth_autz
import aiohttp_auth
from aiohttp_auth import auth, autz
from aiohttp_auth.auth import auth_required
from aiohttp_auth.autz import autz_required
from aiohttp_auth.autz.policy import acl
from aiohttp_auth.permissions import Permission, Group


# DB defination:
from models import *
from utils import return_as_json



# See context: https://github.com/gnarlychicken/aiohttp_auth
# It's a good convention to name roles with UPPER_CASE, so roles like ACCOUNTANT or ADMIN
# are easier to distinguish from permissions.
context = [
# (Permission.Allow, Group.Everyone, ('view',)),
# (Permission.Allow, Group.AuthenticatedUser, ('view', 'view_extra')),
(Permission.Allow, 'SUBSCRIBER',	{"view", }),
(Permission.Allow, 'STAFF',			{"view", "edit", "admin_view", }),
(Permission.Allow, 'ADMIN',			{"admin", }),
(Permission.Allow, 'SUPER ADMIN',	{"super_admin", }),
# Why get I err?..
# AttributeError: type object 'Group' has no attribute 'Everyone'
# (Permission.Allow, Group.Everyone,	{"public"}),
]


async def get_user_obj(login, password=None):

	try:
		# Вываливает трейсбек, если запись не найдена

		if password:
			user_obj = await objects.get(User, login=login, password=password)

		else:
			user_obj = await objects.get(User, login=login)

	except Exception as e:
		logging.error(e)
		user_obj = None

	return user_obj


async def get_user_groups(login):
	
	user_obj = await get_user_obj(login)

	def sync_get_user_groups(user_obj):
		return user_obj.groups

	if user_obj:

		# This is Peewee sync request by default. Use run_in_executor()
		# CHECK output for blocking loop!!!!!!!!!!!!1 See objects.database.allow_sync = True
		# groups = user_obj.groups
		group_objs = await app.loop.run_in_executor(None, lambda: user_obj.groups)

		# import ipdb; ipdb.set_trace()

		groups = []
		for group in group_objs:
			groups.append(group.name)

		return groups
			
	raise Exception()


# create an ACL authorization policy class
class ACLAutzPolicy(acl.AbstractACLAutzPolicy):
	"""The concrete ACL authorization policy."""

	def __init__(self, db, context=None):
		# do not forget to call parent __init__
		super().__init__(context)

		self.db = db

	async def acl_groups(self, user_identity):
		"""Return acl groups for given user identity.

		This method should return a sequence of groups for given user_identity.
		
		Args:
			user_identity: User identity returned by auth.get_auth.
			
		Returns:
			Sequence of acl groups for the user identity.
		"""
        
		# implement application specific logic here
		# user = self.db.get(user_identity, None)

		user_obj = await get_user_obj(user_identity)
		
		if user_obj:

			groups = await get_user_groups(user_identity)
			return groups


		# import ipdb; ipdb.set_trace()

		# return empty tuple in order to give a chance
		# to Group.Everyone
		return tuple()


		

		
		

@return_as_json
async def login_view(request):
	params = await request.json()
	login = params.get("username", None)
	password = params.get("password", None)

	user_obj = get_user_obj(login, password)

	if user_obj:
		await aiohttp_auth.auth.remember(request, login)
		# return web.Response(body='OK'.encode('utf-8'))

		res = {}

		res["roles"] = []
		roles = await get_user_groups(login)
		for item in roles:
			# Выкидываем втсроенные роли:
			if type(item) is str:
				res["roles"].append(item)

		# import ipdb; ipdb.set_trace()
		return res

	raise web.HTTPUnauthorized()


# only authenticated users can logout
# if user is not authenticated auth_required decorator
# will raise a web.HTTPUnauthorized
@auth_required
async def logout(request):

	# forget user identity
	await aiohttp_auth.auth.forget(request)
	
	# return web.Response(text='Ok')
	return web.Response(body='OK'.encode('utf-8'))




# async def check_role(request):

# 	params = await request.json()
# 	role = params.get("role")

# 	# None
# 	# or
# 	# {'SUPER ADMIN', <Group.Everyone: 'aiohttp_auth.acl.group.Everyone'>, 'morfair', <Group.AuthenticatedUser: 'aiohttp_auth.acl.group.AuthenticatedUser'>}
# 	groups = await aiohttp_auth.acl.get_user_groups(request)

# 	if groups:
# 		if role in groups:
# 			return web.Response(body='OK'.encode('utf-8'))

# 	raise web.HTTPNoContent()


# @aiohttp_auth.auth.auth_required
# @return_as_json
# async def get_my_role(request):
# 	groups = await aiohttp_auth.acl.get_user_groups(request)

# 	if groups:
# 		return groups.pop()

# 	raise web.HTTPNoContent()



@aiohttp_auth.acl.acl_required("create_contract", context)
async def create_contract(request):

	params = await request.json()
	user_id = await aiohttp_auth.auth.get_auth(request)
	user_obj = await objects.get(User, login=user_id)
	
	contract_obj = await objects.create(Contract, 
		name=params["name"],
		birthdate=params["birthdayDate"],
		address=params["address"],
		passport=params["passport"],
		phone=params["phone"],
		email=params["email"]
	)
		
	if contract_obj:
		return web.Response(body='OK'.encode('utf-8'))

	raise web.HTTPUnprocessableEntity()

	
@autz_required("admin_view")
@return_as_json
async def get_contracts(request):

	contract_objs = await objects.execute(Contract.select())
	
	res = []
	for obj in contract_objs:
		# res.append(model_to_dict(obj))
		res.append(obj.__dict__["_data"])

	# return web.json_response(res)
	return res






# One time execution my_function:
# loop = asyncio.get_event_loop()
# loop.run_until_complete( my_function() )
# loop.close()


def setup_routes(app):

	app.router.add_post("/api/v1/login", login_view)
	# app.router.add_post("/api/v1/check_role", check_role)
	# app.router.add_get("/api/v1/my_role", get_my_role)
	
	app.router.add_post("/api/v1/contracts/new", create_contract)
	app.router.add_get("/api/v1/contracts/list", get_contracts)

	app.router.add_static("/", "/var/wwws/billing.eth0.pro/html")


def init_app(loop):

	app = web.Application()

	# IT IS OLD LIB!!!!
	# Create a auth ticket mechanism that expires after 1 minute (60
	# seconds), and has a randomly generated secret. Also includes the
	# optional inclusion of the users IP address in the hash
	# 1209600 sec - 2 week
	# auth_policy = aiohttp_auth.auth.CookieTktAuthentication(urandom(32), 60, include_ip=True)
	#auth_policy = aiohttp_auth.auth.SessionTktAuthentication(urandom(32), 1209600, include_ip=True)

	# Create an auth ticket mechanism that expires after 1 minute (60
	# seconds), and has a randomly generated secret. Also includes the
	# optional inclusion of the users IP address in the hash
	auth_policy = auth.CookieTktAuthentication(urandom(32), 60,include_ip=True)

	# Create an ACL authorization policy
	db = None
	autz_policy = ACLAutzPolicy(db, context)

	# setup middlewares in aiohttp fashion
	aiohttp_auth.setup(app, auth_policy, autz_policy)

	# Прописывем роуты web-сервера:
	setup_routes(app)

	return app



loop = asyncio.get_event_loop()
app = init_app(loop)


# Стартуем сервак!!
web.run_app(app, host=server_interface, port=server_port, loop=loop)
