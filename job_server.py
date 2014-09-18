import tornado
import tornado.ioloop
import tornado.web
import os, uuid
import StringIO

# setup config options
import config

from tornado.options import parse_command_line, parse_config_file

import job_manager

import tornado.escape
 
# For error messages
class FlashMessageMixin(object):
    def set_flash_message(self, key, message):
        if not isinstance(message, basestring):
            message = tornado.escape.json_encode(message)
                                
        self.set_cookie('flash_msg_%s' % key, message)
                                            
    def get_flash_message(self, key):
        val = self.get_cookie('flash_msg_%s' % key)
        self.clear_cookie('flash_msg_%s' % key)
                                                                        
        if val is not None:
            val = tornado.escape.json_decode(val)
                                                                                                    
        return val

class SubmitJobForm(tornado.web.RequestHandler, FlashMessageMixin):

    def initialize(self, models):
        self.models = models

    def get(self):
        flash_msg = self.get_flash_message('error')
        self.render("submit_job.html", models=self.models, flash_msg=flash_msg)

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
        if job.status == job_manager.JobManager.STATUS_RUNNING:
           log_option = href_templ % (self.log_url(job), "Log")
           kill_option = href_templ % (self.kill_url(job), "Kill")
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
        self.redirect("/jobs")

class JobHandler(tornado.web.RequestHandler, FlashMessageMixin):

    def initialize(self, job_mgr):
        self.job_mgr = job_mgr

    """
    Store the input file and queue the job

    TODO:  
    - Allow URL based job input
    - Handle exceptions
    """
    def post(self):
        model = self.get_argument('model')
        job_name = self.get_argument('job_name')
         # create new job
        job = job_manager.Job(model)
        job.name = job_name
        file_url = self.get_argument('zip_url', default=False)
        # validation
        if((not file_url) and (not len(self.request.files) > 0)):
            self.set_flash_message('error', "Invalid input.  Please select a valid url or file")
            self.redirect('/jobs/submit')

        # add job to queue and list
        if(file_url):
            self.job_mgr.enqueue(job, job_data_url=file_url)
        else: 
            file_info = self.request.files['zip_file'][0]
            file_name = file_info['filename']
            self.job_mgr.enqueue(job, job_data_blob=file_info['body'])
       
        self.redirect("/jobs")

    """
    Get the list of jobs
    """
    def get(self):
        jobs =  self.job_mgr.get_jobs()
        # order descending
        jobs.sort(key=lambda job: job.created, reverse=True)
        self.render("view_jobs.html", jobs=jobs)
       
if __name__ == "__main__":

    parse_config_file("config.ini")
    parse_command_line()

    # get the command_ keys
    command_dict = config.options.group_dict("model_command")
    models = command_dict.keys()

    jm = job_manager.JobManager(config.options.redis_url, 
                                config.options.primary_url, 
                                config.options.worker_url,
                                config.options.data_dir,
                                command_dict,
                                config.options.worker_is_primary)


    application = tornado.web.Application([
            (r"/jobs/submit", SubmitJobForm, dict(models=models)),
            (r"/jobs", JobHandler, dict(job_mgr=jm)),
            (r"/jobs/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/kill", JobKillHandler, dict(job_mgr=jm)),
            ], 
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=config.options.debug, 
            ui_modules={'JobOptions': JobOptionsModule}
            )

    application.listen(config.options.port)

    # TODO:  Setup JobManager with config options and command_dict
    tornado.ioloop.IOLoop.instance().start()
