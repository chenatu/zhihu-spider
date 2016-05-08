import urllib.request
import http.cookiejar
from string import Template
from bs4 import BeautifulSoup
import json
import re
import time
from random import *
import csv
import codecs

headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94 Safari/537.36',
          'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
          'X-Requested-With':'XMLHttpRequest',
          'Referer':'https://www.zhihu.com/topics',
          'Cookie':'' 
          }

PAGESIZE = 20
TIMEOUT = 30
WAITPERIOD = 10

class Topic(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Person():
    upvote = 0
    thanks = 0
    link = ''
    askCount = 0
    answerCount = 0
    postCount = 0
    collectionCount = 0
    followees = 0
    followers = 0
    gender = True # True for male and False for female
    
    def __init__(self, id, topic):
        self.id = id
        self.topic = topic
        self.link = 'https://www.zhihu.com/people/' + id

    
class Answer():
    content = ''
    def __init__(self, id, questionId, person, topic):
        self.id = id
        self.questionId = questionId
        self.person = person
        self.topic = topic
        self.link = 'https://www.zhihu.com/question/' + questionId + '/answer/' + id

def makeMyOpener(head = {
    'Connection': 'Keep-Alive',
    'Accept': 'text/html, application/xhtml+xml, */*',
    'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko'
}):
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    header = []
    for key, value in head.items():
        elem = (key, value)
        header.append(elem)
    opener.addheaders = header
    return opener

def getTopics():
    zhihuTopics = []
    url = 'https://www.zhihu.com/topics'
    opener = makeMyOpener()
    page = opener.open(url, timeout = TIMEOUT).read().decode('UTF-8')
    pattern = re.compile('<li.*?data-id="(.*?)"><a.*?>(.*?)</a></li>', re.S)
    results = re.findall(pattern, page)
    for result in results:
        topic = Topic(result[0],result[1])
        zhihuTopics.append(topic)
    return zhihuTopics

def getSubTopics(topic):
    subTopics = []
    url = 'https://www.zhihu.com/node/TopicsPlazzaListV2'
    offset = -20;
    isGet = True
    while isGet:
        offset = offset + 20
        values = {'method': 'next', 'params': '{"topic_id":'+topic.id+',"offset":'+str(offset)+',"hash_id":""}'}
        data = urllib.parse.urlencode(values).encode(encoding='utf_8', errors='strict')
        opener = makeMyOpener(headers)
        page = opener.open(url, data, TIMEOUT).read().decode('UTF-8')
        json_str = json.loads(page)
        topicMsg = '.'.join(json_str['msg'])
        pattern = re.compile('<a.*?href="/topic/(.*?)">.*?<strong>(.*?)</strong>.*?</a>', re.S)
        results = re.findall(pattern, topicMsg)
        if len(results) ==0:
                isGet = False
        for result in results:
            topic = Topic(result[0],result[1])
            subTopics.append(topic)
    return subTopics
    

def getFirstSubTopic(topic):
    url = 'https://www.zhihu.com/node/TopicsPlazzaListV2'
    subTopics = ""
    values = {'method': 'next', 'params': '{"topic_id":'+topic.id+',"offset":'+str(0)+',"hash_id":""}'}
    data = urllib.parse.urlencode(values).encode(encoding='utf_8', errors='strict')
    opener = makeMyOpener()
    page = opener.open(url, data, TIMEOUT).read().decode()
    json_str = json.loads(page)
    topicMsg = '.'.join(json_str['msg'])
    pattern = re.compile('<a.*?href="/topic/(.*?)">.*?<strong>(.*?)</strong>.*?</a>', re.S)
    results = re.findall(pattern, topicMsg)
    topic = Topic(results[0][0], results[0][1])
    return topic

def getTopicBestPeople(topic):
    people = []
    url = 'https://www.zhihu.com/topic/' + topic.id + '/hot'
    opener = makeMyOpener(headers)
    page = opener.open(url, timeout = TIMEOUT).read().decode()
    soup = BeautifulSoup(page, 'lxml')
    personItems = soup.find_all('div', class_='zm-topic-side-person-item')
    for personItem in personItems:
        personId = personItem.a['href'][8:]
        person = Person(personId, topic)
        people.append(person)
    return people

# the id and topic of person has been initialized
def getPersonInfo(person):
    url = 'https://www.zhihu.com/people/' + person.id
    opener = makeMyOpener(headers)
    page = opener.open(url, timeout = TIMEOUT).read().decode()
    soup = BeautifulSoup(page, 'lxml')
    upvoteTag = soup.find('span', class_='zm-profile-header-user-agree')
    person.upvote = int(upvoteTag.strong.get_text())
    thanksTag = soup.find('span', class_='zm-profile-header-user-thanks')
    person.thanks = int(thanksTag.strong.get_text())
    askCountTag = soup.find('a', attrs={'href' : '/people/' + person.id + '/asks'})
    person.askCount = int(askCountTag.span.get_text())
    answerCountTag = soup.find('a', attrs={'href' : '/people/' + person.id + '/answers'})
    person.answerCount = int(answerCountTag.span.get_text())
    postCountTag = soup.find('a', attrs={'href' : '/people/' + person.id + '/posts'})
    person.postCount = int(postCountTag.span.get_text())
    collectionCountTag = soup.find('a', attrs={'href' : '/people/' + person.id + '/collections'})
    person.collectionCount = int(collectionCountTag.span.get_text())
    followeesTag = soup.find('a', attrs={'href' : '/people/' + person.id + '/followees'})
    person.followees = int(followeesTag.strong.get_text())
    followersTag = soup.find('a', attrs={'href' : '/people/' + person.id + '/followers'})
    person.followers = int(followersTag.strong.get_text())
    # TODO get gender
    return person
    
def getAnswerByDefaultOrder(person, index):
    pageNo = index // PAGESIZE + 1
    indexInPage = index % PAGESIZE
    url = 'https://www.zhihu.com/people/' + person.id + '/answers?page=' + str(pageNo)
    opener = makeMyOpener(headers)
    page = opener.open(url, timeout = TIMEOUT).read().decode()
    soup = BeautifulSoup(page, 'lxml')
    answerTags = soup.find_all('a', class_='question_link')
    answerTag = answerTags[indexInPage - 1]
    answerLink = answerTag['href']
    answerLinkConponents = answerLink.split('/')
    questionId = answerLinkConponents[2]
    answerId = answerLinkConponents[4]
    return Answer(answerId, questionId, person, person.topic)

def getAnswerContent(answer):
    url = 'https://www.zhihu.com/question/' + answer.questionId + '/answer/' + answer.id
    opener = makeMyOpener(headers)
    page = opener.open(url, timeout = TIMEOUT).read().decode()
    soup = BeautifulSoup(page, 'lxml')
    answerContentTag = soup.find('div', class_='zm-editable-content clearfix')
    answerContent = answerContentTag.get_text()
    answer.content = answerContent
    return answer
    
def selectData(data):
    if data != []:
        pos = randrange( len(data) )
        elem = data[pos]
        data[pos] = data[-1]
        del data[-1]
        return elem
    else:
        return None
    
def selectMultipleData(data, count):
    elems = []
    for i in range(count):
        elem = selectData(data)
        if elem is not None:
            elems.append(elem)
        else:
            break
    return elems

def main():
    peoplefile = codecs.open('people.csv', 'a', 'utf-8')
    peoplefilewriter = csv.writer(peoplefile)
    # peoplefilewriter.writerow(['personId', 'topicId', 'topicName', 'upvote', 'thanks', 'link', 'askCount', 'answerCount', 'postCount', 'collectionCount', 'followees', 'followers'])
    
    answersfile = codecs.open('answers.csv', 'a', 'utf-8')
    answersfilefilewriter = csv.writer(answersfile)
    # answersfilefilewriter.writerow(['answerId', 'questionId', 'link', 'topicId', 'topicName', 'personId', 'personLink', 'content'])
    
    zhihuTopics = getTopics()
    print(zhihuTopics)
    totalAnswers = []
    totalPeople = []
    for i in range(len(zhihuTopics)):
        zhihuTopic = zhihuTopics[i]
        subTopic = getFirstSubTopic(zhihuTopic)
        print(subTopic.id + ' ' + subTopic.name)
        people = getTopicBestPeople(subTopic)
        for person in people:
            getPersonInfo(person)
            time.sleep(WAITPERIOD)
            peoplefilewriter.writerow([person.id, person.topic.id, person.topic.name, str(person.upvote), str(person.thanks), person.link, str(person.askCount), str(person.answerCount), str(person.postCount), str(person.collectionCount), str(person.followees), str(person.followers)])
            elems = selectMultipleData(list(range(person.answerCount)), 2)
            for elem in elems:
                answer = getAnswerByDefaultOrder(person, elem + 1)
                time.sleep(WAITPERIOD)
                getAnswerContent(answer)
                answersfilefilewriter.writerow([answer.id, answer.questionId, answer.link, answer.topic.id, answer.topic.name, answer.person.id, answer.person.link, answer.content])
                time.sleep(WAITPERIOD)
                totalAnswers.append(answer)
            totalPeople.append(person)

                
        
if __name__ == '__main__':
	main()