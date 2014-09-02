import tornado
import tornado.ioloop
import tornado.web
import os, uuid

# setup config options
import config

from tornado.options import parse_command_line, parse_config_file

__JOB_DIR__ = "data/"

class SubmitJobForm(tornado.web.RequestHandler):
    def get(self):
        self.render("submit_job.html")

class JobHandler(tornado.web.RequestHandler):

    """
    Store the input file and queue the job

    TODO:  
    - Allow URL based job input
    - Handle exceptions
    """
    def post(self):
        model = self.get_argument('model')
        fileinfo = self.request.files['zipfile'][0]
        print "fileinfo is", fileinfo
        print "model: %s" % model
        fname = fileinfo['filename']
        
        job_uuid = str(uuid.uuid4())
        this_job_dir = os.path.join(__JOB_DIR__,job_uuid)
        os.makedirs(this_job_dir)

        extn = os.path.splitext(fname)[1]
        #TODO Check if extn is zip 
        fh = open(os.path.join(this_job_dir,"input.zip"), 'w')
        fh.write(fileinfo['body'])
        self.finish(fname + " is uploaded!! Check %s folder" % this_job_dir)

if __name__ == "__main__":
    parse_command_line()
    parse_config_file("config.ini")
    application = tornado.web.Application([
            (r"/jobs/submit", SubmitJobForm),
            (r"/jobs", JobHandler),
            ], 
            debug=config.options.debug)

    application.listen(config.options.port)

    # get the command_ keys
    command_keys = [key for key in config.options.as_dict().keys() if key.startswith("model_command")]
    comand_dict = {k: config.options.as_dict().get(k, None) for k in command_keys}
    # TODO:  Setup JobManager with config options and command_dict
    tornado.ioloop.IOLoop.instance().start()
