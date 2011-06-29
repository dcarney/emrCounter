from bottle import route, run, get, post, static_file
import boto

import datetime
import time
import pytz

#Bottle().catchall = False

def dateToISOString(fromDateObject):
	return fromDateObject.strftime("%Y-%m-%dT%H:%M:%S")
	
FREQUENCY_IN_SECONDS = 30
@get('/frequency')
def frequency():
	return str(FREQUENCY_IN_SECONDS)
	
@route('/css/:filename#.*\.css#')
def send_css(filename):
	return static_file(filename, root='./css/')
	
@route('/img/:filename#.*\.png#')
def send_image(filename):
    return static_file(filename, root='./img/', mimetype='image/png')

@route('/js/:filename#.*\.js#')
def send_js(filename):
    return static_file(filename, root='./js/')
	
@get('/page')
def page():
	return static_file("index.html", root='./')
	
@get('/rate/:current_amount')
def rate(current_amount = 0):
	try:
		pacific_tz = pytz.timezone('America/Los_Angeles')
		pacific_now = datetime.datetime.now(pacific_tz)
		pacific_midnight = pacific_tz.localize(datetime.datetime(pacific_now.year, pacific_now.month, pacific_now.day, 0, 0, 0))

		utc_begin = pacific_midnight.astimezone(pytz.timezone(pytz.utc.zone))
		#utc_now = datetime.datetime.utcnow()

		print "utc equiv: ", dateToISOString(utc_begin)
			
		sdb_conn = boto.connect_sdb('<aws_access_key>', '<aws_secret_key>')
		query = 'SELECT CounterValue FROM EmrStats WHERE CounterName = \'ICA_RECORDS_READ\' AND Date >= \'%s\' LIMIT 10' % dateToISOString(utc_begin)
		
		print query
		next_token = None
		total = 0
	
		while True:
			results = sdb_conn.select('EmrStats', query, next_token, False)
			total += sum(map(lambda i : int(i['CounterValue']), results))
			next_token = results.next_token
			if next_token is None: break
		
		# Determine the rate that the client needs to count (per second) to reach the calculated
		# total in 1 hour (3600 seconds)
		new_rate = (total - int(current_amount)) / FREQUENCY_IN_SECONDS
		print "Total:", total, "Current amount:", current_amount, "New rate:", new_rate	
		return str(new_rate);
		
	except Exception as ex:
		print "EXCEPTION: ", ex
	
run(host='localhost', port=8080)