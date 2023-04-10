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

**/fry99** - Scraping

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

                app.send_video(message.chat.id, document=ele, caption=f"{partt}**{filename}\n By ©️ @movie_time_botonly**", thumb=thumbfile, force_document=True, reply_to_message_id=message.id, progress=progress, progress_args=[message])

        

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

# # Messege Echo
# @app.on_message(filters.chat | filters.photo | filters.text | filters.group | filters.chat)
# def echo(client, message):
#     # Echo the message back to the chat
#     client.send_message(message.chat.id, message.text or message.caption or "", reply_to_message_id=message.id)
# --------------------------------------------------------------------

# @app.on_message(filters.photo | filters.text | filters.group | filters.chat)
# def echo(client, message):
#     # Extract URLs from the message
#     # urls = re.findall(r"(?P<url>https?://[^\s]+)", message.text or message.caption or "")

#     urls = re.findall(r"(?P<url>https?://(?:mdisk\.me|teraboxapp\.com|momerybox\.com)/[^\s]+)", message.text or message.caption or "")
    
#     # Echo the message back to the chat with the extracted URLs
#     if urls:
#         url_text = "\n".join(urls)
#         # client.send_message(message.chat.id, f"{message.text or message.caption}\n\n{url_text}", reply_to_message_id=message.id)

#         client.send_message(message.chat.id, f"{url_text}", reply_to_message_id=message.id)
#     else:
#         client.send_message(message.chat.id, message.text or message.caption or "", reply_to_message_id=message.id)

# ----------------------------------------------------------------
# # Define the "fry99" command handler
# @app.on_message(filters.command("fry99"))
# def fry_command(client, message):

#     # Define a function to create "next" button
#     def next_button(callback_data=None):
#         # Create buttons for navigating to the next page
#         buttons = InlineKeyboardMarkup(
#             [[InlineKeyboardButton("Next", callback_data="next")]]
#         )
#         return buttons

#     # Define initial current page
#     current_page = 2
#     search_input = None

#     # Create buttons for selecting "fry99" or "search" options
#     buttons = InlineKeyboardMarkup(
#         [
#             [InlineKeyboardButton("Fry99", callback_data="fry99"), InlineKeyboardButton("Search", callback_data="search")]
#         ]
#     )

#     # Send a message with the buttons to the user
#     msg = app.send_message(message.chat.id, "Please select an option:", reply_markup=buttons)

#     # Define the URL to scrape
#     base_url = "https://desi2023.com/"

#     # Define a function to scrape the page for download links and titles
#     def scrape_page(url):
#         message.reply_text(f'Url 4 {url}')
#         # Disable SSL certificate verification warning
#         urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#         # Send a GET request to the URL and store the response
#         response = requests.get(url, verify=False)

#         # Parse the HTML content of the response using BeautifulSoup
#         soup = BeautifulSoup(response.content, "html.parser")

#         # Find all <a> tags with class "infos"
#         a_elements = soup.find_all("a", class_="infos")

#         # Extract the URLs from the <a> tags and print them
#         for a in a_elements:
#             url = a["href"]
#             # Send a GET request to the URL and store the response
#             response = requests.get(url, verify=False)

#             # Parse the HTML content of the response using BeautifulSoup
#             soup = BeautifulSoup(response.content, "html.parser")

#             # Find the video title
#             title_element = soup.find("h1")
#             if title_element is not None:
#                 title = title_element.text[:50]
#             else:
#                 title = "Untitled Video"


#             # Find all links with a file download URL
#             file_links = soup.find_all(href=re.compile("https://download.filedownloadlink.xyz/.*\.mp4"))

#             # Print the video title and file download URLs
#             for link in file_links:
#                 print(f"Title: {title}\nDownload URL: {link['href']}")
#                 message.reply_text(f"Title: {title}\nDownload URL: {link['href']}")

    # # Define a function to handle search queries
    # @app.on_message(filters.text & filters.private)
    # def search_keyword(client, message):
    #     nonlocal search_input
    #     search_input = message.text
    #     url = f"{base_url}?search&s={search_input}"
    #     message.reply_text(f'Url 2 {url}')
    #     scrape_page(url)
    #     buttons = next_button()
    #     app.send_message(message.chat.id, "Please select an option:", reply_markup=buttons)

    # # Define a callback function to handle button clicks
    # @app.on_callback_query()
    # def select_option(client, callback_query):
    #     nonlocal current_page
    #     option = callback_query.data
    #     if option == "fry99":
    #         url = base_url
    #         message.reply_text(f'Url 1 {url}')
    #         scrape_page(url)
    #         buttons = next_button()
    #         app.send_message(callback_query.message.chat.id, "Please select an option:", reply_markup=buttons)
    #         # message.reply_text(f'Next Url 1 {url}')
    #     elif option == "search":
    #         app.send_message(callback_query.message.chat.id, "Enter search query:")

    #     elif option == "next":
    #         # Use the current page number to construct the URL
    #         if search_input:
    #             url = f"{base_url}?search&s={search_input}&paged={current_page}"
    #         else:
    #             url = base_url + f"page/{current_page}/"
    #         message.reply_text(f'Url 3 {url}')
    #         scrape_page(url)
    #         current_page += 1 # Increment the current page number
    #         buttons = next_button()
    #         app.send_message(callback_query.message.chat.id, "Please select an option:", reply_markup=buttons)
# ----------------------------------------------------------------------------------------------------------
# Define a function to scrape the page for download links and titles
def scrape_page(url, message):
    message.reply_text(f'Url 4 {url}')
        # Disable SSL certificate verification warning
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Send a GET request to the URL and store the response
    response = requests.get(url, verify=False)

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

            # Print the video title and file download URLs
        for link in file_links:
            print(f"Title: {title}\nDownload URL: {link['href']}")
            message.reply_text(f"Title: {title}\nDownload URL: {link['href']}")

# Define the URL to scrape
base_url = "https://desi2023.com/"

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

def search_and_display(client, message):
    global search_input, current_page_search
    if message.text == "/search":
        message.reply_text("Welcome! Please select an option: /search or /next")
    elif message.text == "/next":
        if search_input:
            url = f"{base_url}?search&s={search_input}&paged={current_page_search}"
            current_page_search += 1
            message.reply_text(f'Url: {url}')
            scrape_page(url, message)
            message.reply_text("Please select an option: **/next**")
        else:
            message.reply_text("Please enter a search keyword first.")
    elif message.text == "/reset":
        current_page_search = 2
        message.reply_text("Current Page Number Reseted")
    else:
        search_input = message.text
        url = f"{base_url}?search&s={search_input}"
        message.reply_text(f'Url: {url}')
        scrape_page(url, message)
        message.reply_text("Please select an option: **/next**")

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
            [InlineKeyboardButton("Fry99", callback_data="fry99"), InlineKeyboardButton("Search", callback_data="search")]
        ]
    )

    # Send a message with the buttons to the user
    msg = app.send_message(message.chat.id, "Please select an option:", reply_markup=buttons)

    # Define the URL to scrape
    base_url = "https://desi2023.com/"

    # Define a callback function to handle button clicks
    @app.on_callback_query()
    def select_option(client, callback_query):
        nonlocal current_page, search_input, current_page_search
        option = callback_query.data
        if option == "fry99":
            url = base_url
            message.reply_text(f'Url 1 {url}')
            scrape_page(url, message)
            buttons = next_button()
            app.send_message(callback_query.message.chat.id, "Please select an option:", reply_markup=buttons)
            # message.reply_text(f'Next Url 1 {url}')
            
        elif option == "search":
            message.reply_text("Enter search query:")
            if search_input:
                search_input = message.text
                url = f"{base_url}?search&s={search_input}"
                message.reply_text(f'Url: {url}')
                scrape_page(url, message)
                message.reply_text("Please select an option: **/next**")

        elif option == "next":
            # Use the current page number to construct the URL
            url = base_url + f"page/{current_page}/"
            message.reply_text(f'Url 3 {url}')
            scrape_page(url, message)
            current_page += 1 # Increment the current page number
            buttons = next_button()
            app.send_message(message.chat.id, "Please select an option:", reply_markup=buttons)
            

# mdisk link in text
@app.on_message(filters.photo | filters.text | filters.group | filters.chat)

def mdisktext(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):

    urls = re.findall(r"(?P<url>https?://(?:mdisk\.me|teraboxapp\.com|terabox\.com|momerybox\.com|nephobox\.com)/[^\s]+)", message.text or message.caption or "")
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

            if len(links) == 1:

                d = threading.Thread(target=lambda:down(message,links[0]),daemon=True)

                d.start()

            else:

                d = threading.Thread(target=lambda:multilinks(message,links),daemon=True)

                d.start()  
    elif "/fry99" in urls:
        print(f"urls fry {message.text}")
        message.reply_text("Please select an option: /search or /next")
        fry_command(client, message)
    else:
        print(f"urls 2 {message.text}")
        search_and_display(client, message)
        # search_keyword(client, message)

# polling

app.run()
