Model Runner 
============

Model Runner is a light-weight job management web application.  
The purpose is to distribute model runs (i.e. jobs) across servers.

If you have a model that takes an input file (or files) and returns an
output file (or files) and runs in memory, you can expose it via the 
web to a broader audience via Model Runner.  

[![Build Status](https://travis-ci.org/SEL-Columbia/modelrunner.svg?branch=master)](https://travis-ci.org/SEL-Columbia/modelrunner.svg?branch=master)


Architecture
------------

![Diagram](http://sel-columbia.github.io/modelrunner/diagram.png "diagram")


Components
----------

- Primary Server
  
    The server that hosts the modelrunner REST API and manages jobs

- Worker 

    A server that runs jobs and exposes job log and ability to stop a running job

- Model
  
    Model that can be run with inputs on a Worker


Worker Process
--------------

Workers wait on 2 queues:

1.  modelrunner:queues:&lt;model&gt;

  This is where it waits for jobs to run a specific model

2.  modelrunner:queues:&lt;worker_id&gt;:&lt;model&gt;

  This is where it waits for a job (specific to model) to be killed

Additionally, the Primary waits on a queue:

- modelrunner:queues:&lt;primary_id&gt;

  This is where it waits to be notified of a finished job

Note:  Workers will log both info and error output which will be available via web-interface through the Primary server


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

- /jobs (get)

    Get all jobs (returns an html view for now)


Bash API
--------

There's a sample bash api for interacting with a modelrunner instance.

Here's a session:

```
# set the modelrunner instance primary server and temp dir
MR_SERVER=127.0.0.1
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

4.  Setup the server via `fab -H mr@your_server setup:config_file=your_config.ini,environment=<dev|prod>` (see sample config.ini for a guide)

5.  Start the server via `fab -H mr@your_server start:configuration=<worker|primary>,environment=<dev|prod>` 

See fabfile.py for more automated deployment details/options.

For production deployments, we use [nginx](http://wiki.nginx.org) as the static file server on the primary and worker servers.  See the sample devops/<primary|worker>.nginx config file for details.

Redis is hosted on the primary server, so you'll want to secure access to the redis port (default 6379) and only allow requests to it from worker ip addresses.  Using ufw for firewall protection with ports secured, this should allow redis access for the worker (to be run on primary server running Ubuntu):

```
ufw allow from <worker_ip_address> to any port 6379
```

### Troubleshooting

When workers start, they wait for all model jobs.  This can result in multiple jobs running on the same server.  To prevent this, kill the unwanted model specific processes via `kill -s TERM $(cat job_worker_<model>.pid)`

When workers are brought down it appears that client connections to redis sometimes remain.  These clients may consume a model job from the queue, making it disappear without being processed.  You can see these connections by doing a `client list` from `redis-cli`.  You can kill these connections with `client kill`.  

Development & Testing
-----------

Assumptions for setting up a development environment:
- [anaconda](https://docs.continuum.io/anaconda/install) is installed (and some familiarity with it is useful)
- This github repository has been cloned to your machine to `mr_src` directory and your are in that directory.

A simple development environment with one primary and one worker can be setup via the following 

```
conda create -n modelrunner python=2.7
source activate modelrunner
python setup.py develop
conda install redis
```

Once you've made changes to your branch, start up a primary and worker in dev mode, run `./testing/test_full.sh <server>` and
ensure it's exit code is 0.
