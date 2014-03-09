# If true, !log <project> <message>
# If false, !log <message>
enable_projects = False

# Relative DN of where the projects live
project_rdn = "ou=projects"

# Log messages to identica
enable_identica = False

# Log messages to Twitter
enable_twitter = False

# OAuth settings and access tokens for the Twitter API
# To obtain these tokens, go to <https://dev.twitter.com/apps> and sign in.
# Click 'Create a new application' and fill out the form. Leave 'Callback URL'
# unspecified. When you've created your application, click 'Settings',
# change 'Application Type' to 'Read and Write', and click 'Update this Twitter
# application's settings'. Finally, go back to the 'Details' tab and click
# 'Create my access token'.
twitter_api_params = {
	'access_token_key': 'NNNNNNNNNN-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',  # noqa
	'access_token_secret': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',       # noqa
	'consumer_key': 'XXXXXXXXXXXXXXXXXXXXX',                                   # noqa
	'consumer_secret': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',            # noqa
}

# Channels to join
targets = ("", "")

# Name of nickserv user
nickserv = "nickserv"

# Nick to use when joining
nick = ""

# Password to identify with
nick_password = ""

# Network to join (ex: irc.freenode.net)
network = ""

# Port to use when joining network (ex: 7000). Should support SSL.
port = 0

# Map irc nick to real name
author_map = {"example": "Example User"}

# Map irc nick to title of the user (how the bot addresses the user)
title_map = {"example": "your exampleness"}

# Scheme and wiki hostname to connect to
wiki_connection = ("https", "example.org")

# Url path
wiki_path = "/w/"

# Username of wiki bot user
wiki_user = ""

# Password of wiki bot user
wiki_pass = ""

# LDAP domain to use, if needed
wiki_domain = ""

# Page to write to; if you have projects enabled, the project is
# substituted by using "%s". For example:
#     wiki_page = "Nova_Resource:%s/SAL"
# If projects are disabled, this is just a normal page name.
wiki_page = ""

# Page to visit to view logs -- used by the bot's help message
log_url = ""

# Header depth for dates written
wiki_header_depth = 3

# Category the articles should be given
wiki_category = ""

# username used for connecting with identica
identica_username = ""

# password used for connecting with identica
identica_password = ""

# Check the logger's username or cloak against a trust list
check_users = False

# A semantic query to use to search the wiki for a trust list; example:
#	user_query = ("[[IRC Nick::+]] or [[IRC Cloak::+]]|?IRC Nick|?IRC Cloak
#                 "|limit=500|format=json")
user_query = ""

# The query path URL; example:
#	wiki_query_path = "/wiki/Special:Ask/"
wiki_query_path = ""

# Whether we "warn" or "error" if the user isn't in the trust list
required_users_mode = "warn"
