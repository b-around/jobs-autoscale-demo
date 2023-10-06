#!/usr/bin/env python
from flask import Flask, request, jsonify
import redis
import logging
import os
import sys
import json

# HOW TO run the app on local machine via podman and check logs
# podman run -itd --name ctasks -p 5000:5000 -e FLASK_DEBUG=True -e REDIS_URL=tasks-queue-rh-fsi-demos.apps.simudyne.fsi-partner.rhecoeng.com -e REDIS_PWD=3R8P8reeQVqTrwGT -e REDIS_PORT=443 localhost/azenhab/demos:latest 
# podman logs -f ctasks


# enable Flask
app = Flask(__name__)

# Read debug level from environment variable or set default to False
fdebug = os.getenv("APP_DEBUG", False)

# Read port number from environment variable or set default to 5000
fPort = int(os.getenv("APP_PORT", 5000))

# define if only requests with authentication will be handled
checkApiToken = os.getenv("API_TOKEN", False)

# define security token secret to validate API access
apiToken = os.getenv("API_TOKEN_VALUE", "96w9EXfen2zEJxcd") 



# define the redis leader instance location - check value of the OCP route (external access) or OCP service (internal access)
rhost=os.getenv("REDIS_URL", "redis-leader-service")

# define redis active port which will be the ocp route (default is 443) or OCP service port (default is 6379)
rport=os.getenv("REDIS_PORT", 6379)

# define redis server password
rpwd=os.getenv("REDIS_PWD", "")

# define redis connection to use standard or encrypted traffice
rssl=os.getenv("REDIS_SSL", False)

# define redis default connection timeout in seconds
rtimeout=15

# define redis default tasks queue name
rqueue=os.getenv("QUEUE_NAME", "default")

# define name of JSON object holding list of tasks
tasksElem = "tasks"

# define debug test data going into redis queue when handling GET requests
debugData = '''
{
    "tasks": [
        "prime 100 150",
        "prime 210 233",
        "prime 345 700",
        "finbonnaci 100 1111"
    ]
}
'''


def connect_to_redis_queue():
    try:
        # Connect to redis server and push data into the queue
        if rpwd == '':
            logging.debug("Connecting to redis in usecure mode")
            rclient = redis.Redis(host=rhost, port=rport, socket_timeout=rtimeout, decode_responses=True)
        elif rpwd != '' and not rssl:
            logging.debug("Connecting to redis with auth only")
            rclient = redis.Redis(host=rhost, port=rport, password=rpwd, decode_responses=True)
        else:
            logging.debug("Connecting to redis with auth and SSL")
            rclient = redis.Redis(host=rhost, port=rport, password=rpwd, ssl=True, ssl_cert_reqs="none", decode_responses=True)
    
        logging.debug("Testing redis server connection")
        rclient.ping()
        return rclient
    except redis.ConnectionError as e:
        logging.error("error: Could not connect to Redis: %s", e)
        return None



def is_valid_token(token):
    # Check if the provided token matches the valid token
    return token == "APIKey " + apiToken


def write_to_redis_queue(redis_client, queue_name, data):
    # Push data into a redis queue
    try:
        app.logger.debug("Writting item to queue: %s", data)
        redis_client.rpush(queue_name, data) 
        app.logger.debug("Write successful")
        return True
    except Exception as e:
        app.logger.error("Error writing to Redis queue: %s", e)
        return False

#stream_handler = logging.StreamHandler(sys.stdout)
#stream_handler.setLevel(logging.DEBUG)
#app.logger.addHandler(stream_handler)
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

@app.route('/', methods=['GET', 'POST'])
def process_request():
    app.logger.info("Processing new request...")

    # Check for the authentication token in the request header
    token = request.headers.get('Authorization')
    app.logger.debug("Auth token value = %s", token)
    
    if checkApiToken and not token:
        return jsonify({"error": "Missing authentication token"}), 401

    if checkApiToken and not is_valid_token(token):
        return jsonify({"error": "Invalid authentication token"}), 403

    data=None    

    if request.method == 'GET':
        # Handle GET requests as debug method
        app.logger.debug("Processing GET")
        try:
            data = json.loads(debugData)
        except json.JSONDecodeError as j:
            return jsonify({"error: Invalid or missing JSON object in request": str(j)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        # Handle POST requests as feeding tasks queue
        app.logger.debug("Processing POST")
        try:
            data = request.get_json()    
        except json.JSONDecodeError as j:
            return jsonify({"error: Invalid or missing JSON object in request": str(j)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        return jsonify({"error": "Method not allowed"}), 405

    app.logger.debug("Validating JSON tasks list: %s", data)

    try:
        if tasksElem in data and isinstance(data[tasksElem], list):
            app.logger.debug("JSON tasks list is valid, connecting to redis service")
            rclient=connect_to_redis_queue()
            if rclient is None:
                return jsonify({"message": "Tasks queue service is temporarly unavailble" }), 500
    
            for item in data[tasksElem]:
                app.logger.debug("Processing next task: %s", item)
                if isinstance(item, str):
                     write_to_redis_queue(rclient, rqueue, item)
                else:
                     app.logger.debug("Invalid item in the array: %s", item)
    
            return jsonify({"message": "Tasks successfully written to Redis queue"}), 200

        else:
            return jsonify({"error": "Invalid request. JSON object 'tasks' should exist and contain an array of strings"}), 400

    except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=fPort, debug=fdebug, threaded=True)

