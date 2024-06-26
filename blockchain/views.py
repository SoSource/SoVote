from django.shortcuts import render
from .models import Blockchain, Block, Node
from accounts.models import Sonet, User, UserPubKey, verify_obj_to_data
from posts.models import sync_and_share_object, sync_model, get_or_create_model, get_dynamic_model, search_and_sync_object, get_data_with_relationships, find_or_create_chain_from_object, now_utc
from blockchain.models import get_signing_data, round_time_down, downstream_broadcast, get_broadcast_peers, process_received_data, NodeChain_genesisId, ValidatorChain_genesisId, number_of_peers, required_validators, Validator, get_node, get_expanded_data, accessed, get_operatorData
from posts.utils import get_user_sending_data
import datetime
import hashlib
import uuid
import json
from uuid import uuid4
import django_rq
from rq import Queue
# import socket
import requests
from urllib.parse import urlparse
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict



@csrf_exempt
def get_broadcast_list_view(request):
    print('get_broadcast_list_view')
    try:
        obj = 'objx'
        obj_json = 'jsonx'
        try:
            if request.method == 'POST':
                print()
                # try:
                obj_json = request.POST.get('obj')
                obj = get_or_create_model(obj_json['object_type'], obj_json)
                broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(obj)
                return JsonResponse({'obj' : obj, 'broadcast_list' : broadcast_list, 'validator_list' : validator_list})
                # except:
                #     return JsonResponse({'obj' : obj, 'broadcast_list' : [], 'validator_list' : []})
            else:
                return JsonResponse({'message' : 'not post'})
        except Exception as e:
            try:
                x = request.POST.get('obj')
            except Exception as x:
                x = str(x)
            return JsonResponse({'message' : str(e) + '__' + str(obj) + '//' + str(obj_json) + '--' + x})
    except Exception as e:
        return JsonResponse({'message' : str(e)})

def get_current_node_list_view(request):
    try:
        chain = Blockchain.objects.filter(genesisType='Nodes', genesisId=NodeChain_genesisId)[0]
        dt = round_time_down(now_utc())
        node_block = Block.objects.filter(blockchainId=chain.id, datetime=dt)[0]

        node_data = json.loads(node_block.data)
        data = {}
        for chain, nodes in node_data['specialChains'].items():
            target_nodes = []
            for i in nodes:
                target_nodes.append(i)
            data[chain] = list(Node.objects.filter(id__in=target_nodes, self_declare_active=True).exclude(deactivated=True).exclude(ip_address='').values_list('ip_address', flat=True))
        for chain, nodes in node_data['regionChains'].items():
            target_nodes = []
            for i in nodes:
                target_nodes.append(i)
            data[chain] = list(Node.objects.filter(id__in=target_nodes, self_declare_active=True).exclude(deactivated=True).exclude(ip_address='').values_list('ip_address', flat=True))
        return JsonResponse({'message' : 'Success', 'data' : json.dumps(data)})
    except Exception as e:
        return JsonResponse({'message' : 'Fail', 'error' : str(e)})

@csrf_exempt
def get_node_request_view(request, node_id):
    print('get_node')
    try:
        if node_id == 'self':
            operatorData = get_operatorData()
            node_obj = get_or_create_model('Node', id=operatorData['nodeId'])
            response = JsonResponse({'nodeData' : get_signing_data(node_obj)})
            return response
        else:
            try:
                sonet = get_signing_data(Sonet.objects.first())
            except:
                sonet = None
            try:
                node = Node.objects.filter(id=node_id)[0]
                print('return 1')
                nodeData = get_signing_data(node)
                print('return sign data', nodeData)
                return JsonResponse({'message' : 'Node found', 'nodeData' : nodeData, 'sonet' : sonet})
            except:
                node_id = node_id
                dt = now_utc()
                node = Node(id=node_id, created=dt)
                nodeData = get_signing_data(node)
                print('node set up', node.__dict__)
                print('return 2')
                return JsonResponse({'message' : 'Node not found', 'nodeData' : nodeData, 'sonet' : sonet})
    except Exception as e:
        return JsonResponse({'message' : 'Fail', 'error' : str(e)})

@csrf_exempt
def declare_node_state_view(request):
    print('declare_node_state_view')
    try:
        if request.method == 'POST':
            print()
            nodeData = json.loads(request.POST.get('nodeData'))
            publicKey = nodeData['publicKey']
            signature = nodeData['signature']
            print()
            print('pubkey', publicKey)
            print('sig', signature)
            try:
                user = User.objects.filter(id=nodeData['User_obj'])[0]
                print('user found', user)
                x = get_signing_data(nodeData)
                print()
                print(x)
                print()
                try:
                    upk = UserPubKey.objects.filter(User_obj=user, publicKey=publicKey)[0]
                    print(upk)
                    # print(signature)
                    # print(x)
                    is_valid = upk.verify(x, signature)
                    # print('is_valid', is_valid)
                    if is_valid:
                        node_obj = get_or_create_model('Node', id=nodeData['id'])
                        # upk.User_obj = user
                        node_obj, good = sync_model(node_obj, nodeData)
                        print('nodeData-good',good)
                        # self_broadcast_list, broadcast_list, validator_list = get_broadcast_peers(node_obj)
                        # downstream_broadcast(broadcast_list, '/blockchain/declare_node_state', nodeData)
                        if good:
                            queue = django_rq.get_queue('default')
                            queue.enqueue(node_obj.broadcast_state, job_timeout=200)

                            response = JsonResponse({'message' : 'Sync success', 'nodeData' : x})
                            return response
                        else:
                            return JsonResponse({'message' : 'Sync failed'})
                    else:
                        return JsonResponse({'message' : 'Verification failed'})
                except Exception as e:
                    print(str(e))
                    return JsonResponse({'message' : 'Invalid Password'})
            except Exception as e:
                print(str(e))
                return JsonResponse({'message' : 'User not found'})
    except Exception as e:
        return JsonResponse({'message' : str(e)})

def receive_disavow(request):
    # if enough nodes disavow self_node:
    # operatorData = get_operatorData()
    # operatorData['disavowed'] = True
    # write_operatorData(operatorData)
    pass

@csrf_exempt
def check_if_exists_view(request):
    if request.method == 'POST':
        obj_type = request.POST.get('obj_type')
        if obj_type == 'Blockchain':
            genesisId = request.POST.get('genesisId')
            obj = get_dynamic_model(obj_type, genesisId=genesisId)
        elif obj_type == 'Block':
            blockchainId = request.POST.get('blockchainId')
            index = request.POST.get('index')
            obj = get_dynamic_model(obj_type, blockchainId=blockchainId, index=index)
        else:
            obj_id = request.POST.get('obj_id')
            obj = get_dynamic_model(obj_type, id=obj_id)

        if obj:
            return JsonResponse({'message' : 'Found', 'obj' : model_to_dict(obj)})
        else:
            return JsonResponse({'message' : 'Not Found'})

def broadcast_dataPackets_view(request):
    # happens when self_node declares self inactive
    pass

@csrf_exempt
def receive_data_view(request):
    try:
        # different types of data should be processed differently
        # ex block should check validation consensus when received, note process_received_block()
        # check sender of content, do not accept if node.disavowed
        if request.method == 'POST':
            data = request.POST.get('data')
            # items = request.POST.get('items')
            result = process_received_data(data)
            return JsonResponse({'message' : 'Finished', 'result' : str(result)})

    except Exception as e:
        return JsonResponse({'message' : 'Fail', 'error' : str(e)})

@csrf_exempt
def request_data_view(request):
    try:
        err = 'x'
        if request.method == 'POST':
            obj_type = request.POST.get('type')
            if obj_type == 'Blockchain':
                genesisId = request.POST.get('genesisId')
                # if genesisId == 'New', 'SoMeta', 'Transactions', 'Nodes
                try:
                    if genesisId == 'Nodes':
                        chain = Blockchain.objects.filter(genesisType=genesisId)[0]
                        chains = [model_to_dict(chain)]
                    elif genesisId == 'SoMeta':
                        chain = Blockchain.objects.filter(genesisType=genesisId)[0]
                        # retreive validator chain as well
                        validatorChain = Blockchain.objects.filter(validatesPointerId=chain.id)[0]
                        chains = [model_to_dict(validatorChain), model_to_dict(chain)]
                    else:
                        chain = Blockchain.objects.filter(genesisId=genesisId)[0]
                        # retreive validator chain as well
                        validatorChain = Blockchain.objects.filter(validatesPointerId=chain.id)[0]
                        chains = [model_to_dict(validatorChain), model_to_dict(chain)]
                    return JsonResponse({'message' : 'Found', 'blockchain' : chains})
                except Exception as e:
                    return JsonResponse({'message' : 'Not Found', 'genesisId' : genesisId, 'error' : str(e)})
            elif obj_type == 'Block':
                index = request.POST.get('index')
                blockchainId = request.POST.get('blockchainId')
                # for i in items:
                try:
                    chain = Blockchain.objects.filter(id=blockchainId)[0]
                except Exception as e:
                    return JsonResponse({'message' : 'Not Found', 'chainId' : blockchainId, 'error' : str(e)})
                try:
                    block = Block.objects.filter(blockchainId=chain.id)[index]
                    if chain.genesisType == 'Nodes' and chain.chain_length > block.index:
                        # only return data content from newest block on 'Nodes' chain
                        block_content = []
                    else:
                        block_content = block.get_full_data()
                    return JsonResponse({'message' : 'Found', 'block' : model_to_dict(block), 'content' : str(block_content)})
                except Exception as e:
                    return JsonResponse({'message' : 'Not Found', 'blockchainId' : blockchainId, 'index' : index, 'error' : str(e)})

            else:
                items = request.POST.get('items')
                index = 'NA'
                if items == 'All':
                    index = request.POST.get('index')
                    models = get_dynamic_model(obj_type, list=[int(index), int(index) + 500])
                    index = int(index) + 500
                elif obj_type == 'Region' and items == 'networkSupported':
                    err = '1'
                    index = request.POST.get('index')
                    err = '2'
                    models = get_dynamic_model(obj_type, list=[int(index), int(index) + 500], is_supported=True)
                    err = '3'
                    index = int(index) + 500
                else:
                    models = get_dynamic_model(obj_type, list=True, id__in=items)
                if models:
                    err = '4'
                    data_to_send = [model_to_dict(obj) for obj in models if verify_obj_to_data(obj, obj)]
                    return JsonResponse({'message' : 'Found', 'data' : str(data_to_send), 'index' : index})
                else:
                    return JsonResponse({'message' : 'Not Found'})
    except Exception as e:
        return JsonResponse({'message' : 'Fail', 'error' : str(e) + '/' + err})

def receive_posts_for_validating_view(request):
    # receive data from scraper node
    # if self_node is assigned to validate, check if second copy received
    # if not received, do nothing
    # if second copy is already received compare data, if match, create validator
    # broadcast validator and first created items, delete copy items
    # take special note of receiving keyphrase or notification
    pass


def request_item(request, item_type, item_id):
    # return item with update, for use in blockchain.models.get_item_data() when validating a block
    item = globals()[item_type].objects.filter(id=item_id)[0]
    return dict_with_relationships(item)

def request_blocks(request):
    # return request blocks, if 1st block included, include blockchain

    if request.method == 'POST':
        received_json = json.loads(request.body)
        blockchain = Blockchain.objects.filter(id=received_json['blockchain_id'])[0]
        # self_node = get_self_node(IpAddr)
        # get_from_node = find_or_sync_node(received_json['sender'])
        json_data = {'type' : 'Blocks', 'blockchain_id' : blockchain.id, 'block_list' : [], 'broadcast_list': [], 'end_of_chain' : True}
        # json_data = {'sender' : self_node.__dict__, 'blockchain' : blockchain.id, 'requests' : list(range(0, int(new_block['index'])))}
        starting_block = received_json['request_first']
        # try:
        #     ending_block = received_json['number_of_blocks']
        # except:
        #     ending_block = blockchain.chain_length
        for n in range(int(starting_block), int(starting_block) + 10):
            block = Block.objects.filter(blockchain=blockchain, index=n['id'])[0]
            validations = Validator.objects.filter(pointerId=block.id)
            validation_list = [v.__dict__ for v in validations]
            json_data['block_list'].append({'block_dict' : block.__dict__, 'block_data' : get_expanded_data(block), 'validations' : validation_list})
        if blockchain.chain_length > int(starting_block) + 10:
            json_data['end_of_chain'] = False
        return JsonResponse(json_data)
    return JsonResponse({'message' : 'not post method'})


def receive_blocks(request):
    if request.method == 'POST':
        received_json = json.loads(request.body)
        
        sender_node = get_node(id=received_json['sender']['id'])
        accessed(node=sender_node)

        queue = django_rq.get_queue('default')
        queue.enqueue(process_received_blocks, received_json, job_timeout=200)


        # block_list = None
        # try:
        #     new_block = received_json['new_block']
        # except:
        #     block_list = received_json['block_list']

        # think long and hard on how to handle discrepancies in chains
            
        # current error - new branch is started on block containing model where
        # blockchain_genesis_type == object_type. that means a block can have multiple
        # branches since each block contains multiple models. is this ok?
            #     # request chain from sender
            #     self_node = get_self_node(IpAddr)
            #     json_data = {'sender' : dict_with_relationships(self_node), 'blockchain_id' : blockchain.id, 'requests' : list(range(0, int(new_block['index'])))}
            #     response = requests.post(sender_node.ip_address + '/request_blocks', json=json_data, timeout=30)
            #     response_json = json.loads(response.body)
            #     for block in response_json['block_list']:
            #         isValid = blockchain.validate_block(block)
            #         if isValid:
            #             try:
            #                 created_block = Block.objects.filter(id=block['object']['updates'][0]['id'])[0]
            #             except:
            #                 created_block = blockchain.create_block(block=block)
            #             if block == new_block:
            #                 broadcast_block = True
            #             for o in block['content']:
            #                 object, databaseUpdated = search_and_sync_object(o)
            #         else:
            #             # request previous 5 blocks until valid one is found
            #             # delete invalid blocks, revoke reward
            #             pass


        # if new_block:
        #     broadcast_peers, broadcast_list, validator_list = get_broadcast_peers(new_block)
        #     if get_self_node(IpAddr).id in validator_list:
        #         is_valid, validator, is_new_validation = validate_block(new_block)
        #         if is_new_validation:
        #             broadcast_validation(validator)
        #     else:
        #         valid = []
        #         not_valid = []
        #         total = 0
        #         for v in received_validations['valid']:
        #             valid.append(v)
        #             total += 1
        #         for v in received_validations['not_valid']:
        #             not_valid.append(v)
        #             total += 1
        #         percent = len(valid) / total * 100
        #         if len(valid) >= required_validators and percent > 90:
        #             is_valid = True
        #         elif total < (len(get_node_list) / 2) and percent > 50:
        #             is_valid, validator = validate_block(new_block)
        #             broadcast_validation(validator_list, validator)
            
                
        #     if is_valid:
        #         try:
        #             blockchain = Blockchain.objects.filter(id=blockchain_id)[0]
        #         except:
        #             blockchain = create_new_chain(new_block)
        #         func(new_block)
        #     else:
        #         is_valid = False
        #         if get_self_node(IpAddr).id in validator_list:
        #             broadcast_validation(validator_list, validator)
                 
        # if new_block:
        #     # block = func(new_block)
        #     # check_validation_consensus(block)

        #     queue = django_rq.get_queue('default')
        #     queue.enqueue(add_received_block, new_block, sender_node, job_timeout=200)

        #     # isValid = blockchain.validate_block(new_block)
        #     # if isValid:
        #     #     func(new_block)
        #     # else:
        #     #     sender = received_json['sender_ip']
        #     #     creator = received_json['creator']
        #         # retrun to creator and sender invalid block response
        #         # or request older blocks, re verify, not sure
        # elif block_list:
        #     for new_block in block_list:
                
        #         queue = django_rq.get_queue('default')
        #         queue.enqueue(add_received_block, new_block, sender_node, job_timeout=200)

                # if is_valid:
                #     try:
                #         blockchain = Blockchain.objects.filter(id=blockchain_id)[0]
                #     except:
                #         blockchain = create_new_chain(new_block)
                #     func(new_block)
        # elif new_block and blockchain.chain_length < (int(new_block['index']) - 1):
        #     self_node = get_self_node(IpAddr)
        #     json_data = {'sender' : dict_with_relationships(self_node), 'blockchain_id' : blockchain.id, 'requests' : list(range(0, int(new_block['index'])))}
        #     response = requests.post(sender_node.ip_address + '/request_blocks', json=json_data, timeout=30)
        #     response_json = json.loads(response.body)

        #     for block in response_json['block_list']:
        #         isValid = blockchain.validate_block(block)
        #         if isValid:
        #             try:
        #                 created_block = Block.objects.filter(id=block['object']['updates'][0]['id'])[0]
        #             except:
        #                 created_block = blockchain.create_block(block=block)
        #             if block == new_block:
        #                 broadcast_block = True
        #             for o in block['content']:
        #                 object, databaseUpdated = search_and_sync_object(o)
        #         else:
        #             # request previous 5 blocks until valid one is found
        #             # delete invalid blocks, revoke reward
        #             pass
    return JsonResponse({'message' : 'success'})

def receive_data_packet_view(request):
    if request.method == 'POST':
        received_json = json.loads(request.body)
        # json_data = received_json['node_data']
        # to_pass_along = []
        
        sender_node = get_node(id=received_json['sender']['id'])
        accessed(node=sender_node)
        queue = django_rq.get_queue('default')
        queue.enqueue(process_data_packet, received_json, job_timeout=200)

        # try:
        #     self_node = get_self_node()
        #     broadcast_peers = broadcast_list[self_node.id]
        #     successes = 0    
        #     tried_nodes = []
        #     send_json_data = {'type' : 'DataToShare', 'broadcast_list' : broadcast_list, 'node_data' : json_data}
        #     for node in broadcast_peers:
        #         tried_nodes.append(node)
        #         success, response = connect_to_node(node, 'receive_data_to_share', send_json_data)
        #         if success:
        #             successes += 1
        #         # add downstream peers if not success
        # except Exception as e:
        #     print(str(e))
        return JsonResponse({'message' : 'success'})
    return JsonResponse({'message' : 'not post method'})
        
        
def request_items(request):
    if request.method == 'POST':
        received_json = json.loads(request.body)
        sender_node = get_node(id=received_json['sender']['id'])
        accessed(node=sender_node)
        # update_node_data(received_json['node_data'])
        json_data = {'content' : []}
        for item in received_json['request_items']:
            try:
                obj = globals()[item[0]].objects.filter(id=item[1])[0]
                obj_data = get_data_with_relationships(obj)
                json_data = ['content'].append(obj_data)
            except:
                obj_data = False
        return JsonResponse(json_data)
    else:
        return JsonResponse({'message' : 'not post method'})
        
            

# @csrf_exempt
def receive_item(request):
    if request.method == 'POST':
        # blockchain = Blockchain.objects.filter(id=iden)[0]
        received_json = json.loads(request.body)
        sender_node = get_node(id=received_json['sender']['id'])
        accessed(node=sender_node)
        update_node_data(received_json['node_data'])
        # try:
        #     blockchain = Blockchain.objects.filter(genesisId=received_json['content'][0]['object']['object_dict']['blockchain_genesis_id'])[0]
        # except:
        #     blockchain = create_new_chain(received_json['content'][0]['object']['object_dict'])
        
        # add to blockchain.to_commit_data
        # if self == blockchain.next_validator and last_block.created > 5mins ago
        # create and broadcast block
        
        # if received object is newer and current object not locked to chain it will update 
        for i in received_json['content']:
            obj, databaseUpdated = search_and_sync_object(i)
            blockchain, obj = find_or_create_chain_from_object(obj)
            blockchain.add_item_to_data(obj)
        # downstream_broadcast(broadcast_list, 'receive_validation', received_json)
        
        response = {'message': f'This transaction will be added to Block'}
    return JsonResponse(response)

def receive_validations(request):
    if request.method == 'POST':
        received_json = json.loads(request.body)
        # validators = received_json['validators']
        # broadcast_list = received_json['broadcast_list']
        sender_node = get_node(id=received_json['sender']['id'])
        accessed(node=sender_node)
        # block = Block.objects.filter(id=validators[0].pointerId)[0]
        # for v in validators:
        #     try:
        #         validator = Validator.objects.filter(id=v['id'])[0]
        #     except:
        #         validator = Validator()
        #         for field in v:
        #             setattr(validator, field, v[field])
        #         validator.save()

        # queue = django_rq.get_queue('default')
        # queue.enqueue(downstream_broadcast, broadcast_list, 'receive_validation', received_json, job_timeout=200)


        # # downstream_broadcast(broadcast_list, 'receive_validation', received_json)
        # update_node_data(received_json['node_data'])

        queue = django_rq.get_queue('default')
        queue.enqueue(process_received_validation, received_json, job_timeout=200)

        return JsonResponse({'message' : 'success'})
    return JsonResponse({'message' : 'not post method'})



# Connecting new nodes
# @csrf_exempt
def node_update(request):
    if request.method == 'POST':
        # received_json = json.loads(request.body)
        # nodes = received_json.get('node_data')
        update_node_data(json.loads(request.body)['node_data'])

        # if nodes is None:
        #     return "No node", HttpResponse(status=400)
        # for node in nodes:
        #     blockchain.add_node(node)
        # response = {'message': 'All the nodes are now connected. The Sudocoin Blockchain now contains the following nodes:',
        #             'total_nodes': list(blockchain.nodes)}
    
        return JsonResponse({'message':'success'})
    else:
        return JsonResponse({'message':'not post method'})
