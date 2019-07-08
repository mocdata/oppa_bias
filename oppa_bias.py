#Obtaining the drama list for the first data set: mydramas
#It is possible to parse the r.text content however using lxml.html is neater because we can retrive the table in a nice format.
#If you want to do this a bit more manual than BeautifulSoup from bs, and parsing it as lxml should give a better format than requestes.text

#Commands for dramalist
#df=parselist('https://mydramalist.com/dramalist/cattibrie_fr')
# One name is problematic in viki, Stranger find and change that to Forest of Strangers
# df.loc[df[df['Title']=='Stranger'].index[0],'Title'] = 'Secret Forest'
# df.to_csv("mydramas.csv")

#Commands for getting the video links for srt download from viki.
#driver=openvikiselenium() #login to viki manually, deal with captcha
#links=getvikivideolist(df,driver)
#with open("links.json","w") as f:
#	json.dump(links,f)
#saved,partial,notsaved=saveallsubs(links)
#


import requests
import lxml.html as lh
import pandas as pd
from bs4 import BeautifulSoup as bs
import json
from selenium import webdriver
import re
from glob import glob
import string
from time import sleep

class MyDramaList():
	'''Obtains the Watched, Dropped , Currently Watching and On hold lists from drama list. Only argument required is the username.
	Returns a pandas data frame with columns ['Title','Year','Score','WatchedTotal','NrOfEpisodes'].
	" ' " character is converted to " ’ " to match names in Viki.
	'''
	def __init__(self,username):
		self.username=username
		self.dramalist=self.parselist()

	def parselist(self):
		'''Parses the list from mydrama list site
		Calls: cleanlist
		'''
		httppath='https://mydramalist.com/dramalist/%s' %self.username
		r = requests.get(httppath)
		if r.status_code != 200:
			print('Is the username %s correct? I could not parse the dramalist' %self.username)
			return None
		#//tr does not get the header and table returns a merged list but can be parsed.
		tabletypes =[i.text_content() for i in lh.fromstring(r.content).xpath('//h3')]
		tables = [ ]
		full=lh.fromstring(r.content).xpath('//table')
		for table in full:
			headers=table.text_content().split('\n')[1].split()
			#Important, . in front of the path makes this relative to the local element. Ohterwise all the tr elements are parsed
			elements=table.xpath('.//tr')
			tables.append([headers,elements])
		if len(tables) != len(tabletypes):
			print('Tables are not equals to table types. Cannot parse this list.')
			return None
		keys = ['Title','Year','Score','WatchedTotal','NrOfEpisodes']
		parsed = {key:[] for key in keys}
		for ind in range(0,len(tables)):
			if tabletypes[ind] not in ['Currently Watching','Completed','Dropped','On hold']:
				continue
			else:
				for clean in self.cleanlist(tables[ind]):
					i=0
					while i < len(clean):
						parsed[keys[i]].append(clean[i])
						i+=1
		parsed=pd.DataFrame(parsed)
		return(parsed)

	def cleanlist(self,table):
		''' Cleans formats and creates the progress percentange
		Called: parselist.'''
		headers = table[0]
		elements = table[1]
		for title in elements:
			title=[col.text_content() for col in title]
			nitem=[]
			if 'Korean Drama' in title[1]:
				ctitle=(' '.join(title[1].split()[:-2]))
				ctitle=re.sub("'","’",ctitle)
				if ctitle == 'Stranger':
					ctitle = 'Secret Forest'
				nitem.append(ctitle)
				nitem.append(int(title[3]))
				nitem.append(float(title[5]))
				watched,total=[float(i) for i in title[6].split('/')]
				nitem.append(float(watched)/total*100)
				nitem.append(total)
				yield nitem
			else:
				continue

class VideoList():
	'''
	This class will get the video links from Viki using the Title column on a pandas data frame. " ' " character, if found, is converted to " ’ " to match the names in Viki.
	Names that are different between drama list and Viki are converted using Videolist.namechanges dictionary. If you want to add more names please initialize this class with a dictionary.
	Format for the dictionary is: {[Drama List Title]:[Viki Title]}. Returned titles will be from Drama List. Please use " ’ " in the dictionary.
	A selenium drive must be started before other functions can be used. Please manually login to Viki in the opened page and do not open any other tabs.
	'''
	def __init__(self,namechanges=None):
		self.namechanges={'Another Miss Oh':'Another Oh Hae Young','Birth of a Beauty':'Birth of the Beauty','Goblin':'Guardian: The Lonely and Great God','Fight For My Way':'Fight My Way',
				'Goong':'Princess Hours','Item':'The Item','Jealousy Incarnate':"Don’t Dare to Dream (Jealousy Incarnate)",'Kill Me, Heal Me':'Kill Me Heal Me',
				"My Wife’s Having an Affair this Week":'My Wife Is Having an Affair This Week','Remember – War of the Son':'Remember',
				'Romantic Doctor, Teacher Kim':'Romantic Doctor Kim','Sassy Go Go':'Cheer Up!','The Great Seducer':'Tempted','The Guardians':'The Guardian','The Heirs':'Heirs',
				"The Master’s Sun":"Master’s Sun","You’re All Surrounded":"You’re All Surrounded",'Advertising Genius Lee Tae Baek':'AD Genius Lee Tae Baek',
				'Blade Man':'Iron Man','Flower Boy Ramen Shop':'Flower Boy Ramyun Shop','Goong S':'Prince Hours','You Who Came From The Stars':'My Love From the Star','Stranger':'Secret Forest'}
		if namechanges and isinstance(dict):
			for key,value in namechanges.items():
				self.namechanges[key]=value
		print('To use the functions, you have to start a drive and login to viki using VideoList.openvikiselenium()')

	def openvikiselenium(self):
		'''This function opens up the chrome driver for logging in. This needs to be run once only. Using requests not all javascripts are available.'''
		browser = webdriver.Chrome()
		browser.get("https://www.viki.com")
		self.driver=browser

	def getvikivideolist(self,cdf):
		'''Returns a dictionary with the same titles as in the data frame given. Links to episodes are stored in a list, in the order they were numbered.
		Special episodes are removed from the list.'''
		videourls={}
		try:
			titles=cdf['Title']
		except:
			print('DataFrame does not contain a Title column, nothing will be searched.')
			return None
		for title in titles:
			#This is an exceptional case where the drama has a movie one with the same name
			if title == 'Stranger':
				title=self.namechanges[title]
				print('Drama Stranges was changed to %s' %title)
			title=re.sub("'","’",title)
			sleep(3) #To prevent sending too many queries one after another
			url=self.parsevikiurl(title)
			if not url:
				print('Drama "%s" not found on Viki' %title)
				videourls[title]=[]
				continue
			self.newtab(url)
			sleep(3) #To prevent sending too many queries one after another
			urls=self.parsevideovikiurl_selenium()
			self.closetab()
			if urls:
				videourls[title]=urls
			else:
				videourls[title]=[]
				print('Drama %s had no links' %title)
		self.videourls=videourls

	def recheck(self,titles=None):
		oldurls=self.videourls
		if titles is None:
			titles={'Title':[]}
			for title in oldurls:
				if len(oldurls[title]) == 0:
					titles['Title'].append(title)
		else:
			titles={'Title':titles}
		titles=pd.DataFrame(titles)
		self.getvikivideolist(titles)
		for key,value in self.videourls.items():
			oldurls[key]=value
		self.videourls=oldurls

	def parsevikiurl(self,ititle):
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
					ftitle.lower() == self.namechanges[ititle].lower()
				except KeyError:
					continue
				else:
					url = filt.find('a')["href"]
					break
		if url:
			url='https://www.viki.com/%s#modal-episode' %url
		return(url)

	def dict_append_on_duplicates(self,ordered_pairs):
		#modified from https://stackoverflow.com/questions/14902299/json-loads-allows-duplicate-keys-in-a-dictionary-overwriting-the-first-value
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

	def manual_parse(self,soup):
		'''If Json load fails try manual parsing with this method. Splits the soup text with newlines and colon. Returns urls with episode in it.
		'''
		sp=soup.find("script",type="application/ld+json").text.split(':')
		episodes=[]
		for line in sp:
			if all(i in line for i in ['episode','www.viki.com/videos']):
				episodes.append("https://www.viki.com/videos/%s" %line.split('\n')[0].split('/')[-1][:-1])
		return(episodes)

	def episodes_list(self,soup):
		try:
			js = json.loads(soup.find("script",type="application/ld+json").text,object_pairs_hook=self.dict_append_on_duplicates)
		except json.decoder.JSONDecodeError:
			episodes=self.manual_parse(soup)
		else:
			episodes=[]
			try:
				js['episode']
			except:
				episodes=None
			else:
				for epi in js['episode']:
					try:
						episodes.append(epi['publication'][0]['publishedOn']['url'])
					except:
						print('Most likely a movie was matched instead of a drama. No links are returned for this drama.')
						episodes=None
		return(episodes)

	def parsevideovikiurl_selenium(self):
		'''Obtains the video urls from Viki page of the drama. Does not care about the order of the episodes in the returned list.
		Issues: Altough video list exists, it is not parsed due to login requirements'''
		soup = bs(self.driver.page_source,features="html.parser")
		while soup.find("script",type="application/ld+json") is None:
			self.driver.refresh()
			soup = bs(self.driver.page_source,features="html.parser")
		episodes=None
		tries=0
		while episodes==None:
			self.driver.refresh()
			episodes=self.episodes_list(soup)
			tries+=1
			if tries >3:
				break
		try:
			last=episodes[-1]
		except:
			episodes=None
		else:
			if last[-1] == '"':
				episodes=episodes[:-1]
			filtepisodes=[]
			for link in episodes:
				ind=int(link.split('-')[-1])
				if 'special' not in link and 'epilogue' not in link:
					filtepisodes.insert(ind,link)
			episodes=filtepisodes
		return(episodes)

	def newtab(self,url):
		'''Opens a new tab and switches the focus to the second one.
		Issues: It assumes there is only tab open'''
		self.driver.execute_script("window.open('%s')" %url)
		self.driver.switch_to.window(self.driver.window_handles[1])

	def closetab(self):
		'''Closes the second tab and switches to the first one'''
		handles=self.driver.window_handles
		self.driver.switch_to.window(handles[1])
		self.driver.close()
		self.driver.switch_to.window(handles[0])




class SaveSub():
	@staticmethod	
	def cleantitle(title):
		'''Cleans the title name from spaces and special characters.
		'''
		newway=re.sub('[^a-zA-Z0-9\n\.]', '_', title)
		return newway

	def getsublink(self,url,title,episode):
		'''Downloads the Korean subtitles for the url. Returns the percentage number associated with the language as well.
		It saves an srt file from the returned url from first part of the function.
		Issues: Redirects are allowed, and I have no idea what kind of security problems this would create.
		'''
		url='/'.join(url.split('/')[2:])[4:]
		dbase="http://downsub.com/?url=%s"
		d="http://downsub.com/%s"
		sub=requests.get(dbase %url)
		soup=bs(sub.text,"html.parser")
		#The texts are only download. To find which one in the list the Korean we have to search the soup again
		sublinks=[link.get('href')[2:] for link in soup.find('div',id="show").find_all('a')]
		ind=0
		percent=0.0
		for lang in soup.find('div',id="show").text.split('\n')[1].split('>>')[1:]:
			if lang.split()[1].strip()=='Korean':
				percent=float(lang.split()[2].strip()[1:-2])
				break
			ind+=1
		try:
			url=d %sublinks[ind]
		except IndexError:
			passed=False
		else:
			outname='%s_%d.srt' %(self.cleantitle(title),episode)
			headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
			srt=requests.get(url,allow_redirects=True,headers=headers)
			passed=False
			for head in srt.headers.values():
				if 'srt' in head and percent != 0.0 :
					passed=True
					break
			if passed:
				with open(outname, 'wb') as f:
					f.write(srt.content)
		return(percent,passed)

	def saveallsubs(self,vlinks):
		subscomplete={'Title':[],'Subs':[]}
		totalsubs={}
		for title,links in vlinks.items():
			tpercent=[]
			passed=[]
			nosubs=[]
			nr=1
			for link in links:
				percent,slink=self.getsublink(link,title,nr)
				if slink and percent != 0.0:
					passed.append(nr)
					tpercent.append(percent)
				elif slink and percent == 0.0:
					nosubs.append(nr)
				else:
					nosubs.append(nr)
				nr+=1
			try:
				total=sum(tpercent)/len(links) #The percentage of subs that are present. Not that the tpercent is already in percantage
			except ZeroDivisionError:
				total=0.0
			totalsubs[title]={'Percent_passed':tpercent,'Episode_passed':passed,'Nosubs':nosubs}
			subscomplete['Title'].append(title)
			subscomplete['Subs'].append(total)
		self.subscomplete=pd.DataFrame(subscomplete)
		self.detailedinfo=totalsubs
		

