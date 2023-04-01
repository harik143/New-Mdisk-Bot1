import requests
import json
import os
import re
import subprocess
from multiprocessing import Pool

# setting
currentFile = __file__
realPath = os.path.realpath(currentFile)
dirPath = os.path.dirname(realPath)
dirName = os.path.basename(dirPath)

# is Windows ?
iswin = os.name == 'nt'

# binary setting
if iswin:
    ytdlp = dirPath + "/binaries/yt-dlp.exe"
    aria2c = dirPath + "/binaries/aria2c.exe"
else:
    ytdlp = dirPath + "/binaries/yt-dlp"
    aria2c = dirPath + "/binaries/aria2c"
    os.system(f"chmod 777 {ytdlp} {aria2c}")

# asking user for the links to download
urls = input('Enter the Links (separated by space or "\\n"): ')
urls_list = re.findall(r'(https?://teraboxapp\.com/\S+)', urls)

def download_video(url):
    redirects = requests.get(url=url)
    inp = redirects.url
    dom = inp.split("/")[2]
    fxl = inp.split("=")
    key = fxl[-1]

    URL = f'https://{dom}/share/list?app_id=250528&shorturl={key}&root=1'

    header = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': f'https://{dom}/sharing/link?surl={key}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    }

    cookies_file = dirPath + '/cookies.txt'

    def parseCookieFile(cookiefile):
        cookies = {}
        with open(cookies_file, 'r') as fp:
            for line in fp:
                if not re.match(r'^\#', line):
                    lineFields = line.strip().split('\t')
                    cookies[lineFields[5]] = lineFields[6]
        return cookies

    cookies = parseCookieFile('cookies.txt')
    print('Cookies Parsed')

    resp = requests.get(url=URL, headers=header, cookies=cookies).json()['list'][0]['dlink']

    # downloading the file
    if iswin:
        subprocess.run([aria2c, '--console-log-level=warn', '-x 16', '-s 16', '-j 16', '-k 1M', '--file-allocation=none', '--summary-interval=10', resp])
    else:
        subprocess.run([aria2c, '--console-log-level=warn', '-x', '16', '-s', '16', '-j', '16', '-k', '1M', '--file-allocation=none', '--summary-interval=10', resp])

# download videos using multiprocessing
with Pool(processes=len(urls_list)) as pool:
    pool.map(download_video, urls_list)
