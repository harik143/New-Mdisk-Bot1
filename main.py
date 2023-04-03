import os
import re
import speedtest_cli
import threading
import subprocess
import time
import pyrogram
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup,InlineKeyboardButton
import mdisk
import extras
import mediainfo
import split
from split import TG_SPLIT_SIZE

import requests
import json
from multiprocessing import Pool
from bs4 import BeautifulSoup

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

# app

bot_token = os.environ.get("TOKEN", "5982883220:AAG40wETqVkiA1KFTkVdt7qAqziw8yJW3SE") 

api_hash = os.environ.get("HASH", "d7720b94d7b075ec7fa414f82f570b22") 

api_id = os.environ.get("ID", "16512912")

app = Client("my_bot",api_id=api_id, api_hash=api_hash,bot_token=bot_token)

# optionals

auth = os.environ.get("AUTH", "5730217267")

ban = os.environ.get("BAN", "")

# start command

@app.on_message(filters.command(["start"]))

def echo(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🉑ASK ACESS🉑",url="https://t.me/fligher")]]))

        return

    app.send_message(message.chat.id, '**Hi, I am Mdisk Video Downloader, you can watch Videos without MX Player.\n\n__Send me a link to Start...__**',reply_to_message_id=message.id,

    reply_markup=InlineKeyboardMarkup([[ InlineKeyboardButton("🏆𝐓𝐑𝐔𝐌𝐁𝐎𝐓𝐒🏆", url="https://t.me/movie_time_botonly")]]))
    
    
# help command

@app.on_message(filters.command(["help"]))

def help(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

        return

    

    helpmessage = """__**/start** - basic usage

**/help** - this message

**/speedtest** - speedtest

**/mdisk mdisklink** - usage

**/thumb** - reply to a image document of size less than 200KB to set it as Thumbnail ( you can also send image as a photo to set it as Thumbnail automatically )

**/remove** - remove Thumbnail

**/show** - show Thumbnail

**/change** - change upload mode ( default mode is Document📂 )__"""

    app.send_message(message.chat.id, helpmessage, reply_to_message_id=message.id,

    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧑‍💻 𝐃𝐄𝐕",url="https://t.me/fligher")]]))
    
# define an event handler for the /speedtest command
@app.on_message(pyrogram.filters.command(["speedtest"]))
async def speedtest(client, message):
    msg = await message.reply_text('Running a speed test. This might take a while...')
    try:
        st = speedtest_cli.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1024 / 1024
        upload_speed = st.upload() / 1024 / 1024
        result_img = st.results.share()
        await client.send_photo(
            chat_id=message.chat.id,
            photo=result_img,
            caption=f'Speed test results:\nDownload speed: {download_speed:.2f} Mbps\nUpload speed: {upload_speed:.2f} Mbps'
        )
    except Exception as e:
        await msg.edit(f'An error occurred while running the speed test: {e}')

# check for user access

def checkuser(message):

    if auth != "" or ban != "":

        valid = 1

        if auth != "":

            authusers = auth.split(",")

            if str(message.from_user.id) not in authusers:

                valid = 0

        if ban != "":

            bannedusers = ban.split(",")

            if str(message.from_user.id) in bannedusers:

                valid = 0

        return valid        

    else:

        return 1

# download status

def status(folder,message,fsize):

    fsize = fsize / pow(2,20)

    length = len(folder)

    # wait for the folder to create

    while True:

        if os.path.exists(folder + "/vid.mp4.part-Frag0") or os.path.exists(folder + "/vid.mp4.part"):

            break

    

    time.sleep(3)

    while os.path.exists(folder + "/" ):

        result = subprocess.run(["du", "-hs", f"{folder}/"], capture_output=True, text=True)

        size = result.stdout[:-(length+2)]

        try:

            app.edit_message_text(message.chat.id, message.id, f"⬇️__Downloaded__⬇️ : **{size} **__of__**  {fsize:.1f}MB**")

            time.sleep(10)

        except:

            time.sleep(5)

# upload status

def upstatus(statusfile,message):

    while True:

        if os.path.exists(statusfile):

            break

    time.sleep(3)      

    while os.path.exists(statusfile):

        with open(statusfile,"r") as upread:

            txt = upread.read()

        try:

            app.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")

            time.sleep(10)

        except:

            time.sleep(5)

# progress writter

def progress(current, total, message):

    with open(f'{message.id}upstatus.txt',"w") as fileup:

        fileup.write(f"{current * 100 / total:.1f}%")

# download and upload

def down(message,link):

    # checking link and download with progress thread

    msg = app.send_message(message.chat.id, '🌀__Downloading__🌐__Initiated__🌀', reply_to_message_id=message.id)

    size = mdisk.getsize(link)

    if size == 0:

        app.edit_message_text(message.chat.id, msg.id,"❌__**Invalid Link**__❌")

        return

    sta = threading.Thread(target=lambda:status(str(message.id),msg,size),daemon=True)

    sta.start()

    # checking link and download and merge

    file,check,filename = mdisk.mdow(link,message)

    if file == None:

        app.edit_message_text(message.chat.id, msg.id,"❌__**Invalid Link**__❌")

        return

    # checking if its a link returned
    if check == -1:
        app.edit_message_text(message.chat.id, msg.id,f"__**Can't Download File but here is the Download Link : {file}**__")
        os.rmdir(str(message.id))
        return

    # checking size

    size = split.get_path_size(file)

    if(size > TG_SPLIT_SIZE):

        app.edit_message_text(message.chat.id, msg.id, "✂️__Splitting__✂️")

        flist = split.split_file(file,size,file,".", TG_SPLIT_SIZE)

        os.remove(file) 

    else:

        flist = [file]

    app.edit_message_text(message.chat.id, msg.id, "⬆️__Uploading__🌐__initiated__⬆️")

    i = 1

    # checking thumbline

    if not os.path.exists(f'{message.from_user.id}-thumb.jpg'):

        thumbfile = None

    else:

        thumbfile = f'{message.from_user.id}-thumb.jpg'

    # upload thread

    upsta = threading.Thread(target=lambda:upstatus(f'{message.id}upstatus.txt',msg),daemon=True)

    upsta.start()

    info = extras.getdata(str(message.from_user.id))

    # uploading

    for ele in flist:

        # checking file existence

        if not os.path.exists(ele):

            app.send_message(message.chat.id,"**👨‍💻Error in Merging File contact our Support👨‍💻**",reply_to_message_id=message.id)
#             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("**SUPPORT**",url="https://t.me/TRUMBOTCHAT")]]))

            return

            

        # check if it's multi part

        if len(flist) == 1:

            partt = ""

        else:

            partt = f"__**part {i}**__\n"

            i = i + 1

        # actuall upload

        if info == "V":

                thumb,duration,width,height = mediainfo.allinfo(ele,thumbfile)

                app.send_video(message.chat.id, video=ele, caption=f"{partt}**{filename}\n By ©️ @movie_time_botonly**", thumb=thumb, duration=duration, height=height, width=width, reply_to_message_id=message.id, progress=progress, progress_args=[message])

                if "-thumb.jpg" not in thumb:

                    os.remove(thumb)

        else:

                app.send_document(message.chat.id, document=ele, caption=f"{partt}**{filename}\n By ©️ @movie_time_botonly**", thumb=thumbfile, force_document=True, reply_to_message_id=message.id, progress=progress, progress_args=[message])

        

        # deleting uploaded file

        os.remove(ele)

        

    # checking if restriction is removed    

    if check == 0:

        app.send_message(message.chat.id,"**IF YOU SEE THIS MESSAGE THE VIDEO/FILE PLAY ONLY [MX PLAYER]**, \n\nThis happens because either the **file** or **video** doesn't have separate **audio layer**__",reply_to_message_id=message.id)
#         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("**SUPPORT**",url="https://t.me/TRUMBOTCHAT")]]))
    if os.path.exists(f'{message.id}upstatus.txt'):

        os.remove(f'{message.id}upstatus.txt')

    app.delete_messages(message.chat.id,message_ids=[msg.id])

# mdisk command

@app.on_message(filters.command(["mdisk"]))

def mdiskdown(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

        return

    try:

        link = message.text.split("mdisk ")[1]

        if "https://mdisk.me/" in link:

            d = threading.Thread(target=lambda:down(message,link),daemon=True)

            d.start()

            return 

    except:

        pass

    app.send_message(message.chat.id, '**Send only __MDisk Link__ with command followed by the link\n\n Do not be over smart👺**',reply_to_message_id=message.id)

# thumb command

@app.on_message(filters.command(["thumb"]))

def thumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

        return

    try:

        if int(message.reply_to_message.document.file_size) > 200000:

            app.send_message(message.chat.id, '**Thumbline size allowed is < 200 KB😡**',reply_to_message_id=message.id)

            return

        msg = app.get_messages(message.chat.id, int(message.reply_to_message.id))

        file = app.download_media(msg)

        os.rename(file,f'{message.from_user.id}-thumb.jpg')

        app.send_message(message.chat.id, '**Thumbnail is Set✅**',reply_to_message_id=message.id)

    except:

        app.send_message(message.chat.id, '**reply __/thumb__ to a image document of size less than 200KB**',reply_to_message_id=message.id)

# show thumb command

@app.on_message(filters.command(["show"]))

def showthumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

        return

    

    if os.path.exists(f'{message.from_user.id}-thumb.jpg'):

        app.send_photo(message.chat.id,photo=f'{message.from_user.id}-thumb.jpg',reply_to_message_id=message.id)

    else:

        app.send_message(message.chat.id, '**Thumbnail is not Set☑️**',reply_to_message_id=message.id)

# remove thumbline command

@app.on_message(filters.command(["remove"]))

def removethumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

        return

    

    

    if os.path.exists(f'{message.from_user.id}-thumb.jpg'):

        os.remove(f'{message.from_user.id}-thumb.jpg')

        app.send_message(message.chat.id, '**Thumbnail is Removed🚮**',reply_to_message_id=message.id)

    else:

        app.send_message(message.chat.id, '**Thumbnail is not Set😤**',reply_to_message_id=message.id)

# thumbline

@app.on_message(filters.photo)

def ptumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

        return

    

    file = app.download_media(message)

    os.rename(file,f'{message.from_user.id}-thumb.jpg')

    app.send_message(message.chat.id, '**Thumbnail is Set✅**',reply_to_message_id=message.id)

    

# change mode

@app.on_message(filters.command(["change"]))

def change(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

        return

    

    info = extras.getdata(str(message.from_user.id))

    extras.swap(str(message.from_user.id))
                             
    info == "V"

    if info == "V":

        app.send_message(message.chat.id, '__Mode changed from **🎞Video🎞** format to **📂Document📂** format__',reply_to_message_id=message.id)

    else:

        app.send_message(message.chat.id, '__Mode changed from **📂Document📂** format to **🎞Video🎞** format__',reply_to_message_id=message.id)

        

# multiple links handler

def multilinks(message,links):

    for link in links:

        d = threading.Thread(target=lambda:down(message,link),daemon=True)

        d.start()

        d.join()

# mdisk link in text

@app.on_message(filters.text)

def mdisktext(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

    if not checkuser(message):

        app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

        return

    if "https://mdisk.me/" in message.text:
        
        text = message.text
        
        mdisk_urls = re.findall(r'(https?://mdisk\.me/\S+)', text)

        links = mdisk_urls

        if len(links) == 1:

            d = threading.Thread(target=lambda:down(message,links[0]),daemon=True)

            d.start()

        else:

            d = threading.Thread(target=lambda:multilinks(message,links),daemon=True)

            d.start()   

    elif "https://teraboxapp.com/" in message.text:

        urls = message.text

        mdisk_urls = re.findall(r'(https?://teraboxapp\.com/\S+)', urls)

        terabox_links = mdisk_urls

        if terabox_links:
            app.send_message(message.chat.id, f"Extracted link: {terabox_links[0]}")

            cookies_file = dirPath + '/cookies.txt'

            def download_video(url):
                redirects = requests.get(url=url)
                inp = redirects.url
                dom = inp.split("/")[2]
                fxl = inp.split("=")
                key = fxl[-1]

                # Extract the video name from the Terabox URL
                response = requests.get(url)
                soup = BeautifulSoup(response.content, "html.parser")
                video_name = soup.title.text.replace(" - Share Files Online & Send Larges Files with TeraBox", "")
                print(video_name)
                app.send_message(message.chat.id, f"Video Name: {video_name}")

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

                app.send_message(message.chat.id, '**Cookies Parsed...**',reply_to_message_id=message.id)

                resp = requests.get(url=URL, headers=header, cookies=cookies).json()['list'][0]['dlink']

                # downloading the file
                app.send_message(message.chat.id, '**Downloading Video**',reply_to_message_id=message.id)
                if iswin:
                    subprocess.run([aria2c, '--console-log-level=warn', '-x 16', '-s 16', '-j 16', '-k 1M', '--file-allocation=none', '--summary-interval=10', resp])
                    app.send_message(message.chat.id, '**Downloading Completed**',reply_to_message_id=message.id)
                else:
                    subprocess.run([aria2c, '--console-log-level=warn', '-x', '16', '-s', '16', '-j', '16', '-k', '1M', '--file-allocation=none', '--summary-interval=10', resp])
                    app.send_message(message.chat.id, '**Downloading Completed**',reply_to_message_id=message.id)
                
                # send video to Telegram
                video_file = os.path.join(os.getcwd(), video_name)
                app.send_video(message.chat.id, video=open(video_file, 'rb'), caption=f"{video_name}", reply_to_message_id=message.id)


            # download videos
            for url in terabox_links:
                download_video(url)
        else:
            app.send_message(message.chat.id, '**Send only __Terabox Link__ Bruh>>>>.........**',reply_to_message_id=message.id)


    else:

        app.send_message(message.chat.id, '**Send only __MDisk Link__ Bruh>>>>.........**',reply_to_message_id=message.id)

# polling

app.run()
