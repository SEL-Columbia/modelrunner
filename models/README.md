models
======

This directory holds scripts to run the models specific to your deployment of modelrunner.

To enable a new model:

1.  Define deployment script for your model in the devops dir.  Deployment
    should allow the model to be invoked via a script running on a worker.  
2.  Modify the fabfile so that it can call your deploy script.   
    TODO:  Decouple model deployment from modelrunner ala Travis
3.  Add an appropriately defined script to this dir (see test.sh for example)
4.  "define" a new config parameter named for the model in config.py.
    Associate that parameter with the "model_command" group.
5.  In your config.ini, assign that config parameter the runnable path to the
    script added in this directory (i.e. test = "./models/test.sh")

Do NOT commit model code to modelrunner directly.  
