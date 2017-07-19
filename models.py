
#
# https://github.com/coleifer/peewee
#

import asyncio
import logging

from peewee import *
# from playhouse.shortcuts import RetryOperationalError

import peewee_async
import peewee_asyncext


# custom loop!
# once objects is created with specified loop, all database connections automatically will be set up on that loop.
loop = asyncio.new_event_loop() 


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
objects = peewee_async.Manager(db)

# No need for sync anymore!
# v1 - ?
# database.set_allow_sync(False)

# this will raise AssertionError on ANY sync call
# v2 - ?
objects.database.allow_sync = False

# alternatevely we can set ERROR or WARNING loggin level to db.allow_sync:
# objects.database.allow_sync = logging.ERROR



class BaseModel(Model):
	class Meta:
		database = db


class User(BaseModel):
	name = CharField()
	password = CharField()
	register_date = DateField()
	active = BooleanField()


# class Group(Model):
# 	
