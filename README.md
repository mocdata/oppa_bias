# Oppa Bias
The functions within this repo are used to extract data to assess the bias in learning foreign words. Since I watch quite a lot of Korean dramas, I have used these as an example. One of the first words I have learned was oppa. Is this because I have heard this word so many times?

Disclamer: mOCData is not responsible from users abusing the usage of the functions below to infringe copyrights. These functions were written for the sole purpose of analyzing data in an automated fashion from a site which the creator of the file already has legal access. The functions below may get you banned from Viki, please note that this website has no API support for non-official developers, hence be reasonable when requesting information. You are responsible from your actions.

**Files:**
* _oppa_bias.py_ has the functions to obtain MyDramaList, video URLs from Viki and downloading subtitles from Downsubs with percentage information.
* _search_algorithm.py_ has the functions to process the individual srt files. It cleans up the files on the go, does not write a cleaned versions.
* _mydramas.csv_ is the resulting data set with columns :  Title  Year  Score  WatchedTotal  NrOfEpisodes        Subs. It will also have the Oppa, Noona and Total columns. 
* links.json is the dictionary where I stored the links to the individual episodes. Viki might block me at some point for enourmous number of http requests. This file is kept to avoid fishing the links again and again.
* _subs_detailed_info.json_ includes infomration about the individual episodes subs. 

## Issues
Korean language uses suffixes and sometimes words can be merged. For oppa and noona there will be other sounds in the end, i.e. oppado also means older brother. Currently only a few of these are parsed. A better search algorigthm is needed. However this will not be possible without some proficieny in Korean. After completing the coursera course, I might be a bit better at it.