
#
# https://github.com/coleifer/peewee
#
#
# For sync debug in shell: 
# objects.database.set_allow_sync(True)
#

import asyncio
import logging

import peewee
from peewee import *
# from playhouse.shortcuts import RetryOperationalError

import peewee_async
import peewee_asyncext

# http://docs.peewee-orm.com/en/latest/peewee/querying.html#implementing-many-to-many
from playhouse.fields import ManyToManyField




# def model_to_dict(model):

# 	import json

# 	res = {}

# 	for key in model.keys():

# 		try:
# 			res[key] = str( getattr(model, key) )

# 		except:
# 			res[key] = json.dumps( getattr(model, key) )

# 	return res


	

# https://github.com/05bit/peewee-async/issues/15
class ExtManager(peewee_async.Manager):
	async def get_related(self, instance, related_name, single_backref=False):
		"""
		return related instance for foreign key relationship
		return query for backref or return related instance if single_backref is True
		"""
		model_cls = type(instance)
		related_field = getattr(model_cls, related_name)

		if isinstance(related_field, peewee.ReverseRelationDescriptor):
			return await self._get_backrefs(instance, related_name, single_backref)
		else:
			return await self._get_foreign_key_target(instance, related_name)

	async def _get_foreign_key_target(self, instance, field_name):
		foreign_key_value = getattr(instance, field_name + "_id")

		model_cls = type(instance)
		foreign_key_field = getattr(model_cls, field_name)
		target_cls = foreign_key_field.rel_model
		target_field = foreign_key_field.to_field

		return await self.get(target_cls, target_field == foreign_key_value)

	async def _get_backrefs(self, instance, related_name, single_backref=False):
		query = getattr(instance, related_name)
		instances = await self.execute(query)

		if single_backref:
			for instance in instances:
				return instance
			raise query.model_class.DoesNotExist
		else:
			return instances

# custom loop!
# once objects is created with specified loop, all database connections automatically will be set up on that loop.
loop_db = asyncio.new_event_loop()


# class PostgresqlReconnectDb(RetryOperationalError, PostgresqlExtDatabase):
# 	pass

# db = PostgresqlDatabase("run-billing", user="run-billing", password="morpass", host="billing.eth0.pro")
# db = PostgresqlExtDatabase("run-billing", user="run-billing", password="morpass", host="billing.eth0.pro")
# db = PooledPostgresqlExtDatabase("run-billing", user="run-billing", password="morpass", host="billing.eth0.pro",max_connections=8,stale_timeout=300)
# db = PostgresqlReconnectDb("run-billing", user="run-billing", password="morpass", host="billing.eth0.pro", register_hstore=False)
db = peewee_asyncext.PostgresqlExtDatabase("run-billing", user="run-billing", password="morpass", host="billing.eth0.pro", register_hstore=False)


# Create async models manager:
# Sometimes, it’s so easy to forget to pass custom loop instance, but now it’s not a problem! Just initialize with an event loop once.
# objects = peewee_async.Manager(db, loop=loop)
# objects = peewee_async.Manager(db)
objects = ExtManager(db)
# objects = ExtManager(db, loop=loop_db)

# No need for sync anymore!
# v1 - ?
# database.set_allow_sync(False)

# this will raise AssertionError on ANY sync call
# v2 - ?
# -- For sync debug in shell: objects.database.set_allow_sync(True)
# objects.database.allow_sync = False

# TODO: Return to FALSE, check for blocking loop!!!!!
# objects.database.allow_sync = True

# alternatevely we can set ERROR or WARNING loggin level to db.allow_sync:
objects.database.allow_sync = logging.ERROR



class BaseModel(Model):
	class Meta:
		database = db


class Contract(BaseModel):
	name = CharField()
	birthdate = DateTimeField()
	address = CharField()
	passport = CharField()
	phone = CharField()
	email = CharField()
	contractor = ForeignKeyField("self")
	date = DateField()



class User(BaseModel):
	login = CharField(unique=True)
	password = CharField()
	active = BooleanField()
	# group = ForeignKeyField(Group)
	contract = ForeignKeyField(Contract)

class Group(BaseModel):
	name = CharField(unique=True)
	users = ManyToManyField(User, related_name="groups")


UserGroup = Group.users.get_through_model()


# class UserGroup(BaseModel):
# 	"""
# 	http://docs.peewee-orm.com/en/latest/peewee/querying.html#implementing-many-to-many
# 	"""
# 	user = ForeignKeyField(User)
# 	group = ForeignKeyField(Group)
