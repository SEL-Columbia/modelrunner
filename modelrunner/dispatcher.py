# -*- coding: utf-8 -*-
from modelrunner.redis_utils import pubsub_listen, pop_command
import logging

logger = logging.getLogger('modelrunner')


class Dispatcher:
    """
    Receives and dispatches commands to command handlers acting as nodes in
    the ModelRunner 'protocol'

    Commands can be received over one of 2 methods:
    - queue:  command will only be processed by one node
    - channels:  command will be processed by any node listening

    Commands are represented as a dict:
    - has a 'command': COMMAND_NAME key/value
    - whatever other key values required to exec the command

    The command_handler member must have a dispatch attribute which
    maps command names to functions

    Implemented via redis (see redis_utils)
    """

    def __init__(
            self,
            redis_conn,
            command_handler,
            queue_name,
            channel_names):
        """
        redis_conn:  redis connection object
        command_handler:  object with a dispatch member
            dispatch:  maps queue or channel command names to functions
        queue_name:  name of queue to wait on
        channel_names:  names of channels to listen on
        """

        self.channel_names = channel_names
        self.queue_name = queue_name
        self.redis_conn = redis_conn
        self.command_handler = command_handler

        assert hasattr(command_handler, 'dispatch')

        # handle STOP_PROCESSING_{QUEUE,CHANNELS} commands by default
        # so that we can always stop the threads
        self.dispatch = {
            'STOP_PROCESSING_QUEUE': self.stop_processing_queue,
            'STOP_PROCESSING_CHANNELS': self.stop_processing_channels
        }

        self._keep_processing_queue = True
        self._keep_processing_channels = True

    def wait_for_channel_commands(self):
        """
        Wait for commands on channels

        loops until a 'STOP_PROCESSING_CHANNELS' command is received
        (which sets self._keep_processing_channels = False)

        Will block and process channels forever, so it should either be
        the last statement in a program OR run in a thread, e.g.:

        >>> Thread(target=my_job_node.wait_for_channel_commands).start()

        """
        pubsub = self.redis_conn.pubsub()
        pubsub.subscribe(self.channel_names)
        logger.info("waiting for commands on channels {}".
                    format(self.channel_names))

        for command_dict in pubsub_listen(pubsub):
            self.process_command(command_dict)
            if not self._keep_processing_channels:
                break

    def wait_for_queue_commands(self):
        """
        Wait for commands on queue

        loops until a 'STOP_PROCESSING_QUEUE' command is received
        (which sets self._keep_processing_queue = False)

        Will block and process the queue forever, so it should either be
        the last statement in a program OR run in a thread, e.g.:

        >>> Thread(target=my_job_node.wait_for_queue_commands).start()

        """
        logger.info("waiting for commands on queue {}".format(self.queue_name))
        while(self._keep_processing_queue):
            # timeout so that we can stop listening via _keep_processing_queue
            command_dict = pop_command(
                            self.redis_conn,
                            self.queue_name,
                            timeout=1)

            if command_dict is not None:
                self.process_command(command_dict)

    def process_command(self, command_dict):
        """
        Main dispatcher for commands that come through on queues or channels
        """
        command = command_dict['command']
        logger.info("command received {}".format(command))
        # first try the command_handler
        if command in self.command_handler.dispatch:
            self.command_handler.dispatch[command](command_dict)
        # now the default
        if command in self.dispatch:
            self.dispatch[command](command_dict)

    def stop_processing_queue(self, command_dict):
        """
        command format {'command': 'STOP_PROCESSING_QUEUE'}
        """
        self._keep_processing_queue = False

    def stop_processing_channels(self, command_dict):
        """
        command format {'command': 'STOP_PROCESSING_CHANNELS'}
        """
        self._keep_processing_channels = False
