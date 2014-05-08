#!/usr/bin/python

from ReddiWrap import ReddiWrap
import MySQLdb
from scikits.crab import datasets
from scikits.crab.models import MatrixPreferenceDataModel
from scikits.crab.metrics import pearson_correlation
from scikits.crab.similarities import UserSimilarity
from scikits.crab.recommenders.knn import UserBasedRecommender
### used for sorting
from operator import itemgetter

#####################used for outputting data model to file
import sys
import os

def printToFile(text,filename):
    f = open(os.getcwd()+'/'+filename+'.txt', 'w')
    sys.stdout = f
    print text
    sys.stdout = sys.__stdout__
#####################Crab Recommender needs a *Bunch* class to work with,
#####################so the next few parts are to do with making those    
class Bunch(dict):
    """
    Container object for datasets: dictionary-like object
    that exposes its keys and attributes. """
    
    def __init__(self,*args, **kwargs):
##        for count, thing in enumerate(args):
##            print 'args '+ '{0}. {1}'.format(count, thing)
##        for name, value in kwargs.items():
##            print 'kwargs' +'{0} = {1}'.format(name, value)
        dict.__init__(self, kwargs)
        self.__dict__ = self

def createBunchFromKeyValue(key,value):
    d = dict({key:value})
    b = Bunch()
    b.update(d)
    return b

def convertTuplesOfKeyValueToDictionary(tuples):
    dictionary = {}
    for t in tuples:
        key = int(t[0])
        value = t[1]
        dictionary.update({key:value})
    return dictionary

def convertDictionaryToBunch(dictionary):
    b = Bunch()
    for key, value in dictionary.iteritems() :
        b.update(createBunchFromKeyValue(key,value))
    return b

def getBunchForTupleList(tuples):    
#convert a tuple(key/value or in this case user/vote) e.g. from the cursor, to a
#we then take each key/value pair in the dictionary and converting them to Bunches
#Finally we add them all into the Bunch b and return it
    dictionary = convertTuplesOfKeyValueToDictionary(tuples)
##    print 'dictionary'
##    print dictionary
    b = convertDictionaryToBunch(dictionary)
##    print 'Bunch'
##    print b
    return b

#########################Recommender    
def recommendPosts(dataModel):
    model = MatrixPreferenceDataModel(dataModel)
    print 'User ID`s: '
    print model.user_ids()
##    print 'Item ID`s: '
##    print model.item_ids()
    userID= input('Please enter a userID: ')
    print 'Loading recommended posts...'
    similarity = UserSimilarity(model, pearson_correlation)
    recommender = UserBasedRecommender(model, similarity, with_preference=True)
    return recommender.recommend(userID)

######################SQL Statements to execute
        
def findUserID(cursor,username):
        cursor.execute("SELECT `UserID` FROM `Users` WHERE `Username`=%s LIMIT 1",[username])
        if cursor.rowcount != 0:
                return int(cursor.fetchone()[0])
        else:
                return -1
def findSubredditID(cursor,subreddit):
        cursor.execute("SELECT `SubredditID` FROM `Subreddits` WHERE `Subreddit`=%s LIMIT 1",[subreddit])
        if cursor.rowcount != 0:
                return int(cursor.fetchone()[0])
        else:
                return -1

def getPostsUserVotes(cursor, postID):
    cursor.execute("SELECT `UserID`, `Vote` FROM `Votes` WHERE `PostID`=%s",(postID))
    if cursor.rowcount != 0:
        data = cursor.fetchall()
        return data
    else:
        return -1

def getUsersVoteHistory(cursor, userID):
    cursor.execute("SELECT `PostID`, `Vote` FROM `Votes` WHERE `UserID`=%s",(userID))
    if cursor.rowcount != 0:
        data = cursor.fetchall()
        return data
    else:
        return -1

def getUsersWhoVotedOnAPost(cursor, postID):
    cursor.execute("SELECT `UserID` FROM `Votes` WHERE `PostID`=%s",(postID))
    if cursor.rowcount != 0:
        data = cursor.fetchall()
        return data
    else:
        return -1
    

def addPostToDatabase(post):
    #Convert these from unicode to ascii (we may lose special characters). Not sure if necessary if we're not printing the strings...
    Title = post.title.encode('ascii', 'ignore')
    Username = post.author.encode('ascii', 'ignore')
    UserID = findUserID(cursor,Username)
    Subreddit = post.subreddit.encode('ascii', 'ignore')
    SubredditID = findSubredditID(cursor,Subreddit)

    if UserID == -1:        #New user, add to Users table
            cursor.execute("INSERT INTO `Users` (`Username`) VALUES (%s)",(Username))
            db.commit()
            cursor.execute("SELECT LAST_INSERT_ID()")
            UserID = int(cursor.fetchone()[0])
    if SubredditID == -1:   #New subreddit, add to Subreddit table
            cursor.execute("INSERT INTO `Subreddits` (`Subreddit`) VALUES (%s)",(Subreddit))
            db.commit()
            cursor.execute("SELECT LAST_INSERT_ID()")
            SubredditID = int(cursor.fetchone()[0])

    cursor.execute("INSERT INTO `Posts` (`Title`,`UserID`,`SubredditID`) VALUES (%s,%s,%s)",(Title,UserID,SubredditID))
    
def searchForPostIDInDatabase(post,cursor):
    Title = post.title.encode('ascii', 'ignore')
    cursor.execute("SELECT PostID FROM Posts WHERE Title = (%s) LIMIT 1",(Title))
    data = cursor.fetchall()    
    #print data
    while data:
        postID = [int(i[0]) for i in data]
        return int(postID[0])
    else:
        return False
     
#Copy 'n paste from reddiwrap examples...
reddit = ReddiWrap(user_agent='ReddiWrap')

USERNAME = ''
PASSWORD = ''
MOD_SUB  = '' # A subreddit moderated by USERNAME

# Load cookies from local file and verify cookies are valid
reddit.load_cookies('cookies.txt')

# If we had no cookies, or cookies were invalid, 
# or the user we are logging into wasn't in the cookie file:
if not reddit.logged_in or reddit.user.lower() != USERNAME.lower():
        print('logging into %s' % USERNAME)
        login = reddit.login(user=USERNAME, password=PASSWORD)
        if login != 0:
                # 1 means invalid password, 2 means rate limited, -1 means unexpected error
                print('unable to log in: %d' % login)
                print('remember to change USERNAME and PASSWORD')
                exit(1)
        # Save cookies so we won't have to log in again later
        reddit.save_cookies('cookies.txt')

print('logged in as %s' % reddit.user)

uinfo = reddit.user_info()
print('\nlink karma:    %d' % uinfo.link_karma)
print('comment karma: %d' % uinfo.comment_karma)
created = int(uinfo.created)
print('account created on:  %s' % reddit.time_to_date(created))
print('time since creation: %s\n' % reddit.time_since(created))

# MySQL Stuff!!
#Connect(host,username,password,database)
db = MySQLdb.connect("URL","USER","PASSWORD","DBNAME")
#Prepare the "cursor" whatever that is
cursor = db.cursor()


searchTerm = raw_input('Please enter a search term: ')
redditSearch = reddit.search(searchTerm)

DataModel = Bunch()
listOfPostID = []
for post in redditSearch:
    #addPostToDatabase(post)
    print post
    postID = searchForPostIDInDatabase(post,cursor)
    listOfPostID.append(postID)
    if(postID):
        Users = getUsersWhoVotedOnAPost(cursor,postID)
        for user in Users:
            userID = int(user[0])
            userVoteHistory = getUsersVoteHistory(cursor,userID)
            userVoteHistoryBunch = getBunchForTupleList(userVoteHistory)
            DataModel.update({userID:userVoteHistoryBunch})
            
##Get logged in users name, get user id for users name
currentUserID = findUserID(cursor,reddit.user)
##Get logged in users vote history and convert to bunch and update datamodel with it
currentUserVoteHistory = getUsersVoteHistory(cursor,userID)
currentUserVoteHistoryBunch = getBunchForTupleList(currentUserVoteHistory)
DataModel.update({currentUserID:currentUserVoteHistoryBunch}

#Commit and close connection to database
db.commit()
db.close()

printToFile(DataModel,'datamodel')
recommendedPosts =  recommendPosts(DataModel)
print 'recommended posts'
for post in recommendedPosts:
    print post
recommendedSearchPosts = []


# MySQL Stuff!!
#Connect(host,username,password,database)
db = MySQLdb.connect("URL","USER","PASSWORD","DBNAME")
#Prepare the "cursor" whatever that is
cursor = db.cursor()


for (recommendedPostID,score) in recommendedPosts:
    for post in redditSearch:
        postID = searchForPostIDInDatabase(post,cursor)
        if (recommendedPostID == postID):
            recommendedSearchPosts.append((post,score,postID))
print 'recommended search posts'
for post in recommendedSearchPosts:
    print post

#Commit and close connection to database
db.commit()
db.close()

####Generate inverse rank for posts and then zip them
rank = range(1,26)
rank.reverse()
zipped = zip(redditSearch, rank,listOfPostID)
rankedPosts = []
print 'zipped posts'
for post in zipped:
    print post
######Apply the score to the rank, if score not present then half the rank, finally add to new list
for (recommendedPost,score,recommendedPostID) in recommendedSearchPosts:
    for (post,rank,postID) in zipped:
        print recommendedPostID
        print postID
        if (recommendedPostID == postID):
            rank = (rank * score)
        else:
            rank = (rank * 0.5)
        if post not in [x[0] for x in rankedPosts]:
             rankedPosts.append((post,rank))
print 'ranked and scored posts'
for post in rankedPosts:
    print post 
#######REORDER THE POSTS BASED ON RANKED SCORE
sortedPosts = sorted(rankedPosts,key=itemgetter(1))
sortedPosts.reverse()
print 'ranked, scored, and sorted zipped posts'
for post in sortedPosts:
    print post
#########UNZIP
rankedSortedposts,rank,postID = zip(*sortedPosts)
######PRINT
print 'Final re-ranked posts'
for post in rankedSortedposts:
    print post