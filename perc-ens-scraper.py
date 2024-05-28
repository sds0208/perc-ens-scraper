import requests
import os
from dotenv import load_dotenv
import psycopg2
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait


load_dotenv()

ensemble_data = []


with open('valid_proxies.txt', 'r') as f:
    proxies = f.read().split('\n')

print(proxies)

def scrape1(site_ens_list, inc, max_inc, sleep, selector, url, site_name):
  
    while inc < max_inc:    
        new_url = ''

        if site_name == 'Rowloff':
            new_url = url + f'/{inc}/'
        elif site_name == 'C.Alan Publications':
            new_url = url + f'{inc}'

        print(f'Scraping for {site_name} ensembles on...')
        print (new_url) 

        proxies = { 
              "http": os.getenv('PROXY_URL')
            }

        r = requests.get(new_url, proxies=proxies)
        soup = BeautifulSoup(r.text, 'html.parser')

        ens_list = soup.select(selector)
        if (not ens_list):
            break
        for ens in ens_list:
            site_ens_list.append(ens)

        inc += 1
        time.sleep(sleep)

    print(f'Found {len(site_ens_list)} {site_name} ensembles.')

def append_ens_data(site_ens_data_list, main_ens_data_list, main_selector, site_name, composer_selector = ''):
    if (site_ens_data_list):    
        for ens in site_ens_data_list:
            obj = {'title': '', 'composer': None, 'link': ''}

            if (ens.select(main_selector)):
                obj['title'] = ens.select(main_selector)[0].get_text().strip()
                obj['link'] = ens.select(main_selector)[0].get('href')

            if (site_name == 'Tapspace' or site_name == 'Rowloff') and ens.select(composer_selector):
                obj['composer'] = ens.select(composer_selector)[0].get_text().strip()

            main_ens_data_list.append(obj)

        print('First entry:', main_ens_data_list[0])
        print('Ensembles found: ', len(main_ens_data_list))

# Scrape C.Alan Publications
c_alan_ensembles = []
x = 1

scrape1(c_alan_ensembles, x, 140, 7, 'ul.ProductList li', 'https://c-alanpublications.com/percussion-ensemble/?sort=alphaasc&page=', 'C.Alan Publications')
append_ens_data(c_alan_ensembles, ensemble_data, 'span.ProductName a', 'C.Alan Publications')

# Scrape Rowloff
rowloff_ensembles = []
y = 1

scrape1(rowloff_ensembles, y, 50, 7, 'ul.products li.product', 'https://rowloff.com/product-category/concert-ensembles/page', 'Rowloff')
append_ens_data(rowloff_ensembles, ensemble_data, 'h2.woocommerce-loop-product__title a', 'Rowloff', '.woocommerce-loop-product__author a')

# Scrape Tapspace
num_ens = 0
driver1 = webdriver.Chrome()
driver1.get('https://www.tapspace.com/percussion-ensemble/')

tapspace_soup = BeautifulSoup(driver1.page_source, 'html.parser')
tapspace_ensembles = tapspace_soup.findAll('div', class_=re.compile('catalog-list2'))

print('Scraping for Tapspace ensembles...')

while (num_ens < len(tapspace_ensembles)):
    # Scroll to bottom of page to initiate lazy loading of more ensembles
    dif = len(tapspace_ensembles) - num_ens
    driver1.execute_script('window.scrollTo(0, document.body.scrollHeight)')

    def determineGreaterLength():
        tapspace_soup = BeautifulSoup(driver1.page_source, 'html.parser')
        return len(tapspace_soup.findAll('div', class_=re.compile('catalog-list2'))) > len(tapspace_ensembles) or dif < 24
    
    wait = WebDriverWait(driver1, timeout=5)
    wait.until(lambda d : determineGreaterLength())
    
    tapspace_soup = BeautifulSoup(driver1.page_source, 'html.parser')
    tapspace_ensembles = tapspace_soup.findAll('div', class_=re.compile('catalog-list2'))
    
    num_ens += dif

driver1.close()

print(f'Found {len(tapspace_ensembles)} Tapspace ensembles.')

append_ens_data(tapspace_ensembles, ensemble_data, 'div.catalog-product-title a', 'Tapspace', 'div.catalog-product-title a.catalog-mfr-name')

# Send scraped data to database
HOST = os.getenv('HOST')
DBNAME = os.getenv('DBNAME')
USER = os.getenv('DBUSER')
PORT = os.getenv('PORT')
PASSWORD = os.getenv('PASSWORD')

conn = psycopg2.connect(host=HOST, dbname=DBNAME, user=USER, port=PORT, password=PASSWORD)

cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS ensembles3 (
    id INT PRIMARY KEY,
    title VARCHAR(255),
    composer VARCHAR(255),
    link VARCHAR(255),
    audio VARCHAR(255)
);
""")

for ind, ens in enumerate(ensemble_data):
    cur.execute("""
        INSERT INTO ensembles3 (id, title, composer, link) 
        VALUES (%(id)s, %(title)s, %(composer)s, %(link)s);
        """,
        {'id': ind + 1, 'title': ens['title'], 'composer': ens['composer'], 'link': ens['link']}
    )

conn.commit()
cur.close()
conn.close()