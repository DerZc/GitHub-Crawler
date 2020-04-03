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
import os

try:
    # Python 3
    from io import BytesIO
except ImportError:
    # Python 2
    from StringIO import StringIO as BytesIO


#############
# Constants #
#############

ACCESS_TOKEN = ""
URL = "https://api.github.com/search/repositories?access_token=" + ACCESS_TOKEN + "&q=" #The basic URL to use the GitHub API
QUERY = "user:DerZc+" #The personalized query (for instance, to get repositories from user 'rsain')
SUBQUERIES = ["language:C+language:cpp+stars:>=50"] #Different subqueries if you need to collect more than 1000 elements
PARAMETERS = "&per_page=100" #Additional parameters for the query (by default 100 items per page)
DELAY_BETWEEN_QUERYS = 10 #The time to wait between different queries to GitHub (to avoid be banned)
OUTPUT_FOLDER = "/home/zhangchi/Github-C/" #Folder where ZIP files will be stored
OUTPUT_TXT_FILE = "/home/zhangchi/Github-C/" #Path to the txt file generated as output
MINIMUM_PROJECT_NUM = 10000 #The minimum num of projects



#############
# Functions #
#############

def getUrl (url) :
	''' Given a URL it returns its body '''
	buffer = BytesIO()
	c = pycurl.Curl()
	c.setopt(c.URL, url)
	c.setopt(c.WRITEDATA, buffer)
	try:
		c.perform()
	except Exception as e:
		print(e)
		time.sleep(DELAY_BETWEEN_QUERYS)
		c.perform()
	c.close()
	body = buffer.getvalue().decode('utf-8')

	return body


########
# MAIN #
########

def downProj ():
	#To save the number of repositories processed
	countOfRepositories = 0
	currentMaxStars = 200000

	#Output CSV file which will contain information about repositories
	f = open(OUTPUT_TXT_FILE + "repositories.txt", "a+")

	#Run queries to get information in json format and download ZIP file for each repository
	#for subquery in range(1, len(SUBQUERIES)+1):
	while currentMaxStars > 50:
		#print "Processing subquery " + str(subquery) + " of " + str(len(SUBQUERIES)) + " ..."
		#print("Processing subquery %d of %d ..." %(subquery, len(SUBQUERIES)))
	
		#Obtain the number of pages for the current subquery (by default each page contains 100 items)
		#url = URL + QUERY + str(SUBQUERIES[subquery-1]) + PARAMETERS			
		#url = URL + str(SUBQUERIES[subquery-1]) + PARAMETERS	
		url = URL + "language:C+language:cpp+stars:50.." + str(currentMaxStars) +  PARAMETERS

		print("query url: ", url)
		try:
			dataRead = simplejson.loads(getUrl(url))	
		except Exception as e:
			print(e)
			time.sleep(DELAY_BETWEEN_QUERYS)
			return 1
		numberOfPages = int(math.ceil(dataRead.get('total_count')/100.0))

		#Results are in different pages
		for currentPage in range(1, numberOfPages+1):
			#print "Processing page " + str(currentPage) + " of " + str(numberOfPages) + " ..."
			print("Processing page %d of %d ..." %(currentPage, numberOfPages))
			#url = URL + QUERY + str(SUBQUERIES[subquery-1]) + PARAMETERS + "&page=" + str(currentPage)	
			#url = URL + str(SUBQUERIES[subquery-1]) + PARAMETERS + "&page=" + str(currentPage)
			url = URL + "language:C+language:cpp+stars:50.." + str(currentMaxStars) +  PARAMETERS + "&page=" + str(currentPage)
			print("current page url: ", url)
			try:
				dataRead = simplejson.loads(getUrl(url))
			except Exception as e:
				print(e)
				if countOfRepositories > MINIMUM_PROJECT_NUM:
					return 0
				else:
					time.sleep(DELAY_BETWEEN_QUERYS)
					return 1
		
			print(dataRead)
			#Iteration over all the repositories in the current json content page
			for item in dataRead['items']:
				#Obtain user and repository names
				user = item['owner']['login']
				repository = item['name']
				stargazers_count = item['stargazers_count']
				if currentPage == 10 :
					currentMaxStars = int(stargazers_count)
				#print(stargazers_count)
				#f.write("user: " + user + "; repository: " + repository + "\n")
				#print(user, ' ', repository)
			
				#Download the zip file of the current project				
				print ("Downloading repository '%s' from user '%s' ..." %(repository,user))
				url = item['clone_url']
				fileToDownload = url[0:len(url)-4] + "/archive/master.zip"
				fileName = item['full_name'].replace("/","#") + ".zip"

				if os.path.exists(OUTPUT_FOLDER + fileName):
					countOfRepositories = countOfRepositories + 1
					continue

				print("download url: " + fileToDownload)

				try:
					wget.download(fileToDownload, out=OUTPUT_FOLDER + fileName)
				except:
					continue
					#https://github.com/antirez/redis/archive/unstable.zip
					#try:
					#	fileToDownload = url[0:len(url)-4] + "/archive/unstable.zip"
					#	wget.download(fileToDownload, out=OUTPUT_FOLDER + fileName)
					#except Exception as e:
					#	ef = open(OUTPUT_TXT_FILE + "error.txt", "a+")
					#	ef.write(e)
					#	ef.close()
							
				#Update repositories counter
				f.write("user: " + user + "; repository: " + repository + "\n")
				countOfRepositories = countOfRepositories + 1

		#A delay between different subqueries
		#if (subquery < len(SUBQUERIES)):
			#print "Sleeping " + str(DELAY_BETWEEN_QUERYS) + " seconds before the new query ..."
			#print("Sleeping %d seconds before the new query ..." %DELAY_BETWEEN_QUERYS)
		print("Sleeping %d seconds before the new query ..." %DELAY_BETWEEN_QUERYS)
		time.sleep(DELAY_BETWEEN_QUERYS)

	#print "DONE! " + str(countOfRepositories) + " repositories have been processed."
	print("DONE! %d repositories have been processed." %countOfRepositories)
	f.close()
	return 0

res = 1
while res:
	res = downProj()
