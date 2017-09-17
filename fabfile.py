# -*- coding: utf-8 -*-
# fabfile for managing modelrunner deployments
import os

from fabric.api import task, env, run, settings, cd, put, sudo

# These are the main arguments for tasks (i.e. included in **args)
# Other arguments will be defined per task
DEFAULTS = {
    'home': '/home/mr',
    'config_file': 'config.ini',
    'redis_config_file': None,
    'environment': 'dev',
    'project': 'modelrunner',
    'modelrunner_repo': 'https://github.com/SEL-Columbia/modelrunner',
    'modelrunner_branch': 'master'
    }


def run_in_conda_env(command, conda_env="modelrunner"):
    d = {
        'conda_env': conda_env,
        'conda_path': os.path.join(env.home, "miniconda", "bin"),
        'command': command
    }
    run("PATH={conda_path}:$PATH && source activate {conda_env} && {command}"
        .format(**d),
        pty=False)


def run_conda_enabled(command):
    d = {
        'conda_path': os.path.join(env.home, "miniconda", "bin"),
        'command': command
    }
    run("PATH={conda_path}:$PATH && {command}".format(**d), pty=False)


setup_called = False


def setup_env(**args):
    global setup_called
    if setup_called:
        return
    setup_called = True
    # use ssh config if available
    if env.ssh_config_path and \
            os.path.isfile(os.path.expanduser(env.ssh_config_path)):
        env.use_ssh_config = True

    env.update(DEFAULTS)
    # allow user to override defaults
    env.update(args)
    env.project_directory = os.path.join(env.home, env.project)


@task
def stop(**args):
    """
    Stops all modelrunner process (except redis)
    """

    setup_env(**args)
    print("stopping modelrunner processes")
    with cd(env.project_directory):
        run("./scripts/stop_processes.sh", pty=False)


@task
def stop_redis(**args):
    """
    Stops redis
    """

    setup_env(**args)
    print("stopping redis")
    # note, to use python based config, stop via python in modelrunner env
    with cd(env.project_directory):
        run_in_conda_env("./scripts/stop_redis.py")


@task
def setup(**args):
    """
    Install or update the deployment on a machine
    (should NOT wipeout any data)
    Assumes machine has been setup with mr user under /home/mr
    """
    setup_env(**args)
    print("baseline setup on {host_string}".format(**env))
    sudo("apt-get -y update", warn_only=True)
    sudo("apt-get -y install git curl", warn_only=True)

    update_modelrunner()

    # setup conda
    run("./modelrunner/devops/setup.sh")

    # create environ for modelrunner
    if(env.environment == "dev"):
        run_conda_enabled("./modelrunner/devops/setup_modelrunner_dev.sh")
    else:
        run_conda_enabled("./modelrunner/devops/setup_modelrunner.sh")


@task
def setup_model(model, **args):
    """
    Install or update the deployment of a model on a machine
    (should NOT wipeout any data)
    Assumes machine has been setup with mr user under /home/mr

    model:  model to setup or update
    """
    setup_env(**args)

    # find setup file
    setup_script = "./modelrunner/devops/setup_{model}.sh".\
        format(model=model)
    run_conda_enabled(setup_script)


@task
def update_modelrunner(**args):
    """
    Updates the model runner code base and devops scripts
    """
    setup_env(**args)
    pull(
        repo=env.modelrunner_repo,
        directory=env.project_directory,
        branch=env.modelrunner_branch)

    # don't rely on remote scripts from repo, instead push local setup scripts
    # to run
    with settings(warn_only=True):
        run("mkdir -p ./modelrunner/devops")
        run("mkdir -p ./modelrunner/scripts")

    put("./devops/*", "./modelrunner/devops", mode=0o755)
    put("./scripts/*", "./modelrunner/scripts", mode=0o755)
    put("./models/*", "./modelrunner/models", mode=0o755)

    # deploy appropriate config files
    put(env.config_file, './modelrunner/config.ini')
    if env.redis_config_file is not None:
        put(env.redis_config_file, './modelrunner/redis.conf')



@task
def update_systemd(**args):
    """
    Sets up systemd scripts and enables them
    """
    setup_env(**args)
    sudo("cp ./devops/set_hosts.service /etc/systemd/system/", warn_only=True)
    sudo("systemctl enable set_hosts.service", warn_only=True)

@task
def start_primary(**args):
    """
    Start the primary server
    """
    setup_env(**args)

    # stop existing processes
    stop()

    print("starting primary server on %(host_string)s" % env)
    with cd(env.project_directory):
        if(env.environment == "prod"):
            run_in_conda_env("./scripts/start_primary_production.sh")
        else:
            run_in_conda_env("./scripts/start_primary.sh")


@task
def start_redis(**args):
    """
    Start the redis server
    """
    setup_env(**args)

    # stop existing redis
    stop_redis()

    print("starting redis server on %(host_string)s" % env)
    with cd(env.project_directory):
        run_in_conda_env("./scripts/start_redis.sh")


@task
def start_worker(model, **args):
    """
    Start the worker server
    """
    setup_env(**args)

    print("starting worker model %s on %s" % (model, env['host_string']))
    with cd(env.project_directory):
        if(env.environment == "prod"):
            run_in_conda_env("./scripts/start_worker_production.sh %s" % model)
        else:
            run_in_conda_env("./scripts/start_worker.sh %s" % model)


def pull(repo, directory, branch="master"):
    with settings(warn_only=True):
        if run("test -d %s" % directory).failed:
            run("git clone %s" % repo)

    with cd(directory):
        # fetch repo, checkout branch and get rid of local
        run("git fetch origin")
        run("git remote update")
        run("git reset --hard origin/%s" % branch)
        if(run("git checkout %s" % branch, warn_only=True).failed):
            run("git checkout -b %s origin/%s" % (branch, branch))

        run("git pull")
        run('find . -name "*.pyc" | xargs rm -rf')
