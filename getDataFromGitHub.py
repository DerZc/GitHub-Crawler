# This script allows to crawl information and repositories from GitHub using the GitHub REST API (https://developer.github.com/v3/search/).
#
# Given a query, the script downloads for each repository returned by the query its ZIP file.
# In addition, it also generates a CSV file containing the list of repositories queried.
# For each query, GitHub returns a json file which is processed by this script to get information about repositories.
#
# The GitHub API limits the queries to get 100 elements per page and up to 1,000 elements in total.
# To get more than 1,000 elements, the main query should be splitted in multiple subqueries using different time windows through the constant SUBQUERIES (it is a list of subqueries).
#
# As example, constant values are set to get the repositories on GitHub of the user 'rsain'.


#############
# Libraries #
#############

import wget
import time
import simplejson
import pycurl
import math

try:
    # Python 3
    from io import BytesIO
except ImportError:
    # Python 2
    from StringIO import StringIO as BytesIO


#############
# Constants #
#############

URL = "https://api.github.com/search/repositories?q=" #The basic URL to use the GitHub API
QUERY = "user:DerZc+" #The personalized query (for instance, to get repositories from user 'rsain')
#SUBQUERIES = ["language%3AC+language%3AC%2B%2B+stars%3A>50"] #Different subqueries if you need to collect more than 1000 elements
SUBQUERIES = ["language:C+stars:>=50","language:cpp+stars:>=50"]
PARAMETERS = "&per_page=100" #Additional parameters for the query (by default 100 items per page)
DELAY_BETWEEN_QUERYS = 10 #The time to wait between different queries to GitHub (to avoid be banned)
OUTPUT_FOLDER = "/home/zhangchi/Github-C/" #Folder where ZIP files will be stored
OUTPUT_TXT_FILE = "/home/zhangchi/Github-C/" #Path to the CSV file generated as output


#############
# Functions #
#############

def getUrl (url) :
	''' Given a URL it returns its body '''
	buffer = BytesIO()
	c = pycurl.Curl()
	c.setopt(c.URL, url)
	c.setopt(c.WRITEDATA, buffer)
	c.perform()
	c.close()
	body = buffer.getvalue().decode('utf-8')

	return body


########
# MAIN #
########

#To save the number of repositories processed
countOfRepositories = 0

#Output CSV file which will contain information about repositories
f = open(OUTPUT_TXT_FILE + "repositories.txt", "a+")

#Run queries to get information in json format and download ZIP file for each repository
for subquery in range(1, len(SUBQUERIES)+1):
	#print "Processing subquery " + str(subquery) + " of " + str(len(SUBQUERIES)) + " ..."
	print("Processing subquery %d of %d ..." %(subquery, len(SUBQUERIES)))
	
	#Obtain the number of pages for the current subquery (by default each page contains 100 items)
	#url = URL + QUERY + str(SUBQUERIES[subquery-1]) + PARAMETERS			
	url = URL + str(SUBQUERIES[subquery-1]) + PARAMETERS	

	print("query url: ", url)
	dataRead = simplejson.loads(getUrl(url))	
	numberOfPages = int(math.ceil(dataRead.get('total_count')/100.0))

	#Results are in different pages
	for currentPage in range(1, numberOfPages+1):
		#print "Processing page " + str(currentPage) + " of " + str(numberOfPages) + " ..."
		print("Processing page %d of %d ..." %(currentPage, numberOfPages))
		#url = URL + QUERY + str(SUBQUERIES[subquery-1]) + PARAMETERS + "&page=" + str(currentPage)	
		url = URL + str(SUBQUERIES[subquery-1]) + PARAMETERS + "&page=" + str(currentPage)
		print("current page url: ", url)
		dataRead = simplejson.loads(getUrl(url))
		
		#Iteration over all the repositories in the current json content page
		for item in dataRead['items']:
			#Obtain user and repository names
			user = item['owner']['login']
			repository = item['name']
			f.write("user: " + user + "; repository: " + repository + "\n")
			print(user, ' ', repository)
			
			#Download the zip file of the current project				
			print ("Downloading repository '%s' from user '%s' ..." %(repository,user))
			url = item['clone_url']
			fileToDownload = url[0:len(url)-4] + "/archive/master.zip"
			fileName = item['full_name'].replace("/","#") + ".zip"
			print("download url: " + fileToDownload)
			try:
				wget.download(fileToDownload, out=OUTPUT_FOLDER + fileName)
			except:
				#https://github.com/antirez/redis/archive/unstable.zip
				try:
					fileToDownload = url[0:len(url)-4] + "/archive/unstable.zip"
				except Exception as e:
					ef = open(OUTPUT_TXT_FILE + "error.txt", "a+")
					ef.write(e)
					ef.close()
							
			#Update repositories counter
			countOfRepositories = countOfRepositories + 1

	#A delay between different subqueries
	if (subquery < len(SUBQUERIES)):
		#print "Sleeping " + str(DELAY_BETWEEN_QUERYS) + " seconds before the new query ..."
		print("Sleeping %d seconds before the new query ..." %DELAY_BETWEEN_QUERYS)
		time.sleep(DELAY_BETWEEN_QUERYS)

#print "DONE! " + str(countOfRepositories) + " repositories have been processed."
print("DONE! %d repositories have been processed." %countOfRepositories)
f.close()
