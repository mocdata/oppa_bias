# Search oppa and noona strings. A better way is required that includes the grammer. 
# For example the suffixes that \오빠 and \오빤 gets will be different. One ends with a wovvel the other ends with a constonant.
# Sometimes words could be merged with 랑, it could be noona and I. 
# I covered some of the cases I found in the translations via a brute force way. Perhaps there is an article about string comparison in Korean.
# Commands for obtaining all the words 
# allwords=uniquewords(cdf)
# Populating the dataframe routine after the check is modified manually
# newcdf=getcountsdrama(cdf)
# newcdf.to_csv("mydramas.csv")

import string
import pandas as pd 
from glob import glob
import re
from konlpy.tag import Mecab
from oppa_bias import SaveSub as ss

class Cleaning():
	'''Functions in this class are used by both search methods. It also serves as a way to clean and leave onl the Korean words.
	'''
	def cleaned(self,words):
		'''Removes the punctuation and the text formatting i, br and a random heart I found while parsing. 
		List Method
		Called: findallmatching, check
		'''
		remove=list(string.punctuation+'♥♬♫'+string.ascii_letters+string.digits)
		for word in words:
			newword=''
			for char in word:
				if char not in remove:
					newword=newword+char
			yield newword

	def cleanstring(self,wordstr):
		'''Removes the punctuation and the text formatting i, br and a random heart I found while parsing. 
		String Method
		'''
		remove=list(string.punctuation+'♥♬♫'+string.ascii_letters+string.digits)
		newword=''
		for char in list(wordstr):
			if char not in remove:
				newword=newword+char
		return(newword)

class GetAllMatching():
	def findallmatching(self,srt):
		'''This generator iterates over the file and it is lines. Returns the word if it finds oppa or noona. 
		This is a more simplified version of the check function to find the words regardless of the position.
		'''
		with open(srt,'r',encoding='utf-8') as fobj:
			for line in fobj:
				words=line.split()
				for word in Cleaning.cleaned(self.words):
					r=False
					if '오빠' in word: r=True
					elif '오빤' in word: r=True
					elif '누나' in word : r=True
					elif '누난'in word : r=True
					if r:
						yield word

	def uniquewords(self,cdf):
		'''This function returns a unique set of words containing oppa and noona. This list was used as a guide to form the check function.
		Calls: findallmatching
		'''
		wordlist=[]
		for title in cdf['Title']:
			title=ss.cleantitle(title)
			srts=glob('%s_[0-9]*.srt' %title)
			for srt in srts:
				for word in findallmatching(srt):
					wordlist.append(word)
		return(set(wordlist))

class MySearch():
	def __init__(self):
		pass

	def check(self,word,noona=False):
		'''The search algorithm for oppa and noona. It finds the oppa or noona in the beginning or the end. 
		Then checkes whether oppa and noona are merged with jamo in singles or doubles. 
		If it does, it considers the word meaningful and returns 1
		Called:counter
		'''
		singles=['랑','은','는','이','가','같','의','어','도','지','다','에','데'] #같 seems like a typo or maybe it is a dialect, my knowledge is limited.
		doubles=['하고','이랑','고요','까지','대신','간다','인데','부터']
		if noona:
			checks=['누나','누난']
		else:
			checks=['오빠','오빤']
		word=list(word)
		if len(word)==2:
			count=1
		#Begins with oppa/noona
		elif ''.join(word[0:2]) in checks:
			#Here maybe I should check if length is 3 to make sure other words are not counted
			if len(word) > 3 and ''.join(word[3:5]) in doubles:
				count=1
			elif word[2] in singles:
				count=1
			else:
				count=0
		#Ends with oppa/noona
		elif len(word) >= 3:
			if ''.join(word[-2:]) in checks:
				count=1
			#Towards the and with 랑 for example , becomes something oppa and ...
			elif ''.join(word[-3:-1]) in checks and word[-1] in singles:
				count=1
			elif ''.join(word[-4:-2]) in checks and ''.join(word[-2:]) in doubles:
				count=1
			#In the middle I have no way of knowing. Mostly likely the sentence was written without spaces *facepalm* Korean had spaces I thought!
			else:
				count=0
		return count

	def counter(self,fobj):
		'''The below code naively uses the decoded comparison for words. If problematic we could use unicode comparison.
		오빠 is oppa, \\uc624\\ube60 . 누나 is noona, \\ub204\\ub098
		https://www.unicode.org/charts/PDF/UAC00.pdf
		Calls: cleaned, check
		Called:readcountwords
		Issues:Korean language has suffixes and merged words. This function only checks a few of these. Writing a better search function calls for profiency in Korean.
		'''
		oppa=0
		noona=0
		total=0
		for line in fobj:
			words=[char.strip(string.punctuation) for char in line.split()]
			for word in Cleaning.cleaned(self,words):
				if any(i in word for i in ['누나','누난']):
					noona+=self.check(word,noona=True)
				elif any(i in word for i in ['오빠','오빤']):
					oppa+=self.check(word,noona=False)
			total+=len(words)
		return(oppa,noona,total)

class KoNLPySearch():
	def mecab_counter(self,fobj,method=Mecab()):
		'''Extracting nouns using Mecab from KoNLPy. Total word count is likely to be different then the other local count.
		'''
		oppa=0
		noona=0
		total=0
		for line in fobj:
			nouns=method.nouns(Cleaning.cleanstring(self,line))
			if '오빠' in nouns or '오빤' in nouns:
				oppa+=1
			if '누나' in nouns or '누난' in nouns:
				noona+=1
			total+=len(nouns)
		return(oppa,noona,total)

class srtSearch():
	def readcountwords(self,title,mecab=True,method=Mecab()):
		'''
		Finds the srt files matching title name and returns the count found for all the srts.
		Calls:counter
		Called:getcountsdrama
		'''
		title=ss.cleantitle(title)
		print(title)
		srts=glob('%s_[0-9]*.srt' %title)
		print(srts)
		oppatotal=0
		noonatotal=0
		allwords=0
		for srt in srts:
			f=open(srt,'r',encoding='utf-8')
			if mecab:
				oppa,noona,total=KoNLPySearch.mecab_counter(self,f,method=method)
			else:
				ma=MySearch()
				oppa,noona,total=ma.counter(f)
			f.close()
			oppatotal+=oppa
			noonatotal+=noona
			allwords+=total
		return(oppatotal,noonatotal,allwords)

	def getcountsdrama(self,cdf,mecab=True,method=Mecab()):
		'''Iterates over the titles and returns a new dataframe with the counts.
		Calls:readcountwords
		'''
		counts={'Title':[],'Oppa':[],'Noona':[],'Total':[]}
		for title in cdf['Title']:
			oppa,noona,total=self.readcountwords(title,mecab=mecab,method=method)
			counts['Title'].append(title)
			counts['Oppa'].append(oppa)
			counts['Noona'].append(noona)
			counts['Total'].append(total)
		counts=pd.DataFrame(counts)
		return(pd.merge(cdf,counts,on=['Title']))