import redis
import argparse

host = "localhost"
port = 6379
queue_name = "model_runner:queue"

rdb = redis.Redis(host=host, port=port)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Run metric model on demand nodes")
    parser.add_argument('-w', '--worker', help="name of worker")
    args = parser.parse_args()
    worker = args.worker

    print "Starting worker: %s" % worker
    while(True):
 
        # Get a job from the queue
        item = rdb.blpop(queue_name)
        print "%s, %s" % (worker, item)
        
        # Update job
        # generate the key for this job
        job_key = "model_runner:jobs:%s" % item[1]
        rdb.hset(job_key, "worker", worker)

        # NOTE:  without transactions, it's "possible" that the above job gets pulled from the queue
        # but not processed and is therefore "lost". 
    
