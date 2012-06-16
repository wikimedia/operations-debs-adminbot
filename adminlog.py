import mwclient
import datetime
import sys
sys.path.append('/etc/adminbot')
import config

if config.enable_identica:
	import statusnet

if config.wiki_category:
	import re

months=["January","February","March","April","May","June","July","August","September","October","November","December"]

def log(message,project,author):
	site=mwclient.Site(config.wiki_connection, path=config.wiki_path)
	site.login(config.wiki_user,config.wiki_pass)
	if config.enable_projects:
		project=project.capitalize()
		pagename=config.wiki_page % project
	else:
		pagename=config.wiki_page
	page=site.Pages[pagename]
	text=page.edit()
	lines=text.split('\n')
	position=0
	# Um, check the date
	now=datetime.datetime.utcnow()
	logline="* %02d:%02d %s: %s" % ( now.hour, now.minute, author, message )
	month = str(now.month)
	day = str(now.day)
	# Try extracting latest date header
	header = "=" * config.wiki_header_depth
	for line in lines:
		position+=1
		if line.startswith(header):
			undef,month,day,undef=line.split(" ",3)
			break
	if months[now.month-1]!=month or now.day!=int(day):
		lines.insert(0,"")
		lines.insert(0,logline)
		lines.insert(0,"%s %s %d %s"%(header, months[now.month-1],now.day,header))
	else:
		lines.insert(position,logline)
	if config.wiki_category:
		if not re.search('\[\[Category:' + config.wiki_category + '\]\]',text):
			lines.append('<noinclude>[[Category:' + config.wiki_category + ']]</noinclude>')
	page.save('\n'.join(lines),"%s (%s)"%(message,author))

	if config.enable_identica:
		snapi = statusnet.StatusNet( { 'user': config.identica_username, 'passwd': config.identica_password, 'api': 'https://identi.ca/api' } )
		snupdate = "%s: %s" % (author, message)
		snupdate = snupdate[:140] # Trim message
		snapi.update(snupdate)
