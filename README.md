Model Runner 
============

Model Runner is a light-weight job management web application.  
The purpose is to distribute model runs (i.e. jobs) across servers.

If you have a model that takes an input file (or files) and returns an
output file (or files) and runs in memory, you can expose it via the 
web to a broader audience via Model Runner.  

[![Build Status](https://travis-ci.org/SEL-Columbia/modelrunner.svg?branch=master)](https://travis-ci.org/SEL-Columbia/modelrunner.svg?branch=master)

[![Coverage Status](https://coveralls.io/repos/github/SEL-Columbia/modelrunner/badge.svg?branch=master)](https://coveralls.io/github/SEL-Columbia/modelrunner?branch=master)

Architecture
------------

![Diagram](http://sel-columbia.github.io/modelrunner/diagram.png "diagram")


Components
----------

- Primary Server
  
    The server that hosts the modelrunner REST API and manages jobs

- Workers 

    Servers that perform model runs as jobs

- Model
  
    Model that can be run with inputs on a Worker


Job Processing
--------------

Worker nodes wait for jobs on a queue `modelrunner:queues:<model>`

The Primary node waits for completed jobs on its own queue `modelrunner:queues:<primary_id>`

Both node types also listen on channels for operational commands (i.e. update status, kill job)


API (Primary Server)
--------

(samples assume Primary running on localhost:8080)

- /jobs (post)

    Post a job 
    ```
    curl -s -F "job_name=test_`date +%Y-%m-%d_%H:%M:%S`" -F "model=test" -F "zip_file=@testing/input.zip" http://localhost:8080/jobs > response

    {
        "id": "6efecaab-7d9f-4207-b68d-5259915213af",
        "message": "OK:  Submitted job id 6efecaab-7d9f-4207-b68d-5259915213af"
    }

    ```

- /jobs/&lt;id&gt;

    Get job status
    ```
    http://localhost:8080/jobs/$job_id

    {
        "created": "2014-09-24T21:22:12.309192",
        "model": "test",
        "name": "test_kill_2014-09-24_17:22:12",
        "primary_data_dir": "data",
        "primary_url": "http://localhost:8000",
        "status": "FAILED",
        "uuid": "df11e13d-87d5-433b-ad28-9b27b95f6e3e",
        "worker_data_dir": "worker_data",
        "worker_url": "http://localhost:8888"
    }

    ```

- /jobs/&lt;id&gt;/kill

    Kill a running job
    ```
    http://localhost:8080/jobs/$job_id/kill

    {
        "id": "df11e13d-87d5-433b-ad28-9b27b95f6e3e",
        "message": "OK:  Killed job id df11e13d-87d5-433b-ad28-9b27b95f6e3e"
    }

    ```

- /jobs 

    Get all jobs

    When http 'Accept' header does not contain 'application/json', then this returns an html view

    When http 'Accept' contains 'application/json', then this returns a json dict of the jobs

    ```
    curl -H 'Accept: application/json' http://localhost:8080/jobs

    {
        "data": [
            {
                "created": "2016-05-24T19:01:10.429422",
                "model": "test",
                "name": "test_full_kill_2016-05-24_15:01:10",
                "on_primary": true,
                "primary_data_dir": "data",
                "primary_url": "http://localhost:8000",
                "status": "FAILED",
                "uuid": "26b8ab04-56a1-4614-83f6-5df843b33072",
                "worker_data_dir": "worker_data",
                "worker_url": "http://localhost:8888"
            },
            {
                "created": "2016-05-24T19:01:01.981654",
                "model": "test",
                "name": "test_full_2016-05-24_15:01:01",
                "on_primary": true,
                "primary_data_dir": "data",
                "primary_url": "http://localhost:8000",
                "status": "COMPLETE",
                "uuid": "d5f31f4d-22ae-4636-9caa-79362a959ba8",
                "worker_data_dir": "worker_data",
                "worker_url": "http://localhost:8888"
            }
        ]
    }
    ```

- /status

  Get status of modelrunner nodes

  ```
  curl -H 'Accept: application/json' http://localhost:8080/status

  {
      "data": [
          {
              "status": "RUNNING",
              "name": "http://localhost:8888;test",
              "node_url": "http://localhost:8888",
              "node_type": "WORKER",
              "version": "0.5.0",
              "model": "test"
          },
          {
              "status": "WAITING",
              "name": "http://localhost:8888;test_2",
              "node_url": "http://localhost:8888",
              "node_type": "WORKER",
              "version": "0.5.0",
              "model": "test_2"
          },
          {
              "status": "WAITING",
              "name": "http://localhost:8000",
              "node_url": "http://localhost:8000",
              "node_type": "PRIMARY",
              "version": "0.5.0",
              "model": null
          }
      ]
  }
  ```

Bash API
--------

There's a sample bash api for interacting with a modelrunner instance.

Here's a session:

```
# set the modelrunner instance primary server and temp dir
MR_SERVER=http://127.0.0.1:8080
# temp dir to store all working data
MR_TMP_DIR=$(mktemp -d)

# source the api
. testing/api_functions.sh

# create job and echo it's status
job_id=$(mr_create_job test_job_1 "test" "@testing/sleep_count_8.zip")
echo $(mr_job_status $job_id)

# kill the job
mr_kill_job $job_id

# create job and echo it's status
job_id=$(mr_create_job test_job_2 "test" "@testing/sleep_count_8.zip")
echo $(mr_job_status $job_id)

# wait for it to complete or until 10 second timeout
mr_wait_for_status $job_id "COMPLETE" 10
echo "SUCCESS"
```

Installation and Deployment
---------------------------

Deployment can be done via [fabric](http://www.fabfile.org) on Debian based distro's.
There are several options for deployment ranging from a single server "dev" to multi-server "prod" setups.  

Here are the basic steps (assumes you have a python environment with fabric installed locally):

1.  Bring up an Ubuntu/Debian instance(s) (henceforth referred to as "your_server").  Make sure the package repositories are updated by running `apt-get update`.  

2.  Create a user named 'mr' to run modelrunner under on your_server 

3.  On your local machine, clone this repo and cd into the modelrunner directory (if not already done)

4.  Update your config files for your primary and workers.  See modelrunner/config.py for parameter definitions.

5.  If servers had previously been started and you need to update modelrunner by running setup, you need to stop the servers via `fab -H mr@your_server stop` for primary and workers.  If you need to update the redis server, you stop it via `fab -H mr@your_server stop_redis`.  

6.  Setup the servers via `fab -H mr@your_server setup:config_file=your_config.ini,environment=<dev|prod>` (see sample config.ini for a guide).  
    - This step is independent of whether the server is a primary or worker server.
    - If environment is dev, then this will setup modelrunner using the source checked out on that server.  Otherwise, it will install modelrunner from the latest modelrunner conda package.

7.  For workers, setup the model to be run via `fab -H mr@your_server setup_model:model=<model_name>`.  Note that some models may not require this step.  It's also recommended that only one model be run per worker.  

8.  [optional] for separate redis servers, setup via `fab -H mr@your_server setup:redis_config_file=your_redis_config.conf` (ensure that the primary and worker configs reflect the correct redis url)

9.  Start servers:
    -  Start redis `fab -H mr@your_redis_server start_redis` 
    -  Start a primary server via `fab -H mr@your_primary_server start_primary:environment=<dev|prod>` 
    -  Start a worker for a particular model via `fab -H mr@your_worker_server start_worker:model=<model_name>,environment=<dev|prod>` (if needed, make sure that step 6 was performed for that model on that worker server) 

10.  Restart servers:
    -  Shutown each worker via `fab -H mr@your_worker_server stop` 
    -  Shutdown primary via `fab -H mr@your_primary_server stop`
    -  Shutdown redis server via `fab -H mr@your_redis_server stop_redis`
    -  Follow step 9 above to start back up

See fabfile.py and the devops sub-directory for more automated deployment details/options.

For production deployments, we use [nginx](http://wiki.nginx.org) as the static file server on the primary and worker servers.  See the sample devops/<primary|worker>.nginx config file for details.

You may want to restrict access to the redis port (default 6379) and only allow requests to it from worker ip addresses.  Using ufw for firewall protection with ports secured, this should allow redis access for the worker (to be run on redis server):

```
ufw allow from <node_ip_address> to any port 6379
```

### Troubleshooting

When workers are brought down it appears that client connections to redis sometimes remain.  These clients may consume a model job from the queue, making it disappear without being processed.  You can see these connections by doing a `client list` from `redis-cli`.  You can kill these connections with `client kill`.  

Development & Testing
-----------

Assumptions for setting up a development environment:
- [anaconda](https://docs.continuum.io/anaconda/install) is installed (and some familiarity with it is useful)
- This github repository has been cloned to your machine to `mr_src` directory and your are in that directory.

A simple development environment with one primary and one worker can be setup via the following 

```
conda create -n modelrunner python=3
source activate modelrunner
python setup.py develop
conda install redis
```

See `.travis.yml` for setup required to run tests.  Note that if you are repeatedly running tests in your local dev environment, you can flush the redis db and cleanup the data directories between tests with:

```
redis-cli flushdb
rm -rf data/*
rm -rf worker_data/*
```

To test, make sure all modelrunner processes have been stopped and startup redis:

```
./scripts/stop_processes.sh
./scripts/start_redis.sh
```

Now you can run `nosetests`

Additionally, you can run broader tests that cover the web application via:

```
# start primary and 2 worker servers
./scripts/start_primary.sh
./scripts/start_worker.sh test
./scripts/start_worker.sh test_2

# now run the tests
./testing/test_full.sh http://localhost:8080
./testing/test_queueing.sh http://localhost:8080
```

### Testing via Docker

You can setup a primary and several workers in a sandbox quickly via docker.  

Currently you'll need a docker image with ssh enabled so you can setup the servers via fabric.

A recommended docker and docker-compose installation, ssh image and compose file is available [here](https://github.com/chrisnatali/devops/tree/master/docker).  Following the guidelines there, you can setup a primary and 2 servers ready for deployment via:

```
docker-compose -p primary up -d server
docker-compose -p worker1 up -d server
docker-compose -p worker2 up -d server
```

Then get the ip addresses and setup the servers via steps 4-7 from the deployment steps above.  

If you want to pass through the ports and/or the worker ip addresses to the host (e.g. to test the web site manually), you may need to create custom docker-compose files (really straightforward following docker documentation)
