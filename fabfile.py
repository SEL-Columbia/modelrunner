# fabfile for managing modelrunner deployments
import os

from fabric.api import env, run, settings, cd, put, sudo
import fabric

DEFAULTS = {
    'home': '/home/mr',
    'configuration': 'primary', 
    'config_file': 'config.ini',
    'environment': 'dev', 
    'project': 'model_runner',
    'modelrunner_repo': 'https://github.com/SEL-Columbia/model_runner',
    'modelrunner_branch': 'master'
    }

def run_in_conda_env(command, conda_env="model_runner"):
    d = {
        'conda_env': conda_env,
        'conda_path': os.path.join(env.home, "miniconda", "bin"),
        'command': command
    }
    run("PATH=%(conda_path)s:$PATH && source activate %(conda_env)s && %(command)s" % d, pty=False)


def run_conda_enabled(command):
    d = {
        'conda_path': os.path.join(env.home, "miniconda", "bin"),
        'command': command
    }
    run("PATH=%(conda_path)s:$PATH && %(command)s" % d, pty=False)


def stop():
    print("stopping modelrunner processes")
    run("./model_runner/devops/stop_processes.sh")

setup_called = False
def setup_env(**args):
    global setup_called
    if setup_called: return
    setup_called = True
    # use ssh config if available
    if env.ssh_config_path and os.path.isfile(os.path.expanduser(env.ssh_config_path)):
        env.use_ssh_config = True

    env.update(DEFAULTS)
    #allow user to override defaults
    env.update(args)
    env.project_directory = os.path.join(env.home, env.project)

def setup(**args):
    """
    Install or update the deployment on a machine
    (should NOT wipeout any data)
    Assumes machine has been setup with mr user under /home/mr
    """
    setup_env(**args)
    print("baseline setup on %(host_string)s" % env)
    sudo("apt-get -y install git curl")

    update_model_runner()
   
    # setup conda
    run("./model_runner/devops/setup.sh")

    # create environ for model_runner
    run_conda_enabled("./model_runner/devops/setup_model_runner.sh")

    # setup sequencer (not truly needed on primary, but keep 'em consistent for now)
    run_conda_enabled("./model_runner/devops/setup_sequencer.sh")

    # deploy appropriate config file
    put(env.config_file, './model_runner/config.ini')

def update_model_runner(**args):
    setup_env(**args)
    # update modelrunner
    pull(repo=env.modelrunner_repo, directory=env.project_directory, branch=env.modelrunner_branch)

    # don't rely on remote scripts from repo, instead push local setup scripts
    # to run
    with settings(warn_only=True):
        if run("test -d ./model_runner/devops").failed:
            run("mkdir -p ./model_runner/devops")
        
    put("./devops/*.sh", "./model_runner/devops", mode=0755) 
 

def start_primary():
    """
    Start the primary server
    """
    with cd(env.project_directory):
        # run_in_conda_env("nohup redis-server > redis.log &")
        if(env.environment == "prod"):
            run_in_conda_env("./devops/start_primary_production.sh")
        else:
            run_in_conda_env("./devops/start_primary.sh")

def start_worker():
    """
    Start the worker server
    """
    with cd(env.project_directory):
        run_in_conda_env("./devops/start_worker.sh")

def start(**args):
    """
    Start server of a particular configuration/environment
    (should NOT wipeout any data)
    Assumes machine has been setup with mr user under /home/mr
    """
    setup_env(**args)
    print("starting %(configuration)s on %(host_string)s" % env)

    start_config = {
        'primary': start_primary,
        'worker': start_worker
    }

    # stop existing processes
    stop()
    # start appropriate processes
    start_config[env.configuration]()

def pull(repo, directory, branch="master"):
    with settings(warn_only=True): 
        if run("test -d %s" % directory).failed:
            run("git clone %s" % repo)

    with cd(directory):
        # fetch repo, checkout branch and get rid of local 
        run("git fetch origin")
        run("git checkout %s" % branch)
        run("git reset --hard origin/%s" % branch)
        run('find . -name "*.pyc" | xargs rm -rf')
