from django.db import models
from posts.models import Government, Post, now_utc, sign_obj, get_dynamic_model, initial_save, get_data, get_data_with_relationships, search_and_sync_object, get_latest_update, Meeting

import datetime
from dateutil import tz
import hashlib
import base64
import json
from uuid import uuid4
import random
import socket
import requests
from urllib.parse import urlparse
from django.http import JsonResponse, HttpResponse, HttpRequest
import django_rq
from rq import Queue
# from django.views.decorators.csrf import csrf_exempt
import operator
from itertools import chain
import ast
from cryptography.fernet import Fernet
import platform


# hostname = socket.gethostname()    
# IpAddr = socket.gethostbyname(hostname)
# IpAddr = '11.11.11.11'
# private_key = get_private_key_from_environ
current_version = 1
number_of_peers = 2 # used for downstream_broadcast
required_validators = 10
validation_consensus = (1/3)*2
fails_to_strike = 10 # x failures == 1 strike
recent_failure_range = 3 # how many days between strikes for node if x failures
too_many_strike_count = 10 # deactivate node after x strikes
striking_days = 30 # too_many_strike count within this number of days before being deactivated
block_time_delay = 10 # minimum time (mins) before next block on chain
number_of_scrapers = 2

# for decoding .data(TextField), maybe use json.loads(.data) instead
# jsonDec = json.decoder.JSONDecoder()
# myPythonList = jsonDec.decode(myModel.myList)

class DataPacket(models.Model):
    object_type = 'DataPacket'
    blockchainType = 'NoChain'
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    automated = models.BooleanField(default=False)
    data = models.TextField(default='[]', blank=True, null=True)
    # regions = models.TextField(default=[], blank=True, null=True)
    # node_length = models.IntegerField(default=1) 
    # creator_node_id = models.CharField(max_length=50, default="0")
    Node_obj = models.ForeignKey('blockchain.Node', blank=True, null=True, on_delete=models.SET_NULL)
    # pass_along_data = models.TextField(default='', blank=True, null=True)
    chainId = models.CharField(max_length=50, default="0")
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")
    
    # upon receiving dataPacket, search_and_sync data
    # immediatly resend received dataPacket according to its broadcast_list

    # every 5 minutes check if there is DataPacket
    # if data in dataPacket, create broadcast_list and broadcast, then empty data
    
    # if data and node was selected to create block, create block, broadcast, delete dataPacket.data
    # if data is more than 6 hours old, hit node that should verify, if not responding move to inactive list, broadcast, and recheck validator 
    # if not selected, broadcast dataPacket, then delete dataPacket.data

    def __str__(self):
        return 'DATAPACKET: %s'%(self.id)
    
    class Meta:
        ordering = ["-created"]

    def broadcast(self, broadcast_list=None):
        self_node = get_self_node()
        if not broadcast_list:
            # iniate broadcast
            try:
                broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(self)
                # include most recent instance of self_node accessing each other node
                accessed = NodeUpdate.objects.filter(creator_id=self_node.id, locked_to_chain=False)
                json_data = json.loads(self.data)
                for a in accessed:
                    json_data.append({a.object_type : a.id})
                self.data = json.dump(json_data)
                self.save()
            except:
                broadcast_peers = None
        else:
            # pass along broadcast from another node
            try:
                broadcast_peers = broadcast_list[self_node.id]
            except:
                broadcast_peers = None
        self.signature = get_user(node=self_node).sign_transaction(base64.b64decode(private_key), str(get_signing_data(self)))
        self.save()
        if broadcast_peers:
            data = get_expanded_data(self)     
            # successes = 0    
            # tried_nodes = []
            json_data = {'type' : 'DataPacket', 'self_dict' : self.__dict__, 'broadcast_list' : broadcast_list, 'packet_data' : data}
            downstream_broadcast(broadcast_list, 'receive_data_packet', json_data, self_dataPacket=True)
            
            
            
    def add_item_to_data(self, object):
        try:
            dataPacket = DataPacket.objects.filter(data__contains=object.id)[0]
            return False
        except:
            data_json = json.loads(self.data)
            # chains_json = json.loads(self.chains)
            # json_block = json.dumps(dict(print_post_data(post)))
            if object.id not in data_json:
                data_json.append({'object_type' : object.object_type, 'obj_id' : object.id})
                # regionId = Blockchain.objects.filter(id=object.blockchainId)[0].regionId
                # if regionId not in chains_json:
                #     chains_json.append(regionId)
                #     self.chains = json.dumps(chains_json)
                self.data = json.dumps(data_json)
                self.save()
            # previous_block = self.get_last_block()
            # return previous_block.index + 1
            return True
    

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
            # self.node_length = len(get_node_list())
        if self.Node_obj == get_self_node():
            sign_obj(self)
            super(DataPacket, self).save()

class Node(models.Model):
    # nodes are saved to blockchain for purpose of a master list, but will fail verification because data can change
    object_type = 'Node'
    blockchainType = 'Nodes'
    # locked_to_chain = models.BooleanField(default=False)
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    ip_address = models.CharField(max_length=50, default="0")
    # ip_address = models.CharField(max_length=50, default="0")
    # last_accessed = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    self_declare_active = models.BooleanField(default=False) 
    deactivated = models.BooleanField(default=False) # deactivated if too many strikes or not resposnsive
    deactivated_time = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    supported_chains = models.TextField(default='[]', blank=True, null=True)
    User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.SET_NULL)
    # user_id = models.CharField(max_length=50, default="0")
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")



    def __str__(self):
        return 'NODE: %s'%(self.ip_address)

    class Meta:
        ordering = ["-last_updated"]

    def get_data(self, node=None):
        if node:
            data = node['id'] + node['ip_address'] + node['user_id'] + node['self_declare_active'] + node['supported_regions']
        else:
            data = str(self.id) + str(self.ip_address) + str(self.User_obj.id) + str(self.self_declare_active)
            # data = str(self.id) + str(self.ip_address) + str(self.User_obj.id) + str(self.self_declare_active) + str(self.supported_regions)


    # def get_data(self):
    #     data = {'deactivated' : [], 'last_accessed' : [], 'strikes' : [], 'failures' : []}
    #     deactivated = self.get_deactivated()
    #     for d in deactivated:
    #         data['deactivated'].append(d.__dict__)
    #     accessed = self.get_last_accessed()
    #     for a in accessed:
    #         data['last_accessed'].append(a.accessed)
    #     strikes = self.get_strikes()
    #     for s in strikes:
    #         data['strikes'].append(s.__dict__)
    #     total, recent = self.get_failures()
    #     for r in recent:
    #         data['failures'].append(r.__dict__)
    #     return data
        
    def assess_activity(self):
        # if fail_count greater than 5 and nodes who determined the failure greater than 5
        last_accessed = self.get_last_accessed()
        self_node = get_self_node()
        total_failures, recent_failures = self.get_failures()
        if recent_failures.count() > fails_to_strike:
            failure_identifiers = []
            for r in recent_failures:
                try:
                    failure_identifiers[r.CreatorNode_obj.id] += 1
                except:
                    failure_identifiers[r.CreatorNode_obj.id] = 1
            if len(failure_identifiers) > fails_to_strike:
                if last_accessed.accessed > recent_failures[0].created:
                    return True
                else:
                    try:
                        strike = NodeUpdate.objects.filter(pointerId=self.id, CreatorNode_obj=self_node, strike_id=self_node.id, created__lte=now_utc() - datetime.timedelta(days=recent_failure_range))[0]
                    except:
                        strike = NodeUpdate(pointerId=self.id, CreatorNode_obj=self_node, strike_id=self_node.id)
                        strike.save()
                        # strike.signature = get_user().sign_transaction(base64.b64decode(private_key), get_expanded_data(strike))
                        # strike.save()
                        # self.get_node(self.creator_node_id)
                        self.too_many_strikes()
                    return False
        
        return True

    def is_active(self): # not used
        def func():
            total, recent = self.get_failures()
            if last_accessed > recent[0].created:
                return True
            else:
                nodes_failed_to_access = []
                for r in recent:
                    if r.CreatorNode_obj.id not in nodes_failed_to_access:
                        nodes_failed_to_access.append(r.CreatorNode_obj.id)
                if len(nodes_failed_to_access) > 10 or len(nodes_failed_to_access) > (len(get_node_list())/2):
                    deactivate(node=self)
                    return False
                else:
                    return True
        if self.deactivated:
            return False
        else:
            try:
                deactivated = NodeUpdate.objects.exclude(deactivated_time=None).order_by('-created')[0]
            except:
                deactivated = None
            last_accessed = self.get_last_accessed().accessed
            if deactivated:
                if last_accessed > deactivated.deactivated_time:
                    return True
                else:
                    return func()
            else:
                return func()

    def get_deactivated(self):
        try:
            return NodeUpdate.objects.filter(deactivated=True).order_by('-created')[0]
        except:
            return None
        
    def get_last_accessed(self):
        try:
            return NodeUpdate.objects.exclude(accessed=None).filter(TargetNode_obj=self).order_by('-created')[0]
        except:
            return None

    def get_failures(self):
        all_failures = NodeUpdate.objects.filter(pointerId=self.id).exclude(fail_time=None).order_by('-created')
        # failures in past recent_failure_range days
        recent_failures = NodeUpdate.objects.filter(pointerId=self.id, fail_time__gte=now_utc() - datetime.timedelta(days=recent_failure_range)).order_by('-created')
        return all_failures, recent_failures
    
    def get_strikes(self):
        try:
            return NodeUpdate.objects.exclude(strike_id=None).filter(TargetNode_obj=self).order_by('-created')
        except:
            return None
        
    def too_many_strikes(self, period=None):
        if period == 'any':
            strike_objects = NodeUpdate.objects.exclude(strike_id=None).filter(pointerId=self.id).order_by('-created')
        else:
            strike_objects = NodeUpdate.objects.exclude(strike_id=None).filter(pointerId=self.id).filter(created__gte=now_utc() - datetime.timedelta(days=striking_days)).order_by('-created')
        node_strikers = {}
        for s in strike_objects:
            if s.CreatorNode_obj.id not in node_strikers:
                try:
                    node_strikers[s.CreatorNode_obj.id] += 1
                except:
                    node_strikers[s.CreatorNode_obj.id] = 1
        strikes = 0
        if len(node_strikers) >= too_many_strike_count:
            for key, value in node_strikers:
                if int(value) >= too_many_strike_count:
                    strikes += 1
        if strikes >= too_many_strike_count or strikes >= len(get_node_list()):
            # if self.deactivated == False:
            #     dataPacket = DataPacket.objects.filter(Node_obj=get_self_node())[0]
            #     dataPacket.add_item_to_data(self)
            self.deactivated = True
            self.save()
            return True
        else:
            return False
        
    def add_failure(self):
        failure = NodeUpdate()
        failure.pointerId = self.id
        failure.CreatorNode_obj = get_self_node()
        failure.fail_time = now_utc()
        failure.save()
        # failure.signature = get_user().sign_transaction(base64.b64decode(private_key), get_expanded_data(failure))
        # failure.save()
        self.assess_activity()  

    def broadcast_state(self):
        broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(self)
        # downstream_broadcast(broadcast_list, 'node_update', {'type' : 'node_update'})
        downstream_broadcast(broadcast_peers, '/blockchain/declare_node_state', get_signing_data(self))
        
        if self.self_declare_active and not self.deactivated:
            if self.id == get_self_node().id:
                # update database
                pass


    def save(self, share=False):
        # if self.id == '0':
        #     self = initial_save(self, share=share)
        from accounts.models import UserPubKey
        for upk in UserPubKey.objects.filter(User_obj=self.User_obj):
            is_valid = upk.verify(get_signing_data(self), self.signature)
            if is_valid:
                super(Node, self).save()
                break

class NodeUpdate(models.Model):
    # historical node configuration data, to maintain consistant node ordering throughout time
    object_type = 'NodeUpdate'
    # blockchainType = 'NodeData'
    # blockchainId = '1'
    # locked_to_chain = models.BooleanField(default=False)
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=False)
    pointerId = models.CharField(max_length=50, default="0") # target node
    pointerType = 'Node'
    TargetNode_obj = models.ForeignKey('blockchain.Node', related_name='target_node_obj', blank=True, null=True, on_delete=models.SET_NULL)
    CreatorNode_obj = models.ForeignKey('blockchain.Node', related_name='creator_node_obj', blank=True, null=True, on_delete=models.SET_NULL)
    # creator_node_id = models.CharField(max_length=50, default="0") # who noticed the failure
    # creatoreType = 'Node'
    # data = models.TextField(default='[]', blank=True, null=True)
    ai_capable = models.BooleanField(default=False)
    
    
    
    accessed = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    response_time = models.IntegerField(blank=True, null=True)
    fail_time = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # is_active = models.BooleanField(default=True) # other nodes registering successful connections
    deactivated_time = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    strike_id = models.CharField(max_length=50, default="0") #blockId if referencing strike for block, else same as CreatorNode_obj.id if referencing inaccessable
    # user_id = models.CharField(max_length=50, default="0")
    last_accessed = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # self_declare_active = models.BooleanField(default=False) 
    # deactivated = models.BooleanField(default=False) # deactivated if too many strikes or not resposnsive
    # supported_regions = models.TextField(default='[]')
    
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")

    def __str__(self):
        return 'NODEUPDATE: %s'%(self.id)
    
    class Meta:
        ordering = ["-created"]

    def get_data(self, update=None):
        if update:
            return update['id'] + update['pointerId'] + update['CreatorNode_obj_id'] + update['accessed'] + update['fail_time'] + update['deactivated_time'] + update['strike_id']
        else:
            return str(self.id) + str(self.pointerId) + str(self.CreatorNode_obj.id) + str(self.accessed) + str(self.fail_time) + str(self.deactivated_time) + str(self.strike_id)


    def save(self, share=True):
        if self.id == '0':
            if self.TargetNode_obj:
                self.pointerId = self.TargetNode_obj.id
            elif self.pointerId:
                self.TargetNode_obj = Node.objects.filter(id=self.pointerId)[0]
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if self.CreatorNode_obj == get_self_node():
                sign_obj(self)
            super(NodeUpdate, self).save()

    def delete(self):
        if not self.locked_to_chain:
            super(NodeUpdate, self).delete()
    
class Block(models.Model):
    object_type = 'Block'
    blockchainType = 'NoChain'
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    automated = models.BooleanField(default=False)
    blockchainId = models.CharField(max_length=50, default="0")
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")
    # branchchainId = models.CharField(max_length=50, default="0")
    # creator_node = models.ForeignKey('blockchain.Node', blank=True, null=True, on_delete=models.RESTRICT)
    Node_obj = models.ForeignKey('blockchain.Node', blank=True, null=True, on_delete=models.SET_NULL)
    # creator_node_id = models.CharField(max_length=50, default="0")
    # validator_nodes = models.TextField(blank=True, null=True)
    version = models.IntegerField(default=1) 
    index = models.IntegerField(default=1) 
    # node_length = models.IntegerField(default=1) 
    datetime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True) # created time round down to nearest 10 mins
    hash = models.CharField(max_length=100, default="0")
    previous_hash = models.CharField(max_length=100, default="0")
    reward = models.CharField(max_length=1000000, default="0")
    data = models.TextField(default='[]', blank=True, null=True)
    number_of_peers = models.IntegerField(default=1) # only used for node chain
    is_valid = models.BooleanField(default=False)
    script = models.TextField(blank=True, null=True)


    def __str__(self):
        return 'BLOCK: %s'%(self.id)
    
    def get_previous_block(self):
        return Block.objects.filter(blockchainId=self.blockchainId, index=self.index-1, is_valid=True).order_by('-index')[0]

    # def get_creator_of_next_block(last_block, target_datetime):
    #     node_list_snapshot = get_closest_snapshot_to_datetime(target_datetime)
    #     selected_value = hash_to_int(last_block.id, len(node_list_snapshot))
    #     date = date_to_int(last_block.created)
    #     position = selected_value + date
    #     node = get_node(node_list_snapshot[position])
    #     return node

    # def get_next_block_validators(self):


    def is_not_valid(self):
        self_node = get_self_node()
        try:
            strike = NodeUpdate.objects.filter(pointerId=self.Node_obj.id, creator_node_id=self_node.id, strike_id=self.id)[0]
        except:
            strike = NodeUpdate(pointerId=self.Node_obj.id, creator_node_id=self_node.id, strike_id=self.id)
            strike.save()
            node = get_node(id=self.Node_obj.id)
            node.too_many_strikes()
        data = json.loads(self.data)
        blockchain = Blockchain.objects.filter(id=self.blockchainId)[0]
        for i in data:
            try:
                block = Block.objects.filter(blockchainId=blockchain.id, is_valid=True, data__contains=i)[0]
            except:
                blockchain.add_item_to_data(i)
        self.delete()
        

    def mark_valid(self):
        data = {}
        for objType, objId in json.loads(self.data):
            try:
                data[objType].append(objId)
            except:
                data[objType] = [objId]
        for objType, idList in data:
            xModels = get_dynamic_model(objType, list=True, id__in=idList)
            # xModels = globals()[objType].objects.filter(id__in=idList)
            for x in xModels:
                x.locked_to_chain = True
                super(objType, x).save()
        self.is_valid = True
        self.save()
        chain = Blockchain.objects.filter(id=self.blockchainId)[0]
        chain.chain_length = Block.objects.filter(blockchainId=chain.id, is_valid=True).count()
        chain.save()
        for block in Block.objects.filter(blockchainId=self.blockchainId, is_valid=False, index__lte=self.index):
            block.delete()

    def save(self, share=False):
        if self.id == '0':
            self = initial_save(self, share=share)
        if self.Node_obj == get_self_node():
            sign_obj(self)
        super(Block, self).save()
    

class Validator(models.Model):
    object_type = 'Validator'
    blockchainType = 'NoChain'
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=False)
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")
    pointerId = models.CharField(max_length=50, default="0", db_index=True)
    pointerType = models.CharField(max_length=50, default="0")
    Node_obj = models.ForeignKey('blockchain.Node', blank=True, null=True, on_delete=models.SET_NULL)
    # creator_node_id = models.CharField(max_length=50, default="0")
    # creator_node_type = 'Node'
    # node = models.ForeignKey('blockchain.Node', blank=True, null=True, on_delete=models.RESTRICT)
    is_valid = models.BooleanField(default=False)

    def __str__(self):
        return 'VALIDATOR: %s'%(self.id)
    
    def get_data(self, validator=None):
        if validator:
            data = validator['id'] + validator['pointerId'] + validator['creator_node_id'] + validator['is_valid']
        else:
            data = str(self.id) + str(self.pointerId) + str(self.Node_obj.id) + str(self.is_valid) 

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if self.Node_obj == get_self_node():
            sign_obj(self)
        super(Validator, self).save()

class Blockchain(models.Model):
    object_type = 'Blockchain'
    # blockchainType = 'NoChain'
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    chain_length = models.IntegerField(default=0) 
    data = models.TextField(default='[]', blank=True, null=True)
    data_added_datetime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True) # when new data was added since last block created
    genesisType = models.CharField(max_length=50, default="0")
    genesisId = models.CharField(max_length=50, default="0", unique=True, db_index=True)
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # regionId = models.CharField(max_length=50, default="0")
    # chainType = models.CharField(max_length=50, default="0") # region, nodeupdates, people, wallet

    def __str__(self):
        return 'BLOCKCHAIN-type:%s-genesisId:%s'%(self.genesisType, self.genesisId)

    def save(self, share=False):
        if self.id == '0':
            self.id = hashlib.md5(str(self.genesisType + self.genesisId).encode('utf-8')).hexdigest()
        super(Blockchain, self).save()
    
    
        
    def commit_to_block(self):
        data = json.loads(self.data)
        post_ids = []
        for i in data:
            post_ids.append(i['obj_id'])
        blocks = Block.objects.filter(data__overlap=post_ids)
        if blocks.count() > 0:
            for b in blocks:
                for i in data:
                    if i['obj_id'] in b.data:
                        data.pop(i)
            self.data = json.dumps(data)

        # if self.chainType == 'NodeData':
        #     # nodes = []
        #     all_nodes = get_node_list()
        #     data = []
        #     for i in all_nodes:
        #         # gets only most recent nodeUpdate
        #         try:
        #             update = NodeUpdate.objects.filter(pointerId=i.id).order_by('-created')[0]
        #             if update.accessed:
        #                 text_bytes = str(update.__dict__).encode('utf-8')
        #                 sha256_hash = hashlib.sha256(text_bytes).hexdigest()
        #                 data.append({'object_type' : update.object_type, 'obj_id' : update.id, 'pointerId' : update.pointerId, 'hash' : sha256_hash})
        #         except:
        #             pass
        #     random.shuffle(data)
        #     self.data = json.dumps(data)
        #     self.save()

        if self.genesisType == 'Nodes':
            data = []
            # get all suppoerted regions
            from posts.models import Region
            supported_regions = Region.objects.filter(is_supported=True)
            for region in supported_regions:
                nodes = Node.objects.filter(supported_chains__icontains=region.id)
                data.append({'region_id' : region.id, 'nodes' : [node.id for node in nodes]})
            self.data = json.dumps(data)
            self.save()
            
            
        previous_block = self.get_last_block()
        previous_hash, expanded_data = get_hash(previous_block)

        hash, expanded_data = get_hash(self)

        new_block = self.create_block(previous_hash=previous_hash, hash=hash)


        # broadcast to all validators
        broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(new_block)
        broadcast_block(new_block, lst=validator_list)
        return JsonResponse(new_block)


    def create_block(self, previous_hash=None, hash=None, block=None, signature=None):
        chain_length = Block.objects.filter(Blockchain=self, is_valid=True).count()
        if block:
            new_block = Block()
            for field in block:
                setattr(new_block, field, block[field])
        else:
            self_node = get_self_node()
            new_block = Block(blockchainId=self.id)
            if self.chainType == 'Nodes':
                new_block.datetime = round_time_up(datetime.datetime.now()) # node block is one step ahead of other blocks to ensure they are all referring to same node list
            else:
                new_block.datetime = round_time_down(datetime.datetime.now())
            new_block.version = current_version
            new_block.index = chain_length + 1

            new_block.creator_node_id = self_node.id
            # new_block.node_snapShot = get_latest_snapshot().created
            # new_block.node_length = len(get_node_list())
            new_block.hash = hash
            new_block.previous_hash = previous_hash
            new_block.data = self.data
            new_block.number_of_peers = number_of_peers
            new_block.save()
            # new_block.signature = get_user(node=self_node).sign_transaction(base64.b64decode(private_key), get_validation_data(new_block))
        new_block.is_valid = False
        new_block.save()
        # self.chain_length = new_block.index
        for item in json.loads(new_block.data):
            self.data.remove(item)
        self.data_added_datetime = None
        self.save()

        return new_block
    

    def get_last_block(self):
        return Block.objects.filter(Blockchain=self, is_valid=True).order_by('-index')[0]


    # add transaction
    def add_item_to_data(self, post):
        try:
            block = Block.objects.filter(data__contains=post.id)[0]
            return False
        except:
            to_commit_json = json.loads(self.data)
            # json_block = json.dumps(dict(print_post_data(post)))
            if post.id not in to_commit_json:
                import hashlib
                text_bytes = str(post.__dict__).encode('utf-8')
                sha256_hash = hashlib.sha256(text_bytes).hexdigest()
                # if post.object_type == ''
                to_commit_json.append({'object_type' : post.object_type, 'obj_id' : post.id, 'hash' : sha256_hash})
                self.data = json.dumps(to_commit_json)
                if not self.data_added_datetime:
                    self.data_added_datetime = datetime.datetime.now()
                self.save()
                # previous_block = self.get_last_block()
                # return previous_block.index + 1
                return True
            else:
                return False

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)



# json_example = {'sender': '', 'node_data':[{'nodes':['node.__dict__'], 'deactivated':['nodeUpdate.__dict__'], 'failures':['nodeUpdate.__dict__']}], 
#                  'content':[{'obj':{'obj_dict':'.__dict__', 'related':[
#                             {'posts':['Post.__dict__']}, {'updates':['Update.__dict__', 'UserOptions.__dict__']},{'references':['xModel.__dict__']}
#                         ]}}]
#             }

# json_example = {'sender': '', 'node_data':[{'nodes':['node.__dict__'], 'deactivated':['nodeUpdate.__dict__'], 'failures':['nodeUpdate.__dict__']}], 
#                  'content': {'objects' : ['obj.__dict__'], 'posts' : ['Post.__dict__'], 'updates' : ['Update.__dict__', 'UserOptions.__dict__'], 'references' : ['xModel.__dict__']}
#             }


def broadcast_block(block, lst=None, validations=None):
    if not lst:
        broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(block)
        lst = broadcast_list
    # validators = Validator.objects.filter(pointerId=block.id)
    # validator_list = []
    # for v in validators:
    #     validator_list.append(v.__dict__)

    # json_data = json.loads(block.data)
    block_data = get_expanded_data(block)
    json_data = {'type' : 'Blocks', 'broadcast_list': broadcast_list, 'blockchainId' : block.blockchainId, 'block_list' : [{'block_dict' : block.__dict__, 'block_data' : block_data, 'validations' : validations,}], 'end_of_chain' : True}
    downstream_broadcast(lst, 'receive_blocks', json_data)

# def get_operatorData():
#     with open("soNodeOperatorData.json", 'r') as file:
#         data = json.load(file)
#     return data

# def write_operatorData(data):
#     with open("operatorData.json", 'w') as file:
#         json.dump(data, file, indent=4)
    
def get_operatorData():
    # print('get_operatorData')
    try:
        with open("soNodeOperatorData.json", 'rb') as file:
            encrypted_data = file.read()
            data_string = decrypt(encrypted_data)
    except Exception as e:
        print(str(e))
        # server_path = Path(homepath + '/SoNodeServer')
        # server_path.mkdir(parents=True, exist_ok=True)
        # data_string = json.dumps({}, indent=4)
        # encrypted_data = encrypt(data_string)
        # with open("soNodeOperatorData.json", 'wb') as file:
        #     file.write(encrypted_data)
        # with open("soNodeOperatorData.json", 'rb') as file:
        #     encrypted_data = file.read()
        #     data_string = decrypt(encrypted_data)
    json_obj = json.loads(data_string)
    # print(json_obj)
    return json_obj

def write_operatorData(data):
    try:
        current_data = get_operatorData()
        data = {**current_data, **data}
    except:
        pass
    data_string = json.dumps(data, indent=4)
    encrypted_data = encrypt(data_string)
    with open("soNodeOperatorData.json", 'wb') as file:
        file.write(encrypted_data)


def load_key():
    print('load_key')
    system = platform.system()
    if system == 'Windows':
        file_path = "soSecret.key"
    elif system in ('Linux', 'Darwin'):  # Darwin is macOS
        file_path = ".soSecret.key"
    try:
        return open(file_path, "rb").read()
    except Exception as e:
        print(str(e))
        # generate_key()
        # return open(file_path, "rb").read()

def encrypt(text):
    key = load_key()
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(text.encode())
    return cipher_text

def decrypt(text):
    # print('decrypt', text)
    key = load_key()
    cipher_suite = Fernet(key)
    decrypted_text = cipher_suite.decrypt(text).decode()
    return decrypted_text

def get_latest_dataPacket():
    data = get_operatorData()
    try:
        dataPacket = DataPacket.objects.filter(Node_obj__User_obj__id=data['user_id'])[0]
    except:
        dataPacket = DataPacket(Node_obj=get_self_node())
        dataPacket.save()
    return dataPacket

def check_dataPacket(obj):
    dataPacket = get_latest_dataPacket()
    data = json.loads(dataPacket.data)
    if not obj:
        return False
    elif obj.id in str(data):
        return True
    else:
        return False

def get_node_list(sort='-last_updated'):
    # nu = NodeUpdate.objects.exclude(deactivated=True).distinct('pointerId').order_by(sort)
    nodes = Node.objects.filter(deactivated=False).order_by(sort)
    node_list = []
    for node in nodes:
        node_list.append(node)
    return nodes
 
# def get_expanded_node_list(sort='-created'):
    # from posts.models import dict_with_relationships
    # nodes = Node.objects.all().order_by(sort)
    # node_list = []
    # for node in nodes:
    #     node_list.append(dict_with_relationships(node))
    # return nodes

# node_list = get_node_list()
# if len(node_list) <= required_validators:
#     required_validators = len(node_list) - 1

def get_latest_node_data(sort='-created'):
    # nodes = Node.objects.all().order_by(sort)
    # node_list = []
    # for node in nodes:
    #     node_list.append(node.get_data())
    #     return nodes    
    json_data = {'nodes' : [], 'deactivated' : [], 'last_accessed' : [], 'recent_failures' : []}
    active_nodes = Node.objects.filter(deactivated=False)
    for n in active_nodes:
        json_data['nodes'].append(n.__dict__)
    deactivated_nodes = NodeUpdate.objects.exclude(deactivated_time=None).order_by('-created')
    for n in deactivated_nodes:
        json_data['deactivated'].append(n.__dict__)
    last_accessed = NodeUpdate.objects.exclude(accessed=None).order_by('-created')[0]
    for n in last_accessed:
        json_data['last_accessed'].append(n.__dict__)
    recent_failures = NodeUpdate.objects.filter(fail_time__gte=now_utc() - datetime.timedelta(days=recent_failure_range)).order_by('-created')
    for n in recent_failures:
        json_data['recent_failures'].append(n.__dict__)
    return json_data

def get_self_node():
    operatorData = get_operatorData()
    return Node.objects.filter(id=operatorData['nodeId'])
    # not sure if ipaddr will work with port
    data = get_operatorData()
    print('get_self_node', data['user_id'])
    try:
        return Node.objects.filter(User_obj__id=data['user_id'])[0]
    except Exception as e:
        print(str(e))
        from accounts.models import User
        u = User.objects.filter(id=data['user_id'])[0]
        node = Node(ip_address='127.0.0.1:3005', User_obj=u)
        node.last_updated = now_utc()
        node.save()
        # node.broadcast_state()
        print('new node')
        return node

def get_user(node=None, user_id=None, public_key=None):
    # print('get user', public_key)
    from accounts.models import User, UserPubKey
    if user_id:
        # print(user_id)
        return User.objects.filter(id=user_id)[0]
    if public_key:
        try:
            upk = UserPubKey.objects.filter(publicKey=public_key)[0]
            return upk.User_obj
        except Exception as e:
            # print('111',str(e))
            return None
    if not node:
        node = get_self_node()
    return User.objects.filter(id=node.user_id)[0]


def get_node(id=None, ip_address=None, publicKey=None):
    if id:
        return Node.objects.filter(id=id)[0]
    elif ip_address:
        return Node.objects.filter(ip_address=ip_address)[0]
    elif publicKey:
        user = get_user(public_key=publicKey)
        return Node.objects.filter(User_obj=user)[0]
    # return node

def get_relevant_nodes_from_block(dt=None, chainId=None, ai_capable=False, firebase_capable=False):
    print('get nodes from b lock')
    chain = Blockchain.objects.filter(genesisType='NodeData', genesisId='1')[0]
    if not dt:
        dt = round_time_down(now_utc())
    else:
        dt = round_time_down(dt)
    node_block = Block.objects.filter(blockchainId=chain.id, datetime=dt)[0]
    data = json.loads(node_block.data)
    if chainId:
        relevant_nodes = Node.objects.filter(id__in=data[chainId])
    else:
        target_nodes = []
        for chain, nodes in data.items():
            for i in nodes:
                target_nodes.append(i)
        relevant_nodes = Node.objects.filter(id__in=target_nodes)
    # for i in data:

    #     relevant_nodes.append(i['pointerId'])
    # if ai_capable:
    #     nodes = Node.objects.filter(ai_capable=True, id__in=target_nodes)
    # elif firebase_capable:
    #     nodes = Node.objects.filter(firebase_capable=True, id__in=target_nodes)
    # else:
    #     nodes = Node.objects.filter(id__in=target_nodes)
    # nodes = Node.objects.filter(id__in=target_nodes)
    # node_list = []
    # # ensure order is according to block
    # for i in data:
    #     for n in nodes:
    #         if i['pointerId'] == n.id:
    #             node_list.append(n.id)
    return relevant_nodes

def accessed(node=None, response_time=None, update_data=None):
    # update = None
    # if update_data:
    #     # accessed_time = convert_to_datetime(update_data['last_accessed'])
    #     # try:
    #     #     node = Node.objects.filter(id=update_data['id'])[0]
    #     #     if node.last_accessed < accessed_time:
    #     #         node.last_accessed = accessed_time
    #     #         node.save()
    #     # except:
    #     #     node = Node()
    #     #     for field in update_data:
    #     #         setattr(node, field, update_data[field])
    #     #     node.save()

    #     nodeUpdates = NodeUpdate.objects.exclude(accessed=None).filter(pointerId=update_data['pointerId']).order_by('-accessed')
    #     if nodeUpdates[0].accessed < convert_to_datetime(update_data['last_accessed']):
    #         for update in nodeUpdates:
    #             update.delete()
    #         update = NodeUpdate()
    #         for field in update_data:
    #             setattr(update, field, update_data[field])
    #         update.save()
    # elif node:
    self_node = get_self_node()
    nodeUpdates = NodeUpdate.objects.exclude(accessed=None).exclude(locked_to_chain=True).filter(pointerId=node.id, CreatorNode_obj=self_node)
    for update in nodeUpdates:
        update.delete()
    update = NodeUpdate()
    update.pointerId = node.id
    update.accessed = now_utc()
    update.response_time = int(response_time)
    update.CreatorNode_obj = self_node
    update.save()

    if node.deactivated:
        node.deactivated = False
        node.save()


    # data = get_expanded_data(update)
    # current_user = get_user()
    # signature = current_user.sign_transaction(base64.b64decode(private_key), data)
    # update.signature = signature
    # update.save()
        
        # if node.last_accessed < datetime.datetime.now():
        #     node.last_accessed = datetime.datetime.now()
        #     node.response_time = str(time)
        #     node.save()
    return node

def deactivate(node=None, update_data=None):
    update = None
    if update_data:
        # last_accessed = NodeUpdate.objects.exclude(accessed=None).filter(pointerId=update_data['pointerId'])[0]
        try:
            node = Node.objects.filter(id=update_data['pointerId'])[0]
            deactivated_time = convert_to_datetime(update_data['deactivated_time'])
            if node.get_last_accessed().accessed < deactivated_time:
                nodeUpdates = NodeUpdate.objects.exclude(deactivated_time=None, locked_to_chain=True).filter(pointerId=update_data['pointerId'])
                for update in nodeUpdates:
                    update.delete()
                update = NodeUpdate()
                for field in update_data:
                    setattr(update, field, update_data[field])
                update.save()
        except:
            pass
        # try:
        #     node = Node.objects.filter(id=update_data['id'])[0]
        #     if node.last_accessed < deactivated_time:
        #         node.last_accessed = deactivated_time
        #         node.save()
        # except:
        #     node = Node()
        #     for field in update_data:
        #         setattr(node, field, update_data[field])
        #     node.save()
    elif node:
        nodeUpdates = NodeUpdate.objects.exclude(deactivated_time=None).filter(pointerId=node.id)
        for update in nodeUpdates:
            update.delete()
    
        update = NodeUpdate()
        update.pointerId = node.id
        update.deactivated_time = now_utc()
        update.CreatorNode_obj = get_self_node()
        update.save()
        node.deactivated = True
        node.save()

        # if node.deactivated_time < datetime.datetime.now():
        #     node.deactivated_time = datetime.datetime.now()
        #     node.save()
    return update

# def update_peer_list(new_node_list):
    # old_nodes = get_node_list()
    updated_nodes = []
    for n in new_node_list:
        try:
            node = Node.objects.filter(id=n['obj']['obj_dict']['id'])[0]
        except:
            node = Node()
            for field in n:
                setattr(node, field, n[field])
            node.save()
        try:
            node_failures = n['obj']['obj_dict']['related']['references']
            for failure in node_failures:
                try:
                    f = NodeUpdate.objects.filter(id=failure['id'])[0]
                except:
                    f = NodeUpdate()
                    for field in n:
                        setattr(f, field, n[field])
                    f.save()
        except Exception as e:
            print(str(e))
        updated_nodes.append(node)
    # for node in old_nodes:
    #     if node not in updated_nodes:
    #         node.delete_with_failures()

def convert_to_datetime(data):
    # possivly different
    # datetime.datetime(2021, 11, 22, 5, 0, tzinfo=<UTC>)
    dt = datetime.datetime.strptime(data, 'datetime.datetime(%Y, %m, %d, %H, %M, tzinfo=<%Z>)')
    return dt

def get_closest_snapshot_to_datetime(dt): # not used
    greater = NodeSnapShot.filter(created__gte=dt).order_by("created")[0]
    less = NodeSnapShot.filter(created__lte=dt).order_by("-created")[0]
    if greater and less:
        if abs(greater.created - dt) < abs(less.created - dt):
            snapshot = greater
        else:
            snapshot = less
    elif greater:
        snapshot = greater
    else:
        snapshot = less
    if snapshot.referenceId:
        referenceShot = NodeSnapShot.objects.filter(id=snapshot.referenceId)[0]
        snapshot = referenceShot
    return json.loads(snapshot.data), snapshot
    # if greater and less:
    #     return json.loads(greater.data) if abs(greater.created - dt) < abs(less.created - dt) else json.loads(less.data)
    # else:
    #     return json.loads(greater.data) or json.loads(less.data)

def get_starting_position(object, node_id_list): # not used
    if object.object_type == 'Block':
        previous_block = object.get_previous_block()
        creator_node = previous_block.get_creator_of_next_block(object.created)
        starting_position = hash_to_int(creator_node.id, len(node_id_list))
        date = date_to_int(object.created)
    elif object.object_type == 'DataPacket':
        self_node = get_self_node()
        starting_position = hash_to_int(self_node.id, len(node_id_list))
        date = date_to_int(object.created)
    elif object.object_type == 'Node':
        starting_position = hash_to_int(object.id, len(node_id_list))
        date = date_to_int(object.created)
    else:
        # chain = Blockchain.objects.filter(id=object['blockchainId'])[0]
        previous_block = Block.objects.filter(BlockchainId=object['blockchainId'], index=int(object['index']) - 1)
        creator_node = previous_block.get_creator_of_next_block(object['created'])
        starting_position = hash_to_int(creator_node.id, len(node_id_list))
        date = date_to_int(convert_to_datetime(object['created']))
    position = starting_position + date
    while position > len(node_id_list):
        position -= len(node_id_list)
    return position, date

def get_hash(obj):
    json_data = get_expanded_data(obj)
    return hashlib.sha256()(str(json_data).encode()).hexdigest(), json_data

def calculate_reward():
    block_count = Block.objects.all().count()
    reward = 1 - (block_count/100)
    return reward

skip_fields = [
            # WARNING changing this will break ALL signing and verification abilities
                'signature', 'publicKey', 'locked_to_chain', 'validated', 'ai_approved', 
               'password', 'rank', 'randomizer', 'keyword_array', 'total_votes', 
               'total_yeas', 'total_nays', 'total_voter_votes', 'total_voter_yeas', 
               'total_voter_nays', 'total_comments','total_saves','total_shares',
               'pointerPublicKey','pointerDateTime', 'Update_obj', 
               'coins', 'is_valid', 'slug', 'last_login', 'date_joined',
               'deactivated_time', 'deactivated', 'appToken', 'isVerified',
               ]
 
def get_signing_data(obj, extra_data=None):
    # WARNING changing this will break ALL signing and verification abilities
    # print()
    # print('get signing data')
    # print('send_user_obj_to_user',send_user_obj_to_user)
    # print(obj)

    # data = {
    #     "key1": "value1",
    #     "key2": 42,
    #     "key3": True,
    #     "key4": ["item1", "item2"],
    #     "key5": {"subkey1": "subvalue1"}
    # }

    # # Serialize the dictionary to a JSON string
    # json_data = json.dumps(data, separators=(',', ':'))


    # these fields don't get included in signature
    data = {}
    # replaceUserArray = {}
    try:
        data['object_type'] = obj.object_type
        fields = obj._meta.fields
        # print(fields)
        # print()
        for f in fields:
            if str(f.name) not in skip_fields:
                # print(f.name)
                # print()
                # if send_user_obj_to_user == False and obj.object_type == 'User' and '_array' in str(f.name):
                #     # print('target',str(getattr(obj, f.name)))
                #     # '''["test"]'''
                #     # q = ast.literal_eval("['test']")
                #     # print('q',q)
                #     target = f'replaceMe_{str(f.name)}'
                #     data[f.name] = target
                #     # print('xx',data[f.name])
                #     # xx = str(getattr(obj, f.name))
                #     replaceUserArray[target] = str(getattr(obj, f.name))
                # else:
                try:
                    # x = getattr(obj, f.name)
                    # print(x)
                    # print(x.id)
                    data[f.name] = getattr(obj, f.name).id
                except Exception as e:
                    # print(str(e))
                    try:
                        data[f.name] = str(getattr(obj, f.name))
                    except Exception as e:
                        # print(str(e))
                        # print(extra_data)
                        if 'matching query does not exist' in str(e):
                            # only for creation of upk and wallet, must have User_obj.id but User not yet created
                            data[f.name] = extra_data[f.name]
        # print('--1')
        # print('json',data)
        # print('dump:',json.dumps(data, separators=(',', ':')))
        json_dump = json.dumps(data, separators=(',', ':'))
        # # print()
        # # ax = json_dump.find('"replace_array_here"')
        # # if '"replace_array_here"' in json_dump:
        # #     print('found')
        # # else:
        # #     print('not found')
        # for key, value in replaceUserArray.items():
        #     json_dump = json_dump.replace(f'"{key}"', value)
        # # print('json_dump', json_dump)
        return json_dump
    except Exception as e:
        # print(str(e))
        try:
            # obj may or not be json object
            obj = json.loads(obj)
        except:
            pass
        # print(obj)
        for f in obj:
            if str(f) not in skip_fields:
                data[f] = obj[f]
    # print('-------')
    # x = json.dumps(data, separators=(',', ':'))
    # print(x)
    # print()
    # print(json.loads(x))
    # print()
    # print(json.loads(x)['isVerified'])
        # print('--2')
        # print(json.dumps(data, separators=(',', ':')))
    # print('----3')
    # print(json.loads(str(data)))
    return json.dumps(data, separators=(',', ':'))

def get_full_data(obj):
    data = {}
    fields = obj._meta.get_fields()
    # print(fields)
    for f in fields:
        # if str(f.name) not in skip_fields:
            # print(f.name)
            try:
                # x = getattr(obj, f.name)
                # print(x)
                # print(x.id)
                data[f.name] = getattr(obj, f.name).id
            except Exception as e:
                # print(str(e))
                data[f.name] = str(getattr(obj, f.name))
    # print('--1')
    # print(json.dumps(data, separators=(',', ':')))
    return json.dumps(data, separators=(',', ':'))

def get_expanded_data(obj, get_relationships=False):
    # json_data = {'reward' : calculate_reward()}
    json_data = {}
    requested_items = []
    expanded_data = []
    # if isinstance(obj, list):
    #     # pass scraped data to validator
    #     items_to_get = [item for sublist in obj for item in sublist]
    #     data, not_found = get_data(items_to_get)
    #     json_data['content'] = data
    #     return json_data
    # else:
    # should only need for blockchain, block and datapacket
    try:
        if obj.object_type == 'Blockchain': # blockchain data yet to be committed to block
            data = json.loads(obj.data)
            previous_block = obj.get_last_block()
            previous_hash = previous_block.hash
            json_data['previous_hash'] = previous_hash
        elif obj.object_type == 'Block':
            data = json.loads(obj.data)
            previous_hash = obj.previous_hash
            json_data['previous_hash'] = previous_hash
        elif obj.object_type == 'DataPacket':
            data = json.loads(obj.data)
        elif obj.object_type and obj.object_type == 'Validator':
            return obj.get_data()
        elif obj.object_type and obj.object_type == 'Node':
            return obj.get_data()
        elif obj.object_type and obj.object_type == 'NodeUpdate':
            return obj.get_data()

    except: # is json
        if obj['object_type'] == 'NodeUpdate':
            nodeUpdate = NodeUpdate.objects.filter(id=obj['id'])
            return nodeUpdate.get_data()
        elif obj['object_type'] == 'Node':
            node = Node.objects.filter(id=obj['id'])
            return node.get_data()
        elif obj['object_type'] == 'Validator':
            validator = Validator.objects.filter(id=obj['id'])
            return validator.get_data()
        else:
            try:
                # received block
                data = json.loads(obj['block_data']['content'])
                # sender_node = get_node(obj['sender']['id'])
                json_data['previous_hash'] = data['block_dict']['previous_hash']
            except:
                # received posts
                data = ''
                for field in obj:
                    data = data + str(obj[field])
                return data
            
    items_to_get = [item for item in data]
    if get_relationships: # not used
        data, not_found = get_data_with_relationships(items_to_get)
    else:
        data, not_found = get_data(items_to_get)
    # for item in data:

    #     obj_data = get_object_with_data_from_json(item)
    #     if not obj_data: # only when receiving block
    #         requested_items.append(item)
    #     else:
    #         expanded_data.append(obj_data)
    
    
    # if not_found:
    #     # from posts.models import dict_with_relationships
    #     self_node = get_self_node()
    #     current_nodes = get_node_list('?')
    #     broadcast_nodes = []
    #     for node in current_nodes[:number_of_peers]:
    #         broadcast_nodes.append(node)
    #     if sender_node:
    #         try:
    #             request_data = {'sender' : dict_with_relationships(self_node), 'nodes': broadcast_nodes, 'request_items' : requested_items}
    #             success, response = connect_to_node(sender_node.ip_address, '/request_items', request_data)
    #             if success:
    #                 returned_objects = response['content']
    #                 for i in returned_objects:
    #                     requested_items.remove(i)
    #                     obj, databaseUpdated = search_and_sync_object(i)
    #                     obj_data = dict_with_relationships(obj)
    #                     expanded_data.append(obj_data)

    #         except Exception as e:
    #             print(str(e))
    #             sender_node.add_failure()
    #     if not_found:
    #         print('searching other nodes for requested items')
    #         request_data = {'sender' : dict_with_relationships(self_node), 'nodes': current_nodes, 'request_items' : requested_items}
    #         for n in current_nodes:
    #             print(n)
    #             try:
    #                 success, response = connect_to_node(sender_node.ip_address, '/request_items', request_data)
    #                 if success:
    #                     returned_objects = response['content']
    #                     for i in returned_objects:
    #                         requested_items.remove(i)
    #                         obj, databaseUpdated = search_and_sync_object(i)
    #                         obj_data = dict_with_relationships(obj)
    #                         expanded_data.append(obj_data)
    #                 if not requested_items:
    #                     break
    #             except Exception as e:
    #                 print(str(e))
    #                 n.add_failure(n)
    json_data['content'] = data
    return json_data

def find_or_create_chain_from_json(obj):
    # if object['blockchainId']
    try:
        blockchain = Blockchain.objects.filter(id=obj['blockchainId'])[0]
    except:
        blockchain = Blockchain()
        blockchain.id = obj['blockchainId']
        blockchain.chainType = obj['blockchainType']
        blockchain.save()
    return blockchain

def hash_to_int(hash, length):
    decimal_value = int(hash, 16)
    return decimal_value % length

def date_to_int(date):
    dtimestamp = date.timestamp()
    hours = int(round(dtimestamp))/60/60 
    result = hours % 450000

    return result

def get_most_recent_even_hour(dt=None):
    if not dt:
        dt = datetime.datetime.now()
    dt = dt - datetime.timedelta(minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
    hour = dt.hour
    while hour % 2 != 0:
        hour -= 1
    dt = dt.replace(hour=hour)
    return dt

def round_time_up(dt):
    return dt - datetime.timedelta(minutes=(dt.minute % 10), seconds=dt.second, microseconds=dt.microsecond) + datetime.timedelta(minutes=10)

def round_time_down(dt):
    return dt - datetime.timedelta(minutes=dt.minute % 10, seconds=dt.second, microseconds=dt.microsecond)

def get_broadcast_peers(obj):
    # receive block, dataPacket or node
    # use receieved object.id to get starting position
    # for each node create a list of peers to broadcast to
    # each node should only receive broadcast once
    # each node should be able to discern entire broadcast list repeatably
    # not all nodes will need to broadcast

    broadcast_list = []
    validator_list = []
    v = 0
    self_node = get_self_node()


    if obj and obj.object_type == 'Blockchain':

        dt = round_time_down(datetime.datetime.now())
        # region_list = [obj.regionId]
        node_list, dt = get_relevant_nodes_from_block(dt=dt, chaindId=obj.genesisId)
        date_int = date_to_int(dt)
        previous_block = obj.get_previous_block()
        starting_position = hash_to_int(previous_block.creator_node_id, len(node_list))
        
    elif obj and obj.object_type == 'Block':

        # region_list = [Blockchain.objects.filter(id=obj.blockchainId)[0].genesisId]
        node_list = get_relevant_nodes_from_block(dt=obj.datetime, chaindId=Blockchain.objects.filter(id=obj.blockchainId)[0].genesisId)
        node_list.remove(obj.Node_obj.id)
        date_int = date_to_int(obj.datetime)
        number_of_peers = obj.number_of_peers
        previous_block = obj.get_previous_block()
        starting_position = hash_to_int(previous_block.creator_node_id, len(node_list))
        
    elif obj and obj.object_type == 'DataPacket':
        
        # nodeUpdate = NodeUpdate.objects.filter(pointerId=self_node.id).order_by('-created')[0]
        # region_list = json.loads(nodeUpdate.supported_regions)

        dt = round_time_down(obj.created)
        node_list = get_relevant_nodes_from_block(dt=dt, chainId=obj.chainId)
        node_list.remove(obj.Node_obj.id)
        date_int = date_to_int(dt)
        starting_position = hash_to_int(obj.creator_node_id, len(node_list))
        
    elif obj and obj.object_type == 'Validator':
        block = Block.objects.filter(id=obj.pointerId)[0]
        # region_list = [Blockchain.objects.filter(id=block.blockchainId)[0].regionId]
        dt = round_time_down(obj.created)
        node_list = get_relevant_nodes_from_block(dt=dt, chaindId=Blockchain.objects.filter(id=block.blockchainId)[0].genesisId)
        # node_list.remove(obj.Node_obj.id)
        date_int = date_to_int(dt)
        starting_position = hash_to_int(obj.creator_node_id, len(node_list))
        
    elif obj and obj.object_type == 'Node':
        # block = Block.objects.filter(id=obj.pointerId)[0]
        # region_list = obj.supported_chains
        dt = round_time_down(obj.last_updated)
        node_list = get_relevant_nodes_from_block(dt=dt)
        node_list.remove(obj.id)
        date_int = date_to_int(dt)
        starting_position = hash_to_int(obj.User_obj.id, len(node_list))

    else:
        dt = round_time_down(obj.created)
        node_list = get_relevant_nodes_from_block(dt=dt)
        # node_list.remove(obj.user_id)
        date_int = date_to_int(dt)
        starting_position = hash_to_int(obj.user_id, len(node_list))
        

    def get_peer_nodes(broadcaster_id, position, node_list, checked_node_list):
        broadcaster_hashed_int = hash_to_int(broadcaster_id, len(node_list))
        def run(position, node_list):
            position += (broadcaster_hashed_int + date_int)
            if position > len(node_list):
                position = position % len(node_list)
            new_node = node_list[position]
            node_list.remove(new_node)
            return new_node, position, node_list
        peers = []
        while len(peers) < number_of_peers and len(node_list) > 0:
            new_node, position, node_list = run(position, node_list)
            peers.append(new_node.ip_address)
            checked_node_list.append(new_node)
        broadcast_list[broadcaster_id] = peers
        return broadcast_list, checked_node_list, node_list
    
    def process(broadcaster_id, position, node_list_snapshot, checked_node_list, broadcast_list, v):
        broadcast_list, checked_node_list, node_list = get_peer_nodes(broadcaster_id, position, node_list_snapshot, checked_node_list)
        if v < required_validators and broadcaster_id != next(iter(broadcast_list)):
            validator_list.append(broadcaster_id)
            v += 1
        return broadcast_list, checked_node_list, node_list, v

    # starting_position, date = get_starting_position(obj, node_list_snapshot)
    # date offset to position
    starting_position += date_int
    creator_node_id = node_list[starting_position]
    checked_node_list = [creator_node_id]
    x = 0
    run = True
    target_node = checked_node_list[x]
    # run for nodes registered at time of previous_block creation
    # node_list = get_relevant_nodes(node_list_snapshot, region_list)
    while x < len(node_list) and run:
        try:
            broadcast_list, checked_node_list, node_list, v = process(target_node, starting_position, node_list, checked_node_list, broadcast_list, v)
            # break if target_node has no broadcast_peers
            peers = broadcast_list[target_node]
            x += 1
            target_node = checked_node_list[x]
        except:
            run = False

    latest_node_list = get_relevant_nodes_from_block(dt=obj.datetime, regions=region_list)

    # latest_node_snapshot = get_latest_snapshot()
    # run for remaining nodes not in initial snapshot
    node_list = latest_node_list
    for node_id in checked_node_list:
        node_list.remove(node_id)
    cross_reference_list = [node_id for node_id in checked_node_list if node_id in latest_node_list]
    run = True
    n = 0
    while len(cross_reference_list) < len(latest_node_list) and run and n < len(node_list):
        try:
            n += 1
            target_node = checked_node_list[x]
            broadcast_list, checked_node_list, node_list, v = process(target_node, starting_position, node_list, checked_node_list, v)
            # break if target_node has no broadcast_peers
            peers = broadcast_list[target_node]
            for peer in peers:
                if peer not in cross_reference_list:
                    cross_reference_list.append(peer)
            x += 1
        except:
            run = False

    return broadcast_list[self_node.id], broadcast_list, validator_list
    
def every_10_mins():
    self_node = get_self_node()
    self_user = get_user(node=self_node)

    dataPacket = DataPacket.objects.filter(creater_node_id=self_node.id)[0]
    if len(json.loads(dataPacket.data)) > 0:
        DataPacket.broadcast()
        new_packet = DataPacket(creater_node_id=self_node.id)
        new_packet.save()

    # check for posts without validation, scrap and validate if appropriate
    # from accounts.models import Region
    scrapers = []
    for gov in Government.objects.filter(region__is_supported=True):
    # for region in Region.objects.filter(is_supported=True):
        region = gov.Region_obj
        # import functions
        r = gov.Region_obj
        x = '%s as %s' %(gov.gov_level, r.Name)
        while r.modelType != 'country':
            x = r.Name + '.' + x 
            r = r.ParentRegion
        x = 'import scrapers.' + x
        exec(x)
        runTimes = exec(f'{region.Name}.runTimes')
        # functions = exec(f'{region.Name}.functions')
        scraping_order = get_scraping_order(region_obj=region)

        # this is no longer accurate and needs work
        unvalidated_posts = Post.objects.filter(validated=False, Region_obj=region, created__lte=now_utc() - datetime.timedelta(minutes=20))
        for p in unvalidated_posts:
            if p.get_pointer().publicKey != self_user.publicKey:
                time_diff = now_utc() - p.created
                # round time_diff to previous 10 mintes then divide by 10
                position = int(((time_diff.seconds//60)%60) / 10)
                new_node_id = scraping_order[position]
                if self_node.id == new_node_id:
                    if p.chamber:
                        x = f'get_{p.chamber}_{p.pointerType}s'
                    else:
                        x = f'get_{p.pointerType}s'
                    if x not in scrapers:
                        timeout = runTimes[runTimes[x]]
                        scrapers.append([f'{region.Name}.{x}', timeout])
                        # scrapers.append(x)

    dt = now_utc()
    td = dt - datetime.timedelta(minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
    time_diff = dt - td
    # if less than 10 minutes from top of the hour
    if ((time_diff.seconds//60)%60) < 10:
        queue = django_rq.get_queue('low')
        queue.enqueue(run_scrape_duty, requested=scrapers, job_timeout=500)
    elif scrapers:
        for function in scrapers:
            x = f'{function[0]}'
            queue = django_rq.get_queue('low')
            queue.enqueue(exec(x), job_timeout=function[1])



    for block in Block.objects.filter(is_valid=False):
        check_validation_consensus(block)

    for chain in Blockchain.objects.exclude(data=[]):
        last_block = chain.get_last_block()
        if last_block.datetime <= now_utc() - datetime.timedelta(minutes=block_time_delay):
            
            broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(chain)
            creator_node = get_node(id=next(iter(broadcast_list)))
            
            if creator_node.id == self_node.id:
                if len(json.loads(chain.data)) > 0:
                    chain.commit_to_block()


def get_scraperScripts(gov):
    region = gov.Region_obj
    if region.modelType == 'country':
        country_name = region.Name.lower()
        importScript = f'scrapers.{country_name}.{gov.gov_level.lower()}'
    elif region.modelType == 'provState':
        # name = region.Name.lower()
        provState_name = region.Name.lower()
        country_name = region.ParentRegion_obj.Name.lower()
        importScript = f'scrapers.{country_name}.{provState_name}.{gov.gov_level.lower()}'
    elif region.modelType == 'city':
        name = region.Name.lower()
        provState_name = region.ParentRegion_obj.Name.lower()
        country_name = region.ParentRegion_obj.ParentRegion_obj.Name.lower()
        importScript = f'scrapers.{country_name}.{provState_name}.{name}'
    
    import importlib
    scraperScripts = importlib.import_module(importScript) 
    return scraperScripts

def get_scraping_order(iden=1, func_name=None, dt=None):
    print('get scraping order')
    scraping_order = []
    dt = get_most_recent_even_hour(dt=dt)
    # if region_obj:
    #     region_id = region_obj.id
    # elif region_json:
    #     region_id = region_json['id']
    
    master_node_list = get_relevant_nodes_from_block(dt=dt)

    text_bytes = str(func_name).encode('utf-8')
    sha256_hash = hashlib.sha256(text_bytes).hexdigest()
    name_position = hash_to_int(sha256_hash, len(master_node_list))

    date_int = date_to_int(dt)
    id_position = hash_to_int(iden, len(master_node_list))
    position = name_position + id_position + date_int

    def run(position, node_list):
        if position > len(node_list):
            position = position % len(node_list)
        return node_list[position], node_list, position
    
    node_list = master_node_list
    while len(node_list) > 0:
        node_id, node_list, position = run(position, node_list)
        scraping_order.append(node_id)
        node_list.remove(node_id)
        position += (hash_to_int(node_id, len(node_list)) + date_int)
        # if len(node_list) == 0:
        #     node_list = master_node_list
    print(scraping_order)
    return scraping_order

def get_scrape_duty(gov, dt, debate_obj=None):
    print('get scrape duty')
    # self_node = get_self_node()
    # self_user = get_user(node=self_node)
    # scrapers = []
    # validators = []

    region = gov.Region_obj
    print(region)
    # convert to local timezone
    # dt_now = datetime.datetime.now().astimezone(pytz.utc)
    today = dt - datetime.timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
    to_zone = tz.gettz(region.timezone)
    today = today.astimezone(to_zone)
    dt = dt.astimezone(to_zone)
    dayOfWeek = today.weekday()

    # import functions
    # r = gov.Region_obj
    # x = '%s as %s' %(gov.gov_level, r.Name)
    # while r.modelType != 'country':
    #     x = r.Name + '.' + x 
    #     r = r.ParentRegion_obj
    # x = 'import scrapers.' + x
    # print(x)
    # exec(x)
    # runTimes = exec(f'{region.Name}.runTimes')


    # r = country
    # if region.modelType == 'country':
    # gov_level = region.gov_level

    scraperScripts = get_scraperScripts(gov)

    # if region.modelType == 'country':
    #     country_name = region.Name.lower()
    #     importScript = f'scrapers.{country_name}.{region.gov_level}'
    # elif region.modelType == 'provState':
    #     # name = region.Name.lower()
    #     provState_name = region.Name.lower()
    #     country_name = region.ParentRegion_obj.Name.lower()
    #     importScript = f'scrapers.{country_name}.{provState_name}.{region.gov_level}'
    # elif region.modelType == 'city':
    #     name = region.Name.lower()
    #     provState_name = region.ParentRegion_obj.Name.lower()
    #     country_name = region.ParentRegion_obj.ParentRegion_obj.Name.lower()
    #     importScript = f'scrapers.{country_name}.{provState_name}.{name}'
    
    # import importlib
    # scraperScripts = importlib.import_module(importScript)
    runTimes = scraperScripts.runTimes
    functions = scraperScripts.functions
    approved_models = scraperScripts.approved_models
    # Now you can use the imported module as CanadaFunctions
    # print(func)  # Prints the module object
    # func()

    # if debate_obj:
    #     scraping_order = get_scraping_order(iden=debate_obj.id, dt=dt, req_count=6)
    #     x = f'get_{debate_obj.chamber}_debates'
    #     timeout = runTimes[x]
    #     scrapers.append([scraping_order[0], [f'{region.Name}.{x}', timeout]])
    #     scrapers.append([scraping_order[1], [f'{region.Name}.{x}', timeout]])
    #     validators.append({'validator':scraping_order[2], 'job':[f'{region.Name}.{x}', timeout]})
        
    #     x = f'get_{debate_obj.chamber}_motions'
    #     timeout = runTimes[x]
    #     scrapers.append([scraping_order[3], [f'{region.Name}.{x}', timeout]])
    #     scrapers.append([scraping_order[4], [f'{region.Name}.{x}', timeout]])
    #     validators.append({'validator':scraping_order[5], 'job':[f'{region.Name}.{x}', timeout]})


    # else:
    # functions = exec(f'{region.Name}.functions')
    function_list = []
    # n = 0
    for function in functions:
        if 'x' in function['hour'] or dt.hour in function['hour']:
            if 'x' in function['dayOfWeek'] or dayOfWeek in function['dayOfWeek']:
                if 'x' in function['date'] or today in function['date']:
                    for f in function['cmds']:
                        # timeout = runTimes[f]
                        function_list.append({'region_id':region.id,'function_name':f, 'function':getattr(scraperScripts, f), 'timeout':runTimes[f]})
                        # scrapers.append({'node_id':scraping_order[n], 'function':f'{region.Name}.{f}', 'timeout':timeout})
                        # scrapers.append({'node_id':scraping_order[n+1], 'function':f'{region.Name}.{f}', 'timeout':timeout})
                        # validators.append({'node_id':scraping_order[n+2], 'function':f'{region.Name}.{f}', 'timeout':timeout})
                        # n += 1
    # n = 0
    # total_length = len(scraping_order)
    master_list = []
    for f in function_list:
        scraping_order = get_scraping_order(iden=region.id, func_name=f['function_name'], dt=dt)
        f['scraping_order'] = scraping_order
        master_list.append(f)

    return master_list, approved_models

def run_scrape_duty(requested=[]):
    # every hour
    self_node = get_self_node()
    self_user = get_user(node=self_node)
    scraper_list = []
    validator_list = []

    # delete posts not validated after 2 hours
    # this should no longer be neccesary, objects are only distributed after validation
    invalid_posts = Post.objects.filter(validated=False, created__lte=now_utc() - datetime.timedelta(minutes=120))
    for p in invalid_posts:
        obj = p.get_pointer()
        obj.delete()

    # import scrapers.canada.federal as canada
    # from scrapers.canada.ontario.provincial import x
    for gov in Government.objects.filter(Region_obj__is_supported=True):
        region = gov.Region_obj
        today = now_utc().date()
        dt = now_utc()
        # convert to local timezone
        to_zone = tz.gettz(region.timezone)
        today = today.astimezone(to_zone)
        dt = dt.astimezone(to_zone)
        # dayOfWeek = today.weekday()

        meeting_functions = []
        meetings = Meeting.objects.filter(meeting_type='Debate', DateTime__gte=now_utc() - datetime.timedelta(days=2), DateTime__lte=datetime.datetime.combine(today, datetime.datetime.min.time()), Region_obj=region, has_transcript=False)
        for d in meetings:
            meeting_functions.append(f'get_{d.chamber}_debates')
            meeting_functions.append(f'get_{d.chamber}_motions')
            # scrapers, validators = get_scrape_duty(gov, dt, debate_obj=d)
            # for s in scrapers:
            #     scraper_list.append(s)
            # for v in validators:
            #     validator_list.append(v)

        scraper_list, approved_models = get_scrape_duty(gov, dt)
        # for s in scrapers:
        #     scraper_list.append(s)
        # for v in validators:
        #     validator_list.append(v)

        for i in scraper_list:
            if self_node.id in i['scraping_order'][:number_of_scrapers]:
            # if i['node_id'] == self_node.id:
                # x = str(i['function'])
                if 'debates' not in i['function_name'] and 'motions' not in ['function_name'] or ['function_name'] in meeting_functions:
                    queue = django_rq.get_queue('low')
                    queue.enqueue(i['function'], job_timeout=i['timeout'])
        # for i in validators:
        #     if i['node_id'] == self_node.id:
        #         x = str(i['function'])
        #         if 'debates' not in x and 'motions' not in x or x in meeting_functions:
        #             queue = django_rq.get_queue('low')
        #             queue.enqueue(exec(x), job_timeout=i['timeout'])
            






def check_post_validations(json_item=None, obj=None, scraping_order=None):
    if not scraping_order:
        if json_item:
            scraping_order = get_scraping_order(region_json=[json_item['Region']], dt=convert_to_datetime(json_item['created']))
        elif obj:
            scraping_order = get_scraping_order(region_obj=[obj.Region], dt=obj.created)
    if json_item:
        public_key = json_item['publicKey']
    elif obj:
        public_key = obj.publicKey
    # item_node = get_node(publicKey=public_key)
    # look for model based on predefined fields for if multiple nodes are scraping the same thing
    # skip_fields = ['id', 'locked_to_chain', 'created', 'automated', 'publicKey', 'signature', 'validated', 'keywords']
    ignore_fields = skip_fields
    ignore_fields.append('id')
    ignore_fields.append('created')
    # ignore_fields.append('keyword_array')
    filters = {}
    if json_item:
        for field in [field for field, value in json_item if field not in ignore_fields]:
            filters[field] = json_item[field]
    elif obj:
        for field in [field for field in obj._meta.get_fields() if str(field) not in ignore_fields]:
            filters[field] = getattr(obj, field)
    try:
        validated = False
        if json_item:
            object_type = json_item['object_type']
        elif obj:
            object_type = obj.object_type
        objs = get_dynamic_model(object_type, list=True, **filters)
        # objs = globals[object_type].objects.filter(**filters)
        earliest_obj = None
        for o in objs:
            if o.validated:
                break
            else:
                obj_node = get_node(publicKey=o.publicKey)
                if not earliest_obj or o.created < earliest_obj.created:
                    earliest_obj = o
        if objs.count() > 0:
            if convert_to_datetime(json_item['created']) < earliest_obj.created:
                obj = sync_model(obj, json_item)
                earliest_obj = obj
        if earliest_obj:
            validate_post(earliest_obj)

        
        # if first scraper and objects match, keep first, validate, add 'validated' to skip_fields in 2 places
        # if objects dont match, call the next scraper,
        # check for objects more than 30 minutes old in scrape_duty, if any, call another scraper
        # if 2 hours have gone by without 2 matches, delete obj
        # once validated, blockchain.add_item_to_data(obj) 
        # or use share_with_network() on all related data
        # automated items should not be immediatly added to blockchain until validated by at least 1 peer

        # add to chain below as well
    except:
        pass

def sync_model2(obj, i):
    fields = obj._meta.get_fields()
    for f in fields:
        try:
            if str(f) != 'validated':
                setattr(obj, f, i[f][:10000000])
        except:
            pass
    try:
        obj.locked_to_chain = False
    except:
        pass
    obj.save()
    return obj

def validate_post(obj):
    # post = Post.objects.filter(pointerId=obj.id)[0]
    # post.validated = True
    # post.save()
    blockchain = Blockchain.objects.filter(id=obj.blockchainId)[0]
    blockchain.add_item_to_data(obj)
    # blockchain.add_item_to_data(post)
    return obj

def process_received_data(received_data, block_data=None):
    from accounts.models import User
    from posts.models import sync_model, find_or_create_chain_from_object, get_or_create_model, get_dynamic_model
    # specialTypes = ['Node', 'User'] # sync previous data, do not write to chain
    databaseUpdated = False
    objs = {}
    for i in received_data:
        try:
            objs[i['object_type']].append(i['id'])
        except:
            objs[i['object_type']] = [i['id']]
    not_found = []
    # mismatchedData = []
    for obj_type, idList in objs:
        existing = get_dynamic_model(obj_type, list=True, id__in=idList)
        if block_data:
            # block data is official data locked to chain
            for e in existing:
                text_bytes = str(e.__dict__).encode('utf-8')
                hash = hashlib.sha256(text_bytes).hexdigest()
                receivedItem = [i for i in block_data if i['obj_id'] == e.id][0]
                if receivedItem['hash'] != hash:
                    target_json = [i for i in received_data if i['id'] == e.id][0]
                    text_bytes = str(target_json).encode('utf-8')
                    target_hash = hashlib.sha256(text_bytes).hexdigest()
                    if target_hash == receivedItem['hash']:
                        sync_model(e, target_json)
                        # mismatchedData.append([e, target_json])
            # else:
        eList = [e.id for e in existing]
        for i in idList:
            if i not in eList:
                not_found.append(i)

    
    # should check if data is already present but with different id
    # for example, Government update['endDate'] could be created by multiple nodes at once
    # should check who was selected to be scraper of that data at that time
    # some funcs like get_user_region may return objects such as 'Region' that may be created on other nodes at the same time
    # get_user_region may be run by anyone

    scraping_order = get_scraping_order()
    for i in received_data:
        hashMatch = True
        if block_data:
            text_bytes = str(i).encode('utf-8')
            hash = hashlib.sha256(text_bytes).hexdigest()
            receivedItem = [i for i in block_data if i['obj_id'] == e.id][0]
            if receivedItem['hash'] == hash:
                hashMatch = True
            else:
                hashMatch = False
        if hashMatch and i['id'] in not_found:

            # this needs work, 'automated' has been elminated
            try:
                automated = i['automated']
            except:
                automated = False
            if automated == 'True':
                if len(scraping_order) > 1:
                    check_post_validations(i)
                else:
                    obj = sync_model(obj, i)
                    validate_post(obj)

            else:
                # if i['object_type'] in specialTypes:
                obj = get_or_create_model(i['object_type'], id=i['id'])
                # try:
                #     obj = globals()[i['object_type']].objects.filter(id=i['id'])[0]
                # except:
                #     obj = globals()[i['object_type']]()
                # else:
                    # obj = globals()[i['object_type']]()
                if obj.object_type == 'Node':
                    if obj.deactivated == True and i['deactivated'] == 'False':
                        is_active = obj.assess_activity()
                        if is_active:
                            sync_model(obj, i)
                        else:
                            obj = sync_model(obj, i)
                            obj.deactivated = True
                            obj.save()
                    else:
                        sync_model(obj, i)
                elif obj.object_type == 'User':
                    # check if username already exists, if so, save first created, delete newer one, may need signature
                    try:
                        must_rename = False
                        u = User.objects.filter(display_name=i['display_name']).exclude(id=i['id'])[0]
                        if u.created > datetime.datetime.fromisoformat(i['created']):
                            u.must_rename = True
                            u.save()
                        else:
                            must_rename = True
                    except:
                        pass
                    # if sync_user:
                    if obj.isVerified == False and i['isVerified'] == 'True' or obj.isVerified == True and i['isVerified'] == 'False':
                        is_verified = obj.assess_verification()
                        sync_model(obj, i)
                        if not is_verified:
                            obj.isVerified = False
                            obj.save()
                    else:
                        sync_model(obj, i)
                    if must_rename:
                        obj.must_rename = True
                        obj.save()
                else:
                    obj = sync_model(obj, i)
                    if obj.object_type == 'Keyphrase':
                        obj.set_trend()
                    if not block_data:
                        blockchain, obj, receiverChain = find_or_create_chain_from_object(obj)
                        blockchain.add_item_to_data(obj)
                databaseUpdated = True
    return databaseUpdated            
            

def process_data_packet(received_json):
    try:
        broadcast_list = received_json['broadcast_list']
    except:
        broadcast_list = []
    self_dict = received_json['self_dict']
    # u = dataPacket.Node_obj.User_obj
    # u.verify
    signature_verified = get_user(public_key=self_dict['publicKey']).verify_signature(str(get_signing_data(self_dict)), self_dict['signature'])
    if signature_verified:
        process_received_data(received_json['packet_data']['content'])

        downstream_broadcast(broadcast_list, 'receive_data_packet', received_json)

def process_received_blocks(received_json):
    from posts.models import sync_model
    broadcast_list = received_json['broadcast_list']
    # block_dict = received_json['block_dict']

    # update_node_data(received_json['node_data'])
    # broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(new_block)


    broadcast_json = {'blockchainId' : blockchain.id, 'broadcast_list': broadcast_list, 'block_list' : []}
    blocks = {}
    for b in json.loads(received_json['block_list']):
        blocks[b['block_dict']['index']] = b
    for index, b in sorted(blocks.items(), key=operator.itemgetter(0)):
        new_block = json.loads(b['block_dict'])

        # u = block.Node_obj.User_obj
        # u.verify
        signature_verified = get_user(public_key=new_block['publicKey']).verify_signature(str(get_signing_data(new_block)), new_block['signature'])
        if signature_verified:
            try:
                # received_validations = b['validations']
                process_received_data(b['validations'])
            except:
                pass


            try:
                blockchain = Blockchain.objects.filter(id=new_block['blockchainId'])[0]
            except:
                blockchain = find_or_create_chain_from_json(new_block)


            if(blockchain.chain_length + 1) == int(new_block['index']) or blockchain.chain_length == int(new_block['index']):
                try:
                    block = Block.objects.filter(id=new_block['id'])[0]
                except:
                    block = blockchain.create_block(block=new_block)
                    process_received_data(b['block_data']['content'], block_data=new_block['data'])
                is_valid, valid_unknown, validations = check_validation_consensus(block)
                broadcast_block = True
                if is_valid and blockchain.chain_length == int(new_block['index']):
                    competing_blocks = Block.objects.filter(blockchainId=blockchain.id, index=block.index)
                    winning_block, validations = resolve_block_differences(competing_blocks)
                    if winning_block != block:
                        broadcast_block = False
                    
                
                if is_valid and broadcast_block or valid_unknown and broadcast_block:
                    broadcast_json['block_list'].append({'new_block' : new_block, 'validations' : validations})
            


            elif (blockchain.chain_length + 1) < int(new_block['index']):
                retrieve_missing_blocks(blockchain, target_node=get_node(id=received_json['sender']['id']))
                break

            elif blockchain.chain_length > int(new_block['index']):
                json_data = {'type' : 'Block', 'broadcast_list': [], 'blockchainId' : blockchain.id, 'block_list' : []}
                for return_block in Block.objects.filter(blockchainId=blockchain.id, index_gt=int(new_block['index'])):
                    validations = Validator.objects.filter(pointerId=return_block.id)
                    validator_list = [v.__dict__ for v in validations]
                    json_data['block_list'].append({'block_dict' : return_block.__dict__, 'block_data' : get_expanded_data(return_block), 'validations' : validator_list})
                success, response = connect_to_node(get_node(id=received_json['sender']['id']), 'receive_blocks', json_data)
                break
                # resolve_block_differences(created_block, competing_blocks)
            
    
    if len(broadcast_json['block_list']):
        downstream_broadcast(broadcast_list, 'receive_block', broadcast_json)
        

def resolve_block_differences(competing_blocks):
    earliest_block = competing_blocks[0]
    validations = {}
    for competing_block in competing_blocks:
        is_valid, status_unknown, validations = check_validation_consensus(competing_block)
        validations[competing_block] = validations
        if is_valid:
            if competing_block.datetime > earliest_block.date_time:
                pass
            elif competing_block.datetime < earliest_block.date_time:
                earliest_block = competing_block
            elif competing_block.created > earliest_block.created:
                pass
            elif competing_block.created < earliest_block.created:
                earliest_block = competing_block
    for block in competing_blocks:
        if block != earliest_block:
            # dont use is_not_valid so not to give strike against node
            block.delete()
    return earliest_block, validations[earliest_block]

def retrieve_missing_blocks(blockchain, target_node=None, starting_point=None):
    if not target_node:
        relevant_node_ids = get_relevant_nodes_from_block(regions=[blockchain.regionId])
        target_node = get_node(id=random.choice(relevant_node_ids))
    json_data = {'type' : 'requesting_blocks', 'blockchainId' : blockchain.id, 'request_first' : blockchain.chain_length}
    success, response = connect_to_node(target_node, 'request_blocks', json_data)
    if success:
        response_json = json.loads(response.body)
        for block in response_json['block_list']:

            signature_verified = get_user(public_key=block['block_dict']['publicKey']).verify_signature(str(get_signing_data(block['block_dict'])), block['block_dict']['signature'])
            if signature_verified:
                process_received_data(block['validations'])
                try:
                    created_block = Block.objects.filter(id=block['block_dict']['id'])[0]
                except:
                    created_block = blockchain.create_block(block=block['block_dict'])
                    process_received_data(block['block_data']['content'])
                is_valid, status_unknown, percent = check_validation_consensus(created_block)
                if is_valid:
                    competing_blocks = Block.objects.filter(blockchainId=blockchain.id, index=block['new_block']['obj']['index']).exclude(id=block['new_block']['obj']['id'])
                    if competing_blocks.count() > 0:
                        resolve_block_differences(created_block, competing_blocks)
        if response_json['end_of_chain'] == 'False':
            retrieve_missing_blocks(blockchain)

def process_received_validation(received_json):
    broadcast_list = received_json['broadcast_list']
    databaseUpdated = process_received_data(received_json['validations'])
    downstream_broadcast(broadcast_list, 'receive_validation', received_json)
    if databaseUpdated:
        block = Block.objects.filter(id=received_json['block_dict']['id'])[0]
        if not block.is_valid:
            check_validation_consensus(block)

def check_validation_consensus(block):
    # return is_valid, valid_unknown, percent, is_valid_count
    self_node = get_self_node()
    broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(block)
    if self_node.id in validator_list:
        try:
            validator = Validator.objects.filter(pointerId=block.id, creator_node_id=self_node.id)[0]
        except:
            is_valid, validator, is_new_validation = validate_block(block, broadcast_list=broadcast_list)
            if is_new_validation:
                broadcast_validation(block, lst=validator_list)

    is_valid = Validator.objects.filter(pointerId=block.id, is_valid=True, creator_node_id__in=validator_list)
    not_valid = Validator.objects.filter(pointerId=block.id, is_valid=False, creator_node_id__in=validator_list)
    validations = list(chain(is_valid, not_valid))
    # validators = []
    # for v in is_valid:
    #     if v.creator_node_id not in validators:
    #         validators.append(v.creator_node_id)
    # for v in not_valid:
    #     if v.creator_node_id not in validators:
    #         validators.append(v.creator_node_id)
    total = len(validations)
    percent = is_valid.count() / total * 100
    # elif self_node.id not in validators and block.created > datetime.datetime.now() - datetime.timedelta(minutes=9) and total < required_validators:

    if total < round(required_validators/10*9) and (block.datetime + datetime.timedelta(minutes=block_time_delay)) < datetime.datetime.now():
        if self_node.id in validator_list:
            time_difference = (datetime.datetime.now() - block.datetime) % 10
            # x = time_difference / 10
            # already_received = len(validator_list) + (time_difference - 10) # all but most recent 10
            temp_broadcast_list = []
            for peer_id in broadcast_list[:required_validators + time_difference]:
                temp_broadcast_list.append(broadcast_list[peer_id])
            broadcast_block(block, lst=temp_broadcast_list)
        is_valid, validator, is_new_validation = validate_block(block, broadcast_list=broadcast_list)
        if is_new_validation:
            broadcast_validation(block)
    elif total >= round(required_validators/10*9) and percent >= validation_consensus:
        block.mark_valid()
        queue = django_rq.get_queue('default')
        queue.enqueue(broadcast_block, block, lst=broadcast_list, job_timeout=200)

        return True, False, validations
        
    # elif percent < 67
    elif total >= round(required_validators/10*9) and percent < 50:
        block.is_not_valid()
        return False, False, validations
    

    elif total >= round(required_validators/10*9) and percent < validation_consensus and percent > 50:
        # rerun using all nodes, besides just selected validators
        is_valid = Validator.objects.filter(pointerId=block.id, is_valid=True)
        not_valid = Validator.objects.filter(pointerId=block.id, is_valid=False)
        validations = list(chain(is_valid, not_valid))
        # validators = []
        # for v in is_valid:
        #     if v.creator_node_id not in validators:
        #         validators.append(v.creator_node_id)
        # for v in not_valid:
        #     if v.creator_node_id not in validators:
        #         validators.append(v.creator_node_id)
        total = len(validations)
        percent = is_valid.count() / total * 100
        if percent >= validation_consensus:
            block.mark_valid()
            queue = django_rq.get_queue('default')
            queue.enqueue(broadcast_block, block, lst=broadcast_list, job_timeout=200)
            return True, False, validations
        elif percent < 50:
            block.is_not_valid()
            return False, False, validations
        elif self_node.id not in validations:
            is_valid, validator, is_new_validation = validate_block(block, broadcast_list=broadcast_list)
            if is_new_validation:
                broadcast_validation(block, lst=validator_list)
                if validator.is_valid:
                    total = len(validations) + 1
                    percent = (is_valid.count() + 1) / total * 100
                    if percent >= validation_consensus:
                        block.is_valid()
                        queue = django_rq.get_queue('default')
                        queue.enqueue(broadcast_block, block, lst=broadcast_list, job_timeout=200)
                        return True, False, validations
                    elif percent < 50:
                        block.is_not_valid()
                        return False, False, validations
    return False, True, validations

def validate_block(block, broadcast_list=None):
    self_node = get_self_node()
    # chain = Blockchain.objects.filter(id=block.blockchainId)[0]
    # last_block = Block.objects.filter(blockchainId=chain.id, index=int(block.index)-1)[0]
    if not broadcast_list:
        broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(block)
    creator_node = get_node(id=next(iter(broadcast_list)))
    # if next(iter(broadcast_list)) == self_node.id:
    #     creator_node = last_block.get_creator_of_next_block(convert_to_datetime(block.created))
    # target_hash = block.hash
    # hash, expanded_data = get_hash(block)
    
    signature_verified = get_user(node=creator_node).verify_signature(str(get_signing_data(block)), block.signature)
    # signature = current_user.sign_transaction(base64.b64decode(private_key), expanded_data)
    
    # if not signature_verified:
    #     return False, None, False
    # else:
    hash, expanded_data = get_hash(block)
    target_hash = block.hash
    try:
        validator = Validator.objects.filter(pointerId=block.id, creator_node_id=self_node.id)[0]
        is_new_validation = False
    except:
        validator = Validator(pointerId=block.id, pointerType='Block', creator_node_id=self_node.id)
        is_new_validation = True
    if hash == target_hash and signature_verified:
        validator.is_valid = True
        validator.save()
    else:
        validator.is_valid = False
        validator.save()
    # if is_new_validation:
    #     signature = get_user(node=self_node).sign_transaction(base64.b64decode(private_key), get_expanded_data(validator))
    #     validator.signature = signature
    #     validator.save()
    return validator.is_valid, validator, is_new_validation

def broadcast_validation(block, lst=None):
    self_node = get_self_node()
    if lst:
        broadcast_list = lst
    else:
        broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(self_node)
    json_data = {'type' : 'Validations', 'block_dict' : block.__dict__, 'validations' : [], 'broadcast_list' : broadcast_list}
    validations = Validator.objects.filter(pointerId=block.id)
    json_data['validations'] = [v.__dict__ for v in validations]
    downstream_broadcast(lst, 'receive_validations', json_data)

def connect_to_node(node, url, json_data):
    print('connect to node')
    json_data['sender'] = get_self_node().__dict__
    # json_data['node_data'] = get_latest_node_data()
    reponse = None
    try:
        if not node.deactivated:
            response = requests.post(node.ip_address + '/' + url, json=json_data, timeout=10)
            if response.status_code == 200:
                accessed(node=node, response_time=response.elapsed.total_seconds())
                return True, response
            else:
                node.add_failure()
                return False, response
        else:
            return False, None
    except Exception as e:
        print(str(e))
        node.add_failure()
        return False, response

def node_ai_capable():
    # when declaring self_node ai_capable, an already established ai_capable node
    # should test the response, should be a simple prompt that it's own ai can verify
    # should also return response in a reasonable time. if good, validate, share validation
    pass

def downstream_broadcast(broadcast_list, target, json_data, self_dataPacket=False):
    print('downstream broadcast')
    successes = 0
    def func(peer_ids):
        successes = 0
        peer_nodes = Node.objects.filter(id__in=peer_ids)
        for node in peer_nodes:
            # node = get_node(id=peer_id)
            if node.deactivated:
                try:
                    func(broadcast_list[node.id])
                except Exception as e:
                    print(str(e))
            else:
                success, response = connect_to_node(node, target, json_data)
                if success:
                    successes += 1
                else:
                    try:
                        s = func(broadcast_list[node.id])
                        successes += s
                    except Exception as e:
                        print(str(e))
        return successes
    try:
        peers = broadcast_list[get_self_node().id]
        s = func(peers)
        successes += s
    except Exception as e:
        print(str(e))
    if successes >= number_of_peers and self_dataPacket:
        try:
            dataPacket = DataPacket.objects.filter(creator_node_id=get_self_node().id).exclude(data=[])[0]
            dataPacket.data = '[]'
            dataPacket.save()
        except Exception as e:
            print(str(e))



# is_not_valid() should register a strike against that node
# each update node data should take a snapshot of node list if deactivation status changes
# each node should sign every nodeUpdate and every block validation
# each nodeUpdate, validation and block should be checked for signiture
# change get broadcast_peers from node.ip_address to node.id
# change dataPacket to dataPacket
# block creator should receive reward money
# attempt to get_peer_nodes or update_node_data all in one line

# official node snapshot that is available to everyone
# updaate snapshot changes every 5 or 10 minutes
# each node gets to validate the NodeSnapShot
# blockchain of snapshots!

# block.is_not_valid needs signature, make sure strikes verify signature
# assess activity needs signature

            