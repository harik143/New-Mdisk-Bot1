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

import urllib3
import random

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

bot_token = os.environ.get("TOKEN", "5982883220:AAHIXfRWiTOJPN_x7ok0VWsqY8UiijwM9GM") 

api_hash = os.environ.get("HASH", "d7720b94d7b075ec7fa414f82f570b22") 

api_id = os.environ.get("ID", "16512912")

app = Client("my_bot",api_id=api_id, api_hash=api_hash,bot_token=bot_token)

# optionals

auth = os.environ.get("AUTH", "5730217267")

ban = os.environ.get("BAN", "")

# Bin Channel Username
channel_username = "mdiskbin"
# chat = app.get_chat(channel_username)
# channel_id = chat.id

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

**/fry99** - Scraping

**/Search** - Search

**/next** - Next Page

**/reset** - Reset Page Number

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

# ---------------------------------------------------------
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

    # Bin Channel Username
    channel_username = "mdiskbin"
    chat = app.get_chat(channel_username)
    channel_id = chat.id

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

        # Save the photo thumbnail if message has a photo
        if message.photo:
            file_path = f"{os.getcwd()}/{filename}.jpg"
            thumbnail_file = app.download_media(message.photo.file_id, file_name=file_path)
            print(f"Thumbnail saved to: {thumbnail_file}")
            app.edit_message_text(message.chat.id, msg.id, text=f"✅ Thumbnail saved 🖼️ ✅")

        if info == "V":

                thumb,duration,width,height = mediainfo.allinfo(ele,thumbfile)

                sent_video = app.send_video(message.chat.id, video=ele, caption=f"{partt}**{filename}\n**", thumb=thumbnail_file, duration=duration, height=height, width=width, reply_to_message_id=message.id, progress=progress, progress_args=[message])
                
                # copy video to channel
                app.edit_message_text(message.chat.id, msg.id, text=f"🚀 Forwarding Video To Channel 🚀")
                app.send_video(chat_id=channel_id, video=sent_video.video.file_id, caption=f"{filename}", supports_streaming=True, thumb=thumbnail_file)
                                

                if "-thumb.jpg" not in thumb:

                    os.remove(thumb)

        else:

                thumb,duration,width,height = mediainfo.allinfo(ele,thumbfile)

                sent_video = app.send_video(message.chat.id, video=ele, caption=f"{partt}**{filename}\n**", thumb=thumbnail_file, duration=duration, height=height, width=width, reply_to_message_id=message.id, progress=progress, progress_args=[message])
                
                # copy video to channel
                app.edit_message_text(message.chat.id, msg.id, text=f"🚀 Forwarding Video To Channel 🚀")
                app.send_video(chat_id=channel_id, video=sent_video.video.file_id, caption=f"{filename}", supports_streaming=True, thumb=thumbnail_file)
                

                if "-thumb.jpg" not in thumb:

                    os.remove(thumb)
        

        # deleting uploaded file

        os.remove(ele)
        os.remove(thumbnail_file)

        

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

# @app.on_message(filters.photo)

# def ptumb(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    

#     if not checkuser(message):

#         app.send_message(message.chat.id, '__You are either not **Authorized** or **Banned**__',reply_to_message_id=message.id)

#         return

    

#     file = app.download_media(message)

#     os.rename(file,f'{message.from_user.id}-thumb.jpg')

#     app.send_message(message.chat.id, '**Thumbnail is Set✅**',reply_to_message_id=message.id)

    

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

# -------------------------------------------------------------------------------------------------------
# Define a function to scrape the page for download links and titles
def scrape_desi49(url, message):

    # Bin Channel Username
    channel_username = "mdiskbin"
    chat = app.get_chat(channel_username)
    channel_id = chat.id

    message.reply_text(f'Scraping: {url}')
    # Disable SSL certificate verification warning
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Send a GET request to the URL and store the response
    response = requests.get(url, verify=False)
    # Send Messege
    msgd = message.reply_text(f'Scraping Started Desi49...')
    # Parse the HTML content of the response using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all 'li' elements with class 'thumi'
    thumi_list = soup.find_all("li", class_="thumi")

    # Loop through each 'li' element and extract the desired information
    for thumi in thumi_list:
        # Extract the 'href' attribute from the first 'a' tag within the 'li' element
        href = thumi.find("a")["href"]

        # Extract the title from the 'a' tag with class 'title'
        title = thumi.find("a", class_="title").get_text()

        # Extract the thumbnail URL from the 'img' tag within the 'span' tag with class 'thumbimg' if it exists
        thumbnail_span = thumi.find("span", class_="thumbimg")
        thumbnail_url = thumbnail_span.find("img")["src"] if thumbnail_span else None

        if thumbnail_url:
            # Print the extracted information
            video_url = href
            print("Video_Url:", video_url)
            print("Title:", title)
            print("Thumbnail URL:", thumbnail_url if thumbnail_url else "N/A")
            
            # Sleep
            time.sleep(3)

            # Disable SSL certificate verification warning
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Send a GET request to the extracted URL and store the response
            download_response = requests.get(href, verify=False)

            # Parse the HTML content of the download response using BeautifulSoup
            download_soup = BeautifulSoup(download_response.content, "html.parser")

            # Extract the download link from the 'source' tag within the 'video' tag
            download_link = download_soup.find("video").find("source")["src"]

            # Filter the download link to only include URLs ending with '*.mp4'
            download_link = re.findall(r"(.*\.mp4)", download_link)[0] if download_link else None

            try:
                urld = message.reply_text(f"✅ Checking Video URL ✅\n{thumbnail_url}\n")
                video_response = requests.get(download_link, stream=True, verify=False, timeout=5)
                total_size = int(video_response.headers.get('content-length', 0))
            except requests.exceptions.RequestException as e:
                print(f"Error downloading video: {e}. Skipping to next URL.")
                app.edit_message_text(message.chat.id, urld.id, text=f"❌ URL Not Valid ❌\n{thumbnail_url}\n")
                continue

            if download_link and total_size:
                # Print the extracted download URL
                print("Download URL:", download_link)

                # Get the filename from the URL
                filename = title
                # Construct the file path
                file_path = os.path.join(os.getcwd(), filename + ".mp4")

                # Send a GET request to the download URL and download the video
                video_response = requests.get(download_link, stream=True, verify=False)
                total_size = int(video_response.headers.get('content-length', 0)) # Fix: Get content-length from headers
                print(f"Downloading {title}...")

                # urld = message.reply_text(f"{thumbnail_url}\n")
                app.edit_message_text(message.chat.id, urld.id, text=f"✅ Downloading ✅\n\n📥 {title} 📥\n\n{thumbnail_url}\n\n{download_link}")
                # message.reply_text(f"Download URL: {download_link}")

                # Define a variable to store the previous message text
                previous_text = ""

                with open(file_path, "wb") as video_file:
                    downloaded = 0
                    for chunk in video_response.iter_content(chunk_size=1024):
                        if chunk:
                            downloaded += len(chunk)
                            video_file.write(chunk)
                            done = int(14 * downloaded / total_size)
                            percent = int(round(100 * downloaded / total_size, 2))
                            progress_text = f"\r{done * '🚀'}{' ' * (10 - done)} : {percent}%"
                            print(progress_text, end='')
                            
                            # Inside the loop where you update the download progress
                            if progress_text != previous_text:
                                # app.edit_message_text(message.chat.id, urld.id, text=progress_text)
                                app.edit_message_text(message.chat.id, urld.id, text=f"{progress_text}\n\n✅ Downloading ✅\n\n📥 {title} 📥\n\n{thumbnail_url}\n\n{download_link}")
                                previous_text = progress_text

                            # app.edit_message_text(message.chat.id, message.message_id, text=progress_text)

                                
                    print(f"\nDownload of {title} is complete!")
                    app.edit_message_text(message.chat.id, urld.id, text=f"✅ Downloaded Successfully! ✅\n\n📥 {title} 📥\n\n{thumbnail_url}\n\n{download_link}")

                print("Video downloaded successfully!")
                # print("------")

                # Download the thumbnail image
                thumbnail_response = requests.get(thumbnail_url)
                thumbnail_file_path = os.path.join(os.getcwd(), f"{title}.jpg")
                with open(thumbnail_file_path, "wb") as f:
                    f.write(thumbnail_response.content)

                app.edit_message_text(message.chat.id, urld.id, text=f"📥💾 {title} 📥💾 is complete!\n\n{thumbnail_url}\n")
                # Send a message to Telegram containing the downloaded file
                app.edit_message_text(message.chat.id, urld.id, text=f"🚀__ Uploading __🎬__ initiated __🚀\n\n{thumbnail_url}\n")
                sent_video = app.send_video(message.chat.id, video=file_path, caption=title, supports_streaming=True, thumb=thumbnail_file_path)

                # copy video to channel
                app.edit_message_text(message.chat.id, urld.id, text=f"🚀 Forwarding Video To Channel 🚀")
                app.send_video(chat_id=channel_id, video=sent_video.video.file_id, caption=f"{title}", supports_streaming=True, thumb=thumbnail_file_path)
                
                
                app.edit_message_text(message.chat.id, urld.id, text=f"✅__ Uploaded __✅")
                # app.send_video(message.chat.id, video=file_path, caption=title, supports_streaming=True, thumb=thumbnail_url)

                # delete video from local storage
                os.remove(file_path) # Remove Video
                os.remove(thumbnail_file_path) # Remove Thumbnail
                # Sleep
                time.sleep(1)
            else:
                # print("No download link found.")
                # pass
                continue
    new_base_url = "https://masahub.net/"
#     message.reply_text("Please select an option: /next")


# Define a function to scrape the page for download links and titles
def scrape_page(url, message):

    # Bin Channel Username
    channel_username = "mdiskbin"
    chat = app.get_chat(channel_username)
    channel_id = chat.id

    message.reply_text(f'Scraping: {url}')
    # Disable SSL certificate verification warning
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Send a GET request to the URL and store the response
    response = requests.get(url, verify=False)
    # Send Messege
    msgg = message.reply_text(f'Scraping Started Fry99...')
    # Parse the HTML content of the response using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all <a> tags with class "infos"
    a_elements = soup.find_all("a", class_="infos")

    # Extract the URLs from the <a> tags and print them
    for a in a_elements:
        url = a["href"]
        # Send a GET request to the URL and store the response
        response = requests.get(url, verify=False)
        # Parse the HTML content of the response using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the video title
        title_element = soup.find("h1")
        if title_element is not None:
            title = title_element.text[:50]
        else:
            title = "Untitled Video"

        # Find all links with a file download URL
        file_links = soup.find_all(href=re.compile("https://download.filedownloadlink.xyz/.*\.mp4"))
        # Download each file
        for i, link in enumerate(file_links):
            # Check if the link ends with .mp4
            if link['href'].endswith('.mp4'):
                # Get the index of .mp4
                mp4_index = link['href'].index('.mp4')
                # Construct the download URL
                download_url = link['href'][:mp4_index+4]
                # Get the filename from the URL
                filename = title
                # Construct the file path
                file_path = os.path.join(os.getcwd(), filename + ".mp4")
                # Send a GET request to the download URL and save the file to disk
                response = requests.get(download_url, stream=True, verify=False)
                total_size = int(response.headers.get('content-length', 0))

                print(f"Downloading {title}...")
                download_url = link['href']
                thumbnail_url = download_url.replace("https://download.filedownloadlink.xyz/", "https://static.filedownloadlink.xyz/thumb/").replace(".mp4", ".jpg")
                print(f"Thumbnail URL: {thumbnail_url}\nTitle: {title}\nDownload URL: {download_url}")
                url = message.reply_text(f"{thumbnail_url}\n")
                app.edit_message_text(message.chat.id, url.id, text=f"✅ Downloading ✅\n\n📥 {title} 📥\n\n{thumbnail_url}\n\n{download_url}")

                # app.edit_message_text(message.chat.id, url.id, text=f"📥 {title} 📥\n\n{thumbnail_url}\n")
                # message.reply_text(f"Title: {title}\n{thumbnail_url}\nDownload URL: {download_url}")

                with open(file_path, "wb") as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            downloaded += len(chunk)
                            f.write(chunk)
                            done = int(50 * downloaded / total_size)
                            percent = round(100 * downloaded / total_size, 2)
                            print(f"\r[{done * '#'}{' ' * (50 - done)}] {percent}%", end='')
                                
                    print(f"\nDownload of {title} is complete!")
                    # message.reply_text(f"\nDownload of {title} is complete!")
                    
                # Download the thumbnail image
                thumbnail_response = requests.get(thumbnail_url)
                thumbnail_file_path = os.path.join(os.getcwd(), f"{title}.jpg")
                with open(thumbnail_file_path, "wb") as f:
                    f.write(thumbnail_response.content)

                app.edit_message_text(message.chat.id, url.id, text=f"📥💾 {title} 📥💾 is complete!\n\n{thumbnail_url}\n")
                # Send a message to Telegram containing the downloaded file
                app.edit_message_text(message.chat.id, url.id, text=f"🚀__ Uploading __🎬__ initiated __🚀\n\n{thumbnail_url}\n")
                sent_video = app.send_video(message.chat.id, video=file_path, caption=title, supports_streaming=True, thumb=thumbnail_file_path)
                
                # copy video to channel
                app.edit_message_text(message.chat.id, url.id, text=f"🚀 Forwarding Video To Channel 🚀")
                app.send_video(chat_id=channel_id, video=sent_video.video.file_id, caption=f"{title}", supports_streaming=True, thumb=thumbnail_file_path)
                
                app.edit_message_text(message.chat.id, url.id, text=f"✅__ Uploaded __✅")
                # app.send_video(message.chat.id, video=file_path, caption=title, supports_streaming=True, thumb=thumbnail_url)

                # delete video from local storage
                os.remove(file_path) # Remove Video
                os.remove(thumbnail_file_path) # Remove Thumbnail
                # Sleep
                time.sleep(1)

# --------------------------------------------------------------------------------------------------------------------------

# Define the URL to scrape
base_url = "https://desi2023.com/"
desi49_url = "https://masahub.net/"
new_base_url = "https://masahub.net/"

# Define initial current page
current_page = 2
current_page_search = 2
search_input = None

# Define a function to create "next" button
def next_button(callback_data=None):
    # Create buttons for navigating to the next page
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Next", callback_data="next")]]
    )
    return buttons

# ----------------Working Code For Search , Next---------------------
def search_and_display(client, message):
    global search_input, current_page_search, base_url, current_page, new_base_url
    # Check if the search_input is present in the titles_list
    titles_list = ['69', 'Affair', 'Amateur', 'Amateur', 'Amature', 'Anal', 'Anal', 'App Video', 'Asian', 'Ass', 'Ass', 'Aunty', 'B Grade', 'Bang', 'Bath', 'bbw', 'Bengali', 'bhabi', 'Bhojpuri', 'Big ass', 'Big belly', 'Big boobs', 'Big dick', 'Big Navel', 'Big pussy', 'Black', 'Black', 'Boss', 'BTS', 'Cam', 'Cam', 'Car', 'Caught', 'celebrities', 'Change', 'Cleavage', 'Close Fuck', 'Couple', 'Crazy', 'Creamy', 'cuckold', 'Cuckold', 'Cum', 'Cute', 'Cute', 'Dance', 'Desi Porn', 'Dirty Mind', 'Dirty Mind', 'Doggy', 'Family', 'Family', 'Fatty', 'Feel', 'Fhot scenes', 'Fingering', 'First Time', 'For Girls', 'For Money', 'Friend gf','Friend wife', 'Full Flim', 'Funny', 'Glamour', 'Group', 'Hairy', 'Hard', 'Hard', 'Hijab', 'Holi', 'Homemade', 'indu', 'Kannada', 'Kerala', 'kiss', 'lesbian', 'Lesbian', 'licking', 'Lover', 'Making', 'Mallu', 'Masala Film', 'Mask', 'Massage', 'Masterbation', 'Milking', 'Model', 'Myanmar', 'Nepali', 'Nipple', 'Odia', 'Old', 'Old is Gold', 'Old Man', 'Onlyfans', 'Opps', 'Outdoor', 'Paid', 'pain', 'Park', 'Pee', 'Period', 'Photoshoot', 'Pk', 'Pornography', 'Pregnant', 'Pregnant', 'Public', 'Pussy show', 'Quick', 'randi', 'Ride', 'saree', 'Selfe', 'Sexy face', 'share', 'shemale', 'Shorts', 'show boobs', 'shy', 'sleep', 'Slim', 'Solo', 'Son-in-law', 'South Porn', 'Special', 'spy', 'Sri Lanka', 'Star', 'Stripchat', 'Suck', 'Swap', 'Tamil', 'tango', 'Tango Special', 'Taxi', 'teen', 'Telugu', 'threesome', 'Threesome', 'Tight', 'Tiktok', 'Toy', 'Tv', 'Uncategorized', 'Uncensored', 'unsatisfied', 'Vege', 'Video Call', 'Village', 'Virgin pussy', 'Wet', 'XhPremium', 'xvideos.red', 'Youtuber']

    if message.text == "/fry999":
        new_base_url = "https://desi2023.com/"

    elif message.text == "/desi49":
        new_base_url = "https://masahub.net/"

    if message.text == "/search":
        message.reply_text("Welcome! Please select an option: \n1. /desi49 \n2. /fry999")
    elif message.text == "/next":

            if search_input:
                url = f"{new_base_url}?search&s={search_input}&paged={current_page_search}"
                current_page_search += 1
                # message.reply_text(f'Url: {url}')
                if new_base_url == "https://desi2023.com/":
                    if search_input.lower() in [title.lower() for title in titles_list]:
                        url = f"{new_base_url}category/{search_input}/page/{current_page_search}/"
                        scrape_page(url, message)
                    else:
                        url = f"{new_base_url}?search&s={search_input}&paged={current_page_search}"
                        scrape_page(url, message)
                elif new_base_url == "https://masahub.net/":
                    scrape_desi49(url, message)
                message.reply_text("Please select an option: /next")
            else:
                url = new_base_url + f"page/{current_page}/"
                current_page += 1
                # message.reply_text(f'Url: {url}')
                if new_base_url == "https://desi2023.com/":
                    scrape_page(url, message)
                elif new_base_url == "https://masahub.net/":
                    scrape_desi49(url, message)
                message.reply_text("Please select an option: /next")

    elif message.text == "/reset":
        current_page_search = 2
        message.reply_text("Current Page Number Reseted")

    elif message.text in ["/desi49", "/fry999"]:
        if message.text == "/desi49":
            new_base_url = "https://masahub.net/"
        elif message.text == "/fry999":
            new_base_url = "https://desi2023.com/"
        message.reply_text("Please enter your search query:")
        search_input = ""

    elif search_input == "":
        search_input = message.text
        url = f"{new_base_url}?search&s={search_input}"
        # message.reply_text(f'Url: {url}')
        if new_base_url == "https://desi2023.com/":
            # scrape_page(url, message)
            if search_input.lower() in [title.lower() for title in titles_list]:
                url = f"{new_base_url}category/{search_input}/"
                scrape_page(url, message)
            else:
                url = f"{new_base_url}?search&s={search_input}"
                scrape_page(url, message)

        elif new_base_url == "https://masahub.net/":
            scrape_desi49(url, message)
            # message.reply_text("Please select an option: /next")
        message.reply_text("Please select an option: /next")
        message.reply_text("If You Want Change select an option: \n1. /desi49 \n2. /fry999")
    else:
        pass
# ----------------------------------

# Define the "fry99" command handler
@app.on_message(filters.command("fry99"))
def fry_command(client, message, search_input=None):

    # Define a function to create "next" button
    def next_button(callback_data=None):
        # Create buttons for navigating to the next page
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Next", callback_data="next")]]
        )
        return buttons

    # Define initial current page
    current_page = 2
    current_page_search = 2
    search_input = None

    # Create buttons for selecting "fry99" or "search" options
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Fry99", callback_data="fry99"),InlineKeyboardButton("Desi49", callback_data="desi49"), 
            InlineKeyboardButton("Search", callback_data="search")]
        ]
    )

    # Send a message with the buttons to the user
    msg = app.send_message(message.chat.id, "Please select an option:", reply_markup=buttons)

    # Define the URL to scrape
    base_url = "https://desi2023.com/"
    desi49_url = "https://masahub.net/"

    # Define a callback function to handle button clicks
    @app.on_callback_query()
    def select_option(client, callback_query):
        nonlocal current_page, search_input, current_page_search
        option = callback_query.data
        if option == "fry99":
            new_base_url = "https://desi2023.com/"
            url = new_base_url
            message.reply_text(f'Url 1 {url}')
            scrape_page(url, message)
            buttons = next_button()
            app.send_message(callback_query.message.chat.id, "Please select an option:", reply_markup=buttons)
            # message.reply_text(f'Next Url 1 {url}')
            
        elif option == "desi49":
            new_base_url = "https://masahub.net/"
            url = new_base_url
            message.reply_text(f'Url 1 {url}')
            scrape_desi49(url, message)
            # message.reply_text("Please select an option: **/next**")
            # search_and_display(client, message)

        elif option == "search":
            # search_and_display(client, message)
            message.reply_text("Welcome! Please select an option: \n1. /desi49 \n2. /fry999")
            # message.reply_text("Enter search query:")
            # if search_input:
            #     search_input = message.text
            #     url = f"{base_url}?search&s={search_input}"
            #     message.reply_text(f'Url: {url}')
            #     scrape_page(url, message)
            #     message.reply_text("Please select an option: **/next**")

        elif option == "next":
            # Use the current page number to construct the URL
            url = base_url + f"page/{current_page}/"
            message.reply_text(f'Url 3 {url}')
            scrape_page(url, message)
            current_page += 1 # Increment the current page number
            buttons = next_button()
            app.send_message(message.chat.id, "Please select an option:", reply_markup=buttons)
            

file = ""

# mdisk link in text
@app.on_message(filters.photo | filters.text | filters.group | filters.chat | filters.private | filters.channel)

def mdisktext(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    # # Save the photo thumbnail if message has a photo
    # if message.photo:
    #     file_path = f"{os.getcwd()}/thumbnail_file.jpg"
    #     thumbnail_file = client.download_media(message.photo.file_id, file_name=file_path)
    #     print(f"Thumbnail saved to: {thumbnail_file}")

    chat = app.get_chat(channel_username)
    channel_id = chat.id

    urls = re.findall(r"(?P<url>https?://(?:mdisk\.me|teraboxapp\.com|terabox\.com|momerybox\.com|nephobox\.com|link\.getnewlink\.com)/[^\s]+)", message.text or message.caption or "")

    if urls:
        print(f"urls 1 {urls}")
        # Echo the message back to the chat with the extracted URLs
        if urls:
            url_text = "\n".join(urls)
            # client.send_message(message.chat.id, f"{url_text}", reply_to_message_id=message.id)
        else:
            client.send_message(message.chat.id, message.text or message.caption or "", reply_to_message_id=message.id)

        if "https://mdisk.me/" in url_text:
        
            text = url_text
            
            mdisk_urls = re.findall(r'(https?://mdisk\.me/\S+)', text)

            links = mdisk_urls

            # Sleep
            message.reply_text("Please Wait 3 Seconds Im Sleeping ")
            time.sleep(3)
            # message.reply_text("Im Running ")

            if len(links) == 1:

                d = threading.Thread(target=lambda:down(message,links[0]),daemon=True)

                d.start()

            else:
                # Sleep
                time.sleep(3)

                d = threading.Thread(target=lambda:multilinks(message,links),daemon=True)

                d.start()   

        elif "https://teraboxapp.com/" in url_text or "https://terabox.com/" in url_text or "https://nephobox.com/" in url_text or "https://momerybox.com/" in url_text or "https://link.getnewlink.com/" in url_text :

            urls = url_text

            mdisk_urls = re.findall(r'(https?://(?:teraboxapp|terabox|nephobox|momerybox|link\.getnewlink)\.com/\S+)', urls)

            terabox_links = mdisk_urls
            
            # Sleep
            # message.reply_text("Please Wait 2 Seconds Im Sleeping ")
            msg = app.send_message(message.chat.id, f"Please Wait 3 Seconds Im Sleeping ", reply_to_message_id=message.id)
            time.sleep(3)
            # message.reply_text("Im Running ")

            if terabox_links:
                # app.send_message(message.chat.id, f"Extracted link: {terabox_links[0]}")

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
                    # app.send_message(message.chat.id, f"Video Name: {video_name}")
                    # msg = app.send_message(message.chat.id, f"Video Name: {video_name}"reply_to_message_id=message.id)

                    # msg = app.send_message(message.chat.id, f"Video Name: {video_name}", reply_to_message_id=message.id)
                    app.edit_message_text(message.chat.id, msg.id, text=f"Video Name: {video_name}")

                    # Save the photo thumbnail if message has a photo
                    if message.photo:
                        file_path = f"{os.getcwd()}/{video_name}.jpg"
                        thumbnail_file = client.download_media(message.photo.file_id, file_name=file_path)
                        print(f"Thumbnail saved to: {thumbnail_file}")
                        app.edit_message_text(message.chat.id, msg.id, text=f"✅ Thumbnail saved 🖼️ ✅")


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

                    app.edit_message_text(message.chat.id, msg.id, text=f'**Cookies Parsed...**')

                    resp = requests.get(url=URL, headers=header, cookies=cookies).json()['list'][0]['dlink']

                    # Sleep
                    time.sleep(3)

                    # downloading the file
                    app.edit_message_text(message.chat.id, msg.id, text=f'🌀__Downloading__🌐__Initiated__🌀')
                    if iswin:
                        subprocess.run([aria2c, '--console-log-level=warn', '-x 16', '-s 16', '-j 16', '-k 1M', '--file-allocation=none', '--summary-interval=10', resp])
                    else:
                        subprocess.run([aria2c, '--console-log-level=warn', '-x', '16', '-s', '16', '-j', '16', '-k', '1M', '--file-allocation=none', '--summary-interval=10', resp])
                    app.edit_message_text(message.chat.id, msg.id, text=f'✅ __Downloaded__ ✅')
                   
                    # Sleep
                    time.sleep(3)
                    # send video to Telegram
                    app.edit_message_text(message.chat.id, msg.id, text=f"🚀__ Uploading __🎬__ initiated __🚀")
                    # app.send_message(chat_id=channel_id, text=f"🚀__ Uploading __🎬__ initiated __🚀")
                    video_file = os.path.join(os.getcwd(), video_name)
                    with open(video_file, 'rb') as f:
                        sent_video = app.send_video(message.chat.id, video=f, caption=f"{video_name}", supports_streaming=True, thumb=thumbnail_file, reply_to_message_id=message.id)

                        # copy video to channel
                        app.edit_message_text(message.chat.id, msg.id, text=f"🚀 Forwarding Video To Channel 🚀")
                        app.send_video(chat_id=channel_id, video=sent_video.video.file_id, caption=f"{video_name}", supports_streaming=True, thumb=thumbnail_file)
                    
                    app.edit_message_text(message.chat.id, msg.id, text=f"✅__ Uploaded __✅")
                    # app.send_message(chat_id=channel_id, text=f"✅__ Uploaded __✅")
                    # delete video from local storage
                    os.remove(video_name)
                    os.remove(thumbnail_file)
                    # Sleep
                    time.sleep(5)
                    # app.delete_message(message.chat.id, msg.message_id)

                # download videos
                for url in terabox_links:
                    download_video(url)

# -------------------------------------------------------------------------------------------------------------
    elif "/fry99" in urls:
        print(f"urls fry {message.text}")
        message.reply_text("Please select an option: /search or /next")
        fry_command(client, message)
    else:
        print(f"urls 2 {message.text}")
        search_and_display(client, message)

# polling
app.run()
