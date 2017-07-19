#!/opt/env/run-billing-admin-backend/bin/python3.6
#
# Ramode 2017
#


# https://docs.python.org/2/howto/logging.html
import logging
logging.basicConfig(level=logging.DEBUG)

import asyncio
from aiohttp import web

