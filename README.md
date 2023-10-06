# jobs-autoscale-demo
## PROJECT OVERVIEW
This project demonstrates how to set up KEDA to manage autoscaling for kubernetes jobs that will process tasks from a Redis list that acts as a FIFO queue.
It consists of a front-end api that creates tasks, a redis server to act as a queue and a worker app that processes the tasks.
The project uses KEDA 2.12 to manage autoscaling and has been tested on OpenShift 4.12.



## WORKING
Fully functional.



## NOT WORKING/NOT TESTED
Nothing identified, you tell me.



## GIT REPO OVERVIEW
The high-level structure of the repository is:
- **api-module:** an API component that receives a list of items to be processed and writes it to the queue
- **queue-module:** a queue componnent supported by a redis server that stores queued items
- **worker-module:** a worker module that consists of a back-end app that reads items from the queue and processes them
- **shared:** openshift and bash scripts that provide general funcionality or are used by multiple modules


## ENVIRONMENT SETUP AND INITIALIZATION
### Overview
This project has been tested with the following setup:
- OpenShift 4.12
- RHEL 8.8 with the following cli tools
- OpenShift cli 4.12
- Keda 2.12
- Helm 3.11.1
- podman version 4.4.1
- git version 2.39.3

Please ensure your environment is using one of the tested setups before reporting any bugs.


### Pre-requisites
1. Ensure all tools have been installed accordingly to the tested setups. Keda instructions are provded below and for the remaining tools follow the usual steps.

2. Ensure you have a docker.io registry, quay.io registry or equivelent registry account to store your container images


### Keda initial setup
1. Review the **app-env-setup.sh** file located in the project root folder file and update the environment variables to match your needs

2. From the project root dir, load environment variables
```
$ source shared/env-setup.sh
```

3. Login to your Openshift cluster
```
$ oc login --server $OCP_API -u $OCP_USER  -p $OCP_PASS
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
1. Create the openshift project to host this demo
```
$ oc new-project $OCP_PROJECT
```

2. Generate your container repository credentials in base64 format.
```
$ echo -n {"auths": {"docker.io": {"username": "<username>", "password": "<password>"}}} | base64
e2F1dGhzOiB7ZG9ja2VyLmlvOiB7dXNlcm5hbWU6IDx1c2VybmFtZT4sIHBhc3N3b3JkOiA8cGFz
c3dvcmQ+fX19
```

2. Generate your redis password in base64 format.
```
$ echo -n 3R8P8reeQVqTrwGT | base64
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


### Building and deploying the API module
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
$ podman image push $CONTAINER_REPO/jobs-api:latest
```


### Building the queue module
1. From the queue-module root dir, build the container
```
$ podman build -f Containerfile -t $C_REPO_PATH/jobs-queue:latest
STEP 1/5: FROM rhel8/redis-6

(OUTPUT SUPRESSED ...)

Successfully tagged docker.io/username/jobs-queue:latest
31b9c7be7df257b386dc22fc18569a60f3be8ca734d3ea1524266ccb28de97d2
```

2. Push the image into your preferred container repo
```
$ podman image push $C_REPO_PATH/jobs-queue:latest
```


### Building and testing the worker module
1. From the worker-module root dir, build the container
```
$ $ podman build -f Containerfile -t $C_REPO_PATH/jobs-worker:latest
[1/2] STEP 1/5: FROM ubi8 AS builder

(OUTPUT SUPRESSED ...)

Successfully tagged docker.io/username/jobs-worker:latest
7c6142e156a14840e85d7bb4efb9ffba46dc0ae97a2c46befd3d5c14a2b710eb
```

2. Push the image into your prefered container repo
```
$ podman image push $C_REPO_PATH/jobs-worker:latest
```



## DEPLOYING AND RUNNING THE APPLICATION

1. From the project root dir, deploy the queue-app into OCP via YAML config file
```
$ oc apply -f jobs-module/openshift/cfg-queue.yaml
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
$ curl -si -H "Authorization: APIKey 96w9EXfen2zEJxcd" --insecure https://$API_URL
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
$ oc rsh svc/redis-svc redis-cli -a 3R8P8reeQVqTrwGT LRANGE default 0 -1
Warning: Using a password with '-a' or '-u' option on the command line interface may not be safe.
1) "prime 100 150"
2) "prime 210 233"
3) "prime 345 700"
4) "finbonnaci 100 1111"
```

5. Call the api via POST method to send your own custom data
```
$ curl -si -X POST -H "Authorization: APIKey 96w9EXfen2zEJxcd" -H "Content-Type: application/json" \
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




