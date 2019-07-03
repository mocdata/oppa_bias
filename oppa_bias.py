#Obtaining the drama list for the first data set: mydramas
#It is possible to parse the r.text content however using lxml.html is neater because we can retrive the table in a nice format.
#If you want to do this a bit more manual than BeautifulSoup from bs, and parsing it as lxml should give a better format than requestes.text
import requests
import lxml.html as lh
import pandas as pd
from bs4 import BeautifulSoup as bs
import load json

namechanges={'Another Miss Oh':'Another Oh Hae Young','Birth of a Beauty':'Birth of the Beauty','Goblin':'Guardian: The Lonely and Great God'}

def parselist(httppath):
	'''Parses the list from mydrama list site
	Issues: Cannot differentiate between dropped, on hold and currently watching. But returns the percent complete.'''
	r = requests.get(httppath)
	#//tr does not get the header and table returns a merged list
	tables = lh.fromstring(r.content).xpath('//tr')
	#From the web structure Table orders . This list can be max 5. But currently I have no direct way of knowing which lists are parsed, it is not important anyway.
	#Currently Watching, Completed, Plan to Watch, On Hold, Dropped. 
	keys=['#','Title','Country','Year','Type','Score','WatchedTotal']
	parsed={key:[] for key in keys}
	for clean in cleanlist(tables):
		i=0
		while i < len(clean):
			parsed[keys[i]].append(clean[i])
			i+=1
	parsed=pd.DataFrame(parsed)
	return(parsed)
		#'https://mydramalist.com/dramalist/cattibrie_fr')

def cleanlist(dlist):
	''' Cleans formats and creates the progress percentange'''
	ind=1
	for item in dlist:
		#Skip Movies and Special episodes of dramas
		if any(filt in item.text_content() for filt in ['Movie','Special']):
			continue
		nitem=[]
		nitem.append(ind)
		for val in item[1:]:
			#The title contains Korean Drama tag, we remove that
			if 'Korean' in val.text_content():
				nitem.append(' '.join(val.text_content().split()[:-2]))
			#The watched percentage to identify dropped or plan to watch ones.
			elif '/' in val.text_content():
				watched,total=[float(i) for i in val.text_content().split('/')]
				nitem.append(watched/total*100)
			else:
				#if it is plan to watch the string will contain nothing.
				#This is an odd place to check but I miss this empty string in the above elif.
				if len(val.text_content().split()) == 0:
					nitem.append(0.0)
				else:
					nitem.append(val.text_content())
		ind+=1
		yield nitem

def parsevikiurl(ititle):
	'''Obtain the url for the video from Viki search'''
	title='%20'.join(ititle.split())
	#Prevents 403 error
	headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
	vikisearch='https://www.viki.com/search?q="%s"' %title
	search=requests.get(vikisearch,headers=headers)
	soup = bs(search.text,"html.parser")
	url=None
	for filt in soup.find_all('h2')[:-1]:
		ftitle= filt.find('a').text.strip()
		if ftitle.lower() == ititle.strip().lower():
			url = filt.find('a')["href"]
			break
		else:
			try:
				ftitle.lower() == namechanges[ititle].lower()
			except KeyError:
				continue
			else:
				url = filt.find('a')["href"]
				break
	if url:
		url='https://www.viki.com/%s#modal-episode' %url
	return(url)

def dict_append_on_duplicates(ordered_pairs):
	"""It finds the duplicate key and appends the new and old value to a list. 
	Issues: It is problematic if the original old value is a list already. Then it creates a list of lists that the first element is expanded"""
	d = {}
	for k, v in ordered_pairs:
		if k in d and isinstance(d[k],list):
			d[k].append(v)
		elif k in d and not isinstance(d[k],list):
			old=d[k]
			d[k]=[old,v]
		else:
			d[k] = v
	return d

def parsevideovikiurl(url):
	'''Obtains the video urls from Viki page of the drama. Does not care about the order of the episodes in the returned list.
	Issues: Altough video list exists, it is not parsed when there is a restriction based on location, or decoding errors are raised when text is sent with /n characters.'''
	completeset=True
	headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
	r=requests.get(url,headers=headers)
	soup = bs(r.text,"html.parser")
	try:
		js = json.loads(soup.find("script",type="application/ld+json").text,object_pairs_hook=dict_append_on_duplicates)
	except json.decoder.JSONDecodeError:
		episodes=[]
		return(completeset,episodes)
	episodes=[]
	totnumber=int(js['numberOfEpisodes'])
	try:
		js['episode']
	except KeyError:
		print(soup.find_all("script").text)
		episodes=[]
	else:
		for epi in js['episode']:
			episodes.append(epi['publication'][0]['publishedOn']['url'])
		if len(episodes) != totnumber:
			completeset=False
	return(completeset,episodes)

def cleantitle(title):
	'''Cleans the title name for an easier pandas access.
	Issues: It currently does not remove special characters'''
	return title.strip().lower().replace(' ', '_').replace('(', '').replace(')', '')

def getvikivideolist(cdf):
	'''Expands the initial list of dramas with episode url. Titles are turned to lower case and cleanded'''
	videourls={}
	titles=cdf['Title']
	for title in titles:
		url=parsevikiurl(title)
		if not url:
			print('Drama "%s" not found on Viki' %title)
			continue
		complete,urls=parsevideovikiurl(url)
		if not complete and len(urls) != 0:
			print('Warning: Total number of episodes for %s do not match the extracted url. Returning the parsed data anyway.' %title)
		elif len(urls) == 0:
			print('No video url found for drama %s' %title)
			continue
		else:
			videourls[cleantitle(title)]=urls
	videourls=pd.DataFrame(videourls)
	return(videourls)
