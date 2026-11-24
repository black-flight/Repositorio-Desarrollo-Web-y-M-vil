"""Consumidor STOMP real de eventos de pedidos; deduplica por event_id."""
import json
import logging
import os
import time
import stomp
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('tokyo.consumer')

class Consumer(stomp.ConnectionListener):
    def __init__(self, conn, mongo):
        self.conn=conn
        self.events=mongo['tokyo_noodles_eval2']['events_consumed']
        self.events.create_index('event_id', unique=True)
    def on_message(self, frame):
        try:
            event=json.loads(frame.body)
            if event.get('event_type') != 'order.paid' or not event.get('event_id'):
                raise ValueError('Evento inválido')
            try:
                self.events.insert_one(event)
                log.info('operacion_id=%s event_id=%s processing=stored_once',event.get('operacion_id'),event['event_id'])
            except DuplicateKeyError:
                log.info('operacion_id=%s event_id=%s processing=duplicate_ignored',event.get('operacion_id'),event['event_id'])
            ackid=frame.headers.get('ack') or frame.headers.get('message-id')
            self.conn.ack(id=ackid, subscription=frame.headers.get('subscription','tokyo-consumer'))
        except Exception as exc:
            log.error('processing=failed error=%s',type(exc).__name__)
    def on_disconnected(self):
        log.warning('broker=disconnected')


def main():
    mongo=MongoClient(os.getenv('MONGO_URL','mongodb://127.0.0.1:27017'),serverSelectionTimeoutMS=3000)
    while True:
        try:
            conn=stomp.Connection12([(os.getenv('ACTIVEMQ_HOST','127.0.0.1'),int(os.getenv('ACTIVEMQ_PORT','61613')))],heartbeats=(10000,10000))
            conn.set_listener('events',Consumer(conn,mongo))
            conn.connect(os.getenv('ACTIVEMQ_USER','admin'),os.getenv('ACTIVEMQ_PASSWORD','admin'),wait=True)
            conn.subscribe('/queue/tokyo.orders',id='tokyo-consumer',ack='client-individual')
            log.info('consumer=active queue=/queue/tokyo.orders')
            while conn.is_connected(): time.sleep(2)
        except Exception as exc:
            log.warning('consumer=reconnecting reason=%s',type(exc).__name__)
        time.sleep(3)

if __name__ == '__main__': main()
