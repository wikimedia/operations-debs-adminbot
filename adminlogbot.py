#!/usr/bin/python
import irclib
import time
import adminlog
import sys
import re
import json
import urllib
sys.path.append('/etc/adminbot')
import config

if config.enable_projects:
	import os
	import ldap
	sys.path.append('/usr/local/lib/user-management')
	import ldapsupportlib

def on_connect(con, event):
	con.privmsg(config.nickserv,"identify " + config.nick + " " + config.nick_password)
	time.sleep(1)
	for target in config.targets:
		con.join(target)
	if con.get_nickname() != config.nick:
		con.privmsg('nickserv', 'ghost %s %s' % (config.nick, config.nick_password))

def on_quit(con, event):
	source = irclib.nm_to_n(event.source())
	if source == config.nick:
		con.nick(config.nick)

def switch_nick(con, event):
	con.nick(con.get_nickname() + "_")
	con.privmsg('nickserv', 'ghost %s %s' % (config.nick, config.nick_password))

def get_cloak(source):
	if re.search("/", source) and re.search("@", source): return source.split("@")[1]

def ask_encode(query):
	matches = {'[': '-5B', ']': '-5D', ' ': '-20', '|': '/', '=': '%3D', '?': '-3F', '\n': '%0A', '\r': '%0D'}
	for match,replace in matches.iteritems():
		query = query.replace(match, replace)
	return query

def get_query(query):
	if not query:
		return {}
	query = ask_encode(query)
	url = config.wiki_connection[0] + '://' + config.wiki_connection[1] + config.wiki_query_path + query
	return get_json_from_url(url)

def get_json_from_url(url):
	if not url:
		return {} 
	f = urllib.urlopen(url)
	results = f.read()
	return json.loads(results)

def find_user(author, cloak, user_json):
	for result in user_json['items']:
		username = result["label"]
		usernick = result["irc_nick"][0]
		usercloak = result["irc_cloak"][0]
		if author == usernick or cloak == usercloak:
			return username
	return ''

def is_stale(cache_filename):
	if (os.path.exists(cache_filename)):
		stat = os.stat(cache_filename)
		now = time.time()
		mtime = stat.st_mtime
		if mtime > now - 300:
			return False
		else:
			return True
	else:
		return True

def on_msg(con, event):
	if event.target() not in config.targets: return
	author,rest = event.source().split('!')
	cloak = get_cloak(event.source())
	if author in config.author_map:
		author = config.author_map[author]
	line = event.arguments()[0]
	if line.startswith("!log "):
		if config.check_users:
			cache_filename = '/var/lib/adminbot/user_json.cache'
			cache_stale = is_stale(cache_filename)
			if cache_stale:
				user_json = ''
				user_json_cache_file = open(cache_filename,'w+')
				if config.user_query:
					user_json = get_query(config.user_query)
				elif config.user_url:
					user_json = get_json_from_url(config.user_url)
				user_json_cache_file.write(json.dumps(user_json))
			else:
				user_json_cache_file = open(cache_filename,'r')
				user_json = user_json_cache_file.read()
				if user_json:
					user_json = json.loads(user_json)
				user_json_cache_file.close()
			username = find_user(author, cloak, user_json)
			if username:
				author = "[[" + username + "]]"
			else:
				if config.required_users_mode == "warn":
					server.privmsg(event.target(),"Not a trusted nick or cloak. This is just a warning, for now. Please add your nick or cloak added to the trust list or your user page.")
				if config.required_users_mode == "error":
					server.privmsg(event.target(),"Not a trusted nick or cloak. Not logging. Please add your nick or cloak added to the trust list or your user page.")
					return
		if config.enable_projects:
			arr = line.split(" ",2)
			if len(arr) < 2:
				server.privmsg(event.target(),"Project not found, O.o. Try !log <project> <message> next time.")
				return
			if len(arr) < 3:
				server.privmsg(event.target(),"Message missing. Nothing logged.")
				return
			undef = arr[0]
			project = arr[1]
			cache_filename = '/var/lib/adminbot/project.cache'
			cache_stale = is_stale(cache_filename)
			if not cache_stale:
				project_cache_file = open(cache_filename,'r')
				project_cache = project_cache_file.read()
				project_cache_file.close()
				projects = project_cache.split(',')
			if cache_stale:
				project_cache_file = open(cache_filename,'w+')
				ldapSupportLib = ldapsupportlib.LDAPSupportLib()
				base = ldapSupportLib.getBase()
				ds = ldapSupportLib.connect()
				try:
					projects = []
					projectdata = ds.search_s(config.project_rdn + "," + base,ldap.SCOPE_SUBTREE,"(objectclass=groupofnames)")
					if not projectdata:
						server.privmsg(event.target(),"Can't contact LDAP for project list.")
					for obj in projectdata:
						projects.append(obj[1]["cn"][0])
					project_cache_file.write(','.join(projects))
				except Exception:
					server.privmsg(event.target(),"Error reading project list from LDAP.")
			if project not in projects:
				server.privmsg(event.target(),project + " is not a valid project.")
				return
			message = arr[2]
		else:
			arr = line.split(" ",1)
			if len(arr) < 2:
				server.privmsg(event.target(),"Message missing. Nothing logged.")
				return
			undef = arr[0]
			project = ""
			message = arr[1]
		try: 
			adminlog.log(message,project,author)
			if author in config.title_map: title = config.title_map[author]
			else: title = "Master"
			server.privmsg(event.target(),"Logged the message, %s" % title)
		except: print sys.exc_info()
		

irc = irclib.IRC()
server = irc.server()
server.connect(config.network,config.port,config.nick)
server.add_global_handler("welcome", on_connect)
server.add_global_handler("pubmsg",on_msg)
server.add_global_handler("nicknameinuse",switch_nick)
server.add_global_handler("nickcollision",switch_nick)
server.add_global_handler("unavailresource",switch_nick)
server.add_global_handler("part",on_quit)
server.add_global_handler("kick",on_quit)
server.add_global_handler("disconnect",on_quit)
server.add_global_handler("quit",on_quit)

irc.process_forever()

