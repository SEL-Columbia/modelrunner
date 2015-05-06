import os, uuid
import StringIO
from urlparse import urlparse
import json

import tornado
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.gen
from tornado.options import parse_command_line, parse_config_file
from concurrent.futures import ThreadPoolExecutor

# setup config options
import config
import job_manager

THREAD_POOL = ThreadPoolExecutor(4)

import datetime

# to allow date_times within an object to be json encoded
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)

class SubmitJobForm(tornado.web.RequestHandler):

    def initialize(self, models):
        self.models = models

    def get(self):
        self.render("submit_job.html", models=self.models)

class JobOptionsModule(tornado.web.UIModule):

    def get_data_dir(self, job, worker_dir=False):
        if(worker_dir): 
            if(getattr(job, "worker_data_dir", False)):
                    return job.worker_data_dir
        if(not worker_dir): 
            if(getattr(job, "primary_data_dir", False)):
                   return job.primary_data_dir
        if(getattr(job, "data_dir", False)): #legacy
               return job.data_dir
        return "data"


    def kill_url(self, job):
        return "jobs/" + job.uuid + "/kill"

    def log_url(self, job):
        # TODO:  Make data dir based on options config
        return job.worker_url + "/" + self.get_data_dir(job, worker_dir=True) + "/" + job.uuid + "/job_log.txt"

    def download_url(self, job):
        return job.primary_url + "/" + self.get_data_dir(job, worker_dir=False) + "/" + job.uuid + "/output.zip"

    def render(self, job):
        href_templ = "<a href=%s>%s</a>" 
        # may be confusing, but we need to make kill links ajax 
        href_ajax_templ = "<a class='ajax_link' href=%s>%s</a>" 
        if job.status == job_manager.JobManager.STATUS_RUNNING:
            log_option = href_templ % (self.log_url(job), "Log")
            kill_option = href_ajax_templ % (self.kill_url(job), "Kill")
            return "%s,%s" % (log_option, kill_option)

        if job.status == job_manager.JobManager.STATUS_COMPLETE:
            log_option = href_templ % (self.log_url(job), "Log")
            dload_option = href_templ % (self.download_url(job), "Download")
            return "%s,%s" % (log_option, dload_option)

        if job.status == job_manager.JobManager.STATUS_FAILED:
            log_option = href_templ % (self.log_url(job), "Log")
            return log_option

        return ""
        

class JobKillHandler(tornado.web.RequestHandler):

    def initialize(self, job_mgr):
        self.job_mgr = job_mgr

    """
    Kill the designated job
    """
    def get(self, job_uuid):
        job =  self.job_mgr.get_job(job_uuid)
        self.job_mgr.kill_job(job)
        response_dict = {'message': "OK:  Killed job id %s" % job.uuid, 'id': job.uuid}
        self.write(response_dict)
        self.finish()

class JobHandler(tornado.web.RequestHandler):

    def initialize(self, job_mgr):
        self.job_mgr = job_mgr

    @tornado.gen.coroutine
    def post(self):
        """
        Store the input file and queue the job

        TODO:  
        - Allow URL based job input
        - Handle exceptions
        """

        model = self.get_argument('model')
        job_name = self.get_argument('job_name')
         # create new job
        job = job_manager.Job(model)
        job.name = job_name
        file_url = self.get_argument('zip_url', default=False)
        # validation
        if((not file_url) and (not len(self.request.files) > 0)):
            response_dict = {'message': "Error:  Invalid input.  Please select a valid url or file"}
            self.write(response_dict)
            self.finish()

        # add job to queue and list
        if(file_url):
            parsed = urlparse(file_url)
            if(not parsed.scheme):
                response_dict = {'message': "Error:  Invalid url (needs a scheme...i.e. http://)"}
                self.write(response_dict)
                self.finish()

            # self.job_mgr.enqueue(job, job_data_url=file_url)
            # don't block
            # yield tornado.gen.Task(self.enqueue, job, job_data_url=file_url)
            yield THREAD_POOL.submit(self.job_mgr.enqueue, job, job_data_url=file_url)

        else: 
            file_info = self.request.files['zip_file'][0]
            file_name = file_info['filename']
            # self.job_mgr.enqueue(job, job_data_blob=file_info['body'])
            # don't block
            # yield tornado.gen.Task(self.enqueue, job, job_data_blob=file_info['body'])
            yield THREAD_POOL.submit(self.job_mgr.enqueue, job, job_data_blob=file_info['body'])
       
        response_dict = {'message': "OK:  Submitted job id %s" % job.uuid, 'id': job.uuid}
        self.write(response_dict)
        self.finish()

    def enqueue(self, job, job_data_blob=None, job_data_url=None, callback=None):
            self.job_mgr.enqueue(job, job_data_blob=job_data_blob, job_data_url=job_data_url)
            return callback()# tornado coroutine yield seems to want a return val

    """
    Get the list of jobs
    """
    def get(self, job_uuid=None):
        if(job_uuid): # single job info
            job = self.job_mgr.get_job(job_uuid)
            json_job = DateTimeEncoder().encode(job.__dict__)
            self.write(json_job)
            self.finish()
        else: # TODO:  refactor to return only job json
            jobs =  self.job_mgr.get_jobs()
            # order descending
            jobs.sort(key=lambda job: job.created, reverse=True)
            self.render("view_jobs.html", jobs=jobs)
           
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

if __name__ == "__main__":

    # so we can load config via cmd line args
    parse_command_line()
    parse_config_file(config.options.config_file)

    # get the command_ keys
    command_dict = config.options.group_dict("model_command")
    models = command_dict.keys()

    jm = job_manager.JobManager(config.options.redis_url, 
                                config.options.primary_url, 
                                config.options.worker_url,
                                config.options.data_dir,
                                command_dict,
                                config.options.worker_is_primary)

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
    }

    application = tornado.web.Application([
            (r"/", MainHandler),
            (r"/jobs/submit", SubmitJobForm, dict(models=models)),
            (r"/jobs", JobHandler, dict(job_mgr=jm)),
            (r"/jobs/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", JobHandler, dict(job_mgr=jm)),
            (r"/jobs/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/kill", JobKillHandler, dict(job_mgr=jm)),
            ], 
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=config.options.debug, 
            ui_modules={'JobOptions': JobOptionsModule},
            **settings
            )

    application.listen(config.options.port)

    # TODO:  Setup JobManager with config options and command_dict
    tornado.ioloop.IOLoop.instance().start()
