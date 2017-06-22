#qubot attempt
#this is the one folks

import os
import time
import urllib #url lib module should be included in default
import feedparser
import pymysql.cursors
#import MySQLdb #appears to be a dead project... not working anyway.
from slackclient import SlackClient

DB_PW = os.environ.get("DB_PW")
BOT_ID = os.environ.get("BOT_ID")
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

connection = pymysql.connect(host="localhost",
					user ='root',
					passwd=DB_PW,
					db= 'pythonspot',
					charset='utf8mb4',
					cursorclass=pymysql.cursors.DictCursor)
#sql table doesnt seem to be playing nice CREATE TABLE 'users' ('id' int(11) NOT NULL AUTO_INCREMENT, 'email' varchar(255) COLLATE utf8_bin NOT_NULL, 'password' varchar(255) COLLATE utf8_bin NOT NULL, PRIMARY KEY ('id')) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=1 ;

cur = connection.cursor()

#qubots ID as an environment variable
#constants
AT_BOT ="<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"
SEARCH_COMMAND = "search"
FETCH_COMMAND = "fetch"


base_url = 'http://export.arxiv.org/api/query?'
start = 0
max_results = 2
sortBy = 'lastUpdatedDate'
sortOrder = 'descending'


def handle_command(command, channel):
	"""
	    Receives commands directed at the bot and determines if they
	    are valid commands. If so, then acts on the commands. If not,
	    returns back what it needs for clarification.
	"""
	response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
	           "* command with numbers, delimited by spaces."
	if command.startswith(EXAMPLE_COMMAND):
	    response = "Sure...write some more code then I can do that!"

	if command.startswith(FETCH_COMMAND):
		if command.lower().find("settings") >= 0:
			response = "Sure, I'll get those settings for you. "
			settings = ""
			cur.execute("SELECT * FROM examples")
			settings = cur.fetchone() #temporary testing just fetching something...
			#for row in cur.fetchall():
			#	new = row[0] + " " + row[1] + "\n"
			#	settings += new
			print(settings)
			#response += settings
		else:
			response = "Hmm... I understood fetch... but fetch what? Maybe mention settings?"


	if command.startswith(SEARCH_COMMAND):
		start_pt = command.find("\"")
		end_pt = command.find("\"", start_pt+1)
		search_query = 'all:'+ command[start_pt+1:end_pt] #grabs the quoted text, THERE WAS AN EXTRA +1 HERE!

		#query = 'search_query=%s&start=%i&max_results=%i' %(search_query,start,max_results)
		query = 'search_query=%s&sortBy=%s&sortOrder=%s&max_results=%i' %(search_query,sortBy,sortOrder, max_results)
		
		#this is ahack to expose both namespaces
		feedparser._FeedParserMixin.namespaces['http://a9.com/-/spec/opensearch/1.1/'] = 'opensearch'
		feedparser._FeedParserMixin.namespaces['http://arxiv.org/schemas/atom'] = 'arxiv'
		#get request on base url and query
		feed_response = urllib.urlopen(base_url+query).read()
		print(base_url+query)
		#parse the response
		feed = feedparser.parse(feed_response)
		#print it out

		#creating a bunch of strings that hold parts of the feed attributes
		title = 'Feed title: %s' % feed.feed.title
		updated = 'Feed last updated: %s' % feed.feed.updated
		TotalResults =  'totalResults for this query: %s' % feed.feed.opensearch_totalresults #+ "\n" + \
		ItemsPerPage = 'itemsPerPage for this query: %s' % feed.feed.opensearch_itemsperpage #+ "\n" + \
		StartIndex = 'startIndex for this query: %s'   % feed.feed.opensearch_startindex #+ "\n" + \
		outputs = "" #start blank so we can avoid overwriting


#COPYING THE BIG LOOP>>> WILL NEED EDITS
		for entry in feed.entries:	
			#'e-print metadata' + "\n" + \
			outputs += 'arxiv-id: %s' % entry.id.split('/abs/')[-1] + "\n" + \
			'Published: %s' % entry.published + "\n" + \
			'Title:  %s' % entry.title

			# feedparser v4.1 only grabs the first author
			author_string = entry.author

			# grab the affiliation in <arxiv:affiliation> if present
			# - this will only grab the first affiliation encountered
			#   (the first affiliation for the first author)
			# Please email the list with a way to get all of this information!
			try:
				author_string += ' (%s)' % entry.arxiv_affiliation
			except AttributeError:
			    pass

			outputs += "\n"+ 'Last Author:  %s' % author_string

			#omitting this attempt for now
			# feedparser v5.0.1 correctly handles multiple authors, print them all
			#try:
			#    print 'Authors:  %s' % ', '.join(author.name for author in entry.authors)
			#except AttributeError:
			#    pass

			# get the links to the abs page and pdf for this e-print
			for link in entry.links:
			    if link.rel == 'alternate':
			        outputs += "\n" + 'abs page link: %s' % link.href
			    elif link.title == 'pdf':
			        outputs += "\n" + 'pdf link: %s' % link.href

			# The journal reference, comments and primary_category sections live under 
			# the arxiv namespace
			try:
			    journal_ref = entry.arxiv_journal_ref
			except AttributeError:
			    journal_ref = 'No journal ref found'
			outputs += "\n" +  'Journal reference: %s' % journal_ref

			try:
			    comment = entry.arxiv_comment
			except AttributeError:
			    comment = 'No comment found'
			#outputs += "\n" +  'Comments: %s' % comment

			# Since the <arxiv:primary_category> element has no data, only
			# attributes, feedparser does not store anything inside
			# entry.arxiv_primary_category
			# This is a dirty hack to get the primary_category, just take the
			# first element in entry.tags.  If anyone knows a better way to do
			# this, please email the list!
			outputs += "\n" +  'Primary Category: %s' % entry.tags[0]['term']

			# Lets get all the categories
			all_categories = [t['term'] for t in entry.tags]
			#outputs += "\n" +  'All Categories: %s' % (', ').join(all_categories)

			# The abstract is in the <summary> element
			outputs += "\n" + 'Abstract: %s' %  entry.summary + "\n"
			outputs +="--------------------------------------------------------------------------" +"\n"

# #END BIG LOOP

		response = "Sure...I can do a search! I'm a smart bot! Here's the result I found: \n" #+ 'Feed title: %s' % feed.feed.title #+"\n"+ \
		#response += title
		#response +=updated
		#response +=TotalResults
		#response +=ItemsPerPage
		#response +=StartIndex
		response += outputs #this should print a giant stack of shit. 

	slack_client.api_call("chat.postMessage", channel=channel, \
	                      text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
	"""
	    The Slack Real Time Messaging API is an events firehose.
	    this parsing function returns None unless a message is
	    directed at the Bot, based on its ID.
	"""

	output_list = slack_rtm_output
	if output_list and len(output_list) > 0:
		for output in output_list:
			if output and 'text' in output and AT_BOT in output['text']:
				# return text after the @ mention, whitespace removed
					return output['text'].split(AT_BOT)[1].strip().lower(), \
						output['channel']    
	return None, None


if __name__ == "__main__":
	READ_WEBSOCKET_DELAY = 1 #1 second dely between reading from firehose

	#print(slack_client.api_call("api.test"))
	#print(slack_client.api_call("auth.test"))
	

	if slack_client.rtm_connect(): #???
		print("qubot connected and running!")
		while True:
			command, channel = parse_slack_output(slack_client.rtm_read())
			if command and channel:
				handle_command(command, channel)
			time.sleep(READ_WEBSOCKET_DELAY)

	else:
		print("Connection failed. Invalid slack token or bot ID?")
