#!/usr/bin/python

""" 
  A generic SPARQL processor and sharing tool. Like http://pastebin.com for SPARQL queries.

@author: Michael Hausenblas, http://sw-app.org/mic.xhtml#i
@since: 2012-08-04
@status: init
"""
import sys
import logging
import getopt
import StringIO
import urlparse
import urllib
import urllib
import string
import cgi
import time
import datetime
import json
from SPARQLWrapper import SPARQLWrapper, JSON
from BaseHTTPServer import BaseHTTPRequestHandler
from os import curdir, sep
from couchdbkit import Server, Database, Document, StringProperty, DateTimeProperty
from restkit import BasicAuth

# Configuration
DEBUG = False
SERVICE_PORT = 6969

if DEBUG:
	FORMAT = '%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]'
	logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%Y-%m-%dT%I:%M:%S')
else:
	FORMAT = '%(asctime)-0s %(message)s'
	logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt='%Y-%m-%dT%I:%M:%S')


# for delegating SPARQL queries
class SPARQLEndpoint(object):
	
	# init with endpoint URL
	def __init__(self, endpoint):
		self.sparql = SPARQLWrapper(endpoint)
		self.sparql.setReturnFormat(JSON)
	
	# delegate SPARQL query to endpoint
	def query(self, q):
		self.sparql.setQuery(q)
		return self.sparql.query().convert()
	
	

# the main SPARQLBin service
class SPARQLBinServer(BaseHTTPRequestHandler):
	
	# reacts to GET request by serving static content in standalone mode and
	# handles API calls to retrieve a SPARQL paste entry
	def do_GET(self):
		parsed_path = urlparse.urlparse(self.path)
		target_url = parsed_path.path[1:]
		
		# API calls
		if self.path.startswith('/q/'): self.serve_paste(self.path.split('/')[-1])

		# static stuff
		if self.path == '/': self.serve_content('index.html')
		if self.path.endswith('.html'): self.serve_content(target_url, media_type='text/html')
		if self.path.endswith('.js'): self.serve_content(target_url, media_type='application/javascript')
		if self.path.endswith('.css'): self.serve_content(target_url, media_type='text/css')
		return
	
	# serves a paste entry using the backend
	def serve_paste(self, entryid):
		try:
			backend = SPARQLBinBackend(serverURL = 'http://127.0.0.1:5984/' , dbname = 'sparqlbin', username = 'admin', pwd = 'admin')
			(entry_found, entry) = backend.find(entryid)
			
			if entry_found:
				self.send_response(200)
				self.send_header('Content-type', 'application/json')
				self.end_headers()
				self.wfile.write(json.dumps(entry))
			else:
				self.send_error(404,'Entry with ID %s not found.' %entryid)
			return
		except IOError:
			self.send_error(404,'Entry with ID %s not found.' %entryid)
	
	# handles API calls to execute query and create permalink
	def do_POST(self):
		ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
		parsed_path = urlparse.urlparse(self.path)
		target_url = parsed_path.path[1:]
		
		# deal with paramter encoding first
		if ctype == 'multipart/form-data':
			postvars = cgi.parse_multipart(self.rfile, pdict)
			logging.debug('POST to %s with multipart/form-data: %s' %(self.path, postvars))
		elif ctype == 'application/x-www-form-urlencoded':
			length = int(self.headers.getheader('content-length'))
			postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
			logging.debug('POST to %s with application/x-www-form-urlencoded: %s' %(self.path, postvars))
		else:
			postvars = {}
		
		# API calls
		if postvars and target_url == 'execute':
			endpoint = urllib.unquote_plus(postvars['endpoint'][0])
			querystr = postvars['query'][0]
			self.executeQuery(endpoint, querystr)
		elif postvars and target_url == 'share':
			endpoint = urllib.unquote_plus(postvars['endpoint'][0])
			querystr = postvars['query'][0]
			backend = SPARQLBinBackend(serverURL = 'http://127.0.0.1:5984/' , dbname = 'sparqlbin', username = 'admin', pwd = 'admin')
			entryid = backend.add({'querystr' : querystr, 'endpoint' : endpoint })
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			self.wfile.write(json.dumps({ 'entryid' : entryid }))
		else:
			self.send_error(404,'File Not Found: %s' % target_url)
		return
	
	# executes the SPARQL query remotely and returns JSON results
	def executeQuery(self, endpoint, querystr):
		logging.debug('Query to endpoint %s with query\n%s' %(endpoint, querystr))
		try:
			ep = SPARQLEndpoint(endpoint)
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			self.wfile.write(json.dumps(ep.query(querystr)))
		except:
			self.send_error(500, 'Something went wrong here on the server side.')
	
	# changes the default behavour of logging everything - only in DEBUG mode
	def log_message(self, format, *args):
		if DEBUG:
			try:
				BaseHTTPRequestHandler.log_message(self, format, *args)
			except IOError:
				pass
		else:
			return
	
	# serves static content from file system
	def serve_content(self, p, media_type='text/html'):
		try:
			f = open(curdir + sep + p)
			self.send_response(200)
			self.send_header('Content-type', media_type)
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
			return
		except IOError:
			self.send_error(404,'File Not Found: %s' % self.path)
	
	# serves remote content via forwarding the request
	def serve_URL(self, turl, q):
		logging.debug('REMOTE GET %s' %turl)
		self.send_response(200)
		self.send_header('Content-type', 'application/json')
		self.end_headers()
		data = urllib.urlopen(turl + '?' + q)
		self.wfile.write(data.read())
	

# a single entry (JSON document) in the backend
class PasteEntry(Document):
	endpoint = StringProperty()
	querystr = StringProperty()
	timestamp = DateTimeProperty()
	

# represents the backend, permanent storage of the queries using Apache CouchDB
class SPARQLBinBackend(object):
	
	# init with URL of CouchDB server and database name and credentials
	def __init__(self, serverURL, dbname, username, pwd):
		self.serverURL = serverURL
		self.dbname = dbname
		self.username = username
		self.pwd = pwd
		self.server = Server(self.serverURL, filters=[BasicAuth(self.username, self.pwd)])
	
	# adds a document to the database
	def add(self, entry):
		try:
			db = self.server.get_or_create_db(self.dbname)
			PasteEntry.set_db(db)
			doc = PasteEntry(endpoint = entry['endpoint'], querystr = entry['querystr'], timestamp = datetime.datetime.utcnow())
			doc.save()
			logging.debug('Adding entry with ID %s' %doc['_id'])
			return doc['_id']
		except Exception as err:
			logging.error('Error while adding entry: %s' %err)
			return None
	
	# finds a document via its ID in the database
	def find(self, eid):
		try:
			db = self.server.get_or_create_db(self.dbname)
			if db.doc_exist(eid):
				ret = db.get(eid)
				# don't expose details, clean up
				ret.pop('doc_type')
				ret.pop('_rev')
				ret.pop('_id')
				return (True, ret)
			else:
				return (False, None)
		except Exception as err:
			logging.error('Error while looking up entry: %s' %err)
			return (False, None)
	

if __name__ == '__main__':
	from BaseHTTPServer import HTTPServer
	server = HTTPServer(('localhost', SERVICE_PORT), SPARQLBinServer)
	logging.info('SPARQLBinServer started on port %s, use {Ctrl+C} to shut-down ...' %SERVICE_PORT)
	server.serve_forever()