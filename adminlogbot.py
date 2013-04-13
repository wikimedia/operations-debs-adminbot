#!/usr/bin/python
import adminlog
import argparse
import imp
import irclib
import json
import logging
import os
import re
from socket import gethostname
import sys
import time
import urllib

import traceback

class logbot():

	def __init__(self, name, conf):
		self.name = name
		self.config = conf
		self.irc = irclib.IRC()

	def on_connect(self, con, event):
		try:
			con.privmsg(self.config.nickserv,
					"identify " + self.config.nick + " " + self.config.nick_password)
		except irclib.ServerNotConnectedError, e:
			logging.debug("Error identifying user")
		logging.debug("'%s' registering with nick '%s'." %
				(self.name, self.config.nick))
		time.sleep(1)
		for target in self.config.targets:
			logging.debug("'%s' joining '%s'." % (self.name, target))
			con.join(target)
		if con.get_nickname() != self.config.nick:
			try:
				con.privmsg('nickserv', 'ghost %s %s' %
						(self.config.nick, self.config.nick_password))
			except irclib.ServerNotConnectedError, e:
				logging.debug("Error ghosting user")

	def on_quit(self, con, event):
		source = irclib.nm_to_n(event.source())
		if source == self.config.nick:
			con.nick(self.config.nick)

	def switch_nick(self, con, event):
		con.nick(con.get_nickname() + "_")
		logging.debug("'%s' switching nick." % self.name)
		try:
			con.privmsg('nickserv', 'ghost %s %s' %
					(self.config.nick, self.config.nick_password))
		except irclib.ServerNotConnectedError, e:
			logging.debug("Error ghosting user")

	def get_cloak(self, source):
		if re.search("/", source) and re.search("@", source):
			return source.split("@")[1]

	def ask_encode(self, query):
		matches = {'[': '-5B', ']': '-5D',
				' ': '-20', '|': '/',
				'=': '%3D', '?': '-3F',
				'\n': '%0A', '\r': '%0D'}
		for match, replace in matches.iteritems():
			query = query.replace(match, replace)
		return query

	def get_query(self, query):
		if not query:
			return {}
		query = self.ask_encode(query)
		url = "%s://%s%s%s", (self.config.wiki_connection[0],
				self.config.wiki_connection[1],
				self.config.wiki_query_path, query)
		return self.get_json_from_url(url)

	def get_json_from_url(self, url):
		if not url:
			return {}
		f = urllib.urlopen(url)
		results = f.read()
		return json.loads(results)

	def find_user(self, author, cloak, user_json):
		for result in user_json['items']:
			username = result["label"]
			usernick = result["irc_nick"][0]
			usercloak = result["irc_cloak"][0]
			if author == usernick or cloak == usercloak:
				return username
		return ''

	def is_stale(self, cache_filename):
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

	def on_msg(self, con, event):
		if event.target() not in self.config.targets:
			return
		author, rest = event.source().split('!')
		cloak = self.get_cloak(event.source())
		if author in self.config.author_map:
			author = self.config.author_map[author]
		line = event.arguments()[0].decode("utf8")

		if (line.startswith(self.config.nick) or
				line.startswith("!%s" % self.config.nick) or
				line.lower() == "!log help"):
			logging.debug("'%s' got '%s'; displaying help message." % (self.name, line))
			try:
				self.server.privmsg(event.target(),
						"I am a logbot running on %s." % gethostname())
				self.server.privmsg(event.target(),
						"Messages are logged to %s." % self.config.log_url)
				self.server.privmsg(event.target(),
						"To log a message, type !log <msg>.")
			except Exception:
				try:
					self.server.privmsg(event.target(),
							"To log a message, type !log <msg>.")
				except irclib.ServerNotConnectedError, e:
					logging.debug("Server connection error when sending message")
		elif line.lower().startswith("!log "):
			logging.debug("'%s' got '%s'; Attempting to log." % (self.name, line))
			if self.config.check_users:
				try:
					cache_filename = '%s/%s-users_json.cache' % (self.config.cachedir, self.name)
				except AttributeError:
					cache_filename = '/var/lib/adminbot/%s-users_json.cache' % self.name

				cache_stale = self.is_stale(cache_filename)
				if cache_stale:
					user_json = ''
					user_json_cache_file = open(cache_filename, 'w+')
					if self.config.user_query:
						user_json = self.get_query(self.config.user_query)
					elif self.config.user_url:
						user_json = self.get_json_from_url(self.config.user_url)
					user_json_cache_file.write(json.dumps(user_json))
				else:
					user_json_cache_file = open(cache_filename, 'r')
					user_json = user_json_cache_file.read()
					if user_json:
						user_json = json.loads(user_json)
					user_json_cache_file.close()
				username = self.find_user(author, cloak, user_json)
				if username:
					author = "[[" + username + "]]"
				else:
					try:
						if self.config.required_users_mode == "warn":
							self.server.privmsg(event.target(),
							"Not a trusted nick or cloak. This is just a warning, for now."
							" Please add your nick or cloak added"
							" to the trust list or your user page.")
						if self.config.required_users_mode == "error":
							self.server.privmsg(event.target(),
							"Not a trusted nick or cloak. Not logging."
							" Please add your nick or cloak added"
							" to the trust list or your user page.")
							return
					except irclib.ServerNotConnectedError, e:
						logging.debug("Server connection error when sending message")
			if self.config.enable_projects:
				arr = line.split(" ", 2)
				try:
					if len(arr) < 2:
						self.server.privmsg(event.target(),
								"Project not found, O.o. Try !log <project> <message> next time.")
						return
					if len(arr) < 3:
						self.server.privmsg(event.target(),
								"Message missing. Nothing logged.")
						return
				except irclib.ServerNotConnectedError, e:
					logging.debug("Server connection error when sending message")
				project = arr[1]
				try:
					cache_filename = '%s/%s-users_json.cache' % (self.config.cachedir, self.name)
				except AttributeError:
					cache_filename = '/var/lib/adminbot/%s-project.cache' % self.name
				cache_stale = self.is_stale(cache_filename)
				if not cache_stale:
					project_cache_file = open(cache_filename,
							'r')
					project_cache = project_cache_file.read()
					project_cache_file.close()
					projects = project_cache.split(',')
				if cache_stale:
					project_cache_file = open(cache_filename, 'w+')
					ldapSupportLib = ldapsupportlib.LDAPSupportLib()
					base = ldapSupportLib.getBase()
					ds = ldapSupportLib.connect()
					try:
						projects = []
						projectdata = ds.search_s(self.config.project_rdn + "," + base,
								ldap.SCOPE_SUBTREE, "(objectclass=groupofnames)")
						if not projectdata:
							self.server.privmsg(event.target(),
									"Can't contact LDAP for project list.")
						for obj in projectdata:
							projects.append(obj[1]["cn"][0])
						project_cache_file.write(','.join(projects))
					except Exception:
						try:
							self.server.privmsg(event.target(),
									"Error reading project list from LDAP.")
						except irclib.ServerNotConnectedError, e:
							logging.debug("Server connection error when sending message")
				if project not in projects:
					try:
						self.server.privmsg(event.target(),
								project + " is not a valid project.")
					except irclib.ServerNotConnectedError, e:
						logging.debug("Server connection error when sending message")
					return
				message = arr[2]
			else:
				arr = line.split(" ", 1)
				if len(arr) < 2:
					try:
						self.server.privmsg(event.target(), "Message missing. Nothing logged.")
					except irclib.ServerNotConnectedError, e:
						logging.debug("Server connection error when sending message")
					return
				project = ""
				message = arr[1]
			try:
				adminlog.log(self.config, message, project, author)
				if author in self.config.title_map:
					title = self.config.title_map[author]
				else:
					title = "Master"
				try:
					self.server.privmsg(event.target(), "Logged the message, %s" % title)
				except irclib.ServerNotConnectedError, e:
					logging.debug("Server connection error when sending message")
			except Exception:
				traceback.print_exc()
				logging.warning(sys.exc_info)

	def connect(self):
		self.server = self.irc.server()
		self.server.add_global_handler("welcome", self.on_connect)
		self.server.add_global_handler("pubmsg", self.on_msg)
		self.server.add_global_handler("nicknameinuse", self.switch_nick)
		self.server.add_global_handler("nickcollision", self.switch_nick)
		self.server.add_global_handler("unavailresource", self.switch_nick)
		self.server.add_global_handler("part", self.on_quit)
		self.server.add_global_handler("kick", self.on_quit)
		self.server.add_global_handler("disconnect", self.on_quit)
		self.server.add_global_handler("quit", self.on_quit)

		self.server.connect(self.config.network,
				self.config.port,
				self.config.nick)


parser = argparse.ArgumentParser(description='IRC log bot.',
		epilog='When run without args it will enumerate bot configs in /etc/adminbot.')
parser.add_argument('--config', dest='confarg', type=str, help='config file that describes a single logbot')
args = parser.parse_args()

bots = []
enable_projects = False
if 'confarg' in args:
	# Use the one config the user requested.
	confdir = os.path.dirname(args.confarg)
	fname = os.path.basename(args.confarg)
	split = os.path.splitext(fname)
	module = split[0]
	conf = imp.load_source(module, confdir + "/" + fname)

	# discard if this isn't actually a bot config file
	if not 'targets' in conf.__dict__:
		logging.error("%s does not appear to be a valid bot config." % args.confarg)
		exit(1)

	if ('enable_projects' in conf.__dict__) and conf.enable_projects:
		enable_projects = True

	bots.append(logbot(module, conf))
	logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
else:
	# Enumerate bot configs in /etc/adminbot;
	# Create a logbot object for each.
	sys.path.append('/etc/adminbot')
	confdir = '/etc/adminbot'
	configfiles = os.listdir(confdir)
	for fname in configfiles:
		split = os.path.splitext(fname)
		if split[1] == ".py":
			module = split[0]
			conf = imp.load_source(module, confdir + "/" + fname)

			# discard if this isn't actually a bot config file
			if not 'targets' in conf.__dict__:
				continue

			bots.append(logbot(module, conf))

			if ('enable_projects' in conf.__dict__) and conf.enable_projects:
				enable_projects = True
	logging.basicConfig(filename="/var/log/adminbot.log", level=logging.DEBUG)

if not bots:
	logging.error("No config files found, so nothing to do.")
	sys.exit(1)

if enable_projects:
	import os
	import ldap
	sys.path.append('/usr/local/sbin/')
	import ldapsupportlib

for bot in bots:
	logging.debug("'%s' starting" % bot.name)
	bot.connect()

while True:
	time.sleep(.1)
	for bot in bots:
		try:
			bot.irc.process_once()
		except:
			traceback.print_exc()
			logging.warning(sys.exc_info)
