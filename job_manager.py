"""
Module for managing job running and sync between primary and workers
"""
import os, uuid, datetime
import redis
import re
import pickle

class JobManager:

    STATUS_CREATED  = "CREATED"
    STATUS_QUEUED   = "QUEUED"
    STATUS_RUNNING  = "RUNNING"
    STATUS_COMPLETE = "COMPLETE"
    STATUS_FAILED   = "FAILED"

    """ Manage running and syncing job data between primary and workers """
    def __init__(self, redis_url, primary_url, worker_url, data_dir):
        port_re = re.compile(r'(?<=:)\d+$')
        host_re = re.compile(r'^.*(?=:\d+$)')
        redis_host_match = host_re.search(redis_url)
        redis_port_match = port_re.search(redis_url)
        if(not redis_host_match or not redis_port_match):
            raise ValueError("invalid redis url: %s" % redis_url)

        self.rdb = redis.Redis(host=redis_host_match.group(0), 
                                 port=redis_port_match.group(0))
        self.primary_url = primary_url
        self.worker_url = worker_url
        if(not os.path.exists(data_dir)):
            os.mkdir(data_dir)
        self.data_dir = data_dir

    # wrapper for redis to pickle input
    def hset(self, hash_name, key, obj):
        pickled_obj = pickle.dumps(obj)
        self.rdb.hset(hash_name, key, pickled_obj)

    # wrapper for redis to unpickle 
    def hget(hash_name, key):
        pickled_obj = self.rdb.hget(hash_name, key)
        return pickle.loads(pickled_obj)

    def enqueue(job, job_data_blob):
    """ write job data to file and queue up for processing
        intended to be run from primary server
        job_data_blob is a blob of a zip file to be written to disk """
        
        file_handle = open(os.path.join(self.data_dir, "input.zip"), "w")
        file_handle.write(job_data_blob)

        # monkey patch server where worker will get data from
        job.primary_url = self.primary_url

        # add to global job list then queue it to be run
        self.hset("model_runner:jobs", job.uuid, job)
        job_queue = "model_runner:queues:%s" % job.model
        self.rdb.rpush(job_queue, job.uuid)
        



    # whether the machine this is running on is also primary  
    def worker_is_primary(self):
        return self.primary_url == self.worker_url

class Job:

    """ Maintain the state of a ModelRunner Job """
    def __init__(self, model):
        self.model = model
        self.uuid = uuid.uuid4() 
        self.created = datetime.datetime.utcnow()
        self.status = JobManager.STATUS_CREATED



