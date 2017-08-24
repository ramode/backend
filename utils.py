
def return_as_json(handler):
	"""
	Это декоратор, который приводит вывод функции в HTTP JSON ответ.
	"""
	from aiohttp import web
	import datetime

	async def middleware_handler(request):
		
		res = await handler(request)

		if type(res) == web.Response:
			return res

		def date_to_isoformat(item):
			print(item)
			for key in item.keys():
				# val = getattr(item, key)
				val = item[key]
				if isinstance(val, datetime.date):
					item[key] = val.isoformat()

		# проверяем, не массив ли это:
		if isinstance(res, list):

			for item in res:
				date_to_isoformat(item)

		else:
			date_to_isoformat(res)

		return web.json_response(res)

	return middleware_handler