# coding: utf-8
import os
import boto
from boto.s3.key import Key
from boto.s3.connection import S3Connection
from bs4 import BeautifulSoup
import csv
from csv import DictWriter
import requests
import codecs
import zipfile
from StringIO import StringIO 
import re
import copy
import io
# ------------------------------
# SETUP Amazon S3 credentials
# ------------------------------

# only needed when running on Heroku
AWS_ACCESS_KEY_ID = os.environ['aws_access_key_id']
AWS_SECRET_ACCESS_KEY = os.environ['aws_secret_access_key']

# see all console steps
#boto.set_stream_logger('boto')

# only use when uploading to heroku
s3 = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

# running locally, use this one:
#s3 = S3Connection(aws_key, aws_secret)

# ----------------------------------------------
# Start Code
# ----------------------------------------------

urlPage = "/open_onderwijsdata/images/Basisgegevens_Instellingen.zip"

# Get main page of Time values
#url = requests.get(urlPage)
#print url.text

# Create iterable variable
#soup = BeautifulSoup(url.text)

# Select latest download link from page
#getDiv = soup.find('a', attrs={"alt":"Basisgegevens instellingen"})
#print getDiv
#urlZip = getDiv.a.get('href')


urlZip="https://www.duo.nl"+urlPage
print urlZip

result = requests.get(urlZip)

# Convert to accepted file format
result = StringIO(result.content)

zf = zipfile.ZipFile(result, 'r')

# Get list of names
fileNames = zf.namelist()

# Get csv with organisations
csvFile = [s for s in fileNames if s.lower().startswith('organisatie') ]
print csvFile[0]

try:
	# set 3 variables to iterate over, one did not work
	data = StringIO(zf.read(csvFile[0]))
	listOrg = copy.copy(data)
	nogeenkopy = copy.copy(listOrg)
except:
	print 'ERROR: Did not find %s in zip file' % csvFile[0]


with open("onderwijsinstellingen_amsterdam.csv","w") as fout:
	
	# covert to bytes for string conversion later
	fout = io.BytesIO()

	# Set writer element
	writer = csv.writer(fout, delimiter=';')            
	
	# write header
	header=csv.DictReader(data, delimiter=',')
	#print header.fieldnames
	
	# append and write header 
	headerTotal = header.fieldnames
	headerTotal.append("type_code")
	headerTotal.append("type_naam")
	headerTotal.append("BRIN_NUMMER")
	#print headerTotal
	writer.writerow(headerTotal)
	
	# fill list with brin id, type_code and type_name 
	organisationsList=[]
	dataSet = csv.reader(listOrg, delimiter=",")
	for row in dataSet: 
		if row[1] == 'U' and row[23] == "363":
			organisationsList.append((row[0],row[5],row[6],row[32],row[33],row[34],row[0]))  
	print organisationsList[0]

	# Select locations and match type/name with brin id. Write if success.
	t2 = organisationsList
	t1 = csv.reader(nogeenkopy, delimiter=",")
	count = 0
	for row in t1:
		for a in t2:
			if row[0][:4] == a[0] and row[1] == 'D' and row[36] != 'H' and row[37] == 'N' and row[23] == "363":
				# append type code and type name
				row.append(a[1])
				row.append(a[2])
				row.append(row[0])
				# add missing tel
				if len(row[32])<2:
					row[32]=a[3]
				# add missing email
				if len(row[33])<2:
					row[33]=a[4]
				# add missing website
				if len(row[34])<2:
					row[34]=a[5]
				# add website based on email address if present
				if len(row[34])<2 and len(row[33])>2:
					Exclusions = ["hotmail.com","gmail.com","outlook.com","xs4all.nl","planet.nl","zonnet.nl"]
					eMailExtension = re.search(r'(@)(.*)',row[33]).group(2)
					if eMailExtension not in Exclusions:
						row[34]= "www.%s" % eMailExtension
					else:
						row[34]=''

				count = count + 1
				print "%s" % (count)
				#print row
				writer.writerow(row)
				# if row match and written stop for loop
				break	
	# dump csv as string
	output = fout.getvalue().strip('\r\n')		

# Instantiate a new client for Amazon Simple Storage Service (S3)
bucket_name = "opendata.lytrix.com" 
bucket = s3.get_bucket(bucket_name, validate=False)

# set empty filename
k = Key(bucket)
k.key = 'onderwijsinstellingen_amsterdam.csv'

#print "Uploading some data to " + bucket_name + " with key: " + k.key

#add strings to file
k.set_contents_from_string(output)
#set file to public
k.set_canned_acl('public-read')
# print link to file

print "File retrievable here: https://s3.amazonaws.com/%s/%s" % (bucket_name,k.key)
