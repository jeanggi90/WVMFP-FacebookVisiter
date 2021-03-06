#!/usr/bin/python

# -*- coding: utf-8 -*-
 
#############
# LIBRARIES #
#############

import mechanize    # Login to facebook
from lxml import html   # Analyse the source code with xpath
import sys


##################
# DATA STRUCTURE #
##################

class User:
    """
        Holds data about the user
    """
    def getLogin():
        login = ""

        with open('login.txt', 'r') as loginFile:
            login = loginFile.read()
            loginFile.close()

        return login.split(":")

    userID = ""
    email = getLogin()[0]
    passwd = getLogin()[1]


#############
# FUNCTIONS #
#############

def setupBrowser():
    """
        Setup the browser which we use for login to facebook and scraping the source code
    """
    br = mechanize.Browser()
    cj = mechanize.LWPCookieJar()
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0')]
    return br

def login(emailAddress,password):
    """
        Login to facebook with the email and password given in the argument
    """

    print("[-] LOGIN")
    print("[+] emailAddress : " + emailAddress)
    print("[+] password : " + "[Password hidden]")
    
    br = setupBrowser()

    br.open('https://facebook.com/')
    br.select_form(nr=0)
    br.form['email'] = emailAddress
    br.form['pass'] = password
    br.submit()

    return br

def logout(br):
    """
        For a proppre sign out of facebook
    """
    print("[-] LOGOUT")
    br.open('https://m.facebook.com/')

    for link in br.links(url_regex="logout.php"):
        br.open('https://m.facebook.com' + link.url)

    print("[-] QUIT")

def getUserID(scrapedCode):
    """
        Scrapes source code and gets the userID from it
    """
    
    tree = html.fromstring(scrapedCode)

    # Depending on the language fb might return a list with several elements, so we have to iterate through them and look for the right one
    for i in tree.xpath('//img[1]/@id'):
        print(i[:19])
        if i[:19] == "profile_pic_header_":
            idValue = i
            break

    print("[+] SUCCESS LOGIN")
    print("[-] GETTING USERID")
    User.userID = idValue[19:] # Strip the beginning and get the userID
    print("[+] GOT USERID")

def getVisiterID(scrapedCode):
    """
        Here we get all script tag sections from the source code, analyse them and select the right one, strip all unnescessary stuff, converte the js object to a json  and save it to a file
    """
    print("[-] GETTING DATA ABOUT THE USERS")
    tree = html.fromstring(scrapedCode)

    scriptTags = tree.xpath('//script')
    scriptTag = ""

    # Iterate over all script tag section and look for the one containing the right keyword
    for s in scriptTags:
        if "InitialChatFriendsList" in html.tostring(s):
            scriptTag = html.tostring(s)
            break

    visitersObject = scriptTag.split('shortProfiles:', 1)[-1].rsplit('nearby:', 1)[0][:-1]

    with open('visiters.json', 'w') as visiters:
        visiters.write(jsObjectToJson(visitersObject))

    print("[+] GOT DATA ABOUT HE VISITERS")

def jsObjectToJson(objectString):
    """
        The retrieved data is in js object format. This means that there are no quotes arround the keys, so we have to add them in otder to get a propre json file
    """
    jsonString = ""
    lastCutPos = 0
    x = 0

    for letter in objectString:
        if (letter == "{" or letter == ",") and not objectString[x + 1] == '"':
            jsonString += objectString[lastCutPos : x + 1] + '"'
            lastCutPos = x + 1
        elif letter == ":" and not (objectString[x - 1] == '"' or objectString[x + 1] == "/" or objectString[x + 1] == "{"):
            jsonString += objectString[lastCutPos : x ] + '":'
            lastCutPos = x + 1

        x += 1

    jsonString += objectString[lastCutPos : ]

    return jsonString

def writeToTestfile(textToSave):
    """
        This function is mainly used for testing and debuggind purpose
    """

    print("[-] WRITE TO FILE")
    with open('test.html', 'w') as file:
        file.write(textToSave)


#################
# MAIN FUNCTION #
#################

if __name__ == '__main__':
    """
        Main Function
    """
    try:
        br = login(User.email, User.passwd)
        # Scrape the main page in order to get the userID
        response = br.open('https://facebook.com/')
        # writeToTestfile(str(response.read()))
        getUserID(str(response.read()))
    except Exception as e:
        print("[+] Your email address or password seems to be wrong. Please try again!")
        print("[+] Quit")
        sys.exit()

    # Scrape the profile page in order to get the js object containing the data about the visiters
    response = br.open('https://facebook.com/' + User.userID)
    getVisiterID(str(response.read()))

    logout(br)

