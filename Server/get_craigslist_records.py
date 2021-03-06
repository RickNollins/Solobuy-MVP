import sys, os, requests, json
from pymongo import MongoClient

def get_records(api_key):
	next_page = 1
	params = { 'auth_token' : api_key, 'status' : 'for_sale', 'lat' : 37.956002, 'long' : -91.774363, 'radius' : '100mi', 'category': 'SANT|SCOL|SJWL', 'has_image': 1, 
	'has_price': 1, 'rpp': 100, 'retvals': 'external_id,category,heading,location,body,timestamp,price,images' }
	
	anchor = None
	external_id_set = set()
	item_list = []
	while(next_page > 0):
		request_url = None
		if anchor is None:
			request_url = "http://search.3taps.com/?" + '&'.join("{!s}={!s}".format(key, val) for (key, val) in params.items())
		else:
			params.update({'anchor': anchor})
			request_url = "http://polling.3taps.com/poll?" + '&'.join("{!s}={!s}".format(key, val) for (key, val) in params.items())
			
		response = requests.get(request_url)
		
		content_decode = response.content.decode("utf-8")
		json_parse = json.loads(content_decode)

		for item in json_parse["postings"]:
			if(item["external_id"] not in external_id_set):
				geojson_obj = {
						'type': 'Point',
						'coordinates': [ float(item["location"]["long"]), float(item["location"]["lat"]) ]
					}
				external_id_set.add(item["external_id"])
				item_list.append({ 'name': item["heading"], 'price': item["price"], 'image_urls': item["images"], 'body': item["body"], 'loc': geojson_obj, 'timestamp': item["timestamp"]})
			
		next_page = json_parse['next_page']
		params = { 'auth_token' : api_key, 'status' : 'for_sale', 'lat' : 37.956002, 'long' : -91.774363, 'radius' : '100mi', 'category': 'SANT', 'has_image': 1, 
			'has_price': 1, 'rpp': 100, 'retvals': 'external_id,category,heading,location,body,timestamp,price,images', 'page': next_page}
	
	anchor = json_parse["anchor"]
	return item_list
	
def put_records_in_db(records, user, password):
	client = MongoClient("mongodb://{db_user}:{db_pass}@ds053300.mongolab.com:53300/solobuy".format(db_user=user, db_pass=password))
	db = client["solobuy"]

	item_collection = db.items
	for item in records:
		inserted_item = item_collection.insert(item)
		print("Inserted: %s" % inserted_item)
		
if __name__ == "__main__":
	global anchor
	anchor = None

	with open("./three_taps_conf") as conf:
		api_key = conf.readline().replace("\n", "")
		db_user = conf.readline().replace("\n", "")
		db_pass = conf.readline().replace("\n", "")
	
	records = get_records(api_key)
	put_records_in_db(records, db_user, db_pass)
	