# -*- coding: utf-8 -*-
"""
Functions and classes supporting tornado based web server for modelrunner
"""

from urlparse import urlparse
import json
import datetime

import tornado
import tornado.web
import tornado.gen
from concurrent.futures import ThreadPoolExecutor

import manager as mgr

# Thread Pool used to handle handle large file uploads in parallel
# TODO:  Research more scalable methods
THREAD_POOL = ThreadPoolExecutor(4)


class DateTimeEncoder(json.JSONEncoder):
    """
    Allows date_times within an object to be json encoded
    """

    def default(self, obj):
        """
        overrides json.JSONEncoder implementation to
        support datetime types
        """
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)


class SubmitJobForm(tornado.web.RequestHandler):
    """
    Handles job submission input page rendering (but not the submission posts)
    """

    def initialize(self, models):
        """
        Args:
            models (list of str):  models to run
        """
        self.models = models

    def get(self):
        self.render("submit_job.html", models=self.models)


class JobKillHandler(tornado.web.RequestHandler):
    """
    Handles requests to kill a job
    """

    def initialize(self, job_mgr):
        """
        init with the Manager instance

        Args:
            job_mgr (modelrunner.JobManager):  JobManager instance
        """

        self.job_mgr = job_mgr

    def get(self, job_uuid):
        """
        Kill the designated job

        Args:
            job_uuid (str):  job id to kill

        """

        job = self.job_mgr.get_job(job_uuid)
        self.job_mgr.kill_job(job)
        response_dict = {'message': "OK:  Killed job id {}".format(job.uuid),
                         'id': job.uuid}
        self.write(response_dict)
        self.finish()


class JobHandler(tornado.web.RequestHandler):
    """
    Handles job submission posts and listing
    """

    def initialize(self, job_mgr):
        """
        init with the Manager instance

        Args:
            job_mgr (modelrunner.JobManager):  JobManager instance
        """

        self.job_mgr = job_mgr

    @tornado.gen.coroutine
    def post(self):
        """
        Store the input file and queue the job

        Input files may be rather large and time consuming to stream in,
        so this is made asynchronous via tornado coroutines in attempt to
        reduce blocking
        """

        model = self.get_argument('model')
        job_name = self.get_argument('job_name')

        # create new job
        job = mgr.Job(model)
        job.name = job_name
        file_url = self.get_argument('zip_url', default=False)
        # validation
        if((not file_url) and (not len(self.request.files) > 0)):
            response_dict = {'message':
                             "Error:  Invalid url or file"}
            self.write(response_dict)
            self.finish()

        # add job to queue and list
        if(file_url):
            parsed = urlparse(file_url)
            if(not parsed.scheme):
                response_dict = {'message': "Error:  Invalid url scheme"}
                self.write(response_dict)
                self.finish()

            yield THREAD_POOL.submit(self.job_mgr.enqueue, job,
                                     job_data_url=file_url)

        else:
            file_info = self.request.files['zip_file'][0]
            # file_name = file_info['filename']
            yield THREAD_POOL.submit(self.job_mgr.enqueue, job,
                                     job_data_blob=file_info['body'])

        response_dict = {'message': "OK:  Submitted job id {}".
                         format(job.uuid),
                         'id': job.uuid}
        self.write(response_dict)
        self.finish()

    def get(self, job_uuid=None):
        """
        Get or view jobs

        Args:
            job_uuid (str):  If not None, the job id to retrieve json for
        """

        if(job_uuid):  # single job info
            job = self.job_mgr.get_job(job_uuid)
            json_job = DateTimeEncoder().encode(job.__dict__)
            self.write(json_job)
            self.finish()
        else:
            # TODO:  refactor to return only job json
            #        for js to render
            jobs = self.job_mgr.get_jobs()
            # order descending
            jobs.sort(key=lambda job: job.created, reverse=True)
            self.render("view_jobs.html", jobs=jobs)


class JobOptionsModule(tornado.web.UIModule):
    """
    Helper class for simplifying job rendering in tornado html templates
    """

    def get_data_dir(self, job, worker_dir=False):
        if(worker_dir):
            if(getattr(job, "worker_data_dir", False)):
                return job.worker_data_dir
        if(not worker_dir):
            if(getattr(job, "primary_data_dir", False)):
                return job.primary_data_dir
        return "data"

    def kill_url(self, job):
        return "jobs/" + job.uuid + "/kill"

    def log_url(self, job):
        # TODO:  Make data dir based on options config
        return job.worker_url + "/" +\
                self.get_data_dir(job, worker_dir=True) + "/" +\
                job.uuid + "/job_log.txt"

    def download_url(self, job):
        return job.primary_url + "/" +\
                self.get_data_dir(job, worker_dir=False) + "/" +\
                job.uuid + "/output.zip"

    def render(self, job):
        """
        main method for rendering job links based on job status

        Args:
            job (modelrunner.Job):  job instance to render links for
        """

        href_templ = "<a href=%s>%s</a>"
        # may be confusing, but we need to make kill links ajax
        href_ajax_templ = "<a class='ajax_link' href=%s>%s</a>"
        if job.status == mgr.JobManager.STATUS_RUNNING:
            log_option = href_templ % (self.log_url(job), "Log")
            kill_option = href_ajax_templ % (self.kill_url(job), "Kill")
            return "%s,%s" % (log_option, kill_option)

        if job.status == mgr.JobManager.STATUS_COMPLETE:
            log_option = href_templ % (self.log_url(job), "Log")
            dload_option = href_templ % (self.download_url(job), "Download")
            return "%s,%s" % (log_option, dload_option)

        if job.status == mgr.JobManager.STATUS_FAILED:
            log_option = href_templ % (self.log_url(job), "Log")
            return log_option

        return ""


class MainHandler(tornado.web.RequestHandler):
    """
    root request handler for splash page
    """

    def get(self):
        self.render("index.html")
