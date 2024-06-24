import os

# from redis import Redis
import redis
from rq import Worker, Queue, Connection
# from urllib.parse import urlparse
import urllib.parse
import django
# django.setup()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sovote.settings")
# django.setup()
if __name__ == '__main__':
   django.setup()

# DJANGO_SETTINGS_MODULE=station5.settings rq worker --worker-class='worker_django_1_11.Worker'


listen = ['high', 'default', 'low']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

# redis_url = os.getenv('REDISTOGO_URL')

# urllib.parse.uses_netloc.append('redis')
# url = urllib.parse.urlparse(redis_url)
# conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)




if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()


