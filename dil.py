import datetime
import requests
import progressbar
import time
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures


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
    r = requests.get(img_url)
    return r.content


def save_image(img_bytes, date):
    image = Image.open(BytesIO(img_bytes))
    image_name = construct_image_name('dilbert', date, image.format)
    image.save(image_name, image.format)


def construct_image_name(path, date, format):
    return "{0}/{1}.{2}".format(path, date, format.lower())


def build_url(date):
    return URL + str(date)

days = (FINAL_DATE - INITIAL_DATE).days
bar = progressbar.ProgressBar(max_value=1000)



def main():
    initial_date = INITIAL_DATE
    items = 1
    while items <= days:
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
        items += 12
        time.sleep(2)


if __name__ == '__main__':
    main()