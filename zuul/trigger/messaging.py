# Copyright 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
from oslo.config import cfg
from oslo import messaging

from zuul.model import TriggerEvent
import threading


class MessagingTriggerEndpoint(object):
    log = logging.getLogger("zuul.messaging.MessagingTriggerEndpoint")

    def __init__(self, server):
        self.server = server

    def trigger(self, context, arg):
        self.log.debug('trigger called. will generate trigger event.')
        event = TriggerEvent()

        event.trigger_name = self.server.name
        event.type = arg['event_type']
        event.project_name = arg['project_name']
        event.newrev = arg['newrev']
        event.oldrev = arg['oldrev']
        event.ref = arg['ref']

        self.server.sched.addEvent(event)
        return "ok"


class MessagingTriggerServer(threading.Thread):
    log = logging.getLogger("zuul.messaging.MessagingTriggerServer")

    def __init__(self, server):
        super(MessagingTriggerServer, self).__init__()
        if server.config.has_option('messaging', 'message_queue_url'):
            srv_msg_cfg = server.config.get('messaging', 'message_queue_url')
            transport = messaging.get_transport(cfg.CONF, srv_msg_cfg)
        else:
            transport = messaging.get_transport(cfg.CONF)
        target = messaging.Target(topic='zuul', server='trigger')
        endpoints = [
            MessagingTriggerEndpoint(server)
        ]
        self.server = messaging.get_rpc_server(transport, target, endpoints)
        self.log.debug('Server configured.')

    def run(self):
        self.server.start()
        self.log.debug("Server started")
        self.server.wait()

    def stop(self):
        self.log.debug("Server stopped")
        self.server.stop()


class Messaging(object):
    name = 'messaging'
    log = logging.getLogger("zuul.messaging.Messaging")

    def __init__(self, config, sched):
        self.config = config
        self.sched = sched
        self.rpc_server = MessagingTriggerServer(self)
        if (self.config.has_option('messaging', 'enabled') and
            self.config.getboolean('messaging', 'enabled')):
            self.log.debug('Inside Messaging. Starting RPC Server.')
            self.rpc_server.start()

    def stop(self):
        self.rpc_server.stop()
        self.rpc_server.join()

    def isMerged(self, change, head=None):
        raise Exception("RPC trigger does not support checking if "
                        "a change is merged.")

    def canMerge(self, change, allow_needs):
        raise Exception("RPC trigger does not support checking if "
                        "a change can be merged.")

    def maintainCache(self, relevant):
        return

    def getChange(self, number, patchset, refresh=False):
        raise Exception("RPC trigger does not support changes.")

    def getGitUrl(self, project):
        pass

    def getGitwebUrl(self, project, sha=None):
        pass

    def postConfig(self):
        pass
