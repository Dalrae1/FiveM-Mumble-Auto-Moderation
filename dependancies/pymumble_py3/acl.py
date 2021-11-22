# -*- coding: utf-8 -*-
import time

from .errors import ACLChanGroupNotExist
from threading import Lock
from . import messages


class ACL(dict):
    def __init__(self, mumble_object, channel_id):
        self.mumble_object = mumble_object
        self.channel_id = channel_id  # channel id attached to the ACLS
        self.inherit_acls = False
        self.groups = {}
        self.acls = {}
        self.lock = Lock()

    def update(self, message):
        self.lock.acquire()
        self.inherit_acls = bool(message.inherit_acls)
        for msg_group in message.groups:
            if msg_group.name in self.groups:
                self.groups[msg_group.name].update(msg_group)
            else:
                self.groups[msg_group.name] = ChanGroup()
                self.groups[msg_group.name].update(msg_group)
        for msg_acl in message.acls:
            if msg_acl.group in self.acls:
                self.acls[msg_acl.group].update(msg_acl)
            else:
                self.acls[msg_acl.group] = ChanACL()
                self.acls[msg_acl.group].update(msg_acl)
        self.lock.release()

    def request_group_update(self, group_name):
        if group_name not in self.groups:
            self.mumble_object.channels[self.channel_id].request_acl()
            i = 0
            while group_name not in self.groups and i < 20:
                time.sleep(0.2)
                i += 1
            if i == 20:
                raise ACLChanGroupNotExist(group_name)

    def add_user(self, group_name, user_id):
        self.request_group_update(group_name)
        if user_id not in self.groups[group_name].add:
            self.groups[group_name].add.append(user_id)
            self.send_update()

    def del_user(self, group_name, user_id):
        self.request_group_update(group_name)
        self.groups[group_name].add.remove(user_id)
        self.send_update()

    def add_remove_user(self, group_name, user_id):
        self.request_group_update(group_name)
        if user_id not in self.groups[group_name].remove:
            self.groups[group_name].remove.append(user_id)
            self.send_update()

    def del_remove_user(self, group_name, user_id):
        self.request_group_update(group_name)
        self.groups[group_name].remove.remove(user_id)
        self.send_update()

    def send_update(self):
        all_groups = self.groups.items()
        res_group = [vars(i[1]) for i in all_groups]  # Transform the Class into a dictionary

        all_acls = self.acls.items()
        res_acl = [vars(i[1]) for i in all_acls]  # Transform the Class into a dictionary

        cmd = messages.UpdateACL(channel_id=self.channel_id, inherit_acls=self.inherit_acls, chan_group=res_group, chan_acl=res_acl)
        self.mumble_object.execute_command(cmd)


class ChanGroup(dict):
    """Object that stores and update all ChanGroups ACL"""

    def __init__(self):
        self.name = None
        self.acl = None
        self.inherited = None
        self.inherit = None
        self.inheritable = None
        self.add = []
        self.remove = []
        self.inherited_members = []

    def update(self, message):
        """Update a ACL information, based on the incoming message"""
        self.name = str(message.name)

        if message.HasField('inherit'):
            self.inherit = bool(message.inherit)
        if message.HasField('inherited'):
            self.inherited = bool(message.inherited)
        if message.HasField('inheritable'):
            self.inheritable = bool(message.inheritable)

        if message.add:
            for user in message.add:
                self.add.append(int(user))
        if message.remove:
            for user in message.remove:
                self.remove.append(int(user))
        if message.inherited_members:
            for user in message.inherited_members:
                self.inherited_members.append(int(user))


class ChanACL(dict):
    """Object that stores and update all ChanACL ACL"""

    def __init__(self):
        self.apply_here = None
        self.apply_subs = None
        self.inherited = None
        self.user_id = None
        self.group = None
        self.grant = None
        self.deny = None

    def update(self, message):
        """Update a ACL information, based on the incoming message"""
        if message.HasField('apply_here'):
            self.apply_here = bool(message.apply_here)
        if message.HasField('apply_subs'):
            self.apply_subs = bool(message.apply_subs)
        if message.HasField('inherited'):
            self.inherited = bool(message.inherited)
        if message.HasField('user_id'):
            self.user_id = int(message.user_id)
        if message.HasField('group'):
            self.group = str(message.group)
        if message.HasField('grant'):
            self.grant = int(message.grant)
        if message.HasField('deny'):
            self.deny = int(message.deny)
