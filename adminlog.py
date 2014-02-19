import mwclient
import datetime

months = ["January", "February", "March", "April", "May", "June", "July",
			"August", "September",
			"October", "November", "December"]


def log(config, message, project, author):
	if config.enable_identica:
		import statusnet

	if config.wiki_category:
		import re

	site = mwclient.Site(config.wiki_connection, path=config.wiki_path)
	site.login(config.wiki_user, config.wiki_pass, domain=config.wiki_domain)
	if config.enable_projects:
		project = project.capitalize()
		pagename = config.wiki_page % project
	else:
		pagename = config.wiki_page

	page = site.Pages[pagename]
        if page.redirect:
            page = next(p.links())

	text = page.edit()
	lines = text.split('\n')
	position = 0
	# Um, check the date
	now = datetime.datetime.utcnow()
	logline = "* %02d:%02d %s: %s" % (now.hour, now.minute, author, message)
	month = str(now.month)
	day = str(now.day)
	# Try extracting latest date header
	header = "=" * config.wiki_header_depth
	for line in lines:
		position += 1
		if line.startswith(header):
			undef, month, day, undef = line.split(" ", 3)
			break
	if months[now.month - 1] != month or now.day != int(day):
		lines.insert(0, "")
		lines.insert(0, logline)
		lines.insert(0, "%s %s %d %s" % (header, months[now.month - 1],
			now.day, header))
	else:
		lines.insert(position, logline)
	if config.wiki_category:
		if not re.search('\[\[Category:' + config.wiki_category + '\]\]', text):
			lines.append('<noinclude>[[Category:' +
					config.wiki_category + ']]</noinclude>')
	page.save('\n'.join(lines), "%s (%s)" % (message, author))

	micro_update = ("%s: %s" % (author, message))[:140]

	if config.enable_identica:
		snapi = statusnet.StatusNet({'user': config.identica_username,
			'passwd': config.identica_password,
			'api': 'https://identi.ca/api'})
		snapi.update(micro_update)

	if config.enable_twitter:
		import twitter
		twitter_api = twitter.Api(**config.twitter_api_params)
		twitter_api.PostUpdate(micro_update)
