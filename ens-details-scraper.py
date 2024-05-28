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
cur.execute('SELECT * from ensembles3')
result = cur.fetchall()

# Get IP Proxies from hidden file
with open('valid_proxies.txt', 'r') as f:
    proxiesList = f.read().split('\n')

# Loop through each row
for item in result:
    id = item[0]
    title = item[1]
    composer = item[2]
    url_to_scrape = item[3]
    audio = item[4]

    # Modify this condition based on what data is still needed
    if ('c-alan' in url_to_scrape) and (not 'digital' in title.lower()) and (not composer and not composer == '') and (not audio and not audio == ''):
        print('*** SCRAPING ***', title)
        print()
        
        # Randomize how much time is between each request
        sleep_num = random.choice([210, 290, 51, 200, 220, 250, 30])

        # Randomize IPs used
        proxy_url = random.choice(proxiesList)

        # Define selectors to look for on each site
        c_alan_composer_selector = ''
        selector = ''

        if 'tapspace' in url_to_scrape:
            selector = '.product-custom-field iframe'
        elif 'c-alan' in url_to_scrape:
            selector = '.product-details iframe'
            c_alan_composer_selector = '.product-details .BrandRow .Value a span'
        elif 'rowloff' in url_to_scrape:
            selector = '.audio-player audio source'

        # Make request for HTML
        proxies = { 
                "http": proxy_url
                }
        r = requests.get(url_to_scrape, proxies=proxies)

        # Parse HTML
        soup = BeautifulSoup(r.text, 'html.parser')
        audioElList = soup.select(selector)
        audioUrl = ''
        if (len(audioElList) > 0):
            audioUrl = audioElList[0].get('src')

        # If C.Alan, get audio and composer
        if ('c-alan' in url_to_scrape) and (not composer):
            composer = soup.select(c_alan_composer_selector)[0].get_text().strip()
            
            # Update database
            cur.execute('UPDATE ensembles3 SET composer=%s WHERE id=%s;', (composer, id))
            cur.execute('UPDATE ensembles3 SET audio=%s WHERE id=%s;', (audioUrl, id))
            
            # Commit updates
            conn.commit()

            # See new entry
            cur.execute("""SELECT * FROM ensembles3 WHERE id=%s""", ([id]))
            res = cur.fetchall()
            print(res)
            print()

        # Otherwise just get audio
        elif not 'c-alan' in url_to_scrape:
            # Update database
            cur.execute('UPDATE ensembles3 SET audio=%s WHERE id=%s;', (audioUrl, id))
            
            # Commit updates
            conn.commit()

            # See new entry
            cur.execute("""SELECT * FROM ensembles3 WHERE id=%s""", ([id]))
            res = cur.fetchall()
            print(res)
            print()
        

        # Wait a few seconds before executing next request
        time.sleep(sleep_num)

cur.close()
conn.close()