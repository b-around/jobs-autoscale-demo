# jobs-autoscale-demo
## PROJECT OVERVIEW
This project demonstrates how to set up KEDA to manage autoscaling for kubernetes jobs that will process tasks from a Redis list that acts as a FIFO queue.
It consists of a front-end api that creates a list of mathematical calculations tasks, a redis server to act as a queue for the tasts and a worker app that processes the tasks.
The application can handle two types of tasks: 
i)calulating the prime numbers for any given start number and end number range
ii)calulating the fibonacci sequence numbers for any given start number and end number range
All caculated values are written to the console. 
A tasks list is sent into the API using the following JSON format:
```
{  "tasks": ["<prime | fibonacci> <start-number> <end-number>", <additional tasks>]}
```
An example of a valid API request is:
```
{  "tasks": ["prime 1200 1300", "prime 2222 3455", "fibonacci 999 5000", "prime 10 555"]}
```



## WORKING
Fully functional.



## NOT WORKING/NOT TESTED
- Future update will include an option to save outputs onto persistent storage



## GIT REPO OVERVIEW
The high-level structure of the repository is:
- **api-module:** an API component that receives a list of items to be processed and writes it to the queue
- **queue-module:** a queue component supported by a redis server that stores queued items
- **worker-module:** a worker module that consists of a back-end app that reads items from the queue and processes them
- **shared:** OpenShift and bash scripts that provide general functionality or are used by multiple modules


## ENVIRONMENT SETUP AND INITIALIZATION
### Overview
This project has been tested with the following setup:
- OpenShift 4.12
- RHEL 8.8 with a valid RH developer susbcription and the following cli tools installed
- OpenShift cli 4.12
- Keda 2.12
- Helm 3.11.1
- podman version 4.4.1
- git version 2.39.3

Please ensure your environment is using one of the tested setups before reporting any bugs.


### Pre-requisites
1. Ensure all tools have been installed accordingly to the tested setups. Keda instructions are provided below and for the remaining tools follow the usual steps.

2. Ensure you have a docker.io registry, quay.io registry or equivalent registry account to store your container images


### Keda initial setup
The steps detailed in this section should only be executed ONCE per new cluster.
The instructions are referring to an explicit version of keda to avoid unintentional version upgrades in the event of accidentally running these instructions multiple times.

1. Review the **app-env-setup.sh** file located in the project root folder file and update the environment variables to match your needs

2. From the project root dir, load environment variables
```
$ source shared/env-setup.sh
```

3. Login to your Openshift cluster
```
$ oc login --server $OCP_API -u $OCP_USER -p $OCP_PASS
```

4. Add the Helm repo for keda
```
$ helm repo add kedacore https://kedacore.github.io/charts
```

5. Update the Helm repo
```
$ helm repo update
```

6. Install KEDA
```
$ helm install keda kedacore/keda --namespace keda --create-namespace --version 2.12.0
```

### OCP initial setup
The steps detailed in this section should only be executed ONCE per new project.

1. Create the OpenShift project to host this demo
```
$ oc new-project $OCP_PROJECT
```

2. Generate your container repository credentials in base64 format.
Note that in some environments the base64 encoded result may be split into two lines.
When using the output, make sure this is used as a single line.
```
$ echo -n {"auths": {"docker.io": {"username": "$C_REPO_USER", "password": "$C_REPO_PASS"}}} | base64

e2F1dGhzOiB7ZG9ja2VyLmlvOiB7dXNlcm5hbWU6IDx1c2VybmFtZT4sIHBhc3N3b3JkOiA8cGFz
c3dvcmQ+fX19
```

2. Generate your redis password in base64 format.
```
$ echo -n $REDIS_PWD | base64

M1I4UDhyZWVRVnFUcndHVA==
```

3. Update the secrets file shared/cfg-ocp-apps-parms.yaml to reflect your environment requirements
Do not forget the secrets should be entered base64 encoded

4. Create the configmaps and secrets
```
$ oc apply -f shared/cfg-ocp-apps-params.yaml 

configmap/my-configmap created
secret/redis-secret created
secret/my-dockerio-secret created
```

5. Create the persistent volume and claim to allow pods using persistent storage
```
$ oc apply -f shared/cfg-ocp-apps-storage.yaml 

persistentvolume/jobs-pv created
persistentvolumeclaim/jobs-vol-claim created
```



### (OPTIONAL) Podman initial setup
To test this application in a local developer machine and using podman, follow the instructions below.
The default podman network does not allow container name resolution and limits inter-container connectivity. Therefore, some additional plugins need to be installed.
These steps should only be executed ONCE per developer machine and when using a fresh podman installation that only has a default network.

1. Check have a custom podman network with DNS resolution active.
On a fresh installation you will only have the default 'podman' network and without dns enabled.
```
$ podman network ls

NETWORK ID    NAME        DRIVER
2f259bab93aa  podman      bridge

$ podman network inspect podman

[
     {
          "name": "podman",
          "id": "2f259bab93aaaaa2542ba43ef33eb990d0999ee1b9924b557b7be53c0b7a1bb9",
          "driver": "bridge",
          "network_interface": "cni-podman0",
          "created": "2023-10-11T11:59:48.552190757+01:00",
          "subnets": [
               {
                    "subnet": "10.88.0.0/16",
                    "gateway": "10.88.0.1"
               }
          ],
          "ipv6_enabled": false,
          "internal": false,
          "dns_enabled": false,
          "ipam_options": {
               "driver": "host-local"
          }
     }
]
```

2. Install podman plugins to allow dns resolution
```
$ sudo dnf install podman-plugins -y
```

3. Create a new network (demo-net in this example) to which you will later on attach the application containers
```
$ podman network create demo-net
```

4. Verify the network is available
```
$ podman network ls

NETWORK ID    NAME        DRIVER
37e3da108b96  demo-net    bridge
2f259bab93aa  podman      bridge 
```

5. Inspect the network settings and verify that dns resolution is now enabled for the new network
```
$ podman network inspect demo-net

[
     {
          "name": "demo-net",
          "id": "37e3da108b96ba7e9114894b39f78d949265fef2d529256ef854d0ca591b7c70",
          "driver": "bridge",
          "network_interface": "cni-podman1",
          "created": "2023-10-11T15:00:27.919566997+01:00",
          "subnets": [
               {
                    "subnet": "10.89.0.0/24",
                    "gateway": "10.89.0.1"
               }
          ],
          "ipv6_enabled": false,
          "internal": false,
          "dns_enabled": true,
          "ipam_options": {
               "driver": "host-local"
          }
     }
]
```



## BUILDING AND TESTING THE APPLICATION
### Loading environment variables
1. Login to your container repository to upload your container images
```
$ podman login -u $C_REPO_USER -p $C_REPO_PASS $C_REPO
```

2. Login to the redhat registry to get access to Red Hat ubi and redis images
```
$ podman login -u $RH_REPO_USER -p $RH_REPO_PASS $RH_REPO
```


### API module
1. From the api-module root dir, build the container
```
$ podman build -f Containerfile -t $C_REPO_PATH/jobs-api:latest

STEP 1/10: FROM ubi8/python-311

(OUTPUT SUPRESSED ...)

Successfully tagged docker.io/username/jobs-api:latest
99b8dea9c2bc6a990bed570ecf681a192889feaead06295ec48c07b96f04f50b
```

2. Push the image into your preferred container repo
```
$ podman image push $C_REPO_PATH/jobs-api:latest
```


### Queue module
1. From the queue-module root dir, build the container
```
$ podman build -f queue-app/Containerfile -t $C_REPO_PATH/jobs-queue:latest

STEP 1/5: FROM rhel8/redis-6

(OUTPUT SUPRESSED ...)

Successfully tagged docker.io/username/jobs-queue:latest
31b9c7be7df257b386dc22fc18569a60f3be8ca734d3ea1524266ccb28de97d2
```

2. Push the image into your preferred container repo
```
$ podman image push $C_REPO_PATH/jobs-queue:latest
```


### Worker module
1. From the worker-module root dir, build the container
```
$ podman build -f Containerfile -t $C_REPO_PATH/jobs-worker:latest

[1/3] STEP 1/3: FROM ubi8 AS builder
[1/3] STEP 2/3: USER root
--> 745f1af98c4

(OUTPUT SUPRESSED ...)

[3/3] STEP 9/9: CMD ["python3", "worker.py"]
[3/3] COMMIT docker.io/username/jobs-worker:latest
--> e20525d3b16
Successfully tagged docker.io/username/jobs-worker:latest
e20525d3b16b5eb5dd2070ddccc70e2b3fb49000fd87a73ebea1c34bc4c7fba2
```


2. Push the image into your prefered container repo
```
$ podman image push $C_REPO_PATH/jobs-worker:latest
```


### (OPTIONAL) Testing all modules locally
Follow the steps below if you want to test the app locally on a developer machine using podman and prior to deploying into an OpenShift cluster

1. Start up the api module attached to the podman demo-net network
```
$ podman run -itd --name api-app \
  --network demo-net \
  -e APP_DEBUG=True \
  -e API_TOKEN=True \
  -e API_TOKEN_VALUE=$API_TOKEN \
  -e REDIS_URL=queue-app \
  -e REDIS_PWD=$REDIS_PWD \
  -p 5000:5000 \
  --volume /home/user/local/path:/container/path:z \
  $C_REPO_PATH/jobs-api:latest
```

2. Start up the queue module attached to the podman demo-net network
```
$ podman run -d --name queue-app \
  --network demo-net \
  $C_REPO_PATH/jobs-queue:latest \
  redis-server --bind 0.0.0.0 --loglevel debug --requirepass $REDIS_PWD --save ""
```


3. Populate the queue with a couple of tasks. 
When using a HTTP GET, the API self generates test data.
```
$ curl -H "Authorization: APIKey $API_TOKEN" \
   --insecure http://127.0.0.1:5000
```

4. Check the data is written to the queue
```
$ podman exec queue-app redis-cli -a $REDIS_PWD LRANGE default 0 -1

Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.
prime 100 150
prime 210 233
prime 345 700
finbonnaci 100 1111
```

5. Populate the queue with additional tasks provided via HTTP POST
```
$ curl -X POST -H "Authorization: APIKey $API_TOKEN" -H "Content-Type: application/json" \
   -d ' {"tasks": ["prime 1200 1300", "prime 2222 3455", "fibonacci 999 5000", "prime 10 555"]} ' \
   --insecure http://127.0.0.1:5000
```

6. Check the additional data is written to the queue
```
$ podman exec queue-app redis-cli -a $REDIS_PWD LRANGE default 0 -1

Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.
prime 100 150
prime 210 233
prime 345 700
finbonnaci 100 1111
prime 1200 1300
prime 2222 3455
fibonacci 999 5000
prime 10 555
```

7. Start up the worker module attached to the podman demo-net network
```
$ podman run -d --name worker-app \
  --network demo-net \
  -e APP_DEBUG=True \
  -e REDIS_URL=queue-app \
  -e REDIS_PWD=$REDIS_PWD \
  --volume /home/user/local/path:/container/path:z \
  $C_REPO_PATH/jobs-worker:latest
```

8. Run a watcher on the container processes and wait until the worker-app container finishes.
Note that the worker app has a built-in function to delay/sleep 30 seconds between each processed task to simulate computational complexity.
Once all tasks are processed and the queue empty, the container will gracefully exit. Hit CTRL-Z to exit the watcher.
```
$ watch podman ps

CONTAINER ID  IMAGE                                 COMMAND               CREATED         STATUS         PORTS                   NAMES
e4adf927e98e  docker.io/username/jobs-api:latest     python3 tasks-api...  2 hours ago     Up 2 hours     0.0.0.0:5000->5000/tcp  api-app
0d70013eec6c  docker.io/username/jobs-queue:latest   redis-server --bi...  2 hours ago     Up 2 hours                             queue-app
41f052d756cb  docker.io/username/jobs-worker:latest  python3 worker.py     33 seconds ago  Up 33 seconds                          worker-app
```



9. Review the worker-app logs and verify that each message gets processed and prime or fibonacci sequence numbers logged to the console.
```
$ podman logs worker-app

INFO:root:App log level set to DEBUG
DEBUG:root:Connecting to redis with auth only
DEBUG:root:Testing redis server connection
DEBUG:root:Processing tasks in the queue

(OUTPUT SUPRESSED ...)

*** PRIME CALCULATION COMPLETE ***

DEBUG:root:Message processed: prime 10 555
DEBUG:root:Reading message from queue: default
DEBUG:root:Finished processing all allocted tasks. Now exiting...
```




## OPTION 1 - DEPLOYING AND RUNNING THE APPLICATION VIA MANUAL YAML DEPLOYMENT
Follow the steps below to manually deploy each component of the application by using YAML config files

1. From the project root dir, deploy the queue-app into OCP via YAML config file
```
$ oc apply -f queue-module/openshift/cfg-queue.yaml

deployment.apps/redis-queue created
service/redis-svc created
```

2. From the project root dir, deploy the api-app into OCP via YAML config file
```
$ oc apply -f api-module/openshift/cfg-api.yaml 

deployment.apps/jobs-api created
service/jobs-api-svc created
route.route.openshift.io/jobs-api created
```

3. Call the api via GET method to automatically generate test data
```
$ curl -si -H "Authorization: APIKey $API_TOKEN" --insecure https://$API_URL

HTTP/1.1 200 OK
server: Werkzeug/3.0.0 Python/3.11.2
date: Fri, 06 Oct 2023 00:56:25 GMT
content-type: application/json
content-length: 61
set-cookie: 5af449b256b3c19b9ab88be409cc7341=c7c1b074b51175cd4241b910f84f5f87; path=/; HttpOnly; Secure; SameSite=None
cache-control: private

{
  "message": "Tasks successfully written to Redis queue"
}

```

4. Connect to the redis server via ocp service to verify that the items exist in the list
```
$ oc rsh svc/redis-svc redis-cli -a $REDIS_PWD LRANGE default 0 -1

Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.
1) "prime 100 150"
2) "prime 210 233"
3) "prime 345 700"
4) "finbonnaci 100 1111"
```

5. Call the api via POST method to send your own custom data
```
$ curl -si -X POST -H "Authorization: APIKey $API_TOKEN" -H "Content-Type: application/json" \
  -d '{  "tasks": ["prime 1200 1300", "prime 2222 3455", "prime 4123 5000"]}' \
  --insecure https://$API_URL

HTTP/1.1 200 OK
server: Werkzeug/3.0.0 Python/3.11.2
date: Fri, 06 Oct 2023 00:58:19 GMT
content-type: application/json
content-length: 61
set-cookie: 5af449b256b3c19b9ab88be409cc7341=c7c1b074b51175cd4241b910f84f5f87; path=/; HttpOnly; Secure; SameSite=None

{
  "message": "Tasks successfully written to Redis queue"
}
```

6. Connect to the redis server via ocp service to verify that additional items have been added
```
$ oc rsh svc/redis-svc redis-cli -a $REDIS_PWD LRANGE default 0 -1

Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.
1) "prime 100 150"
2) "prime 210 233"
3) "prime 345 700"
4) "finbonnaci 100 1111"
5) "prime 1200 1300"
6) "prime 2222 3455"
7) "prime 4123 5000"
```

7. From the project root dir, deploy the worker-app into OCP via YAML config file
```
$ oc apply -f worker-module/openshift/cfg-keda-worker.yaml 

triggerauthentication.keda.sh/keda-trigger-auth-redis-secret created
scaledjob.keda.sh/jobs-worker created
```

8. Verify that a set of jobs gets triggered immediately after creating the scaledjob resource
```
$ oc get jobs

NAME                COMPLETIONS   DURATION   AGE
jobs-worker-4lrqh   0/1           7s         7s
jobs-worker-644zs   0/1           7s         7s
jobs-worker-7jf78   0/1           7s         7s
jobs-worker-h9nm2   0/1           7s         7s
jobs-worker-m8cxh   0/1           7s         7s
jobs-worker-vwbck   0/1           7s         7s
jobs-worker-w2z47   0/1           7s         7s
```

9. Verify that after a couple of minutes all jobs come to a completion
```
$ oc get jobs

NAME                COMPLETIONS   DURATION   AGE
jobs-worker-4lrqh   1/1           37s        2m8s
jobs-worker-644zs   1/1           38s        2m8s
jobs-worker-7jf78   1/1           38s        2m8s
jobs-worker-h9nm2   1/1           37s        2m8s
jobs-worker-m8cxh   1/1           38s        2m8s
jobs-worker-vwbck   1/1           38s        2m8s
jobs-worker-w2z47   1/1           38s        2m8s
```

10. Inspect the logs for each pod associated with the completed jobs to see the outputs of the prime or Fibonacci calculations


## OPTION 2 - PACKAGING, DEPLOYING AND RUNNING THE APPLICATION VIA HELM CHART
Follow the steps below to use helm to automate deployment of this apllication components

1. Check you are using the correct project namespace
```
$ echo current_project is: $(oc config view --minify=true -o jsonpath='{.contexts[*].context.namespace}')
```

2. Go through the helm chart folder located under ./jobschart and review all values.yaml files and yaml template files
Update content as needed case the default values are not fir for pourpose

3. From the project root directory run a chart validation
```
$ helm install myapp ./jobschart --dry-run --debug --namespace $OCP_PROJECT
```

4. If the step above succeeded, proceed to install the app
All resources will be prefixed with the chosen release name, 'myapp' in the example below
```
$ helm install myapp ./jobschart --debug --namespace $OCP_PROJECT
```

5. (OPTIONAL) If you want to update the application following any changes to the chart values or templates run the command below
```
$ helm upgrade v2 . --debug --namespace $OCP_PROJECT
```

6. (OPTIONAL) If you want to remove the application run the command below
```
$ helm uninstall myapp --namespace $OCP_PROJECT
```

7. (OPTIONAL) If you want to share the helm cart you can package it using the command below fromt he project root directory
Distribute the tgz file along and the container images
```
$ helm package ./jobschart

Successfully packaged chart and saved it to: /home/admin/workspace/jobs-autoscale-demo/jobschart-0.2.0.tgz
```



