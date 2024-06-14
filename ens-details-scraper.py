# This file is the 2nd step of the scraping process for this project.
# It adds data that's more easily gained from individual ensemble pages 
# rather than the ensemble list pages that the first scraper gathers.

import requests
import os
from dotenv import load_dotenv
import psycopg2
from bs4 import BeautifulSoup
import random
import time

load_dotenv()

# Database info
HOST = os.getenv('HOST')
DBNAME = os.getenv('DBNAME')
USER = os.getenv('DBUSER')
PORT = os.getenv('PORT')
PASSWORD = os.getenv('PASSWORD')

# Connect to the database
conn = psycopg2.connect(host=HOST, dbname=DBNAME, user=USER, port=PORT, password=PASSWORD)
cur = conn.cursor()

# Get all rows from the table
cur.execute('SELECT * from ensembles5')
result = cur.fetchall()

# Get IP Proxies from hidden file
with open('valid_proxies.txt', 'r') as f:
    proxies_list = f.read().split('\n')

# Loop through each row
for item in result:
    id = item[0]
    title = item[1]
    composer = item[2]
    url_to_scrape = item[3]
    audio = item[4]
    description = item[5]

    # Modify this condition based on what data is still needed
    if (not composer) or (not description) or (not audio):
        print('*** SCRAPING ***', title)
        print()
        
        # Randomize how much time is between each request
        sleep_num = random.choice([210, 290, 51, 200, 220, 250, 30])

        # Randomize IPs used
        proxy_url = random.choice(proxies_list)

        # Define selectors to look for on each site
        composer_selector = ''
        audio_selector = ''
        description_selector = ''

        if 'tapspace' in url_to_scrape:
            audio_selector = '.product-custom-field iframe'
            description_selector = '.product-right .purchase-l'
        elif 'c-alan' in url_to_scrape:
            audio_selector = '.product-details iframe'
            composer_selector = '.product-details .BrandRow .Value a span'
            description_selector = '#DescriptionTab p'
        elif 'rowloff' in url_to_scrape:
            audio_selector = '.audio-player audio source'
            description_selector = '.product-details'

        # Make request for HTML
        r = requests.get(url_to_scrape, proxies={ "http": proxy_url })

        # Parse HTML
        soup = BeautifulSoup(r.text, 'html.parser')    

        audio_element_list = soup.select(audio_selector)
        description_element_list = soup.select(description_selector)
        composer_element_list = []

        if composer_selector:
            composer_element_list = soup.select(composer_selector)
        
        # Update database
        if (len(composer_element_list) > 0):
            composer = composer_element_list[0].get_text().strip()
            cur.execute('UPDATE ensembles5 SET composer=%s WHERE id=%s;', (composer, id))
        
        if (len(description_element_list) > 0):
            description = description_element_list[0].get_text().strip()
            cur.execute('UPDATE ensembles5 SET description=%s WHERE id=%s;', (description, id))

        if (len(audio_element_list) > 0):
            audio_url = audio_element_list[0].get('src')
            cur.execute('UPDATE ensembles5 SET audio=%s WHERE id=%s;', (audio_url, id))
        
        
        # Commit updates
        conn.commit()

        # See new entry
        cur.execute('SELECT * FROM ensembles5 WHERE id=%s', ([id]))
        res = cur.fetchall()
        print(res)
        print()
        
        # Wait a while before executing next request
        time.sleep(sleep_num)

cur.close()
conn.close()