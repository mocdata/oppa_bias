# Oppa Bias
The functions within this repo are used to extract data to assess the bias in learning foreign words. Since I watch quite a lot of Korean dramas, I have used these as an example. One of the first words I have learned was oppa. Is this because I have heard this word so many times?

**Files:**
* _oppa_bias.py_ has every function I used. All the functions to extract the data are included here. It uses mixed methods and require a little manual work since Viki does not support (for a good reason) web scrapping and have captchas and other methods to prevent it. The major issue is matching the words oppa and noona. Other than that this file is ready to be transformed for automated work. But I am done with the web scraping that I will not update it. Instead move the search function to a separate file and improve it.
* _mydramas.csv_ is the resulting data set from parsed subtitle files. 95 dramas from this list was found in Viki.
* links.json is the dictionary where I stored the links to the individual episodes. Viki might block me at some point for enourmous number of http requests. This file is kept to avoid fishing the links again and again.
* _srt_lists_complete_partial_not_parsed.json_ was written after subtitle files were parsed. 32/95 had all srt files. 32/95 had some srt files. 31/95 had no srt file. 

## Issues
Korean language uses suffixes and sometimes words can be merged. For oppa and noona there will be other sounds in the end, i.e. oppado also means older brother. Currently only a few of these are parsed. A better search algorigthm is needed. However this will not be possible without some proficieny in Korean. After completing the coursera course, I might be a bit better at it.