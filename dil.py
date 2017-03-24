import datetime
import requests
import progressbar
import time
from bs4 import BeautifulSoup
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
import sys


URL = 'http://dilbert.com/strip/'
INITIAL_DATE = datetime.date(year=1996, month=1, day=15)
FINAL_DATE = datetime.date(year=2017, month=3, day=1)
DAY = datetime.timedelta(hours=24)


def get_page(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'}
    r = requests.get(url, headers=headers)
    return r.text


def find_image_url(page):
    soup = BeautifulSoup(page, 'lxml')
    image_url = soup.find('img', {'class': 'img-comic'}).get('src')
    return image_url


def download_image_bytes(img_url):
    r = requests.get(img_url, stream=True)
    return r


def save_image(request_stream, date):
    image_name = construct_image_name('dilbert', date, request_stream.headers['content-type'])
    with open(image_name, 'wb') as out_stream:
        for chunk in request_stream:
            out_stream.write(chunk)


def construct_image_name(path, date, format_header):
    format = format_header.split('/')[-1]  
    return "{0}/{1}.{2}".format(path, date, format.lower())


def build_url(date):
    return URL + str(date)

days = (FINAL_DATE - INITIAL_DATE).days
bar = progressbar.ProgressBar(max_value=days)



def main():
    try:
        initial_date = INITIAL_DATE
        for items in range(1, days, 12):
            with ProcessPoolExecutor() as executor:
                future_results = []
                urls = []
                date = initial_date
                for i in range(12): #or server is gonna punish me
                    url = build_url(date)
                    task = executor.submit(get_page, url)
                    future_results.append(task)
                    date = date + DAY
                    
                date = INITIAL_DATE
                print('##### Processing URLs... #####')
                for future in concurrent.futures.as_completed(future_results):
                    img_url = find_image_url(future.result())
                    urls.append(img_url)
                    date = date + DAY
                
                future_results = []
                
                for url in urls:
                    task = executor.submit(download_image_bytes, url)
                    future_results.append(task)
                
                date = initial_date
                print('##### Downloading images #####')
                for future in concurrent.futures.as_completed(future_results):
                    save_image(future.result(), date)
                    date = date + DAY
                executor.shutdown()
            initial_date = date
            bar.update(items)
            time.sleep(2)
    except:
        print("Error!", sys.exc_info()[0])


if __name__ == '__main__':
    main()