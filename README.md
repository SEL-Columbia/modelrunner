Model Runner 
============

Model Runner is a light-weight job management web application.  
The purpose is to distribute model runs (i.e. jobs) across servers.

[![Build Status](https://travis-ci.org/SEL-Columbia/model_runner.svg?branch=master)](https://travis-ci.org/SEL-Columbia/model_runner.svg?branch=master)

Components
----------

- Primary Server
  
    The server that hosts the model_runner REST API and manages jobs

- Worker 

    A server that runs jobs and exposes job log and ability to stop a running job

- Model
  
    Model that can be run with inputs on a Worker


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
    http://localhost:8080/jobs/$job_id

    {
        "id": "df11e13d-87d5-433b-ad28-9b27b95f6e3e",
        "message": "OK:  Killed job id df11e13d-87d5-433b-ad28-9b27b95f6e3e"
    }

    ```

- /jobs (get)

    Get all jobs (returns an html view for now)


Worker Process
--------------

Workers wait on 2 queues:

1.  model_runner:queues:&lt;model&gt;

  This is where it waits for jobs to run a specific model

2.  model_runner:queues:&lt;worker_id&gt;

  This is where it waits for a job to be killed

Additionally, the Primary waits on a queue:

- model_runner:queues:&lt;primary_id&gt;

  This is where it waits to be notified of a finished job

Note:  Workers will log both info and error output which will be available via web-interface through the Primary server

![Diagram](http://sel-columbia.github.io/model_runner/diagram.png "diagram")

Installation and Deployment
---------------------------

See .travis.yml for details

Development & Testing
-----------

Once you've made changes to your branch run `./testing/test_full.sh` and
ensure it's exit code is 0.
