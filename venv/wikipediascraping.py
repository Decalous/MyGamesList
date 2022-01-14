import wikipedia                    #https://wikipedia.readthedocs.io/en/latest/code.html
import re                           #https://docs.python.org/3/library/re.html
from html.parser import HTMLParser  #https://docs.python.org/3/library/html.parser.html
import sqlite3                      #https://docs.python.org/3/library/sqlite3.html
import _markupbase
import webbrowser                   
import pandas as pd                 #https://pandas.pydata.org/docs/
## SQLite tutorial                  https://www.sqlitetutorial.net/
##        docs                      https://sqlite.org/docs.html
## Trello:                          https://trello.com/b/169s96xm/mygameslist

## TO DO:
## ADD USER-GAME RELATIONSHIP 
## PROBLEM WITH VERSIONS IN PUBLISHERS WITH REGIONS (SEE CATHERINE FULL BODY) Handled?
## MAYBE ADD NAMED RERELEASES LIKE CATHERINE CLASSIC AND FULL BODY
## SEPERATE SCRIPT FOR MORE DETAILED AND CUSTOMIZABLE QUERIES
## ABILITY TO GO BACK IN AND ADD / CHANGE ANY ERRORS
## ERROR CATCHING SO NOT EVERYTHING IS LOST!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
## HANDLE DATES NOT IN MONTH, DD, YYYY FORMAT LIKE Q2 2021
## INSTEAD OF DOING ALL THE WORK TO GET MULTIPLE RELEASES WORKING, COULD JUST TAKE THE FIRST DATE AND USE IT
## ADD A WAY TO GO BACK AFTER ENTERING A WRONG NAME DURING THE NAME PICKING PHASE
## 000 GOT ACCEPTED AS 0 WHEN CHOOSING A NAME, PROBABLY NOT CORRECT


def main():
    notfound = []
    
    filename = "dabiglist.txt"
    gamenames = iterCSV(filename)
    #gamenames = ["skyrim", "botw","meat boy","hades","Super Smash Bros brawl"] 
    gamesdict = {}
    ## can use start and end for troubleshooting different parts of the list without going through the whole list
    ## start should be 0 and end should be len(gamenames) once project is ready
    #start = 0
    start = 188 ## right now going through all and checking for errors; up to this number do not raise errors
    end = len(gamenames)
    #end = 50
    for i in range(start, len(gamenames)):
        ## Super Smash Bros Brawl (video game) opens the wiki page for Super Smash Bros (Video game)
        ## going to have to ask the user to choose the wikipedia title from a search for every game
        ## could maybe avoid by doing some clever thing like looking into the page and finding something that would only be in a video game page but idk
        print(f"Index of gamenames list: {i}")
        name = findName(f"{gamenames[i]} (video game)")
        print(name)
        if (name != None):
            gamesdict[name] = findInfo(f"{name}")
            gamesdict[name] = checkdict(gamesdict[name]) ## let user double check and edit if needed
        else:
            notfound.append(gamenames[i])
    #dictprint(gamesdict)
    # for game in gamesdict:
        # for r in gamesdict[game]["Release"]: 
            # list = r.getPlatforms()
            # print(f"Region: {r.region}\nDate: {r.date}\nPlatforms: {list}\n")
    exporttoSQLite(gamesdict)
    print(f"Couldn't find these games: {notfound}")

## replaces &nbsp; with a space and strips any leading or trailing whitespace and returns the cleaned string
def cleanString(string):
    string = string.replace("&nbsp;", " ")
    string = string.strip()
    return string


## documentation linked at the top with the import lines
## personal note: important lesson in class attribute (MyHTMLParser.tbodycount) and instance attribute (self.tbodycount)
##                class attribute is kept even between new instances of the class and instance attributes are reset with a new instance
##                (https://stackoverflow.com/questions/9056957/correct-way-to-define-class-variables-in-python)
class MyHTMLParser(HTMLParser):
    
    ## personal note: elements in init are instance attributes and outside of init are class attributes
    def __init__(self, *, convert_charrefs=True):
        """Initialize and reset this instance.
        If convert_charrefs is True (the default), all character references
        are automatically converted to the corresponding Unicode characters.
        """
        self.convert_charrefs = convert_charrefs
        self.reset()
        
        ## my instance variables
        self.countdown = 0
        self.title = ""
        self.donesearch = True #turns false when it finds a table in html
        self.tbodycount = 0  
        
        self.infodic = {}
        self.infodic.clear()
        self.infodic = {"Director(s)": [],"Publisher(s)": [],"Developer(s)": [],"Producer(s)": [],"Programmer(s)": [],
            "Artist(s)": [],"Writer(s)": [],"Composer(s)": [],"Series": [],"Platform(s)": [],"Release": [],"Genre(s)": [],
            "Mode(s)": [],"Designer(s)": [],"Engine": []}
        
    
    def handle_starttag(self, tag, attrs):
        if (tag == "tbody" and self.tbodycount == 0):
            self.donesearch = False
            self.tbodycount += 1
    
    def handle_endtag(self, tag):
        if (tag == "tbody"): # in every sample I've looked at the first tbody is the table with all the info I want
            self.donesearch = True
        
    def handle_data(self, data):
        if (not self.donesearch):
            if (data in list(self.infodic)):
                self.title = data
            # make sure not making a match with no title or awkward bits of data I don't want
            elif (not (self.title == "" or data[0] in ["[",",","&"] or data in [""," ","\n"])): ## & starts HTML entities like the popular &nbsp; https://mailtrap.io/blog/nbsp/
                self.infodic[self.title].append(cleanString(data))

    def getInfodic():
        return self.infodic


## takes a date like Month, DD, YYYY and returns it formatted like YYYY-MM-DD
def dateFormatter(date):
    monthdict = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06", "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}

    date = date.split() ## default split() catches more whitespace characters than doing split(" ")
    for i in date:
        i = cleanString(i)
        i = i.strip(",")
        ## since dates aren't in a set format, need to search for each part (most are month dd, yyyy but Aviary Attorney is dd month yyyy)
        if bool(re.match("^[0-9]{1,2}$", i)):
            day = i
            print("matched day")
        elif bool(re.match("^[0-9]{4}$", i)):
            year = i
            print("matched year")
        elif i in monthdict:
            month = i
            print("matched month")

    if (len(day) == 1):
        day = ''.join(("0",day)) ## add the zero at beginning 
    month = monthdict[month] ## translates the written month to a string of the number
    date = '-'.join((year,month,day))
    return date


## container for a region, date, and a list of platforms
class Release:
    def __init__(self, region, date, platforms):
        self.region = region
        if (self.region == None):
            self.region = "WW"
        self.date = date
        self.platforms = platforms 
    
    def getPlatforms(self):
        return self.platforms
   
   
## Takes the ugly unformatted information from wikipedia on releases for a game and
## sorts them into a list of Release objects (see above) and returns it
def releaseFormatter(list,totalplatforms):
    releaselist = []
    date = None
    region = None
    myplatforms = []
    altplatformnames = {"Windows": "Microsoft Windows", "PS3": "PlayStation 3", "PS4": "PlayStation 4", "PS5": "PlayStation 5", "PS2": "PlayStation 2"} ## will need updates
    regionnames = ["NA", "JP", "PAL", "WW", "AU", "EU"]                                                                         ## will need updates

    if (len(totalplatforms) == 1):
        myplatforms.append(totalplatforms[0])

    ## check number of things in list
    leng = len(list)
    if leng == 0:
        return

    if (leng == 1):
        ## reformat in the case of one things
        date = dateFormatter(list[0])
        newRelease = Release(region, date, totalplatforms)
        releaselist.append(newRelease)
    else:
        ## sort and reformat all the information in case of multiple things
        start = 0
        ## this first date is just the first release date so it isn't paired with anything and we can ignore it
        if bool(re.match("^\s*\w+\s[0-9]{1,2},\s[0-9]{4}\s*$", list[0])):
            start = 1
        for i in range(start, len(list)):
            ## if region
            #if len(list[i]) == 2: ## assuming re0gions are 2 (jp, na, au, eu, ww)  ### BIG PROBLEM THERE IS THE "PAL" REGION SO NOT ALL 2 LONG
            if (list[i] in regionnames):
                region = list[i]
            ## if date
            elif bool(re.match("^\s*\w+\s[0-9]{1,2},\s[0-9]{4}\s*$", list[i])):   ## someone added a random space infront so now I am allowing whitespace before and after
                ## if already found a date, finish the release object and start a new one
                date = dateFormatter(cleanString(list[i]))
                ## only add if there are platforms in the list
                if (len(myplatforms) > 0):
                    newRelease = Release(region, date, myplatforms.copy())
                    releaselist.append(newRelease)
            mytotalplatforms = []
            myaltplatforms = []
            for p in totalplatforms:
                if list[i].find(p) != -1:
                    mytotalplatforms.append(p)
            if len(mytotalplatforms) > 0:
                myplatforms.clear()
            for ap in altplatformnames:
                if list[i].find(ap) != -1:
                    myaltplatforms.append(altplatformnames[ap])
            if len(myaltplatforms) > 0:
                myplatforms.clear()
            myplatforms.extend(mytotalplatforms)
            myplatforms.extend(myaltplatforms)
    return releaselist


## WIP / Abandoned attempt at a prettyprint for dictionary
def dictprint(mydict, tab = 0):
    for k in mydict:
        for i in range(tab):
            print("\t",end = "")
        print(f"{k}:")
        if (isinstance(mydict[k], dict)):
            dictprint(mydict[k],tab+1)
        else:
            for i in range(tab):
                print("\t",end = "")
            print(f"\t{mydict[k]}")


## originally let user change information in dictionary by hand, now just points towards releaseFormatter
def checkdict(mydict):
    mydict["Release"] = releaseFormatter(mydict["Release"],mydict["Platform(s)"])
    ## EVEN IF NOT USING HERE, COULD STILL BE USEFUL BASE FOR CHANGING THINGS LATER
    ## hand change things
    # print(f"Please look over the data I found and tell me if it looks alright")
    # dictprint(mydict)
    # while(True):
        # ans = input("Does it look correct?(y/n)\n")
        # if (ans == "y"):
            # ## double check
            # ans = input("Are you sure it is correct?(y/n)\n")
            # if (ans == "y"):
                # print(f"Alright, returning dictionary")
                # break
            # else:
                # print(f"Try again")
        # elif (ans == "n"):
            # ## ask if it should open the wikipedia page in a browser
            # ans = input("Would you like the wikipedia page opened in your default browser?(y/n)\n")
            # if (ans == "y"):
                # sugname = wikipedia.search(f"{game} (video game)")
                # pageurl = f"https://en.wikipedia.org/wiki/ {sugname[0]}"
                # webbrowser.open(pageurl, 2, autoraise = True)
            # ## ask to change each item
            # for i in mydict:                
                # print(i)
                # print(mydict[i])
                # if (isinstance(mydict[i],list)):
                    # ## prompt for a list
                    # ans = input("Do you want to change this item?(y/n)\n")
                    # if (ans == "y"):
                        # while True:
                            # inp = input("What should the list be?(formatted: a\\b\\c)\nRemember that dates should be formatted YYYY-MM-DD(Region)")
                            # inp = inp.split("\\")
                            # print(f"You entered this: {inp}")
                            # ans = input("Does that look right?(y/n)\n")
                            # if (ans == "y"):
                                # mydict[i] = inp
                                # break
                # # # should only be lists and strings
                # # else:
                    # # # prompt for single item
                    # # while True:
                        # # inp = input("What should the item be?(enter a single string)")
                        # # print(f"You entered this: {inp}")
                        # # ans = input("Does that look right?(y/n)")
                        # # if (ans == "y"):
                            # # break
            # dictprint(mydict)
            # ## let while loop again to check if it looks correct 
        # else:
            # print(f"I was expecting a 'y' or a 'n'. Try again.")
    return(mydict)
    
   
## iterate through a csv file and splits a given character (or default new line) and returns a list
def iterCSV(filename, split = "\n"):
    file = open(filename)
    rows = re.split(split, file.read())
    print("finished splitting rows")
    return rows


## uses the wikipedia search function to get numresults for a name, asks for the user to pick the 
## correct one, and then returns it; the user can also pick none of the results to return None
def findName(name, numresults = 5):
    print(f"\nSearching for {name}.\nPlease help me choose the correct wikipedia page title.")
    results = wikipedia.search(name, results = numresults, suggestion = False)
    for i in range(len(results)):
        print(f"{i}: {results[i]}")
    print(f"{numresults}: Choose this if no results look correct, there may not be a wikipedia page for this game")
    print(f"{numresults+1}: Choose this if you want to search wikipedia without the \" (video game)\" at the end")
    while True:
        try:
            inp = int(input("Press the number that matches the correct page.\n"))
            if (inp == numresults):
                name = None
                break
            elif (0 <= inp < numresults):
                name = results[inp]
                break
            elif (inp == numresults+1):
                ## search without the (video game) at the end
                name = findName(name.removesuffix(" (video game)"))
                break
            else:
                print("Unexpected input (please enter a digit (ie: 3)")
        except ValueError:
            print("Unexpected input (please enter a digit (ie: 3)")
    return name


## finds the summary from a page on wikipedia and gets a number of paragraphs that defaults to one
## returns a list of the paragraphs
def findSummary(name, numpara=1):
    paragraphs = []
    try:
        paragraphs = re.split("\n", wikipedia.summary(name, auto_suggest=False)) ## summary defaults to auto_suggest=True
    except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError) as error:
        try:
            sugname = wikipedia.search(name) ## can use for miss spelling or wrong page stuff
            paragraphs = re.split("\n", wikipedia.summary(sugname[0], auto_suggest=False))
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError, ValueError, IndexError) as error:
                print("I couldn't find ", name, sugname[0])
    result = []
    for p in range(numpara):
    # try used to avoid the problem of numpar exceeding the number of paragraphs 
        try:
            result.append(cleanString(paragraphs[p]))
        except IndexError:
            break
    return result


## finds the html of a wikipedia page and hand it to MyHTMLParser
## returns a dictionary full of info scraped by MyHTMLParser
def findInfo(name):
    parser = MyHTMLParser()
    info = {}
    info.clear() ## not sure if still need to do this

    print(f"\nI'm looking for {name}\n")
    try:
        myhtml = wikipedia.page(name, auto_suggest = False).html()
    except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError) as error:
        try:
            sugname = wikipedia.search(name) ## can use for miss spelling or wrong page stuff
            myhtml = wikipedia.page(sugname[0], auto_suggest = False).html()
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError, ValueError, IndexError) as error:
                print(f"I couldn't find {name}")
                notfound.append(name)
    parser.feed(myhtml)
    info = parser.infodic
    parser.reset()
    parser.close()
    return info


## takes a mysql cursor, role is a member of list
## INSERTS into tables persons and developmentToRole
def addPerson(cur, role, list, gameID):
    for i in list[f"{role}(s)"]:
            try:
                cur.execute("INSERT INTO persons (name) VALUES (?)", (i,))
                myperson_id = cur.lastrowid
            except (sqlite3.IntegrityError):## if unique contraint failed
                cur.execute("SELECT person_ID FROM persons WHERE name = ?", (i,))
                myperson_id = cur.fetchall()[0][0] 
            try:
                cur.execute("INSERT INTO developmentToRole (game_id, person_id, role) VALUES (?, ?, ?)", (gameID, myperson_id, role))
            except:
                print(f"ERROR! I tried adding gameID: {gameID}, personID: {myperson_id}, and role: {role}")


## ADD REGIONS TO PUBLISHERS?
## takes a mysql cursor, role is a member of list
## INSERTS into tables companies and companyToRole
def addCompany(cur, role, list, gameID):
    regionnames = ["NA", "JP", "PAL", "WW", "AU", "EU"]                                                                         ## will need updates
    region = None
    
    ## do it normally if handling developers 
    if (role == "Developer"):
        for i in list[f"{role}(s)"]:
                try:
                    cur.execute("INSERT INTO companies (name) VALUES (?)", (i,))
                    mycompany_id = cur.lastrowid
                except (sqlite3.IntegrityError):## if unique contraint failed
                    cur.execute("SELECT company_ID FROM companies WHERE name = ?", (i,))
                    mycompany_id = cur.fetchall()[0][0] 
                try:
                    cur.execute("INSERT INTO companyToRole (game_id, company_id, role) VALUES (?, ?, ?)", (gameID, mycompany_id, role))
                except:
                    print(f"ERROR! I tried adding gameID: {gameID}, personID: {mycompany_id}, and role: {role}")
    ## handle publishers; look for regions tied to the publishers
    else:
        for i in list[f"{role}(s)"]:
            ## strip any white space at beginning or end, this lets me match regions with spaces around them and cleans for database entry
            i = i.strip(" ")
            ## making the assumption that if there are regions it will be formatted region : publisher
            if (i in regionnames): 
                region = i
            elif (i != ":"): ## ignore the :
                pub = i 
                try:
                    cur.execute("INSERT INTO companies (name) VALUES (?)", (pub,))
                    mycompany_id = cur.lastrowid
                except (sqlite3.IntegrityError):## if unique contraint failed
                    cur.execute("SELECT company_ID FROM companies WHERE name = ?", (pub,))
                    mycompany_id = cur.fetchall()[0][0] 
                try:
                    cur.execute("INSERT INTO companyToRole (game_id, company_id, role, region) VALUES (?, ?, ?, ?)", (gameID, mycompany_id, role, region))
                except:
                    print(f"ERROR! I tried adding gameID: {gameID}, personID: {mycompany_id}, and role: {role}")
                ## in case the next publisher doesn't have a region, reset region
                region = None
            

## formats the data and sorts out any unneeded data from in mydict
## creates a lot of tables and populates them with information from mydict
def exporttoSQLite(mydict):
    dbname = "MyGamesList\MyGamesListv0-1.db"  #:memory: creates a temporary database, good for testing
    con = sqlite3.connect(dbname)
    cur = con.cursor()
    ## Create tables
    ## this is going to be ugly looking; maybe I can clean up later?
    cur.execute("CREATE TABLE games (game_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, summary TEXT);")
    cur.execute("CREATE TABLE platforms (platform_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);")
    cur.execute("CREATE TABLE genres (genre_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);")
    cur.execute("CREATE TABLE modes (mode_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);")
    cur.execute("CREATE TABLE series (series_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);")
    cur.execute("CREATE TABLE engines (engine_id INTEGER PRIMARY KEY, name TEXT NOT NULL);")
    cur.execute("CREATE TABLE persons (person_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);")
    cur.execute("CREATE TABLE companies (company_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);")
    ## most confusing one so far; dates in format: YYYY-MM-DD
    cur.execute("CREATE TABLE releases (game_id INTEGER, platform_id INTEGER, region TEXT, date TEXT, release_id INTEGER PRIMARY KEY, FOREIGN KEY (game_id) REFERENCES games (game_id), FOREIGN KEY (platform_id) REFERENCES platforms (platform_id));")
    
    
    ## TO DO "ON DELETE" AND "ON UPDATE" ACTIONS FOR FOREIGN KEYS
    cur.execute("CREATE TABLE developmentToRole (game_id INTEGER, person_id INTEGER, role TEXT, PRIMARY KEY (game_id, person_id, role), FOREIGN KEY (game_id) REFERENCES games (game_id), FOREIGN KEY (person_id) REFERENCES persons (person_id));")
    cur.execute("CREATE TABLE companyToRole (game_id INTEGER, company_id INTEGER, role TEXT, region TEXT, PRIMARY KEY (game_id, company_id, role), FOREIGN KEY (game_id) REFERENCES games (game_id), FOREIGN KEY (company_id) REFERENCES companies (company_id));")
    cur.execute("CREATE TABLE genreToGame (game_id INTEGER, genre_id INTEGER, PRIMARY KEY (game_id, genre_id), FOREIGN KEY (game_id) REFERENCES games (game_id), FOREIGN KEY (genre_id) REFERENCES genres (genre_id));")
    cur.execute("CREATE TABLE modeToGame (game_id INTEGER, mode_id INTEGER, PRIMARY KEY (game_id, mode_id), FOREIGN KEY (game_id) REFERENCES games (game_id), FOREIGN KEY (mode_id) REFERENCES modes (mode_id));")
    cur.execute("CREATE TABLE seriesToGame (game_id INTEGER, series_id INTEGER, PRIMARY KEY (game_id, series_id), FOREIGN KEY (game_id) REFERENCES games (game_id), FOREIGN KEY (series_id) REFERENCES series (series_id));")
    cur.execute("CREATE TABLE engineToGame (game_id INTEGER, engine_id INTEGER, PRIMARY KEY (game_id, engine_id), FOREIGN KEY (game_id) REFERENCES games (game_id), FOREIGN KEY (engine_id) REFERENCES engines (engine_id));")
    ## for now I am only user so don't need to add a reference to a user yet; would also have to make a users table
    ## can add stuff like amount paid, date added, etc later
    cur.execute("CREATE TABLE userToRelease (release_id INTEGER, status TEXT NOT NULL, score INTEGER, userToRelease_id INTEGER PRIMARY KEY, FOREIGN KEY (release_id) REFERENCES releases (release_id));")

    ## Populate tables
    # "Director(s)": [],"Publisher(s)": [],"Developer(s)": [],"Producer(s)": [],"Programmer(s)": [],
            # "Artist(s)": [],"Writer(s)": [],"Composer(s)": [],"Series": [],"Platform(s)": [],"Release": [],"Genre(s)": [],
            # "Mode(s)": [],"Designer(s)": [],"Engine": []}
    for game in mydict:
        summary = str(findSummary(game))
        cur.execute("INSERT INTO games (name, summary) VALUES (?, ?)", (game, summary))
        ## grab gameID to use in future INSERTS
        mygame_id = cur.lastrowid
        ## handle people
        for role in ["Director", "Producer", "Programmer", "Artist", "Writer", "Composer", "Designer"]:
            addPerson(cur, role, mydict[game], mygame_id)
        ## handle companies
        ## ADD REGIONS TO PUBLISHERS?
        for role in ["Publisher", "Developer"]:
            addCompany(cur, role, mydict[game], mygame_id)
        ## add genre, mode, series,engine
        for i in mydict[game]["Genre(s)"]:
            try:
                cur.execute("INSERT INTO genres (name) VALUES (?)", (i,))
                mygenre_id = cur.lastrowid
            except (sqlite3.IntegrityError):## if unique contraint failed
                cur.execute("SELECT genre_id FROM genres WHERE name = ?", (i,))
                mygenre_id = cur.fetchall()[0][0] 
            try:
                cur.execute("INSERT INTO genreToGame (game_id, genre_id) VALUES (?, ?)", (mygame_id, mygenre_id))
            except:
                print(f"ERROR adding genre!")
        for i in mydict[game]["Mode(s)"]:
            try:
                cur.execute("INSERT INTO modes (name) VALUES (?)", (i,))
                mymode_id = cur.lastrowid
            except (sqlite3.IntegrityError):## if unique contraint failed
                cur.execute("SELECT mode_id FROM modes WHERE name = ?", (i,))
                mymode_id = cur.fetchall()[0][0] 
            try:
                cur.execute("INSERT INTO modeToGame (game_id, mode_id) VALUES (?, ?)", (mygame_id, mymode_id))
            except:
                print(f"ERROR adding mode!")
        for i in mydict[game]["Series"]:
            try:
                cur.execute("INSERT INTO series (name) VALUES (?)", (i,))
                myseries_id = cur.lastrowid
            except (sqlite3.IntegrityError):## if unique contraint failed
                cur.execute("SELECT series_id FROM series WHERE name = ?", (i,))
                myseries_id = cur.fetchall()[0][0] 
            try:
                cur.execute("INSERT INTO seriesToGame (game_id, series_id) VALUES (?, ?)", (mygame_id, myseries_id))
            except:
                print(f"ERROR adding series!")
        for i in mydict[game]["Engine"]:
            try:
                cur.execute("INSERT INTO engines (name) VALUES (?)", (i,))
                myengine_id = cur.lastrowid
            except (sqlite3.IntegrityError):## if unique contraint failed
                cur.execute("SELECT engine_id FROM engines WHERE name = ?", (i,))
                myengine_id = cur.fetchall()[0][0] 
            try:
                cur.execute("INSERT INTO engineToGame (game_id, engine_id) VALUES (?, ?)", (mygame_id, myengine_id))
            except:
                print(f"ERROR adding engine!")
        ## only add new platforms into platform table
        for i in mydict[game]["Platform(s)"]:
            try:
                cur.execute("INSERT INTO platforms (name) VALUES (?)", (i,))
                #myplatform_id = cur.lastrowid
            except (sqlite3.IntegrityError): ## if unique contraint failed
                ## adding platforms to games happens in the release table
                pass
        for i in range(len(mydict[game]["Release"])):
            for p in mydict[game]["Release"][i].platforms:
                #try:
                cur.execute("SELECT platform_id FROM platforms WHERE name = ?", (p,))
                myplatform_id = cur.fetchall()[0][0]
                cur.execute("INSERT INTO releases (game_id, platform_id, region, date) VALUES (?, ?, ?, ?)", (mygame_id, myplatform_id, mydict[game]["Release"][i].region, mydict[game]["Release"][i].date))
                #except:
                    #print("ERROR ADDING RELEASE")

    ## Commit changes
    con.commit()

    ## do some queries to check db while we have con open
    queries(con)
    
    ## Close connection
    con.close()


def queries(con):
    ## Test some queries
    #cur.execute("SELECT * FROM games")
    #print(cur.fetchall())
    print(pd.read_sql_query("SELECT game_id, name FROM games", con))
    #print(pd.read_sql_query("SELECT * FROM persons", con))
    #print(pd.read_sql_query("SELECT * FROM developmentToRole", con))
    #print(pd.read_sql_query("SELECT * FROM companies", con))
    #print(pd.read_sql_query("SELECT * FROM companyToRole", con))
    #print(pd.read_sql_query("SELECT * FROM series", con))
    #print(pd.read_sql_query("SELECT * FROM modes", con))
    #print(pd.read_sql_query("SELECT * FROM genres", con))
    ## INNER JOIN going to be my best friend for these relational tables
    print(pd.read_sql_query("SELECT games.name, series.name FROM seriesToGame INNER JOIN games USING (game_id) INNER JOIN series USING (series_id)", con))
    print(pd.read_sql_query("SELECT games.name, platforms.name, date, releases.region FROM releases INNER JOIN games USING (game_id) INNER JOIN platforms USING (platform_id)", con))
    #print(pd.read_sql_query("SELECT * FROM modeToGame", con))
    #print(pd.read_sql_query("SELECT * FROM genreToGame", con))


if __name__ == '__main__': ## note to self: https://www.youtube.com/watch?v=g_wlZ9IhbTs
    main()



## class = infobox hproduct