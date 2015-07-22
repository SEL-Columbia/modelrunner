# -*- coding: utf-8 -*-
# fabfile for managing modelrunner deployments
import os

from fabric.api import task, env, run, settings, cd, put, sudo

DEFAULTS = {
    'home': '/home/mr',
    'configuration': 'primary',
    'config_file': 'config.ini',
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


def stop():
    print("stopping modelrunner processes")
    with cd(env.project_directory):
        run("./scripts/stop_processes.sh", pty=False)


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
def setup(**args):
    """
    Install or update the deployment on a machine
    (should NOT wipeout any data)
    Assumes machine has been setup with mr user under /home/mr
    """
    setup_env(**args)
    print("baseline setup on {host_string}".format(**env))
    sudo("apt-get -y install git curl", warn_only=True)

    update_modelrunner()

    # setup conda
    run("./modelrunner/devops/setup.sh")

    # create environ for modelrunner
    run_conda_enabled("./modelrunner/devops/setup_modelrunner.sh")

    # setup sequencer and networker
    run_conda_enabled("./modelrunner/devops/setup_sequencer.sh")
    run_conda_enabled("./modelrunner/devops/setup_networker.sh")


@task
def setup_model(**args):
    """
    Install or update the deployment of a model on a machine
    (should NOT wipeout any data)
    Assumes machine has been setup with mr user under /home/mr
    """
    setup_env(**args)

    # find setup file
    setup_script = "./modelrunner/devops/setup_{model}.sh".\
        format(model=args['model'])
    # setup sequencer and networker
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
    put("./scripts/*.sh", "./modelrunner/scripts", mode=0o755)

    # deploy appropriate config file
    put(env.config_file, './modelrunner/config.ini')


def start_primary():
    """
    Start the primary server
    """
    with cd(env.project_directory):
        if(env.environment == "prod"):
            run_in_conda_env("./scripts/start_primary_production.sh")
        else:
            run_in_conda_env("./scripts/start_primary.sh")


def start_worker():
    """
    Start the worker server
    """
    with cd(env.project_directory):
        if(env.environment == "prod"):
            run_in_conda_env("./scripts/start_worker_production.sh")
        else:
            run_in_conda_env("./scripts/start_.sh")


@task
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
        run("git remote update")
        run("git reset --hard origin/%s" % branch)
        if(run("git checkout %s" % branch, warn_only=True).failed):
            run("git checkout -b %s origin/%s" % (branch, branch))

        run('find . -name "*.pyc" | xargs rm -rf')
