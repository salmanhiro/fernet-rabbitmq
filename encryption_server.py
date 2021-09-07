import pika
import json
from cryptography.fernet import Fernet


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='rpc_queue')

def encrypt(text):
    key = Fernet.generate_key()
    
    f = Fernet(key)
    token = f.encrypt(b"{text}")
    return token, text, key


def on_request(ch, method, props, body):
    body = json.loads(body)
    text = body["text"]
    encrypted_text, plain_text, fernet_key = encrypt(text)
    
    response = {"encrypted token": str(encrypted_text.decode("utf-8")), 
    "generated key": str(fernet_key)}

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=json.dumps(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

print(" [x] Awaiting RPC requests")
channel.start_consuming()