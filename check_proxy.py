import threading
import queue
import requests

q = queue.Queue()
valid_proxies = []

# Check the validity of the supposedly valid ip proxies
with open('valid_proxies.txt', 'r') as f:
    proxies = f.read().split('\n')
    for p in proxies:
        q.put(p)

def check_proxies():
    global q
    while not q.empty():
        proxy = q.get()
        try:
            res = requests.get('http://ipinfo.io/json',
                               proxies={'http': proxy,
                                        'https': proxy})
        except:
            print('exception encountered')
            continue
        if res.status_code == 200:
            print(proxy)
        else:
            print(proxy, res.status_code)

check_proxies()

for _ in range(10):
    threading.Thread(target=check_proxies).start()

