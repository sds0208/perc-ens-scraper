import os
from dotenv import load_dotenv
import psycopg2
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

load_dotenv()

ensemble_data = []

def scrape1(site_ens_list, driver, inc, max_inc, sleep, timeout, selector, url, site_name):
    while inc < max_inc:    
        time.sleep(sleep)
        new_url = ''
        if site_name == 'Rowloff':
            new_url = url + f'/{inc}/'
        elif site_name == 'C.Alan Publications':
            new_url = url + f'{inc}'
        print(f'Scraping for {site_name} ensembles on...')
        print (new_url) 
        driver.get(new_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        try:
            wait = WebDriverWait(driver, timeout=timeout)
            wait.until(lambda d : len(soup.select(selector)) > 0)
        except TimeoutException:
            driver.close()
            print('entered timeout exception')
            break
        ens_list = soup.select(selector)
        for ens in ens_list:
            site_ens_list.append(ens)
        inc += 1

    print(f'Found {len(site_ens_list)} {site_name} ensembles.')

def append_ens_data(site_ens_data_list, main_ens_data_list, main_selector, site_name, composer_selector = ''):
    for ens in site_ens_data_list:
        obj = {'title': '', 'composer': None, 'link': ''}
        if (ens.select(main_selector)):
            obj['title'] = ens.select(main_selector)[0].get_text().strip()
            obj['link'] = ens.select(main_selector)[0].get('href')

        if site_name == 'Tapspace' and ens.select(composer_selector):
                obj['composer'] = ens.select(composer_selector)[0].get_text().strip()
        
        main_ens_data_list.append(obj)

    print('First entry:', main_ens_data_list[0])
    print('Ensembles found: ', len(main_ens_data_list))

# Scrape Tapspace
num_ens = 0
driver1 = webdriver.Chrome()
driver1.get('https://www.tapspace.com/percussion-ensemble/')

tapspace_soup = BeautifulSoup(driver1.page_source, 'html.parser')
tapspace_ensembles = tapspace_soup.findAll('div', class_=re.compile('catalog-list2'))

print('Scraping for Tapspace ensembles...')

while (num_ens < len(tapspace_ensembles)):
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

# Scrape Rowloff
rowloff_ensembles = []
y = 1
driver3 = webdriver.Chrome()
url = 'https://rowloff.com/product-category/concert-ensembles/page'

scrape1(rowloff_ensembles, driver3, y, 100, 5, 10, 'ul.products li.product', url, 'Rowloff')
append_ens_data(rowloff_ensembles, ensemble_data, 'h2.woocommerce-loop-product__title a', 'Rowloff')

# Scrape C.Alan Publications
c_alan_ensembles = []
x = 1
driver2 = webdriver.Chrome()

scrape1(c_alan_ensembles, driver2, x, 300, 0, 3, 'ul.ProductList li', 'https://c-alanpublications.com/percussion-ensemble/?sort=alphaasc&page=', 'C.Alan Publications')
append_ens_data(c_alan_ensembles, ensemble_data, 'span.ProductName a', 'C.Alan Publications')


# Send scraped data to database
HOST = os.getenv('HOST')
DBNAME = os.getenv('DBNAME')
USER = os.getenv('DBUSER')
PORT = os.getenv('PORT')
PASSWORD = os.getenv('PASSWORD')

conn = psycopg2.connect(host=HOST, dbname=DBNAME, user=USER, port=PORT, password=PASSWORD)

cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS ensembles2 (
    id INT PRIMARY KEY,
    title VARCHAR(255),
    composer VARCHAR(255),
    link VARCHAR(255)
);
""")

for ind, ens in enumerate(ensemble_data):
    cur.execute("""
        INSERT INTO ensembles2 (id, title, composer, link) 
        VALUES (%(id)s, %(title)s, %(composer)s, %(link)s);
        """,
        {'id': ind + 1, 'title': ens['title'], 'composer': ens['composer'], 'link': ens['link']}
    )

conn.commit()
cur.close()
conn.close()