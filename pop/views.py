# Scraping
import json
import time
import pandas as pd
import requests
import sqlite3
import mpld3
import matplotlib.pyplot as plt
import FinanceDataReader as fdr
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import datetime , timedelta
from dateutil.relativedelta import relativedelta


# Deep Learning
# [설치]CUDA 설치 참조 : https://chancoding.tistory.com/89
# [설치]Cuda toolkit 설치 : https://developer.nvidia.com/cuda-toolkit-archive
# [설치]cuDNN 설치 참조 : https://webnautes.tistory.com/1423

# [에러]cudart64_110.dll not found 에러 : https://goddessbest-qa.tistory.com/47
# [에러]오른쪽 오류시 아래링크 참조 :  _jpype.cp36-win_amd64.pyd already loaded in another classloader
# https://byeon-sg.tistory.com/entry/%EC%9E%90%EC%97%B0%EC%96%B4-%EC%B2%98%EB%A6%AC-konlpy-%EC%84%A4%EC%B9%98-%EC%98%A4%EB%A5%98-okt%EC%97%90%EB%9F%AC-already-loaded-in-another-classloader-SystemErro-1
# [에러] _jpype.cp36-win_amd64.pyd already loaded in another classloader 아래 링크 참조
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#jpype

import numpy as np
import tensorflow as tf
import pickle
import konlpy


# Proccess
from django.shortcuts import render
from django.http import HttpResponse


print('서버시작')

now = datetime.now()
gap = now - timedelta(days=10)
yesterday = now - timedelta(days=1)

now = str(now)[0:10]
gap = str(gap)[0:10]
year = str(now)[0:5]
yesterday = str(yesterday)[0:10]

df_krx = fdr.StockListing('KRX')
df_krx = df_krx.fillna('no')
df_krx_list = df_krx['Name'].tolist()

company_info = df_krx[['Name','Symbol','Market','Sector','Industry','ListingDate','SettleMonth','Representative','Region','HomePage']]
company_list = company_info.values.tolist()

ks11 = fdr.DataReader('KS11', year)
kq11 = fdr.DataReader('KQ11', year)

ks11_date = ks11.index
kq11_date = kq11.index
ks11_close = ks11['Close']
kq11_close = kq11['Close']

# print('올해 ks11 그래프 생성')
ks11_plt = plt.figure()
plt.plot(ks11_date, ks11_close)
graph_ks11 = mpld3.fig_to_html(ks11_plt , figid='THIS_IS_FIGID')
file = open('./pop/templates/graph_ks11.html','w',encoding='UTF-8')
file.write(graph_ks11)
#
# print('올해 kq11 그래프 생성')
kq11_plt = plt.figure()
plt.plot(kq11_date, kq11_close)
graph_kq11 = mpld3.fig_to_html(kq11_plt , figid='THIS_IS_FIGID')
file = open('./pop/templates/graph_kq11.html','w',encoding='UTF-8')
file.write(graph_kq11)


def item_code_by_item_name(item_name):
    # 종목명을 받아 종목코드를 찾아 반환하는 함수
    item_code_list = df_krx.loc[df_krx["Name"] == item_name, "Symbol"].tolist()
    if len(item_code_list) > 0:
        item_code = item_code_list[0]
        return item_code
    else:
        return False
        # 예외처리

def scrap_company_stock():

    now = datetime.now()
    # gap = now - relativedelta(years=2)
    gap = now - timedelta(days=1)

    now = str(now)[0:10]
    gap = str(gap)[0:10]

    dt_index = pd.date_range(start=gap, end=gap)
    dt_list = dt_index.strftime("%Y%m%d").tolist()

    conn = sqlite3.connect('./db.sqlite3')
    c_select = conn.cursor()
    c_insert = conn.cursor()

    yesterday_data = c_select.execute(
        "SELECT title , date , time , stock , press , posi_nega , link FROM article where date ='" + gap + "' order by date desc , time desc")
    df = pd.DataFrame(yesterday_data)

    if len(df) != 0:
        df.columns = ['title', 'date', 'time', 'stock', 'press', 'posi_nega' , 'link']
        df_list = df['title'].values.tolist()
    else:
        df_list = []

    def search_title(title):

        okt = konlpy.tag.Okt()

        new_sentence = okt.morphs(title, stem=True)
        new_sentence = [tok for tok in new_sentence if tok not in stopwords]

        vob_size = len(tokenizer.word_index)

        encoded = tokenizer.texts_to_sequences([new_sentence])
        pad_new = tf.keras.preprocessing.sequence.pad_sequences(encoded, maxlen=50)

        score = model.predict(pad_new)
        acp = np.argmax(score)

        # if acp == 0:
        #     print('부정')
        # elif acp == 1:
        #     print('중립')
        # else:
        #     print('긍정')

        return acp

    stopwords = pickle.load(open('./pop/process/stopwords.pkl', 'rb'))
    tokenizer = pickle.load(open('./pop/process/tokenizer.pkl', 'rb'))
    model = tf.keras.models.load_model('./pop/process/posnev.h5')

    for j in dt_list:

        date_cnt_uri = 'https://finance.naver.com/news/news_list.nhn?mode=LSS3D&section_id=101&section_id2=258&section_id3=402&date=' + j + '&page=100'
        date_cnt_target = date_cnt_uri
        date_cnt_req = requests.get(date_cnt_target)
        date_cnt_soup = BeautifulSoup(date_cnt_req.content, 'html.parser')
        date_cnt_page = int(date_cnt_soup.select('td.on > a ')[0].get_text())

        uri = 'https://finance.naver.com/news/news_list.nhn?mode=LSS3D&section_id=101&section_id2=258&section_id3=402&date=' + j + '&page='

        df_krx_list = df_krx['Name'].tolist()

        for page in range(1, date_cnt_page + 1):

            target = uri + str(page)
            req = requests.get(target)
            soup = BeautifulSoup(req.content, 'html.parser')
            datas = soup.select('#contentarea_left > ul.realtimeNewsList')

            for content in datas:

                titles = content.select(' li > dl > dd.articleSubject')
                article_date = content.select('li > dl > dd.articleSummary > span.wdate ')
                article_press = content.select('li > dl > dd.articleSummary > span.press ')
                article_link = content.select('li > dl > dd.articleSubject > a ')

                article_sum = list()

                for i in range(0, len(titles) - 1):
                    article_data = list()

                    data_date = article_date[i].get_text(" ", strip=True)[0:10]
                    data_time = article_date[i].get_text(" ", strip=True)[11:17]
                    data_press = article_press[i].get_text(" ", strip=True)
                    data_title = titles[i].get_text(" ", strip=True)
                    data_link = "https://finance.naver.com" + article_link[i]["href"]
                    data_link = data_link.replace('§','&')

                    data_stock = 'stock'
                    for i in range(0, len(data_title.split())):

                        data_title_splt = ''.join(filter(str.isalnum, data_title.split()[i])) # 특수문자 제거

                        if data_title_splt in df_krx_list:
                            data_stock = data_title_splt

                    data_posi_nega = str(search_title(data_title))
                    # print(data_title,data_stock,data_posi_nega)

                    if data_title not in df_list and data_stock != 'stock':
                        c_insert.execute( "INSERT INTO article( date , time , press , title, stock , posi_nega ,link ) VALUES(?,?,?,?,?,?,?)", (data_date, data_time, data_press, data_title, data_stock, data_posi_nega, data_link))
                        conn.commit()
                        print( data_date, data_time, data_press, data_title, data_stock, data_posi_nega, data_link )
                        print('DB저장완료')
    print('스크랩 완료')

# 기업 종목 관련 어제 기사 스크랩
print('기업 종목 관련 어제 기사 스크랩')
scrap_company_stock()

# 장중 기사 스크랩
# print('장중 기사 스크랩')
# scrap_market()

# 장중 기사 스크랩
# print('장중 기사 스크랩')
# scrap_market()


def index(request):

    now = datetime.now()
    gap = now - timedelta(days=7)
    yesterday = now - timedelta(days=1)

    now = str(now)[0:10]
    gap = str(gap)[0:10]
    year = str(now)[0:4]
    yesterday = str(yesterday)[0:10]

    print('DB로드시작')
    # 기사 DB
    conn = sqlite3.connect('./db.sqlite3')
    c_select = conn.cursor()

    # 언론사 정보
    conn_press = sqlite3.connect('./percentage.sqlite3')
    c_select_press = conn_press.cursor()
    datas = pd.read_sql('select press , sum(percentage) / count(percentage) as wei from percentage group by press ', con=conn_press)

    # print(datas)

    print('DB로드완료')
    today_data = c_select.execute( "SELECT title , date , time , stock , press , posi_nega , link FROM article where stock != 'stock' and date > '"+ gap + "' and date < '" + now +"' order by date desc , time desc")
    df = pd.DataFrame(today_data)
    df.columns = ['title', 'date', 'time', 'stock' , 'press' , 'posi_nega' ,'link']

    article_list = []
    stock_list = ""
    stock_sugg_list = []
    article_list_dup = []

    for i in range(1, len(df.values)):
        article = {}
        sugg_list = {}

        article['title'] = df['title'][i]
        article['date'] = df['date'][i]
        article['time'] = df['time'][i]
        article['stock'] = df['stock'][i].replace("'", "")
        article['press'] = df['press'][i]
        article['posi_nega'] = df['posi_nega'][i]
        article['link'] = df['link'][i].replace("§", "&")
        article_list.append(article)

        if i == len(df.values) - 1:
            stock_list += article['stock']
        else:
            stock_list += article['stock'] + ','

        stock_code = item_code_by_item_name(article['stock'])
        stock_sugg = fdr.DataReader( stock_code , gap, now)
        stock_sugg = stock_sugg.fillna(0)
        # print( article['stock'] ,  gap , now , stock_sugg  )
        # print( stock_sugg.iloc[-1]['Close'] )
        stock_sugg_close = stock_sugg.iloc[-1]['Close']
        stock_sugg_change = stock_sugg.iloc[-1]['Change'] * 100
        stock_sugg_volume = stock_sugg.iloc[-1]['Volume']

        sugg_list['stock'] = article['stock']
        sugg_list['close'] = stock_sugg_close
        sugg_list['change_disp'] = str(round(stock_sugg_change, 3)) + '%'
        sugg_list['change'] = round(stock_sugg_change, 3)
        sugg_list['volume'] = stock_sugg_volume
        sugg_list['link'] = 'https://finance.naver.com/item/main.nhn?code=' + stock_code

        stock_sugg_list.append(sugg_list)

    stock_sugg_list_final = []

    for stock in stock_sugg_list:
        if stock not in stock_sugg_list_final:
            stock_sugg_list_final.append(stock)


    df_art = pd.DataFrame(article_list)
    df_merge = pd.merge(df_art,datas,how='outer',on='press')
    df_merge_fn = df_merge.fillna(0)

    stock_score_list = []

    for i in range(0, len(stock_sugg_list_final)):

        df_stock = df_merge_fn[df_merge_fn['stock'] == stock_sugg_list_final[i]['stock']]

        df_stock_cp = df_stock.copy()

        df_stock_cp['posi_nega_int'] = pd.to_numeric(df_stock_cp['posi_nega'])
        df_stock_cp['wei_int'] = pd.to_numeric(df_stock_cp['wei'])

        score = 0

        for j in range(0, len(df_stock_cp)):
            score += df_stock_cp['posi_nega_int'].iloc[j] * df_stock_cp['wei'].iloc[j] * 0.01

        df_stock_per = score / ( 2 * len(df_stock_cp) )

        stock_score =  [ stock_sugg_list_final[i]['stock'] , round(df_stock_per,2) , len(df_stock_cp) ]

        stock_score_list.append(stock_score)

    ai_list = []

    for k in range(0, len(stock_score_list)):

        if stock_score_list[k][2] > 3 and stock_score_list[k][1]  > 0.3 :
            ai_list.append(stock_score_list[k][0])

    context = {'articles': article_list, 'stock_list': stock_list, 'stock_sugg_list' : stock_sugg_list_final , 'ai_sugg':ai_list}

    return render(request, 'index.html', context)

def index2(request):

    stock_list = []

    for i in range(1,len(company_list)):
        stock_list.append(company_list[i][0])

    context = {
        'section': 'index2_data.html' , 'keyword' : stock_list
    }
    return render(request, 'index2.html', context)

def company_info(request):

    search = request.GET['search']

    # Name,Symbol,Market,Sector,Industry,ListingDate,SettleMonth,Representative,Region,HomePage
    for i in range(1,len(company_list)):
        if company_list[i][0] == search:
            Name= company_list[i][0]
            Symbol=company_list[i][1]
            Market=company_list[i][2]
            Sector=company_list[i][3]
            Industry=company_list[i][4]
            ListingDate=company_list[i][5]
            SettleMonth=company_list[i][6]
            Representative=company_list[i][7]
            Region=company_list[i][8]
            HomePage=company_list[i][9]
            break

    # print('기업관련 기사 가져오기')
    # 기업 관련 기사 가져오기
    conn = sqlite3.connect('./db.sqlite3')
    c_select = conn.cursor()
    today_data = c_select.execute( "SELECT title , date , time , stock , press , link FROM article where stock ='" + search +"' order by date desc , time desc")
    df = pd.DataFrame(today_data)

    article_list = []

    if len(df) != 0:

        df.columns = ['title', 'date', 'time', 'stock', 'press', 'link' ]

        for i in range(1, len(df.values)):
            article = {}

            article['title'] = df['title'][i]
            article['date'] = df['date'][i]
            article['time'] = df['time'][i]
            article['stock'] = df['stock'][i].replace("'","")
            article['press'] = df['press'][i]
            article['link'] = df['link'][i].replace("§","&")
            article_list.append(article)

    context = { 'section': 'index2_data.html' , 'articles' : article_list
                , 'Name':Name
               ,'Symbol':Symbol
               ,'Market':Market
               ,'Sector':Sector
               ,'Industry':Industry
               ,'ListingDate':ListingDate
               ,'SettleMonth':SettleMonth
               ,'Representative':Representative
               ,'Region':Region
               ,'HomePage':HomePage
              }
    # print(context)
    return render(request, 'index2_data.html', context)

def home(request):
    return render(request, 'home.html')

def graph_kq11(request):
    return render(request, 'graph_kq11.html')


def graph_ks11(request):
    return render(request, 'graph_ks11.html')

def stock_realtime(request):

    search = request.GET['search']
    gap = request.GET['gap']

    html = 'https://finance.naver.com/item/main.nhn?code='+ item_code_by_item_name(search)
    req = requests.get(html)
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')
    my_stock = soup.select('div > #img_chart_area') # .lst_pop
    img = my_stock[0].get("src")
    # img = 'https://ssl.pstatic.net/imgfinance/chart/item/area/day/005930.png?sidcode=1629299388530'

    img = img.replace("day",gap)

    context = { 'img' : img }

    return render(request, 'stock_realtime.html', context)

def keyword(request):

    search = request.GET['search']
    result = []

    tag = ""

    if search != "":
        for i in range(1,len(company_list)):
            if search in company_list[i][0] and "KBG" not in company_list[i][0] and ( company_list[i][2] == "KOSPI" or company_list[i][2] == "KOSDAQ" ) and company_list[i][3] != "no" :

                result.append(company_list[i][0])

                if len(result) < 6:
                    tag += "<li style='width:200px;'><a class='dropdown-item' href='#'>"+ company_list[i][0]+ " ( " + company_list[i][1] +" ) - " + company_list[i][2] +"</a></li>"

    return HttpResponse(json.dumps(tag), content_type='application/json')


# if __name__ == '__main__':
#     scrap_market('self')