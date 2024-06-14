import os
from dotenv import load_dotenv
import psycopg2

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

digital_str = '%[DIG%'

# Get all rows from the table
cur.execute('SELECT * from ensembles3 WHERE title NOT like %s', [digital_str])
result = cur.fetchall()

# Loop through each row
for item in result:
    id = item[0]
    title = item[1]
    composer = item[2]
    link = item[3]
    audio = item[4]
    description = item[5]
    player_start_ind = None
    level_start_ind = None

    if (description):
        if 'c-alan' in link:
            if ('# of Players:' in description):
                player_start_ind = description.index('# of Players:') + 14
            if ('Level:' in description):
                player_stop_ind = description.index('Level:') - 1
                level_start_ind = description.index('Level:') + 7
            if ('Series:' in description):
                player_stop_ind = description.index('Series:') - 1
            if (' | Duration:' in description):
                level_stop_ind = description.index(' | Duration:')
            elif (' | Duration:' not in description and 'Instrumentation' in description):
                level_stop_ind = description.index('Instrumentation')

            
        elif 'tapspace' in link:
            if ('Personnel:' in description):
                player_start_ind = description.index('Personnel:') + 11
            if ('Release Date:' in description):
                player_stop_ind = description.index('Release Date:')
            if ('State Lists:' in description):
                player_stop_ind = description.index('State Lists:')
            if ('Level:' in description):
                level_start_ind = description.index('Level:') + 7
            if ('Duration:' in description):
                level_stop_ind = description.index('Duration:')
            elif ('Duration:' not in description and 'Pages:' in description):
                level_stop_ind = description.index('Pages:')

        elif 'rowloff' in link:
            if ('Players:' in description):
                player_start_ind = description.index('Players:') + 9
                level_stop_ind = description.index('Players:')
            if ('Length:' in description):
                player_stop_ind = description.index('Length:')
                if ('Players:' not in description):
                    level_stop_ind = description.index('Length:')
            if ('State Lists:' in description) and (('Length:' not in description) or ('Length:' in description and description.index('State Lists:') < description.index('Length:'))):
                    player_stop_ind = description.index('State Lists:')
            elif ('Instrumentation:' in description and 'Length:' not in description and 'State Lists:' not in description):
                player_stop_ind = description.index('Instrumentation:')
            if ('Level:' in description):
                level_start_ind = description.index('Level:') + 7

        if (player_start_ind):
            players = slice(player_start_ind, player_stop_ind)
            print(description[players])

            cur.execute('UPDATE ensembles3 SET players=%s WHERE id=%s;', (description[players], id))

        if (level_start_ind):
            level = slice(level_start_ind, level_stop_ind)
            print(description[level])
            print()
            print()

            cur.execute('UPDATE ensembles3 SET level=%s WHERE id=%s;', (description[level], id))

# Commit updates and close connection
conn.commit()
cur.close()
conn.close()