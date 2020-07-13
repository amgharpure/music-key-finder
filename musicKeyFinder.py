import csv
import os
import sys
import time
import getopt
import requests

from mutagen.id3 import ID3
from bs4 import BeautifulSoup
from pathlib import Path

def printHeader():
        print("""
╭━╮╭━╮╱╱╱╱╱╱╱╱╱╱╭╮╭━╮╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╭╮╭━━╮╭━━━┳━╮╭━╮╭━━━╮╱╱╱╱╱╭╮
┃┃╰╯┃┃╱╱╱╱╱╱╱╱╱╱┃┃┃╭╯╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱┃┃┃╭╮┃┃╭━╮┃┃╰╯┃┃┃╭━━╯╱╱╱╱╱┃┃
┃╭╮╭╮┣╮╭┳━━┳┳━━╮┃╰╯╯╭━━┳╮╱╭╮╭━━┳━╮╭━╯┃┃╰╯╰┫╰━╯┃╭╮╭╮┃┃╰━━┳┳━╮╭━╯┣━━┳━╮
┃┃┃┃┃┃┃┃┃━━╋┫╭━╯┃╭╮┃┃┃━┫┃╱┃┃┃╭╮┃╭╮┫╭╮┃┃╭━╮┃╭━━┫┃┃┃┃┃┃╭━━╋┫╭╮┫╭╮┃┃━┫╭╯
┃┃┃┃┃┃╰╯┣━━┃┃╰━╮┃┃┃╰┫┃━┫╰━╯┃┃╭╮┃┃┃┃╰╯┃┃╰━╯┃┃╱╱┃┃┃┃┃┃┃┃╱╱┃┃┃┃┃╰╯┃┃━┫┃
╰╯╰╯╰┻━━┻━━┻┻━━╯╰╯╰━┻━━┻━╮╭╯╰╯╰┻╯╰┻━━╯╰━━━┻╯╱╱╰╯╰╯╰╯╰╯╱╱╰┻╯╰┻━━┻━━┻╯
╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╭━╯┃
╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱╰━━╯
    """)
def printFooter():
    print("""
╭━━━╮╱╱╱╱╭╮
┃╭━━╯╱╱╱╱┃┃
┃╰━━┳━╮╭━╯┃
┃╭━━┫╭╮┫╭╮┃
┃╰━━┫┃┃┃╰╯┃
╰━━━┻╯╰┻━━╯
""")
def getSearchString(s):
    return s.replace(" ", "+")

def getFormattedUrl(prefix, searchStringsArray):
    arr = [getSearchString(s) for s in searchStringsArray]
    return prefix + "+".join(arr);

def searchSongInfo(urlPrefix, artistName, trackName):
    url = getFormattedUrl(urlPrefix, [artistName, trackName])
    response = requests.get(url)
    #
    soup = BeautifulSoup(response.content, "html5lib")
    searchResultList = soup.find("div", attrs = {"class":"searchResultList"})
    row = searchResultList.find("div", attrs={"class":"search-info-container"})
    song = {}
    song["Artist"] = row.find("div", attrs={"class":"row search-artist-name"}).text
    song["Title"] = row.find("div", attrs={"class":"row search-track-name"}).text
    for attribute in row.findAll("div", attrs={"class": "col-md-4 col-sm-4 col-xs-4"}):
        attributeVal = attribute.find("div", attrs={"class":"row search-attribute-value"}).text
        attributeLabel = attribute.find("div", attrs={"class":"row search-attribute-label"}).text
        song[attributeLabel] = attributeVal
    return song

def readLocalSongs(basepath):
    localSongs = []
    # Get music info
    try:
        for entry in os.listdir(basepath):
            if os.path.isfile(os.path.join(basepath, entry)) and Path(entry).suffix == '.mp3':
                audio = ID3(os.path.join(basepath, entry))
                localSong = {}
                localSong['Artist'] = audio["TPE1"].text[0]
                localSong['Title'] = audio["TIT2"].text[0]
                localSongs.append(localSong)
    except FileNotFoundError:
        print("Please give a valid directory")
    print(" ".join(["Found", str(len(localSongs)), "songs in the directory"]))
    return localSongs

def getSongsInfo(localSongs):
    songsInfo = []
    songsMissingInfo = []
    urlPrefix = "https://tunebat.com/Search?q="
    if len(localSongs) > 0:
        print("\nSearching for information on songs:")

    for localSong in localSongs:
        try:
            songInfo = searchSongInfo(urlPrefix,
            localSong.get('Artist'), localSong.get('Title'))
            print("Found info for:\t\t\t" +
            '\t'.join([localSong.get('Artist'), localSong.get('Title')]))
            songsInfo.append(songInfo)
        except Exception as ex:
            songsMissingInfo.append(localSong)
            print("Could not find info for:\t" +
            '\t\t'.join([localSong.get('Artist'), localSong.get('Title')]))
    time.sleep(2)
    return songsInfo, songsMissingInfo

def writeSongInfoToFile(filename, songsInfo):
    shouldWriteHeader = not os.path.exists(filename)
    if songsInfo != None and len(songsInfo) > 0:
        print("\nWriting to file...")
        headers = songsInfo[0].keys()
        with open(filename, "a+", newline="") as f:
            w = csv.DictWriter(f, headers)
            if shouldWriteHeader:
                w.writeheader()
            for song in songsInfo:
                w.writerow(song)
        print("Writing to file has been completed")

if __name__ == "__main__":

    printHeader();
    directoryName = None
    isDirectoryError = False
    outputFileName = "/home/agharpur/Music/Music Key and BPM Info.csv"
    try:
        directoryName=sys.argv[1]
    except:
        print('Error : Please pass the complete directory path for the local songs.')
        isDirectoryError = True

    if not isDirectoryError:
        localSongs = readLocalSongs(directoryName)
        songsInfo, songsMissingInfo = getSongsInfo(localSongs)
        songsInfoRetry, songsMissingInfoRetry = getSongsInfo(songsMissingInfo)
        writeSongInfoToFile(outputFileName, songsInfo)
    printFooter()
