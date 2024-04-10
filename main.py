import requests
from bs4 import BeautifulSoup
from celery import Celery
import time

from celery.exceptions import MaxRetriesExceededError

app = Celery('app', broker='amqp://guest:guest@127.0.0.1:5672/')
app.conf.task_queues = {
    'celery': {
        'exchange': 'celery',
        'routing_key': 'celery',
        'options': {
            'queue_arguments': {
                'x-max-priority': 10,
                'x-queue-mode': 'lazy',
                'x-prefetch-count': 1
            }
        }
    }
}

base_url = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on&pageNumber='
start_page = 1
end_page = 2

@app.task
def pars_links(urls_pages):
    links = []
    for url in urls_pages:
        while True:
            r = requests.get(url)
            if r.status_code == 200:
                sait = BeautifulSoup(r.text, 'html.parser')
                links_sait = sait.find_all('div', class_='registry-entry__header-top__icon')
                for link in links_sait:
                    a_tags = link.find_all('a', {'target': '_blank'})
                    for a in a_tags:
                        href = 'https://zakupki.gov.ru' + a.attrs.get('href')
                        href_xml = href.replace('view.html', 'viewXml.html')
                        links.append(href_xml)
                break
            else:
                print(f"Ошибка: статус ответа {url}: {r.status_code}, повтор запроса...")
                time.sleep(1)
    return links

@app.task(bind=True, max_retries=5, default_retry_delay=2)
def parser(self, links):
    data= {}
    for link in links:
        try:
            r = requests.get(link)
            if r.status_code == 200:
                soup = BeautifulSoup(r.content, features='lxml-xml')
                publish_dt = soup.find('publishDTInEIS')
                if publish_dt is not None:
                    data[link.replace('viewXml.html', 'view.html')] = publish_dt.text
                else:
                    raise ValueError(f"Ошибка: статус ответа {r.status_code}, повтор запроса...")
        except Exception as e:
            try:
                raise self.retry(exc=e, countdown=2 ** self.request.retries)
            except MaxRetriesExceededError:
                print(f"Превышено максимальное количество попыток для ссылки {link}")
    return data

urls_pages = [base_url + str(i) for i in range(start_page, end_page + 1)]

link = pars_links(urls_pages)

print(parser.delay(link))

