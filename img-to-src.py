import pytesseract
from pytesseract import Output
import requests
from bs4 import BeautifulSoup
import re
import argparse
import os

# pytesseract Page segmentation modes and OCR engine mode
# psm range is 0-13; 6 assumes a single uniform block of text. ocr is default.
myConfig = r"--psm 6 --oem 3"

# Confidence threshold for word recognition. Higher T will may result in less words being detected. Lower T may result in unrecognizable characters.
confThreshold = 70

def imgToText(imagePath):
    data = pytesseract.image_to_data(imagePath, config=myConfig, output_type=Output.DICT)
    textLength = len(data['text'])
    textWords = []
    for i in range(textLength):
        if float(data['conf'][i]) >= confThreshold:
            textWords.append(data['text'][i])
    return (" ".join(textWords))


def getResults(query, se='google'):
    resultLinks = []
    acceptedSE = ['google', 'brave', 'duckduckgo', 'bing', ]
    # Arbitrary header params for DDG
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0",}
    if se in acceptedSE:
        print(f"\nSearching with {se}:\n")
        if se == 'google':
            url = f"https://www.google.com/search?q={query}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, features="html.parser")
            for link in soup.find_all("a",href=re.compile("(?<=/url\?q=)(htt.*://.*)")):
                match = link["href"].split("&sa=U&ved=")[0]
                resultLinks.append(re.split(":(?=http)",match.replace("/url?q=","")))
            return resultLinks
        elif se == 'brave':
            url = f"https://search.brave.com/search?q={query}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, features="html.parser")
            for result in soup.select('.snippet'):
                resultLinks.append(result.select_one('.result-header').get('href'))
            return resultLinks
        elif se == 'duckduckgo':
            # DDG obfuscates search results using regular url, have to use html version to extract links
            url = 'https://html.duckduckgo.com/html/'
            # Since POST method, need a payload with our query
            paylod =  {'q': f'{query}', 'b': ''}
            response = requests.post(url,paylod,headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find_all("a", class_="result__url", href=True):
                resultLinks.append(re.split(":(?=http)",link["href"].replace("/url?q=","")))
            return resultLinks
    else:
        print("Unaccepted search engine.")

# If image is a link, download it to 'tempIMG.jpg'.
def downloadImage(url):
    response = requests.get(url)
    with open('tempIMG.jpg', 'wb') as jpg:
        jpg.write(response.content)
    return jpg.name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--search', type=str, required=False, help='Search engine to query.')
    parser.add_argument('-u','--url', type=str, required=False, help='URL of image.')
    parser.add_argument('-f','--file', type=str, required=False, help='File path of image.')
    args = parser.parse_args()
    imagePath = False


    if args.url:
        imagePath = args.url
    if args.file:
        imagePath = args.file
    if not imagePath:
        imagePath = input('Enter file path or url: ')
    if imagePath.split(":")[0] == ("https" or "http"):
        imagePath = downloadImage(imagePath)
    text = imgToText(imagePath)
    print("Text: \n")
    print(text)
    
    if args.search:
        queryLinks = getResults(text, args.search)
    else:
        queryLinks = getResults(text)
    for link in queryLinks:
        print(link)

    # Delete temporarily created image file
    os.remove(imagePath)

if __name__ == '__main__':
    main()
