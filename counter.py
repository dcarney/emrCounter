import ConfigParser
import datetime
import time
from dateutil.parser import parse

from bottle import route, run, get, post, static_file, request, response
import boto
import pytz
import simplejson

#Bottle().catchall = False

config = ConfigParser.ConfigParser()
config.read("config.ini")

AWS_ACCESS_KEY = config.get("AWS_KEYS", "AWS_ACCESS_KEY")
AWS_SECRET_KEY = config.get("AWS_KEYS", "AWS_SECRET_KEY")

def to_utc(local_datetime):
    return local_datetime.astimezone(pytz.timezone(pytz.utc.zone))
    
def date_to_ISO_string(fromDateObject):
	return fromDateObject.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

def date_to_index(start_date, date):
	if type(date) is not datetime.datetime:
		date = parse(date)
	if type(start_date) is not datetime.datetime:
		start_date = parse(start_date)
	
	delta = date - start_date
	return int(delta.days)

def retrieve_client_emr_history(start_date_utc, end_date_utc):
	try:
		end_date_clause = ''
		if end_date_utc is not None:
			end_date_clause = ' AND Date <= \'%s\'' % date_to_ISO_string(end_date_utc)
		else:
			local_tz = pytz.timezone('America/Los_Angeles')
			end_date_utc = datetime.datetime.now(local_tz)
		
		query = ('SELECT Date, EmrJobName, CounterValue FROM EmrStats WHERE CounterName = '
				'\'ICA_RECORDS_READ\' AND Date >= \'%s\' %s') % (date_to_ISO_string(start_date_utc), end_date_clause)
		
		# create global dict object that will hold all graph data
		data = dict()
		
		# establish SBD connection
		sdb_conn = boto.connect_sdb(AWS_ACCESS_KEY, AWS_SECRET_KEY)
		next_token = None
		total = 0
		while True:
			results = sdb_conn.select('EmrStats', query, next_token, False)
			
			for row in results:
				if row['EmrJobName'] is None or row['EmrJobName'] is '':
					continue
				client_name = row['EmrJobName'].split('_',3)[1]
				index = date_to_index(start_date_utc, row['Date'])
				
				# if we've already added some data for this client_name
				if client_name in data:
					
					# if current index in client's list already has some data, add to the existing 'y' value
					if data[client_name][index] is not None:
						data[client_name][index]['y'] += int(row['CounterValue'])
						
					else: # if current index in client's list has no data, create the dict!
						data[client_name][index] = dict({ 'x': index, 'y': int(row['CounterValue']) })
						
				else: # if we haven't added any data for this client_name yet
					# create a new list of dicts for client_name
					# frist create the list with enough spots to hold every day's history
					data[client_name] = [None] * (date_to_index(start_date_utc, end_date_utc)+1)
					
					# now create a dict for the specific day we're on
					# the rest will stay as None
					data[client_name][index] = dict({ 'x': index, 'y': int(row['CounterValue']) })
					
			next_token = results.next_token
			if next_token is None: break
		
		# now replace the data dict with an array, as required by d3
		arrayed_data = []
		for client in data:
			for i in range(0,len(data[client])):
				if data[client][i] is None:
					data[client][i] = { "x": i, "y": 0 }
			arrayed_data.append(data[client])
			
		return arrayed_data
		
	except Exception as ex:
		print "EXCEPTION: ", ex
		print sys.exc_info()

def retrieve_emr_totals(start_date_utc, end_date_utc):
	try:
		end_date_clause = ''
		if end_date_utc is not None:
		    end_date_clause = ' AND Date <= \'%s\'' % date_to_ISO_string(end_date_utc)
		    
		query = ('SELECT CounterValue FROM EmrStats WHERE CounterName = '
				 '\'ICA_RECORDS_READ\' AND Date >= \'%s\' %s') % (date_to_ISO_string(start_date_utc),
				                                                            end_date_clause)
		
		# establish SBD connection
		sdb_conn = boto.connect_sdb(AWS_ACCESS_KEY, AWS_SECRET_KEY)
		next_token = None
		total = 0
		while True:
		    results = sdb_conn.select('EmrStats', query, next_token, False)
		    total += sum(map(lambda i : int(i['CounterValue']), results))
		    next_token = results.next_token
		    if next_token is None: break
		
		return total
	except Exception as ex:
	    print "EXCEPTION: ", ex


@route('/css/:filename#.*\.css#')
def send_css(filename):
	return static_file(filename, root='./css/')

@route('/img/:filename#.*\.png#')
def send_image(filename):
    return static_file(filename, root='./img/', mimetype='image/png')

@route('/js/:filename#.*\.js#')
def send_js(filename):
    return static_file(filename, root='./js/')

@get('/')
def page():
	return static_file("index.html", root='./')

@get('/frequencies')
def frequencies():
    # FREQUENCY_IN_SECONDS = frequency with which the UI will check-in with the server
    # RATE_CATCHUP_WINDOW = client will calculate a rate, based on the difference
    #                       between the client/server counts, and this "window" 
	return simplejson.dumps({'FREQUENCY_IN_SECONDS': config.get("MISC", "FREQUENCY_IN_SECONDS"),
	                         'RATE_CATCHUP_WINDOW': config.get("MISC", "RATE_CATCHUP_WINDOW")})

@get('/previous')
def previous():
	local_tz = pytz.timezone('America/Los_Angeles')
	local_now = datetime.datetime.now(local_tz)
	local_midnight = local_tz.localize(datetime.datetime(local_now.year, 
	                                                     local_now.month, 
	                                                     local_now.day, 
	                                                     0, 0, 0))
	beginning = local_midnight + datetime.timedelta(days = -1)

	return str(retrieve_emr_totals(to_utc(beginning), to_utc(local_midnight)))
    	
@get('/current')
def rate():
	local_tz = pytz.timezone('America/Los_Angeles')
	local_now = datetime.datetime.now(local_tz)
	local_midnight = local_tz.localize(datetime.datetime(local_now.year,
	                                                       local_now.month,
	                                                       local_now.day,
	                                                       0, 0, 0))

	return str(retrieve_emr_totals(to_utc(local_midnight), None))

@get('/client_emr_history')
def client_history():
	response.content_type = 'application/json'
	
	days_param = int( request.GET.get('days', '5') )
	local_tz = pytz.timezone('America/Los_Angeles')
	local_now = datetime.datetime.now(local_tz)
	local_midnight = local_tz.localize(datetime.datetime(local_now.year,
	                                                       local_now.month,
	                                                       local_now.day,
	                                                       0, 0, 0))
	
	days_back = datetime.timedelta(days=-days_param)
	start_date = local_midnight + days_back
	history_data = retrieve_client_emr_history(start_date, None)
	
	return simplejson.dumps(history_data)
	
run(host='0.0.0.0', port=config.get("MISC", "LISTEN_ON_PORT"))