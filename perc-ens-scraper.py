import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import time
driver = webdriver.Chrome()

# Tapspace
num_ens = 0

driver.get('https://www.tapspace.com/percussion-ensemble/')

tapspace_soup = BeautifulSoup(driver.page_source, 'html.parser')
tapspace_ensembles = tapspace_soup.findAll('div', class_=re.compile('catalog-list2'))
for ens in tapspace_ensembles:
    print(ens.find('div', {'class': 'catalog-product-title'}).find('a', {'class': 'catalog-mfr-name'}).get_text())
    print(ens.find('div', {'class': 'catalog-product-title'}).find('a').get('href'))

while (num_ens < len(tapspace_ensembles)):
    dif = len(tapspace_ensembles) - num_ens
    print(dif)
    print('inside while loop')
    print(num_ens, len(tapspace_ensembles))
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')

    def determineGreaterLength():
        tapspace_soup = BeautifulSoup(driver.page_source, 'html.parser')
        return len(tapspace_soup.findAll('div', class_=re.compile('catalog-list2'))) > len(tapspace_ensembles) or dif < 24
    
    wait = WebDriverWait(driver, timeout=5)
    wait.until(lambda d : determineGreaterLength())
    
    tapspace_soup = BeautifulSoup(driver.page_source, 'html.parser')
    tapspace_ensembles = tapspace_soup.findAll('div', class_=re.compile('catalog-list2'))
    
    num_ens += dif

ensemble_data = []

for ens in tapspace_ensembles:
    obj = {'title': '', 'composer': '', 'link': ''}
    if (ens.find('div', {'class': 'catalog-product-title'}).find('a')):
        obj['title'] = ens.find('div', {'class': 'catalog-product-title'}).find('a').get_text()

    if (ens.find('div', {'class': 'catalog-product-title'}).find('a', {'class': 'catalog-mfr-name'})):
        obj['composer'] = ens.find('div', {'class': 'catalog-product-title'}).find('a', {'class': 'catalog-mfr-name'}).get_text()
    
    if (ens.find('div', {'class': 'catalog-product-title'}).find('a')):
        obj['link'] = ens.find('div', {'class': 'catalog-product-title'}).find('a').get('href')

    ensemble_data.append(obj)

print(ensemble_data)


# TODO - parse data and send to a database
# TODO - add at least a couple more data sources
# TODO - figure out how to use cron to schedule this to run once a week


