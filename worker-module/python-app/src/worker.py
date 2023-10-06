#!/usr/bin/env python
import redis
import sys
import os
import subprocess
import logging
import time

#### time.sleep(10) # Put your actual work here instead of sleep.



# Set the debug mode
debug=bool(os.getenv("APP_DEBUG", False))

# Create logger object
logger = logging.getLogger()

# define the redis leader instance location - check value of the OCP route (external access) or OCP service (internal access)
rhost=os.getenv("REDIS_URL", "redis-leader-service")

# define redis active port which will be the ocp route (default is 443) or OCP service port (default is 6379)
rport=os.getenv("REDIS_PORT", 6379)

# define redis server password
rpwd=os.getenv("REDIS_PWD", "")

# define redis connection to use standard or encrypted traffice
rssl=os.getenv("REDIS_SSL", False)

# define redis connection to use standard or encrypted traffice
extpath=os.getenv("EXT_APP_PATH", "./calculator")

# define redis default connection timeout in seconds
rtimeout=15

# define redis default tasks queue name
rqueue=os.getenv("QUEUE_NAME", "default")

# define maximum number of tasks this process will handle before gracefully terminating where -1 means keep running until all tasks are processed
maxtasks=os.getenv("MAX_TASKS", -1)


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


def read_from_redis_queue(redis_client, queue_name):
    # Push data into a redis queue
    try:
        logging.debug("Reading message from queue: %s", queue_name)
        data = redis_client.lpop(queue_name)
        return data
    except Exception as e:
        logging.error("error: Could not read from Redis queue: %s", e)
        return None

def process_message(message):
    try:
        # Call the external command-line based application with the message content as an argument
        args = message.split()
        subprocess.run([extpath, args[0], args[1], args[2]])
        logging.debug("Message processed: %s", message)
    except subprocess.CalledProcessError as e:
        logging.error("error: Error processing message: %s. Detail: %s", message, error)


def main():
    if debug:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    logging.info("App log level set to %s", logging.getLevelName(logging.getLogger().getEffectiveLevel()))

    # Connect to the Redis server
    rclient = connect_to_redis_queue()
    if rclient is None:
        logging.warning("message: Tasks queue service is temporarly unavailble")

    else:
        max_iterations = maxtasks if maxtasks > 0 else sys.maxsize
        i = 0
        logging.debug("Processing tasks in the queue")

        # Loop until the Redis queue is empty or max tasks count has been reached
        while True:
            # get message from the queue
            message = read_from_redis_queue(rclient, rqueue)

            # Break the loop if the queue is empty or the maximum number of iterations is reached
            if not message or i >= max_iterations:
                logging.debug("Finished processing all allocted tasks. Now exiting...")
                break

            # Introduce delay in processing messages when using debug mode
            if debug:
               logging.debug("Sleeping...")
               time.sleep(30)
               logging.debug("Simulated delay complete...")

            # Process the message
            logging.debug("Handing over task to external app: %s", message)
            if message != None:
                process_message(message)    
            else:
                logging.warning("message: Invalid or empty message, skipping to next task")


if __name__ == "__main__":
    main()


