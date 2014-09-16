Model Runner
============

Model Runner is a light-weight job management web application.  
The purpose is to distribute model runs (i.e. jobs) across servers.

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

- /jobs (post)

    Post a job (input as name, model, zip)

- /jobs (get)

    Get all jobs (as a view for now)

- /jobs/&lt;id&gt;/kill

    Kill a running job


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
