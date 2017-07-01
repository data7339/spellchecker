import urllib.request
from bs4 import BeautifulSoup
import enchant
import re
import feedparser
from nltk.tokenize import sent_tokenize, word_tokenize
import dataset
import datetime

db = dataset.connect('sqlite:///:memory:')

def get_url():

    url_list = []
    # RSS with latest news
    d = feedparser.parse('http://www.dn.se/rss/senaste-nytt/')
    # Max quantity is 39, using 5 to show how code works
    number_of_articles = 39
    for i in range(number_of_articles):
        url = str(d.entries[i].link)
        # Saving URLs of latest news to a list
        url_list.append(url)
    get_article(number_of_articles, url_list)

def get_article(number_of_articles, url_list):

    for i in range(number_of_articles):
        url = url_list[i]

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read()
        soup = BeautifulSoup(html, "html.parser")
        article_data = soup.find("div", {'class':'js-article'})
        title = article_data["data-article-title"]
        date = article_data["data-article-publish-date"]
        time = article_data["data-article-publish-time"]
        author = article_data["data-authors"]
        main_section = article_data["data-article-main-section"]
        sub_section = article_data["data-article-sub-section"]

        text_file = open("article.txt", "w")

        for article_body in soup.findAll('div',{'class':'article__body-content'}):
            text_file.write(str(article_body) + "\n")
        text_file.close()
        
        clean_up_article(url, title, date, author)
        

def clean_up_article(url, title, date, author):

    number_of_words = 0
    words = []

    f = open('article.txt','r')
    lst = []
    for line in f:
        line = re.sub(r'\<script>.*?\</script>', '', line)
        line = re.sub(r'\<.*?\>', '', line)
        for word in line.split():
                 number_of_words += 1
        lst.append(line)
    f.close()

    f = open('article.txt','w')
    for line in lst:
        f.write(line)
    f.close()

    f = open('article.txt','r').read()
    tokens = word_tokenize(f)

    typos = []
    d = enchant.Dict("sv_SE")
    for word in tokens:
        chkr = d.check(word)
        if chkr == False:
            typos.append(word)

    # Remove weird signs
    while "." in typos: typos.remove(".")
    while "," in typos: typos.remove(",")
    while "``" in typos: typos.remove("``")
    while "''" in typos: typos.remove("''")

    # Since Swedish spellcheckers for Python aren't that advanced some innovative
    # solutions hade to be made. If the word starts with a capital letter it is automatically
    # seen as correct as there are so many names and cities that isn't included in 
    # enchants dictionary.
    typos = [word for word in typos if word[0].islower()]  
    number_of_typos = len(typos)

    # print("Typos: " + str(typos))
    # print("Number of typos: " + str(number_of_typos))
    # print("Number of words: " + str(number_of_words))
    # if not number_of_words == 0:
    #     print("Percent of typos: " + str(100 * number_of_typos/number_of_words) + " %")
    # if number_of_words == 0:
    #     print("Something wrong, no words...")

    current_time = str(datetime.datetime.today())
    current_time = current_time[:10]+'_'+current_time[11:16]
    #print(current_time)

    table_typos = db['typso']
    
    table_typos.insert(dict(url=str(url), title=str(title), author=str(author), number_of_typos=number_of_typos, number_of_words=number_of_words, typos=str(typos)))

    result = db['typso'].all()
    dataset.freeze(result, format='csv', filename=current_time + 'spell_check.csv')

get_url()





