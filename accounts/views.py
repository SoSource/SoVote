
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils.text import slugify
from django.template.defaulttags import register
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,

    )

from scrapers.canada.federal import get_federal_match

from .models import *
from .forms import *
from posts.models import *
from posts.utils import *
from posts.forms import SearchForm
from posts.views import render_view
from blockchain.models import get_signing_data
from django.http import JsonResponse, HttpResponse, HttpRequest

# from fcm_django.models import FCMDevice
# from firebase_admin.messaging import Message, Notification
from django.db.models import Q, Value, F
# import auth_token
import os
import datetime
import requests
import json
from bs4 import BeautifulSoup
import time
from uuid import uuid4
import operator
import ast

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

headers = {
    'User-Agent': "OOrss-get"
} 

def privacy_policy_view(request):
    style = request.GET.get('style', 'index')
    context = {
        'title': 'Privacy Policy',
        'cards': 'privacyPolicy',
    }
    return render_view(request, context)
    
def values_view(request):
    style = request.GET.get('style', 'index')
    context = {
        'title': 'Values',
        'cards': 'values',
    }
    return render_view(request, context)

def hero_view(request):
    style = request.GET.get('style', 'index')
    context = {
        'title': 'So, You want to be a Hero?',
        'cards': 'hero',
    }
    return render_view(request, context)

def about_view(request):
    style = request.GET.get('style', 'index')
    context = {
        'title': 'About Us',
        'cards': 'about',
    }
    return render_view(request, context)

def contact_view(request):
    style = request.GET.get('style', 'index')
    context = {
        'title': 'Contact',
        'cards': 'contact',
    }
    return render_view(request, context)

def get_app_view(request):
    style = request.GET.get('style', 'index')
    context = {
        'title': 'Get the App',
        'cards': 'getApp',
    }
    return render_view(request, context)

def story_view(request):
    style = request.GET.get('style', 'index')
    context = {
        'title': 'A So-So Story',
        'cards': 'story',
    }
    return render_view(request, context)

def login_signup_view(request):
    print('login signup view')
    user_id = uuid.uuid4().hex
    # wallet_id = uuid.uuid4().hex
    # upk_id = uuid.uuid4().hex
    dt = now_utc()
    user_obj = User(id=user_id, username=user_id, created=dt)
    context = {
        'title': 'Login/Signup',
        'user_dict': get_signing_data(user_obj),
        # 'wallet_dict': get_signing_data(wallet_obj),
        # 'upk_dict': get_signing_data(upk_obj),
    }
    # print('n2')
    return render(request, "forms/login-signup.html", context)

def rename_setup_view(request):
    print('rename_setup view')
    # user_id = uuid.uuid4().hex
    # wallet_id = uuid.uuid4().hex
    # upk_id = uuid.uuid4().hex
    # dt = now_utc()
    # user_obj = User(id=user_id, username=user_id, created=dt)
    context = {
        'title': 'Mandatory User Rename',
        'text': 'Unfortunately your username was previously registered and must be replaced.',
        # 'user_dict': get_signing_data(user_obj),
        # 'wallet_dict': get_signing_data(wallet_obj),
        # 'upk_dict': get_signing_data(upk_obj),
    }
    # print('n2')
    return render(request, "forms/must_rename.html", context)

@csrf_exempt
def receive_rename_view(request):
    print('receive_rename_view')
    if request.method == 'POST':
        # received_json = request.POST
        # print(received_json)
        # print()
        userData = request.POST.get('userData')
        print(userData)
        userData_json = json.loads(userData)
        
        try:
            User.objects.filter(display_name=userData_json['display_name']).exclude(id=userData_json['id'])[0]
            return JsonResponse({'message':'Username taken'})
        except:
            
            user = request.user
            # data is verified during sync
            user, synced = sync_and_share_object(user, userData)
            print('synced',synced)
            user.slug = user.slugger()
            user.save()
            if synced:
                return JsonResponse({'message':'success'})
            else:
                return JsonResponse({'message':'Failed to sync'})
    return JsonResponse({'message':'Failed'})


def register_options_view(request):
    print('register options')
    from webauthn import (
        generate_registration_options,
        verify_registration_response,
        options_to_json,
        base64url_to_bytes,
    )
    from webauthn.helpers.cose import COSEAlgorithmIdentifier
    from webauthn.helpers.structs import (
        AttestationConveyancePreference,
        AuthenticatorAttachment,
        AuthenticatorSelectionCriteria,
        PublicKeyCredentialDescriptor,
        ResidentKeyRequirement,
    )



    user_id = uuid.uuid4().hex
    dt = datetime.datetime.now()
    print(user_id.encode())
    # print(bytes(user_id))
    # salt = os.urandom(16)
    user_obj = User(id=user_id, created=dt)
    # options_obj = UserOptions(id=uuid.uuid4().hex, user=user_id, created=dt, salt=salt)
    # userForm = UserRegisterForm(request.POST or None)

    simple_registration_options = generate_registration_options(
        rp_id='localhost',
        rp_name="SoVote",
        user_name="bob",
        user_id='679563c4a4214dc2ba7b6cb5896757f2'.encode(),
    )

    print(options_to_json(simple_registration_options))
    return JsonResponse(json.loads(options_to_json(simple_registration_options)))


def verify_transaction(transaction_data, signature):
    from ecdsa import SECP256k1, VerifyingKey, BadSignatureError, util
    import hashlib

    try:

        # Create a verifying key from the public key (assuming it's the compressed form of the key)
        # verifying_key = VerifyingKey.from_public_key_recovery(signature, SECP256k1, hashlib.sha256, util.sigdecode_string(signature, SECP256k1.order)[0] - 27)
        verifying_key = VerifyingKey.from_public_key_recovery(signature, SECP256k1, hashlib.sha256)  # The last argument is the hashing algorithm

        # Verify the signature
        is_verified = verifying_key.verify_digest(signature, bytes.fromhex(transaction_data), sigdecode=util.sigdecode_string)
        return is_verified
    

        # # Create a verifying key from the public key (assuming it's the compressed form of the key)
        # verifying_key = VerifyingKey.from_public_key_recovery(signature, SECP256k1, hashlib.sha256, util.sigdecode_string(signature, SECP256k1.order)[0] - 27)

        # # Verify the signature
        # is_verified = verifying_key.verify_digest(signature, to_buffer(transaction_data), sigdecode=util.sigdecode_string)
        # return is_verified

    except BadSignatureError:
        return False
    


    # # from ethereum.utils import ecrecover, pub_to_address, to_buffer, to_checksum_address, from_rpc_sig
    # from ethereum.utils import ecrecover, pub_to_address, to_buffer, to_checksum_address, from_rpc_sig, sha3

    # # In this example, I assume the transaction_data is the hash of the transaction
    # transaction_hash = sha3(to_buffer(transaction_data))

    # # Perform Ethereum signature verification
    # try:
    #     public_key = ecrecover(transaction_hash, signature.v, signature.r, signature.s)
    #     sender_address = to_checksum_address(pub_to_address(public_key))
        
    #     # Compare sender_address with the expected fromAddress or perform additional checks if needed
    #     expected_sender_address = 'YourFromAddress'
    #     return sender_address == expected_sender_address

    # except Exception as e:
    #     print(f"Error during signature verification: {e}")
    #     return False

# not used
def get_user_data_view(request, username):
    print('get user data view')
    try:
        user_obj = User.objects.filter(username=username)[0]
        return JsonResponse({'message' : 'User found', 'userData' : get_signing_data(user_obj)})
    except:
        user_id = uuid.uuid4().hex
        dt = datetime.datetime.now()
        user_obj = User(id=user_id, username=username, created=dt)
    # context = {
    #     'user_dict': get_signature_data(user_obj)
    # }
    # return render_view(request, context)
    x = get_signing_data(user_obj)
    # print(x)
    return JsonResponse(x)
    # return render(request, "utils/dummy.html", {'result': x})

def register_verify_view(request):

    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import ec
    import hashlib

    print('verify view')
    # print(request.body)
    print()
    import base64
    # print(request.POST)
    print('1')
    # elem = base64.b64decode(request.POST)
    # print(request.body.decode())
    # print(elem)
    received_json = request.POST
    print(received_json)
    # for i in received_json:
    #     print(i)
    #     print(received_json[i])
    print()
    print(received_json['publicKeyHex'])
    print()
    print('td', str(received_json['transactionData']))
    print()
    # print('privKey received',received_json['privateKey'])
    print()
    print(str(received_json['signature']))
    # print()
    # print(received_json['r'])
    # print()
    # print(received_json['s'])
    # from ethereum.utils import ecrecover, pub_to_address, to_buffer, to_checksum_address, from_rpc_sig
    from ecdsa import SECP256k1, VerifyingKey, BadSignatureError, util

    # signed_tx_data = request.POST.get('signedData')
    # print(signed_tx_data)
    # privateKey = request.POST.get('privateKey')
    publicKey = request.POST.get('publicKeyHex')
    transaction_data = request.POST.get('transactionData')
    signature = request.POST.get('signature')
    # r = request.POST.get('r')
    # s = request.POST.get('s')
    # signature = ['48', '68', '2', '32', '75', '213', '151', '71', '233', '42', '173', '36', '183', '158', '166', '10', '106', '120', '212', '39', '50', '167', '38', '155', '126', '181', '25', '253', '206', '34', '83', '133', '14', '214', '31', '255', '2', '32', '34', '43', '162', '192', '13', '128', '84', '45', '29', '73', '173', '198', '201', '81', '84', '42', '206', '249', '189', '189', '198', '13', '167', '13', '144', '63', '177', '244', '12', '6', '101', '139']
    # signature = ''.join(signature)
    # print(signature)
    print()

    samplepubkey = '04f8ccf508990ceef9e5b84f5aeb9fee1739d3d3b140fc05e5b2ff58524c660ba27f654ed36fe7dd9923a1ffaf5caa774c2e9fd18ffb486432f44914c22c29eccf'
    samplesig = '3044022010f92d4771aac187375265167f43854d510428a131124df798b406a5dcc7eab5022029bbadf9aa6b4741d7fed01999121fe34ad8b2216f7200d953904bbd271d84e0'
    sampler = '10f92d4771aac187375265167f43854d510428a131124df798b406a5dcc7eab5'
    samples = '29bbadf9aa6b4741d7fed01999121fe34ad8b2216f7200d953904bbd271d84e0'

    nextpubkey= 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEKFCwY4ysc/3EvJWfYhhmrg3qSzz1qiradgh+QH/P44eWTUq0v5HKbIbIMPdHSZb6pSjCnniBrwHMwVC3bM6VBQ=='
    nextsig = 'DlScOm5IU7/DFdN5wI/WBJNhIp4yJAKzsttmrxsOIduKbTgn53zBsqsKqd7qw0A9I7GjDkxLhyBE78EXND04Ug=='

    from ecdsa import SECP256k1, VerifyingKey

    # Received signature and public key from JavaScript
    signature_hex = "..."
    public_key_hex = "..."

    # Decode public key
    public_key = VerifyingKey.from_string(bytes.fromhex(publicKey), curve=SECP256k1)

    # Prepare data (replace with the same data used in JavaScript)
    data = "Transaction data"
    # hash = bytes.fromhex(require('crypto').createHash('sha256').update(data).digest('hex'))
    message = b"testmessage"

    # Verification
    try:
        if public_key.verify(bytes.fromhex(signature), message):
            print("Signature is valid!")
        else:
            print("Signature is invalid!")
    except Exception as e:
        print(str(e)) 
        print("Verification failed!")


    # import ecdsa
    # from ecdsa.util import sigencode_der
    # from hashlib import sha256
    # message = b"testmessage"
    # public_key = '98cedbb266d9fc38e41a169362708e0509e06b3040a5dfff6e08196f8d9e49cebfb4f4cb12aa7ac34b19f3b29a17f4e5464873f151fd699c2524e0b7843eb383'
    # sig = '740894121e1c7f33b174153a7349f6899d0a1d2730e9cc59f674921d8aef73532f63edb9c5dba4877074a937448a37c5c485e0d53419297967e95e9b1bef630d'
    # # sig = '3045022010f92d4771aac187375265167f43854d510428a131124df798b406a5dcc7eab5022100d64452065594b8be28012fe666ede01b6fd62ac53fd69f626c4212cfa918bc61'
    # # sig = '10f92d4771aac187375265167f43854d510428a131124df798b406a5dcc7eab529bbadf9aa6b4741d7fed01999121fe34ad8b2216f7200d953904bbd271d84e0'
    # sig = r + s

    # vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(publicKey), curve=ecdsa.SECP256k1) # the default is sha1
    # # vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1, hashfunc=sha256) # the default is sha1
    
    # from ecdsa.util import sigdecode_der
    # # signature_bytes = util.sigdecode_der(bytes.fromhex(signature), vk.pubkey.order)
    # # assert vk.verify(bytes.fromhex(signature), message, hashlib.sha256, sigdecode=sigdecode_der)
    # # assert vk.verify(signature, message, hashlib.sha256, sigdecode=sigencode_der)
    # is_valid = vk.verify(bytes.fromhex(sig), message) # True

    # # def verify_transaction(public_key, signature, message):
    # #     from ecdsa.util import sigdecode_der
    # #     vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    # #     print('vk', vk)
    # #     # signature_bytes = bytes.fromhex(signature)
    # #     # signature_bytes = bytes.fromhex(signature)
    # #     # signature_bytes = util.sigdecode_der(signature, vk.pubkey.order)
    # #     return vk.verify(signature, message.encode('utf-8'))
    # #     # return vk.verify(signature_bytes, message.encode('utf-8'), hashlib.sha256, sigdecode=sigdecode_der)
    # # # Replace these values with the corresponding values from your JavaScript code
    # # public_key_hex = publicKey
    # # signature_der_hex = signature
    # # # transaction_data = "Message"

    # # # Verify the transaction
    # # # message_hash = hash_message(transaction_data)
    # # is_valid = verify_transaction(public_key_hex, signature_der_hex, transaction_data)

    # if is_valid:
    #     print("Transaction is valid!")
    # else:
    #     print("Transaction is not valid.")




# --------this one works

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
    from cryptography.hazmat.primitives.serialization import load_der_public_key
    from cryptography.hazmat.primitives import hashes
    from cryptography.exceptions import InvalidSignature
    import base64
    import json



    publicKey = base64.b64decode(publicKey)
    # data = {
    # "data_1":"The quick brown fox",
    # "data_2":"jumps over the lazy dog"
    # }
    # data = "jumps over the lazy dog1111"
    # print('d', data)
    print('td', transaction_data)
    data = transaction_data
    signature = base64.b64decode(signature)

    publicKey = load_der_public_key(publicKey, default_backend())
    r = int.from_bytes(signature[:32], byteorder='big')
    s = int.from_bytes(signature[32:], byteorder='big')

    try:
        publicKey.verify(
            encode_dss_signature(r, s),
            json.dumps(data, separators=(',', ':')).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())    
        )
        print("verification succeeded")
    except InvalidSignature:
        print("verification failed")

# # -------------




    # publikKeyDer = base64.b64decode(publicKey)
    # # publikKeyDer = base64.b64decode("MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEWzC5lPNifcHNuKL+/jjhrtTi+9gAMbYui9Vv7TjtS7RCt8p6Y6zUmHVpGEowuVMuOSNxfpJYpnGExNT/eWhuwQ==")
    # # data = "jumps over the lazy dog"
    # print('trans_data', transaction_data)
    # # print('data', data)
    # signature = base64.b64decode(signature)
    # # signature = base64.b64decode("XRNTbkHK7H8XPEIJQhS6K6ncLPEuWWrkXLXiNWwv6ImnL2Dm5VHcazJ7QYQNOvWJmB2T3rconRkT0N4BDFapCQ==")

    # publicKey = load_der_public_key(publikKeyDer, default_backend())
    # r = int.from_bytes(signature[:32], byteorder='big')
    # s = int.from_bytes(signature[32:], byteorder='big')

    # try:
    #     publicKey.verify(
    #         encode_dss_signature(r, s),
    #         json.dumps(transaction_data).encode('utf-8'),
    #         ec.ECDSA(hashes.SHA256())    
    #     )
    #     print("verification succeeded")
    # except InvalidSignature:
    #     print("verification failed")






    # import hashlib
    # from ecdsa import SigningKey, SECP256k1, VerifyingKey

    def hash_message(message):
        sha256 = hashlib.sha256()
        sha256.update(message.encode('utf-8'))
        return sha256.hexdigest()

    # def verify_transaction(public_key, signature, message):
    #     from ecdsa.util import sigdecode_der
    #     vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    #     # signature_bytes = bytes.fromhex(signature)
    #     signature_bytes = bytes.fromhex(signature)
    #     # signature_bytes = util.sigdecode_der(bytes.fromhex(signature), vk.pubkey.order)
    #     return vk.verify(signature_bytes, message.encode('utf-8'))
    #     # return vk.verify(signature_bytes, message.encode('utf-8'), hashlib.sha256, sigdecode=sigdecode_der)
    # # Replace these values with the corresponding values from your JavaScript code
    # public_key_hex = publicKey
    # signature_der_hex = signature
    # transaction_data = "Message"

    # # Verify the transaction
    # message_hash = hash_message(transaction_data)
    # is_valid = verify_transaction(public_key_hex, signature_der_hex, message_hash)

    # if is_valid:
    #     print("Transaction is valid!")
    # else:
    #     print("Transaction is not valid.")





    # from cryptography.hazmat.primitives.serialization import load_der_private_key
    # # def sign_transaction(private_key, message):
    # #     private_key_obj = ec.derive_private_key(
    # #         int(private_key, 16),
    # #         ec.SECP256K1(),
    # #         default_backend()
    # #     )
    # #     print('priv key discoverd:', private_key)
    # #     signature = private_key_obj.sign(
    # #         message,
    # #         ec.ECDSA(hashes.SHA256())
    # #     )
    # #     return signature
    
    # def sign_transaction(private_key_hex, message):
    #     private_key_obj = ec.derive_private_key(
    #         int(private_key_hex, 16),
    #         ec.SECP256K1(),
    #         default_backend()
    #     )
    #     print('priv key discovered:', private_key_hex)
    #     signature = private_key_obj.sign(
    #         message,
    #         ec.ECDSA(hashes.SHA256())
    #     )
    #     return signature
    # privKey = '97ddae0f3a25b92268175400149d65d6887b9cefaf28ea2c078e05cdc15a3c0a'
    # message_bytes = str.encode('Message')
    # transaction_signature = sign_transaction(privKey, message_bytes)
    # print('!!!!!', transaction_signature.hex())

    # print('sig', signature)


    # message_bytes = str.encode(transaction_data)
    # private_key_bytes = str.encode(privateKey)
    # print('riv_key_bytes', private_key_bytes)



    # print('done')
    # # Message that was signed
    # message = transaction_data.encode()

    # # Convert the public key and signature values to bytes
    # public_key_bytes = bytes.fromhex(publicKey)
    # signature_bytes = bytes.fromhex(transaction_signature.hex())
    
    # # Create an Elliptic Curve Public Key object
    # public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
    # print('pubkey', public_key)
    # # Verify the signature
    # try:
    #     public_key.verify(signature_bytes, message_bytes, ec.ECDSA(hashes.SHA256()))
    #     print("Signature is valid.")
    # except Exception as e:
    #     print(str(e))
    #     print("Signature is invalid.")


    # from ecdsa import SigningKey
    # from ecdsa.curves import SECP256k1
    # ecdsakey = "59b1ad799522457fa5ed171cb850800fe511e55181d81250e66d42ff536427a1"
    # sk = SigningKey.from_string(bytes.fromhex(privateKey), curve=SECP256k1)
    # hash = "b93b25c03a2238e749272a99d8a47dbcc19c2db65b9b27671f1ec6b5defd279b"
    # # print(hash)
    # signature_bytes = bytes.fromhex(signature)
    # print('sig0', signature_bytes)
    # print()
    # signature_bytes = bytes.fromhex(r + s)
    # print('sig1', signature_bytes)
    # print()
    # # hash = codecs.decode(hash, 'hex')
    # message = str.encode('9a59efbc471b53491c8038fd5d5fe3be0a229873302bafba90c19fbe7d7c7f35')
    # sig = sk.sign_deterministic(message)
    # print('sig2', sig)
    # print()
    # vk = sk.get_verifying_key()
    # print(vk.verify(sig, message))










    # from ecdsa import SigningKey, SECP256k1, VerifyingKey
    # import hashlib

    # # Create an elliptic curve object for secp256k1
    # ec = SECP256k1

    # # Generate key pair or load from private key
    # private_key_hex = "97ddae0f3a25b92268175400149d65d6887b9cefaf28ea2c078e05cdc15a3c0a"
    # key_pair = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ec)

    # # Get private key and public key
    # priv_key = key_pair.to_string().hex()
    # pub_key = key_pair.get_verifying_key()

    # print(f"Private key: {priv_key}")
    # print("Public key:", pub_key.to_string().hex()[2:])
    # print("Public key (compressed):", pub_key.to_string("compressed").hex())





    # import ecdsa
    # import hashlib

    # # Convert the public key and signature values to bytes
    # public_key_bytes = bytes.fromhex(publicKey)
    # signature_bytes = bytes.fromhex(signature)
    # print('sig', signature_bytes)
    # # message_hash = hash_message(transaction_data)

    # message = str.encode(transaction_data)
    # print(message)
    # # from .curves import NIST192p, Curve, Ed25519, Ed448
    # # Create a VerifyingKey object from the public key bytes
    # vk = VerifyingKey.from_string(public_key_bytes, curve=ecdsa.SECP256k1)
    # try:
    #     # Verify the signature
    #     vk.verify(signature_bytes, message)
    #     print("Signature is valid.")
    # except BadSignatureError:
    #     print("Signature is invalid.")

    # import ecdsa
    # import hashlib





    # # Replace 'your_private_key_hex' with your actual private key
    # your_private_key_hex = "your_private_key_here"
    # priv_key = ecdsa.SigningKey.from_string(bytes.fromhex(privateKey), curve=ecdsa.SECP256k1)

    # # Replace 'inputted_public_key_hex' with the inputted public key
    # inputted_public_key_hex = "inputted_public_key_here"
    # inputted_pub_key = ecdsa.VerifyingKey.from_string(bytes.fromhex(publicKey), curve=ecdsa.SECP256k1)
    # print('pubkey', inputted_pub_key)


    # message = b"Message"
    # message = str.encode(transaction_data)
    # print(message)
    # message_hash = hashlib.sha256(message).digest()
    # signature1 = priv_key.sign(message_hash)
    # print("The signature is:\n", signature1)
    # print()
    # signature1 = bytes.fromhex(signature)
    # print("The signature is:\n", signature1)

    # try:
    #     inputted_pub_key.verify(signature1, message_hash)
    #     print("Signature verified: True")
    # except ecdsa.BadSignatureError:
    #     print("Signature verified: False")
    # except Exception as e:
    #     print(str(e))
    # print()



    # from ellipticcurve.ecdsa import Ecdsa
    # from ellipticcurve.privateKey import PrivateKey


    # # Generate new Keys
    # # privateKey = PrivateKey()
    # # print(privateKey)
    # # publicKey = privateKey.publicKey()
    # # print(publicKey)

    # message = "My test message"
    # print(message)
    # # Generate Signature
    # signature = Ecdsa.sign(message, privateKey)
    # print('sig', signature)

    # # To verify if the signature is valid
    # print(Ecdsa.verify(message, signature, publicKey))


    # import ecdsa
    # print()
    # from ecdsa import VerifyingKey, SECP256k1

    # # def verifySignature(dataToVerify, signatureBase64, publicKeyPem):
    # #     # Decode signature from base64
    # #     signature = bytes.fromhex(signatureBase64)
        
    # #     verifying_key = VerifyingKey.from_pem(publicKeyPem, curve=SECP256k1)
    # #     return verifying_key.verify(signature, dataToVerify)
    # from hashlib import sha256
    # # Example usage
    # data = b"Message"
    # # signatureBase64 = base64.b64decode(signature)  # Replace with the base64 encoded signature from JavaScript
    # publicKeyPem = publicKeyHex  # Replace with your public key in PEM format
    # is_valid = ecdsa.verify(data, signature, publicKeyHex, hashfunc=sha256)
    # # is_valid = verifySignature(data, signature, publicKeyPem)
    # print(f"Signature is valid: {is_valid}")
    # # Sign a message
    # msg = b'Message'
    # signature = key_pair.sign(msg, hashfunc=hashlib.sha256)

    # print(f"Msg: {msg.decode()}")
    # print("Signature:", signature.hex())

    # print()
    # import ecdsa
    # import hashlib
    # # your_private_key_hex = "97ddae0f3a25b92268175400149d65d6887b9cefaf28ea2c078e05cdc15a3c0a"
    # # priv_key = ecdsa.SigningKey.from_string(bytes.fromhex(your_private_key_hex), curve=ecdsa.SECP256k1)


    # # priv_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    # # public_key = priv_key.get_verifying_key()


    # # Replace 'inputted_public_key_hex' with the inputted public key
    # inputted_public_key_hex = "inputted_public_key_here"
    # public_key = ecdsa.VerifyingKey.from_string(bytes.fromhex(publicKeyHex), curve=ecdsa.SECP256k1)
    # print(public_key)
    # print(bytes.fromhex(signature))

    # message = b"Message"
    # message_hash = hashlib.sha256(message).digest()
    # print('1')
    # # signature = priv_key.sign(message_hash)
    # # print("The signature is:\n",signature)
    # try:
    #     public_key.verify(bytes.fromhex(signature), message_hash)
    #     print("Signature verified: True")
    # except ecdsa.BadSignatureError:
    #     print("Signature verified: False")
    # Recover public key from signature
    # def hex_to_decimal(x):
    #     return int(x, 16)

    # pub_key_recovered = VerifyingKey.from_public_point(
    #     hex_to_decimal(pub_key.to_string().hex()[-64:]), curve=ec)

    # print("Recovered pubKey:", pub_key_recovered.to_string("compressed").hex())

    # Verify the signature
    # valid_sig = pub_key_recovered.verify(signature, msg, hashfunc=hashlib.sha256)

    # print("Signature valid?", valid_sig)
    # public_key = base64.b64decode(publicKeyHex)
    # print(public_key)
    # # Hash the transaction data
    # digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    # digest.update(transaction_data.encode('utf-8'))
    # hashed_transaction = digest.finalize()

    # from cryptography.hazmat.primitives.asymmetric import ec
    # # # Verify the signature using the public key
    # try:
    #     pub_key.verify(signature.hex(), msg, ec.ECDSA(hashes.SHA256()))
    #     print('valid')
    # except Exception as e:
    #     print(f"Signature verification failed: {str(e)}")
    #     # return False  # Verification failed



    # import ecdsa
    # from hashlib import sha256
    # message = b"Message"
    # public_key = '98cedbb266d9fc38e41a169362708e0509e06b3040a5dfff6e08196f8d9e49cebfb4f4cb12aa7ac34b19f3b29a17f4e5464873f151fd699c2524e0b7843eb383'
    # sig = '740894121e1c7f33b174153a7349f6899d0a1d2730e9cc59f674921d8aef73532f63edb9c5dba4877074a937448a37c5c485e0d53419297967e95e9b1bef630d'


    # from ecdsa.util import sigdecode_der
    # # assert vk.verify(signature, data, hashlib.sha256, sigdecode=sigdecode_der)

    # vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(publicKeyHex), curve=ecdsa.SECP256k1, hashfunc=sha256) # the default is sha1
    # vk.verify(bytes.fromhex(signature), message, hashlib.sha256, sigdecode=sigdecode_der) # True
    # print('verify', vk.verify(bytes.fromhex(signature), message, hashlib.sha256, sigdecode=sigdecode_der))
    
    
    
    
    # s = request.POST.get('s')
    # r = request.POST.get('r')
    # v = request.POST.get('v')

    # Reconstruct the signature
    # r = signed_tx_data[0]
    # s = signed_tx_data[1]
    # v = signed_tx_data[2]
    # print(r)
    # print(s)
    # signature = util.sigdecode_string(bytes.fromhex(r + s), SECP256k1.order)  # Convert r and s to a DER-encoded signature
    # # signature = util.sigdecode_string(to_buffer(r + s), SECP256k1.order)  # Convert r and s to a DER-encoded signature

    # # Perform verification logic
    # is_verified = verify_transaction(transaction_data, signature)

    # # if is_verified:
    # print('verified', is_verified)
    
    # import ecdsa
    # from hashlib import sha256
    # message = b"message"
    # public_key = '98cedbb266d9fc38e41a169362708e0509e06b3040a5dfff6e08196f8d9e49cebfb4f4cb12aa7ac34b19f3b29a17f4e5464873f151fd699c2524e0b7843eb383'
    # sig = '740894121e1c7f33b174153a7349f6899d0a1d2730e9cc59f674921d8aef73532f63edb9c5dba4877074a937448a37c5c485e0d53419297967e95e9b1bef630d'

    # vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(publicKeyHex), curve=ecdsa.SECP256k1, hashfunc=sha256) # the default is sha1
    # verify = vk.verify(bytes.fromhex(signature), message) # True
    # print('verify', verify)
    # signed_tx_data = request.data.get('signedData')
    # transaction_data = request.data.get('transactionData')

    # # Reconstruct the signature
    # r = signed_tx_data['r']
    # s = signed_tx_data['s']
    # v = signed_tx_data['v']
    # signature = from_rpc_sig(to_buffer(r), to_buffer(s), to_buffer(v))
    # print('sig', signature)
    # # Perform verification logic
    
    # # Perform verification logic
    # is_verified = verify_transaction(transaction_data, signature)
    # print('verified', is_verified)

    # # Process the transaction if verification is successful
    # # Your custom logic here...

    # return JsonResponse({'status': 'success', 'verification_result': True})


    # if request.method == 'POST':
    #     # Get data from the POST request
    #     public_key_hex = request.POST.get('publicKeyHex')
    #     signature_hex = request.POST.get('signature')
    #     transaction_data = request.POST.get('transactionData')

    #     # Convert hexadecimal public key to bytes
    #     public_key_bytes = bytes.fromhex(public_key_hex)

    #     # Convert hexadecimal signature to bytes
    #     signature_bytes = bytes.fromhex(signature_hex)

    #     # Create an ECDSA public key object
    #     public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)

    #     # Verify the signature
    #     try:
    #         public_key.verify(signature_bytes, transaction_data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    #         print('is valid')
    #         return JsonResponse({'result': 'Signature is valid'})
    #     except Exception as e:
    #         print(str(e))
    #         print('is not valid')
    #         return JsonResponse({'result': 'Signature is not valid'})

    # # Handle other HTTP methods or return an error response if needed
    # return JsonResponse({'error': 'Invalid request method'})



    # data = received_json
    # public_key_hex = data['publicKeyHex']
    # signature_hex = data['signature']
    # transaction_data = data['transactionData']

    # # Convert hexadecimal public key to bytes
    # public_key_bytes = bytes.fromhex(public_key_hex)

    # # Convert hexadecimal signature to bytes
    # signature_bytes = bytes.fromhex(signature_hex)

    # # Create an ECDSA public key object
    # public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)

    # # Verify the signature
    # try:
    #     public_key.verify(signature_bytes, transaction_data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    #     print({'result': 'Signature is valid'})
    # except:
    #     print({'result': 'Signature is not valid'})




    # from cryptography.hazmat.primitives import hashes
    # from cryptography.hazmat.backends import default_backend
    # from cryptography.hazmat.primitives.asymmetric import ec

    # # Replace these values with the corresponding values from the JavaScript code
    # public_key_hex = received_json['publicKeyHex'].replace('"', '')  # The public key in hexadecimal format
    # signature_hex = received_json['signature'].replace('"', '')  # The signature in hexadecimal format
    # transaction_data = received_json['transactionData']

    # # Convert hexadecimal public key to bytes
    # public_key_bytes = bytes.fromhex(public_key_hex)

    # # Convert hexadecimal signature to bytes
    # signature_bytes = bytes.fromhex(signature_hex)

    # # Create an ECDSA public key object
    # public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)

    # # Verify the signature
    # try:
    #     public_key.verify(signature_bytes, transaction_data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    #     print('Signature is valid.')
    # except:
    #     print('Signature is not valid.')









    #     from webauthn import (
    #         generate_registration_options,
    #         verify_registration_response,
    #         options_to_json,
    #         base64url_to_bytes,
    #     )
    #     from webauthn.helpers.cose import COSEAlgorithmIdentifier
    #     from webauthn.helpers.structs import (
    #         AttestationConveyancePreference,
    #         AuthenticatorAttachment,
    #         AuthenticatorSelectionCriteria,
    #         PublicKeyCredentialDescriptor,
    #         ResidentKeyRequirement,
    #     )


    # # 1
    # # {'id': 'AZ3rpIpPFHA75irNXUDf4mbGo5oBJ4Lbm-haWsRNhyWGSANDmzxVfK0CHMa5IYtxTujPJMnidL2dO9eNWZmfGs4', 'rawId': 'AZ3rpIpPFHA75irNXUDf4mbGo5oBJ4Lbm-haWsRNhyWGSANDmzxVfK0CHMa5IYtxTujPJMnidL2dO9eNWZmfGs4', 'response': {'attestationObject': 'o2NmbXRkbm9uZWdhdHRTdG10oGhhdXRoRGF0YVjFSZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NFAAAAAAAAAAAAAAAAAAAAAAAAAAAAQQGd66SKTxRwO-YqzV1A3-JmxqOaASeC25voWlrETYclhkgDQ5s8VXytAhzGuSGLcU7ozyTJ4nS9nTvXjVmZnxrOpQECAyYgASFYIKijphsXKur5xaXF8QOpfU6IddY8KvqqZxcN35hSYMCCIlggeRbMkdLQi43wF9YIuC7ES3tB29xIgJGZO8H2QFJ-V_o', 'clientDataJSON': 'eyJ0eXBlIjoid2ViYXV0aG4uY3JlYXRlIiwiY2hhbGxlbmdlIjoiUGFDVkhOUlp1ZU9fTU1jdnlHcV82aXJ1NGdmSkZWU3BPdktwSGRGTGpXQURsakFHRG1FeC1OMnpQUGhHZ1VwUnpVR21tb3RPQ0Z5TkhqVVdCT2pNc2ciLCJvcmlnaW4iOiJodHRwOi8vbG9jYWxob3N0OjMwMDUiLCJjcm9zc09yaWdpbiI6ZmFsc2UsIm90aGVyX2tleXNfY2FuX2JlX2FkZGVkX2hlcmUiOiJkbyBub3QgY29tcGFyZSBjbGllbnREYXRhSlNPTiBhZ2FpbnN0IGEgdGVtcGxhdGUuIFNlZSBodHRwczovL2dvby5nbC95YWJQZXgifQ', 'transports': ['hybrid', 'internal'], 'publicKeyAlgorithm': -7, 'publicKey': 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEqKOmGxcq6vnFpcXxA6l9Toh11jwq-qpnFw3fmFJgwIJ5FsyR0tCLjfAX1gi4LsRLe0Hb3EiAkZk7wfZAUn5X-g', 'authenticatorData': 'SZYN5YgOjGh0NBcPZHZgW4_krrmihjLHmVzzuoMdl2NFAAAAAAAAAAAAAAAAAAAAAAAAAAAAQQGd66SKTxRwO-YqzV1A3-JmxqOaASeC25voWlrETYclhkgDQ5s8VXytAhzGuSGLcU7ozyTJ4nS9nTvXjVmZnxrOpQECAyYgASFYIKijphsXKur5xaXF8QOpfU6IddY8KvqqZxcN35hSYMCCIlggeRbMkdLQi43wF9YIuC7ES3tB29xIgJGZO8H2QFJ-V_o'}, 'type': 'public-key', 'clientExtensionResults': {}, 'authenticatorAttachment': 'cross-platform'}
        
    #     registration_verification = verify_registration_response(
    #         # Demonstrating the ability to handle a plain dict version of the WebAuthn response
    #         credential=received_json,
    #         # expected_challenge=base64url_to_bytes(
    #         #     "CeTWogmg0cchuiYuFrv8DXXdMZSIQRVZJOga_xayVVEcBj0Cw3y73yhD4FkGSe-RrP6hPJJAIm3LVien4hXELg"
    #         # ),
    #         # expected_origin="http://localhost:5000",
    #         # expected_rp_id="localhost",
    #         # require_user_verification=True,
    #     )

    #     print("\n[Registration Verification - None]")
    #     print(registration_verification)
    #     # assert registration_verification.credential_id == base64url_to_bytes(
    #     #     "ZoIKP1JQvKdrYj1bTUPJ2eTUsbLeFkv-X5xJQNr4k6s"
    #     # )
    #     return JsonResponse(json.loads(registration_verification))


def register_view(request):
    print('register view')
    print(request.user.is_authenticated)
    style = request.GET.get('style', 'index')
    title = "Sign Up"
    cards = 'register'

    print()
    print(request)
    # from webauthn import (
    #     generate_registration_options,
    #     verify_registration_response,
    #     options_to_json,
    #     base64url_to_bytes,
    # )
    # from webauthn.helpers.cose import COSEAlgorithmIdentifier
    # from webauthn.helpers.structs import (
    #     AttestationConveyancePreference,
    #     AuthenticatorAttachment,
    #     AuthenticatorSelectionCriteria,
    #     PublicKeyCredentialDescriptor,
    #     ResidentKeyRequirement,
    # )

    # simple_registration_options = generate_registration_options(
    #     rp_id="sovote.org",
    #     rp_name="SoVote",
    #     user_name="bob",
    # )

    # print(options_to_json(simple_registration_options))










    user_id = uuid.uuid4().hex
    dt = datetime.datetime.now()
    salt = os.urandom(16)
    user_obj = User(id=user_id, created=dt)
    # options_obj = UserOptions(id=uuid.uuid4().hex, user=user_id, created=dt, salt=salt)
    userForm = UserRegisterForm(request.POST or None)
    # optionsForm = UserOptionsRegisterForm(request.POST or options_obj)

    # user = userForm.save(commit=False)
    # # options = optionsForm.save(commit=False)
    # # print(user)
    # #password = form.cleaned_data.get('password')
    # # import re
    # pattern = re.compile("[A-Za-z0-9+_-]+")
    # # email = optionsForm.cleaned_data.get('email')
    # password = userForm.cleaned_data.get('password')
    # password_confirm = userForm.cleaned_data.get('password_confirm')
    # if userForm.is_valid():
    #     if not pattern.fullmatch(user.username):
    #         userForm.add_error('username', 'Only A-Z, 0-9, +, _, or - allowed')
    #     elif email == None:
    #         # print(form.errors)
    #         userForm.add_error('email', 'Please enter an email address')
        
    #     elif '@' not in email:
    #         # raise forms.ValidationError("Passwords must match")
    #         # print(form.errors)
    #         userForm.add_error('email', 'Please enter a valid email address')
    #     elif password != password_confirm:
    #         # raise forms.ValidationError("Passwords must match")
    #         # print(form.errors)
    #         userForm.add_error('password', 'Passwords must match')
    #     else:
    #         # print('else')
    #         try:
    #             user_name = UserOptions.objects.filter(display_name=user.username)[0]
    #             userForm.add_error('username', 'Username already taken')
    #         except:

                
    #             if userForm.signature and optionsForm.signature:
    #                 print('has sigs')
    #                 from blockchain.models import get_signature_data
    #                 # verfiy userForm
    #                 public_key = base64.b64decode(optionsForm['public_key'])
    #                 digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    #                 digest.update(str(get_signature_data(userForm)).encode('utf-8'))
    #                 hashed_transaction = digest.finalize()
    #                 try:
    #                     public_key.verify(userForm['signature'], hashed_transaction, ec.ECDSA(hashes.SHA256()))
    #                     userForm_is_valid = True
    #                 except Exception as e:
    #                     print(f"Signature verification failed: {str(e)}")
    #                     userForm_is_valid = False
    #                 # verify optionsForm
    #                 # public_key = base64.b64decode(optionsForm['public_key'])
    #                 digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    #                 # digest.update(str(get_signature_data(optionsForm)).encode('utf-8'))
    #                 hashed_transaction = digest.finalize()
    #                 # try:
    #                 #     public_key.verify(optionsForm['signature'], hashed_transaction, ec.ECDSA(hashes.SHA256()))
    #                 #     optionsForm_is_valid = True
    #                 # except Exception as e:
    #                 #     print(f"Signature verification failed: {str(e)}")
    #                 #     optionsForm_is_valid = False
                    
    #                 # if optionsForm_is_valid and userForm_is_valid:
    #                 #     # try: 
    #                 #     #     u = UserOptions.objects.filter(email=email)[0]
    #                 #     #     # print(form.errors)
    #                 #     #     userForm.add_error('email', 'Email is already in use')
    #                 #     # except Exception as e:`
    #                 #     # print(str(e))
    #                 #     # try:
    #                 #     #     userToken = request.COOKIES['userToken']
    #                 #     # except:
    #                 #     #     userToken = None
    #                 #     # if userToken:
    #                 #     #     try:
    #                 #     #         anon_user = User.objects.filter(userToken=userToken, anon=True)[0]
    #                 #     #         anon_user.anon = False
    #                 #     #         anon_user.username = user.username
    #                 #     #         anon_user.email = user.email
    #                 #     #         user = anon_user
    #                 #     #     except:
    #                 #     #         pass
    #                 #     user.set_password(password)
    #                 #     user.save()
    #                 #     # return JsonResponse(user.__dict__)
    #                 #     # options = UserOptions(user=user, display_name=user.username, email=email)
    #                 #     # options.save()
    #                 #     new_user = authenticate(username=user.username, password=password)
    #                 #     login(request, new_user)
    #                 #     # print('1111')
    #                 #     # if not options.userToken:
    #                 #     #     options.userToken = uuid4()
    #                 #     #     options.save()
    #                 #     # return 
    #                 #     # print(user.token)
    #                 #     # try:
    #                 #     #     u = User.objects.filter(username='Sozed')[0]
    #                 #     #     u.alert('New registered user', None, user.username)
    #                 #     #     # print('alert sent')
    #                 #     # except Exception as e:
    #                 #     #     print(str(e))
    #                 #     #     u = User.objects.filter(username='Sozed')[0]
    #                 #     #     u.alert('new user alert fail', None, str(e))
    #                 #     return redirect("/home")
    # else:
    #     print(userForm.errors)
    options = {'Login': '/login'}
    context = {
        'title': title,
        'cards': cards,
        "userForm": userForm,
        # "optionsForm": optionsForm,
        # 'view': view,
        'nav_bar': list(options.items()),
        'user_dict': get_signing_data(user_obj),
        # 'userOptions_dict': get_signature_data(options_obj),
        # 'feed_list':setlist,
        # 'topicList': topicList,
    }
    return render_view(request, context)

# not used
def login_options_view(request):
    from webauthn import (
        generate_authentication_options,
        verify_authentication_response,
        options_to_json,
        base64url_to_bytes,
    )
    from webauthn.helpers.structs import (
        PublicKeyCredentialDescriptor,
        UserVerificationRequirement,
    )

    # Simple Options
    simple_authentication_options = generate_authentication_options(rp_id="localhost")

    print("\n[Authentication Options - Simple]")
    print(options_to_json(simple_authentication_options))

    # # Complex Options
    # complex_authentication_options = generate_authentication_options(
    #     rp_id="localhost",
    #     challenge=b"1234567890",
    #     timeout=12000,
    #     allow_credentials=[PublicKeyCredentialDescriptor(id=b"1234567890")],
    #     user_verification=UserVerificationRequirement.REQUIRED,
    # )

    # print("\n[Authentication Options - Complex]")
    # print(options_to_json(complex_authentication_options))

    return JsonResponse(json.loads(options_to_json(simple_authentication_options)))

@csrf_exempt
def get_user_login_request_view(request):
    print('get_user')
    # for u in UserPubKey.objects.all():
    #     super(UserPubKey, u).delete()
    # for u in User.objects.all():
    #     u.delete()
    # for w in Wallet.objects.all():
    #     w.delete()
    # print('all deleted')
    # print(User.objects.all())
    # u = UserPubKey.objects.all()[0]
    # from accounts.models import sign
    from blockchain.models import get_signing_data, get_operatorData
    # data = get_operatorData()
    # # print(data)
    # # user = User.objects.filter()
    # print('privkey', data['privKey'])
    # sig = sign(data['privKey'], get_signing_data(u))
    # print('sig',sig)
    # print()
    # get_signing_data(u)
    if request.method == 'POST':
        received_json = request.POST
        print(received_json.get('display_name'))
        try:
            user = User.objects.filter(display_name=received_json.get('display_name'))[0]
            print(user.display_name)
            print('return 1')
            # include sig and pubkey for user to locally verify data
            userData = get_signing_data(user)
            # user_json = json.loads(userData)
            # user_json['signature'] = user.signature
            # user_json['publicKey'] = user.publicKey
            # userData = json.dumps(user_json, separators=(',', ':'))
            try:
                sonet = get_signing_data(Sonet.objects.first())
            except:
                sonet = None
            print('return sign data', userData)
            return JsonResponse({'message' : 'User found', 'userData' : userData, 'sonet' : sonet})
        except:
            user_id = uuid.uuid4().hex
            wallet_id = uuid.uuid4().hex
            upk_id = uuid.uuid4().hex
            dt = now_utc()
            display_name = received_json.get('display_name')
            print('new display_name',display_name)
            user = User(id=user_id, username=user_id, display_name=display_name, created=dt, last_updated=dt)
            
            wallet_obj = Wallet(id=wallet_id, User_obj_id=user_id, pointerId=user_id, created=dt)
            upk_obj = UserPubKey(id=upk_id, User_obj_id=user_id, created=dt)
            extra_data = {'User_obj':user_id}
            print('user set up', user.__dict__)
            try:
                sonet = get_signing_data(Sonet.objects.first())
            except:
                sonet = None
            # print('extra_data',extra_data)
            print('return 2')
            return JsonResponse({'message' : 'User not found', 'userData' : get_signing_data(user), 'walletData' : get_signing_data(wallet_obj, extra_data=extra_data), 'upkData' : get_signing_data(upk_obj, extra_data=extra_data), 'sonet' : sonet})

@csrf_exempt
def receive_user_login_view(request):
    print('receive_user22')
    if request.method == 'POST':
        print()
        userData = json.loads(request.POST.get('userData'))
        # print(received_json)
        # newPrivateKey = request.POST.get('new_private_key')
        publicKey = request.POST.get('publicKey')
        registeredPublicKey = request.POST.get('registered_public_key')
        # transaction_data = request.POST.get('transactionData')
        publicKey = userData['publicKey']
        signature = userData['signature']
        # transaction_data = "Your transaction data here"
        # print()
        # print('userData', userData)
        print()
        print('pubkey', publicKey)
        print()
        # print('registeredPublicKey', registeredPublicKey)
        # print()
        # tester = User.objects.filter()
        print('sig', signature)
        try:
            user = User.objects.filter(id=userData['id'])[0]
            print('user found', user)
            # print('usg', user.signature)
            if user.must_rename:
                if User.objects.filter(display_name=userData['display_name']).exclude(id=userData['id']).count() > 0:
                    return JsonResponse({'message' : 'Username taken'})
            #     else:
            #         x = get_signing_data(userData)
            # else:
            x = get_signing_data(userData)
            print()
            print(x)
            print()
            # user.delete()
            # for i in UserPubKey.objects.all():
            #     print(i.publicKey)
            #     print(i.User_obj.display_name)
            # print('--')
            try:
                upk = UserPubKey.objects.filter(User_obj=user, publicKey=publicKey)[0]
                print(upk)
                # print(signature)
                # print(x)
                is_valid = upk.verify(x, signature)
                # print('is_valid', is_valid)
                if is_valid:
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    print('user logged in')
                    response = JsonResponse({'message' : 'Valid Username and Password', 'userData' : x})
                    # response.set_cookie(key='userData', value=json.dumps(x), expires=datetime.datetime.today()+datetime.timedelta(days=3650))
                    return response
                else:
                    return JsonResponse({'message' : 'Verification failed'})
            except Exception as e:
                print(str(e))
                return JsonResponse({'message' : 'Invalid Password'})
        except Exception as e:
            print(str(e))
            try:
                print('1')
                walletData = json.loads(request.POST.get('walletData'))
                print('walletData',walletData)
                walletSignature = walletData['signature']
                print('walletSignature',walletSignature)
                upkData = json.loads(request.POST.get('upkData'))
                print('upkData',upkData)
                upkSignature = upkData['signature']
                print('upkSignature',upkSignature)


                print('Intial userData',userData)
                # user and upk must exist before attempts to verify signature
                user = User()
                fields = user._meta.fields
                # print(userData)
                print()
                for key, value in userData.items():
                    if value != 'None':
                        # print(key, value)
                        if '_array2' in str(key):
                            print('TARGET',key, ast.literal_eval(value))
                            setattr(user, key, ast.literal_eval(value))
                        else:
                            setattr(user, key, value)
                print('save')
                user.slug = 'tmp'
                user.save(share=False)
                # print('new user', user)
                wallet = Wallet()
                fields = wallet._meta.fields
                # print(userData)
                for key, value in walletData.items():
                    if value != 'None':
                        if str(key) == 'User_obj':
                            setattr(wallet, 'User_obj_id', value)
                        else:
                            setattr(wallet, key, value)
                # print('save')
                wallet.save(share=False)
                # print()
                # print('create 111')
                upk = UserPubKey()
                fields = upk._meta.fields
                # print(userData)
                for key, value in upkData.items():
                    if value != 'None':
                        # print(key,value)
                        if str(key) == 'User_obj':
                            setattr(upk, 'User_obj_id', value)
                        else:
                            setattr(upk, key, value)
                # print('save')
                upk.save(share=False)
                # print('create 222')
                # try:
                #     wallet = Wallet.objects.filter(pointerId=user.id)[0]
                # except:
                #     wallet = Wallet(pointerId=user.id)
                #     wallet.save()
                # upk = add_or_verify_pubkey(user, registeredPublicKey, newPublicKey, signature)
                # print(upk)
                # x = 
                # print(x)
                # is_valid = False
                proceed_to_login = False
                is_valid = upk.verify(get_signing_data(upkData), upkSignature)
                if is_valid:
                    is_valid = upk.verify(get_signing_data(userData), signature)
                    if is_valid:
                        is_valid = upk.verify(get_signing_data(walletData), walletSignature)
                        if is_valid:
                            try:
                                # print('try')
                                user = get_or_create_model(userData['object_type'], id=userData['id'])
                                # upk.User_obj = user
                                user, good = sync_and_share_object(user, userData)
                                # print('done user22',user)
                                user.slug = user.slugger()
                                user.save()
                                print('user-good',good)
                                # print('new user data', get_signing_data(user))
                                print()
                                upk = get_or_create_model(upkData['object_type'], id=upkData['id'])
                                # upk.User_obj = user
                                upk, good = sync_and_share_object(upk, upkData)
                                print('upk-good',good)

                                wallet = get_or_create_model(walletData['object_type'], id=walletData['id'])
                                # wallet.User_obj = user
                                wallet, good = sync_and_share_object(wallet, walletData)
                                print('wallet-good',good)
                                proceed_to_login = True
                            except Exception as e:
                                print(str(e))

                        new_user_valid = upk.verify(get_signing_data(user), signature)
                        print('new_user_valid',new_user_valid)
                        # print()
                        # print('signingdata',get_signing_data(userData))
                        # print()
                        # print('signinguser', get_signing_data(user))
                # print('is valid', is_valid)
                if proceed_to_login:
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    print('user logged in')
                    try:
                        sonet = get_signing_data(Sonet.objects.all()[0])
                    except:
                        sonet = get_signing_data(Sonet())
                    return JsonResponse({'message' : 'User Created', 'userData' : get_signing_data(user), 'sonet' : sonet})
                else:
                    try:
                        user.delete()
                    except:
                        pass
                    try:
                        upk.delete()
                    except:
                        pass
                    try:
                        wallet.delete()
                    except:
                        pass
                    return JsonResponse({'message' : 'There was a problem creating this user'})
            except Exception as e:
                print('fail94578', str(e))
                try:
                    user.delete()
                except:
                    pass
                try:
                    upk.delete()
                except:
                    pass
                try:
                    wallet.delete()
                except:
                    pass

                return JsonResponse({'message' : 'There was a problem creating this user'})
        # import ecdsa
        # import hashlib

        # # Transaction data

        # # Load the private key
        # # private_key_hex = 'a666e350e85efafa3477ad95ab407cad2069665973ffa9f2eccdee35d954c957'
        # # private_key_bytes = bytes.fromhex(privateKey)
        # # print(private_key_bytes)
        # # sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
        # # # print('sk', sk)
        # # signature = sk.sign(transaction_data.encode('utf-8'), hashfunc=hashlib.sha256)
        # # signature_hex = signature.hex()
        # # print("Signature:", signature_hex)

        # print('next')

        # data = transaction_data

        # from cryptography.hazmat.primitives.asymmetric import ec
        # from cryptography.hazmat.primitives import hashes
        # from cryptography.exceptions import InvalidSignature

        # private_key_bytes = bytes.fromhex(privateKey)
        # private_key = ec.derive_private_key(int.from_bytes(private_key_bytes, byteorder='big'), ec.SECP256K1())

        # signature = private_key.sign(data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
        # signature_hex = signature.hex()

        # print("Signature:", signature_hex)
        # print('next')


        # signature_bytes = bytes.fromhex(signature_hex)
        # print(signature_bytes.hex())
        # public_key_bytes = bytes.fromhex(publicKey)
        # public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
        # print('pubkey loaded', publicKey)
        # try:
        #     public_key.verify(signature_bytes, data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
        #     print("Signature is valid YAY IT WORKED!!!.")
        # except InvalidSignature:
        #     print("Invalid signature.")
        # except Exception as e:
        #     print(str(e))
    return JsonResponse({'message' : 'success'})


# not currently used
def login_verify_view(request):
    print('login verify')
    import hashlib

    # from webauthn import (
    #     generate_authentication_options,
    #     verify_authentication_response,
    #     options_to_json,
    #     base64url_to_bytes,
    # )
    # from webauthn.helpers.structs import (
    #     PublicKeyCredentialDescriptor,
    #     UserVerificationRequirement,
    # )
    # received_json = json.loads(request.POST['content'])
    # print(received_json)
    # # Authentication Response Verification
    # authentication_verification = verify_authentication_response(
    #     # Demonstrating the ability to handle a stringified JSON version of the WebAuthn response
    #     credential=received_json,
    #     expected_challenge=base64url_to_bytes(
    #         "iPmAi1Pp1XL6oAgq3PWZtZPnZa1zFUDoGbaQ0_KvVG1lF2s3Rt_3o4uSzccy0tmcTIpTTT4BU1T-I4maavndjQ"
    #     ),
    #     expected_rp_id="localhost",
    #     expected_origin="http://localhost:5000",
    #     # credential_public_key=base64url_to_bytes(
    #     #     "pAEDAzkBACBZAQDfV20epzvQP-HtcdDpX-cGzdOxy73WQEvsU7Dnr9UWJophEfpngouvgnRLXaEUn_d8HGkp_HIx8rrpkx4BVs6X_B6ZjhLlezjIdJbLbVeb92BaEsmNn1HW2N9Xj2QM8cH-yx28_vCjf82ahQ9gyAr552Bn96G22n8jqFRQKdVpO-f-bvpvaP3IQ9F5LCX7CUaxptgbog1SFO6FI6ob5SlVVB00lVXsaYg8cIDZxCkkENkGiFPgwEaZ7995SCbiyCpUJbMqToLMgojPkAhWeyktu7TlK6UBWdJMHc3FPAIs0lH_2_2hKS-mGI1uZAFVAfW1X-mzKL0czUm2P1UlUox7IUMBAAE"
    #     # ),
    #     credential_current_sign_count=0,
    #     require_user_verification=True,
    # )
    # print("\n[Authentication Verification]")
    # print(authentication_verification)
    # assert authentication_verification.new_sign_count == 1
    # # return JsonResponse(json.loads(options_to_json(authentication_verification)))

    print()
    import base64
    # print(request.POST)
    print('1')
    # elem = base64.b64decode(request.POST)
    # print(request.body.decode())
    # print(elem)
    received_json = request.POST
    print(received_json)
    # for i in received_json:
    #     print(i)
    #     print(received_json[i])
    print()
    print(received_json['publicKeyHex'])
    print()
    print('td', str(received_json['transactionData']))
    print()
    # print('privKey received',received_json['privateKey'])
    print()
    print(str(received_json['signature']))
    # print()
    # print(received_json['r'])
    # print()
    # print(received_json['s'])
    # from ethereum.utils import ecrecover, pub_to_address, to_buffer, to_checksum_address, from_rpc_sig
    from ecdsa import SECP256k1, VerifyingKey, BadSignatureError, util

    # signed_tx_data = request.POST.get('signedData')
    # print(signed_tx_data)
    # privateKey = request.POST.get('privateKey')
    publicKey = request.POST.get('publicKeyHex')
    transaction_data = request.POST.get('transactionData')
    signature = request.POST.get('signature')
    # r = request.POST.get('r')
    # s = request.POST.get('s')
    # signature = ['48', '68', '2', '32', '75', '213', '151', '71', '233', '42', '173', '36', '183', '158', '166', '10', '106', '120', '212', '39', '50', '167', '38', '155', '126', '181', '25', '253', '206', '34', '83', '133', '14', '214', '31', '255', '2', '32', '34', '43', '162', '192', '13', '128', '84', '45', '29', '73', '173', '198', '201', '81', '84', '42', '206', '249', '189', '189', '198', '13', '167', '13', '144', '63', '177', '244', '12', '6', '101', '139']
    # signature = ''.join(signature)
    # print(signature)
    print()


    from ecdsa import SECP256k1, VerifyingKey

    # Received signature and public key from JavaScript
    signature_hex = signature
    public_key_hex = publicKey

    # # Decode public key
    # public_key = VerifyingKey.from_string(bytes.fromhex(publicKey), curve=SECP256k1)

    # # Prepare data (replace with the same data used in JavaScript)
    data = "Transaction data"
    # # hash = bytes.fromhex(require('crypto').createHash('sha256').update(data).digest('hex'))
    message = b"testmessage"
    print(message)
    # sig = r+s
    # # Verification
    # try:
    #     if public_key.verify(bytes.fromhex(sig), message):
    #         print("Signature is valid!")
    #     else:
    #         print("Signature is invalid!")
    # except Exception as e:
    #     print(str(e)) 
    #     print("Verification failed!")
    # public_key_hex = '04f8ccf508990ceef9e5b84f5aeb9fee1739d3d3b140fc05e5b2ff58524c660ba27f654ed36fe7dd9923a1ffaf5caa774c2e9fd18ffb486432f44914c22c29eccf'
    # signature_hex = '3044022010f92d4771aac187375265167f43854d510428a131124df798b406a5dcc7eab5022029bbadf9aa6b4741d7fed01999121fe34ad8b2216f7200d953904bbd271d84e0'

    # # Parse the public key
    # vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)

    # # Parse the signature
    # r, s = int(signature_hex[:64], 16), int(signature_hex[64:], 16)
    # print(r)
    # print(s)
    # # Verify the signature
    # if vk.verify(bytes.fromhex(signature_hex), message, hashfunc=hashlib.sha256, sigdecode="raw"):
    #     print("Signature is valid!")
    # else:
    #     print("Signature is invalid!")
    

    # from ecdsa import SECP256k1, VerifyingKey

    # vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
    # print(vk.verify(bytes.fromhex(signature), message))
    # import binascii                         #you'll need this module for this one
    # ecdh = ec.keyFromSecret(password)       #//password is your seed phrase here
    # hex_string = binascii.unhexlify(signature);  #//signature should be hexadecimal string containing r value, s value and recovery id
    # binint = int.from_bytes(hex_string, 'big')   #this will convert the byte string into a big integer object


    # ecdh = ec.keyFromSecret(password)   #password is your seed phrase here
    # verified = ecdh.verify(binint, message);    
    # # //data can be a string or number and signature is hexadecimal string containing r value, s value and recovery id


    # # Replace with the retrieved signature (in bytes)
    # signature_bytes = str.encode(signature)

    # # Replace with the retrieved public key (in DER format)
    # public_key_der = str.encode(publicKey)

    # # Decode the public key from DER format
    # # curve = ecdsa.curves.SECP256k1  # Assuming secp256k1 curve
    # # public_key = curve.decode_point(public_key_der)



    # from asn1crypto import DER

    # # Replace with the retrieved public key in DER format
    # # public_key_der = b"your_public_key_in_der_format"

    # # Decode the DER-encoded public key
    # decoded_data = DER().decode(public_key_der)

    # # Extract the X and Y coordinates (assuming uncompressed format)
    # x = decoded_data[1].as_integer()
    # y = decoded_data[2].as_integer()

    # # Create a public key object suitable for ecdsa
    # curve = ecdsa.curves.SECP256k1  # Assuming secp256k1 curve
    # public_key = ecdsa.Public_key(curve, x, y)

    # # ... (Rest of the verification code using the public_key object)




    # Hash the message (ensure it matches the hashing algorithm used in JavaScript)
    message = b"testmessage"  # Replace with the actual message
    hash_func = hashlib.sha256  # Assuming SHA-256 was used
    message_hash = hash_func(message).digest()

    # # Verify the signature
    # try:
    #     ecdsa.VerifyingKey.from_public_point(public_key, curve=curve).verify(signature_bytes, message)
    #     print("Signature is valid")
    # except ecdsa.BadSignatureError:
    #     print("Signature is invalid")
    # except Exception as e:
    #     print(str(e))






    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
    from cryptography.hazmat.primitives.serialization import load_der_public_key
    from cryptography.hazmat.primitives import hashes
    from cryptography.exceptions import InvalidSignature
    import base64
    import json



    # Uncompressed public key (hexadecimal string)
    # uncompressed_public_key_hex = "04f8ccf508990ceef9e5b84f5aeb9fee1739d3d3b140fc05e5b2ff58524c660ba27f654ed36fe7dd9923a1ffaf5caa774c2e9fd18ffb486432f44914c22c29eccf"

    # Decode the uncompressed public key from hexadecimal
    # uncompressed_public_key_bytes = bytes.fromhex(publicKey)

    # # Load the DER-encoded public key
    # publicKey = serialization.load_der_public_key(uncompressed_public_key_bytes, backend=default_backend())

    # Construct an EllipticCurvePublicKey object directly
    # public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), uncompressed_public_key_bytes)

    # der_public_key = bytes.fromhex('04f8ccf508990ceef9e5b84f5aeb9fee1739d3d3b140fc05e5b2ff58524c660ba27f654ed36fe7dd9923a1ffaf5caa774c2e9fd18ffb486432f44914c22c29eccf')
    # publicKey = base64.b64decode('027b83ad6afb1209f3c82ebeb08c0c5fa9bf6724548506f2fb4f991e2287a77090')
    # publicKey = base64.b64decode('''MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+6gvHdCUCjnc4hSMwbdIIspk469pVAzjjb8tDJsCH/QpiK9vXe4nDZ7p9kiw2ACw0fkWaPnApKBwXNB9Nd9Sf+XFtcIzdqKKBcAqZZCu2pA729amNRug9DoZdkstaBG+VfTxXhdzQRSTxxqJQWgdV8ejKkt4D1M6pAiTkAyD0eQIDAQAB''')
    # data = {
    # "data_1":"The quick brown fox",
    # "data_2":"jumps over the lazy dog"
    # }
    # data = "jumps over the lazy dog1111"
    # print('d', data)
    print('td', transaction_data)
    data = transaction_data


    
    # signature = base64.b64decode(signature)

    # (r, s) = decode_dss_signature(signature)
    # print(r)
    # print(s)
    # signatureP1363 = r.to_bytes(32, byteorder='big') + s.to_bytes(32, byteorder='big')
    # print(base64.b64encode(signatureP1363).decode('utf-8'))

    # publicKey = load_der_public_key(der_public_key, default_backend())
    signature_bytes = bytes.fromhex(signature)
    print(signature_bytes.hex())
    public_key_bytes = bytes.fromhex(publicKey)
    public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
    print('pubkey loaded', publicKey)
    # data = "testmessage"
    try:
        public_key.verify(signature_bytes, data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
        print("Signature is valid YAY IT WORKED!!!.")
    except InvalidSignature:
        print("Invalid signature.")
    except Exception as e:
        print(str(e))
    

    # r = int.from_bytes(r.encode('utf-8'), byteorder='big')
    # s = int.from_bytes(s.encode('utf-8'), byteorder='big')
    # print(r)
    # print(s)

    # try:
    #     publicKey.verify(
    #         encode_dss_signature(r, s),
    #         json.dumps(data, separators=(',', ':')).encode('utf-8'),
    #         ec.ECDSA(hashes.SHA256())    
    #     )
    #     print("verification succeeded")
    # except InvalidSignature:
    #     print("verification failed")
    # except Exception as e:
    #     print(str(e))



# not used
def login_view(request):
    if request.user.is_authenticated:
        return redirect("/home")
    style = request.GET.get('style', 'index')
    title = "Login"
    cards = 'login'
    form = UserLoginForm(request.POST or None)
    # print(form)
    if form.is_valid():
        # print('isvalid')
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get('password')
        # print(username)
        user = authenticate(username=username, password=password)
        # print(user)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        # print('logged in')
        try:
            userToken = request.COOKIES['userToken']
        except:
            userToken = None
        if userToken and userToken != user.userToken:
            try:
                anon_user = User.objects.filter(userToken=userToken, anon=True)[0]
                reactions = Reaction.objects.filter(user=anon_user)
                for r in reactions:
                    r.user = user
                    r.save()
                if anon_user.keywords:
                    if not user.keywords:
                        user.keywords = []
                    for k in anon_user.keywords:
                        user.keywords.append(k)
                    user.save()
                # anon_user.delete()
            except:
                pass
        if not user.userToken:
            rand_token = uuid4()
            user.userToken = rand_token
            user.save()
        # print(user.token)
        try:    
            fcmDeviceId = request.COOKIES['fcmDeviceId']
            # print(fcmDeviceId)
            devices = FCMDevice.objects.filter(user=request.user, registration_id=fcmDeviceId)
            for d in devices:
                d.send_message(Message(data={"signin" : "True", 'token' : user.appToken}))
            return redirect("/home?appToken=%s&fcmDeviceId=%s" %(user.appToken, fcmDeviceId))
        except Exception as e:
            print(str(e))
            
            # if next:
            #     return redirect(next)
            return redirect("/home")
    else:
        print(form.errors)
    options = {'Sign Up': '/signup'}
    context = {
        'title': title,
        'cards': cards,
        "form": form,
        # 'view': view,
        'nav_bar': list(options.items()),
        # 'feed_list':setlist,
        # 'topicList': topicList,
    }
    return render_view(request, context)


def logout_view(request):
    # print('logout')
    # print(request.user)
    try:    
        fcmDeviceId = request.COOKIES['fcmDeviceId']
        print(fcmDeviceId)
        devices = FCMDevice.objects.filter(user=request.user, registration_id=fcmDeviceId)
        for d in devices:
            # d.send_message(Message(notification=Notification(title=request.user.username, body="body")))
            d.send_message(Message(data={"logout" : "True"}))
            d.active = False
            d.save()
    except Exception as e:
        print(str(e))
    # try:
    #     userToken = request.COOKIES['userToken']
    # except Exception as e:
    #     userToken = None
    logout(request)
    context = {
        "user": None,

    }
    response = render(request, "index.html", context)
    # response = redirect("/")
    response.set_cookie(key='appToken', value=None)
    response.set_cookie(key='userData', value=None)
    # response.set_cookie(key='userToken', value=userToken)
    return response

def get_index_view(request):
    print('get index view')
    if request.user.is_authenticated:
        user = request.user
    else:
        user = None
    context = {
        "user": user,
    }
    return render(request, "index.html", context)

def get_country_modal_view(request):
    print('country modal view')
    user_data, user = get_user_data(request)
    if not user:
        user_id = uuid.uuid4().hex
        dt = datetime.datetime.now()
        user_obj = User(id=user_id, created=dt)
        context = {
            'title': 'Login/Signup',
            'user_dict': get_signing_data(user_obj),
        }
        return render(request, "forms/login-signup.html", context)
    else:
        return render(request, "forms/region_modal1.html")

def get_region_modal_view(request, country):
    print('region modal view')
    return render(request, "forms/region_modal2.html", {'country': country})

def run_region_modal_view(request):
    print('run region modal')
    if request.method == 'POST':
        u = request.user
        # do not save data to user profile, must be sent to user for signature then returned
        # u = User()
        # fields = user._meta.fields
        # for f in fields:
        #     setattr(u, f.name, getattr(user, f.name))
        # received_json = request.POST
        # print(received_json)
        # newPrivateKey = request.POST.get('new_private_key')
        address = request.POST.get('address')
        country = request.POST.get('country')
        # regionSetDate = request.POST.get('regionSetDate')
        # signature = request.POST.get('setDateSig')
        # user_id = request.POST.get('userId')
        # print('user_id', user_id)
        # print('sig', signature)
        # try:
        #     user = User.objects.filter(id=user_id)[0]
        #     print(user)
        #     pubKeys = UserPubKey.objects.filter(User=user)
        #     print(pubKeys)
        #     for pubKey in pubKeys:
        #         print(pubKey.publicKey)
        #         is_valid = pubKey.verify(signature, regionSetDate)
        #         if is_valid:
        #             break
        # except Exception as e:
        #     print(str(e))
        #     is_valid = False
        print('start hree')
        if country == 'canada':
            try:
                from scrapers.canada.federal import get_user_region
                if len(address) <= 7:
                    print('1')
                    address = address.upper().replace(' ', '')
                    # u.postal_code = address
                    # u = u.clear_region()
                    url = 'https://represent.opennorth.ca/postcodes/%s/' %(address)
                    # print('get user data')
                    result = get_user_region(u, url)
                    # u.region_set_date = datetime.datetime.now()
                else:
                    print('2')
                    url = 'http://dev.virtualearth.net/REST/v1/Locations/CA/%s?output=xml&key=AvYxl5kFcs1G1CKjpXM8atABzd_8Wb8shd8OJ2cG3-MtQjOa6Bg7rIOthHLGbDgA' %(address)
                    r = requests.get(url)
                    soup = BeautifulSoup(r.content, 'lxml')
                    latitude = soup.find('latitude').text
                    longitude = soup.find('longitude').text
                    url = 'https://represent.opennorth.ca/boundaries/?contains=%s,%s' %(latitude, longitude)
                    print(url)
                    # u = u.clear_region()
                    result1 = get_user_region(u, url)
                    url = 'https://represent.opennorth.ca/representatives/?point=%s,%s' %(latitude, longitude)
                    print(url)
                    # print('----------------------------------------------------')
                    result2 = get_user_region(u, url)
                    result = {**result1, **result2}
                    # result = {**result1, **result2}
                    # u.address = address
                    # u.region_set_date = datetime.datetime.now()
                # if is_valid:
                #     # Mon, 12 Sep 2022 18:15:18 GMT
                #     setDate = datetime.datetime.strptime(regionSetDate, '%a, %d %b %Y %H:%M:%S %Z')
                #     # user.region_set_date = setDate
                #     # user.save()
                #     result['regionSetDate'] = setDate
                # print(u.__dict__)
                # print()
                # u.last_updated = datetime.datetime.now()
                x = get_user_sending_data(u)
                # print()
                print('check here 1')
                print(x)
                # print()
                # dump = json.dump(x)
                # print(dump)
                return JsonResponse({'message': 'success', "userData": x, 'result':result})
            except Exception as e:
                print(str(e))
                return JsonResponse({'message' : 'Failed to set region'})

@csrf_exempt
def set_user_data_view(request):
    print('set user data view')
    if request.method == 'POST':
        # received_json = request.POST
        # print(received_json)
        # print()
        userData = request.POST.get('userData')
        print('received', userData)
        print()
        # print('siging_data', str(get_signing_data(userData)))
        print()
        # print('siging_local', str(get_signing_data(request.user)))
        # userData = json.load(x)
        
        user = request.user
        # data is verified during sync
        user, synced = sync_and_share_object(user, userData)
        print('synced',synced)
        if synced:
            return JsonResponse({'message':'success'})
        else:
            return JsonResponse({'message':'Failed to sync'})
    return JsonResponse({'message':'Failed verification'})

def redirect_to_social_auth_view(request):
    fcmDeviceId = request.GET.get('fcmDeviceId', '')
    if fcmDeviceId:
        response = redirect("/accounts/google/login")
        print('writing cookie')
        response.set_cookie(key='fcmDeviceId', value=fcmDeviceId, expires=datetime.datetime.today()+datetime.timedelta(days=3650))
        # response.set_cookie(key='sotoken', value=token)
        return response
    else:
        return redirect("/accounts/google/login")

def redirect_from_social_auth_view(request):
    # try:
    #     u = User.objects.filter(socialAuth=request.user)[0]
    # except:
    #     from random_username.generate import generate_username
    #     rand_username = generate_username(1)[0] 
    #     u = User(socialAuth=request.user, username=rand_username)
    #     u.set_password(uuid4())
    #     u.slugger()
    #     u.save()
    # user = authenticate(username=u.username, password=u.password)
    # login(request, user)
    user = request.user
    if not user.slug:
        user.slugger()
        user.save()
    try:
        userToken = request.COOKIES['userToken']
    except:
        userToken = None
    if userToken and userToken != user.userToken:
        try:
            anon_user = User.objects.filter(userToken=userToken, anon=True)[0]
            reactions = Reaction.objects.filter(user=anon_user)
            for r in reactions:
                r.user = user
                r.save()
            if anon_user.keywords:
                if not user.keywords:
                    user.keywords = []
                for k in anon_user.keywords:
                    user.keywords.append(k)
                user.save()
            # anon_user.delete()
        except:
            pass
    if not user.userToken:
        rand_token = uuid4()
        user.userToken = rand_token
        user.save()
    try:
        u = User.objects.filter(username='d704bb87a7444b0ab304fd1566ee7aba')[0]
        u.alert('New registered user', None, user.username)
    except:
        pass
    try:    
        fcmDeviceId = request.COOKIES['fcmDeviceId']
        if fcmDeviceId:
            print(fcmDeviceId)
            devices = FCMDevice.objects.filter(user=request.user, registration_id=fcmDeviceId)
            for d in devices:
                d.send_message(Message(data={"signin" : "True", 'token' : user.appToken}))
            return redirect("/home?appToken=%s&fcmDeviceId=%s" %(user.appToken, fcmDeviceId))
        else:
            return redirect("/home")
    except Exception as e:
        return redirect("/home")


def api_login_view(request):
    try:
        username = request.GET.get("name")
        user = User.objects.get(username=username)
        password = request.GET.get('pass')
        # print(username)
        user = authenticate(username=username, password=password)
        # print(user)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        # print('logged in')
        try:
            userToken = request.COOKIES['userToken']
        except:
            userToken = None
        if userToken and userToken != user.userToken:
            try:
                anon_user = User.objects.filter(userToken=userToken, anon=True)[0]
                reactions = Reaction.objects.filter(user=anon_user)
                for r in reactions:
                    r.user = user
                    r.save()
                # anon_user.delete()
            except:
                pass
        if not user.userToken:
            rand_token = uuid4()
            user.userToken = rand_token
            user.save()
        if not user.appToken:
            rand_token = uuid4()
            user.appToken = rand_token
            user.save()
        return render(request, "utils/dummy.html", {"result": user.appToken})
        
    except Exception as e:
        print(str(e))
        return render(request, "utils/dummy.html", {"result": 'Fail'})

def api_create_user_view(request):
    try:
        username = request.GET.get('name')
        password = request.GET.get('pass')
        email = request.GET.get('email')
        pattern = re.compile("[A-Za-z0-9_-]+")
        if not pattern.fullmatch(username):
            return render(request, "utils/dummy.html", {"result": 'Incorrect Characters'})
        else:
            try:
                user = User.objects.filter(username=username)[0]
                return render(request, "utils/dummy.html", {"result": 'Username Taken'})
            except:
                try:
                    user = User.objects.filter(email=email)[0]
                    return render(request, "utils/dummy.html", {"result": 'Email Taken'})
                except:
                    user = User(username=username)
                    user.email = email
                    try:
                        userToken = request.COOKIES['userToken']
                    except:
                        userToken = None
                    if userToken:
                        try:
                            anon_user = User.objects.filter(userToken=userToken, anon=True)[0]
                            anon_user.anon = False
                            anon_user.username = user.username
                            anon_user.email = user.email
                            user = anon_user
                        except:
                            pass
                    user.set_password(password)
                    user.slugger()
                    user.save()
                    user = authenticate(username=username, password=password)
                    login(request, user)
                    if not user.appToken:
                        from uuid import uuid4
                        rand_token = uuid4()
                        # print(rand_token)
                        user.appToken = rand_token
                        user.save()
                    return render(request, "utils/dummy.html", {"result": user.appToken})
    except Exception as e:
        print(str(e))
        return render(request, "utils/dummy.html", {"result": 'Fail'})

def user_view(request, username):
    print('profile')
    username = username.replace('|', '')
    print('username',username)
    u = User.objects.get(display_name=username)
    title = 'V/%s' %(str(u.display_name))
    print('title',title)
    cards = 'user_view'
    style = request.GET.get('style', 'index')
    # sort = request.GET.get('sort', 'alphabetical')
    page = request.GET.get('page', 1)
    view = request.GET.get('view', 'all')
    topicList = []
    options = {'Votes':'%s?view=Votes'%(u.get_absolute_url()), 'Cheers':'cheer','Statements':'%s?view=Statements'%(u.get_absolute_url()), 'Replies':'%s?view=Replies'%(u.get_absolute_url()),  'Polls':'%s?view=Polls'%(u.get_absolute_url()), 'Petitions':'%s?view=Petitions'%(u.get_absolute_url()), 'Saved': '%s?view=Saved'%(u.get_absolute_url()), 'Following': '%s?view=Following'%(u.get_absolute_url())}
    if style == 'index':
        context = {
            'title': title,
            'cards': cards,
            'view': view,
            'user': u,
            'nav_bar': list(options.items()),
        }
        return render_view(request, context)
    else:
        # roles = Role.objects.filter(position='Member of Parliament', end_date=None).select_related('person').order_by('person')
        if view == 'all':
            posts = Reaction.objects.filter(user=u).filter(Q(isYea=True)|Q(isNay=True)|Q(saved=True)).select_related('post').order_by('-updated')
        elif view == 'Votes':
            posts = Reaction.objects.filter(user=u).filter(Q(isYea=True)|Q(isNay=True)).exclude(isPreviousVote=True).select_related('post').order_by('-updated')
        elif view == 'nays': 
            posts = Reaction.objects.filter(user=u).filter(isNay=True).select_related('post').order_by('-updated')
        elif view == 'Saved':
            posts = Reaction.objects.filter(user=u).filter(saved=True).select_related('post').order_by('-updated')
        elif view == 'Following':
            getList = []
            for p in u.follow_person.all():
                # print(p)
                getList.append(p)
            for p in u.follow_bill.all():
                # print(p)
                getList.append(p.get_latest_version())
            for p in u.follow_committee.all():
                # print(p)
                getList.append(p)
            for p in u.get_follow_topics():
                # print(p)
                getList.append(p)
            posts = getList
            # print(getList)
            # tmp = Archive.objects.filter(keywords__icontains='Escorted temporary absence')
            # print(tmp.count())
            # posts = Post.objects.filter(keywords__overlap=getList).select_related('committeeMeeting', 'committeeItem','bill','hansardItem').order_by('-date_time')
            # print(posts.count())
            # posts = Post.objects.filter(Q(committeeMeeting__committee__in=committees)|Q(bill__in=bills)|Q(hansardItem__person__in=people)|Q(committeeItem__person__in=people)|Q(hansardItem__Terms__contains=topicList)|Q(committeeItem__Terms__contains=topicList)).order_by('-date_time')
            # print('posts')
        elif view == 'constituency':
            # print('con')
            if not u.riding:  
                response = redirect('/user/%s/set-constituency' %(str(u.username)))
                print(response)
                return response
        elif view == 'province':
            pass
        elif view == 'municipality':
            pass
        setlist = paginate(posts, page, request)
        # for i in setlist:
        #     print(i, i.id, i.postId, i.post)
        context = {
            'title': title,
            'cards': cards,
            'view': view,
            'user': u,
            'nav_bar': list(options.items()),
            'feed_list':setlist,
            'topicList': topicList,
        }
    return render_view(request, context)


def user_settings_view(request):
    # username = username.replace('|', '')
    # u = User.objects.get(display_name=username)
    u = request.user
    title = 'V|%s settings' %(str(u.display_name))
    cards = 'user_settings'
    style = request.GET.get('style', 'index')
    context = {
        'title': title,
        'cards': cards,
    }
    return render_view(request, context)

def officials_list(request, region):
    print('Mp list')
    cards = 'mp_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'alphabetical')
    page = request.GET.get('page', 1)
    search = request.POST.get('post_type')
    view = request.GET.get('view', 'Current')    
    searchform = SearchForm()
    # chamber = get_chamber(request)
    # province, region = get_region(request)
    # if not province:
    #     province_name = None
    # else:
    #     province_name = province.name

    # parl = Parliament.objects.filter(country='Canada', organization=province_name).first()
    # person = Person.objects.filter(gov_profile_page='https://www.ola.org/en/members/all/deepak-anand')[0]
    # MPP = Role.objects.filter(position='MPP', current=True, parliament=None, province_name=province_name)
    # print(MPP.count())
    # for p in MPP:
    #     p.parliament = parl
    #     p.save()

    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    govs = get_gov(country, gov_levels)
    print('gov', govs)
    gov = govs[0]
    filter = ''
    # if request.method == 'POST':
    #     subtitle = search
    #     view = None
    #     if chamber == 'All':
    #         title = "Government Officials"
    #         roles = Role.objects.filter(person__full_name__icontains=search).filter(Q(position='Member of Parliament')&Q(current=True)|Q(position='Senator')&Q(current=True)|Q(position='MPP')&Q(province_name=province.name)&Q(current=True)).filter(current=True).select_related('person').order_by('person')
    #     elif chamber == 'House':
    #         title = "Members of Parliament"
    #         roles = Role.objects.filter(person__full_name__icontains=search).filter(position='Member of Parliament', current=True).select_related('person').order_by('person')
    #     elif chamber == 'Senate':
    #         title = "Senators"
    #         roles = Role.objects.filter(person__full_name__icontains=search).filter(position='Senator', current=True).select_related('person').order_by('person')
    #     elif chamber == 'Assembly':
    #         title = "Members of Provincial Parliament"
    #         roles = Role.objects.filter(person__full_name__icontains=search).filter(position='MPP', current=True, province_name=province_name).select_related('person').order_by('person')
    # else:
    #     if chamber == 'All':
    #         roles = Role.objects.filter(Q(position='Member of Parliament')&Q(current=True)|Q(position='Senator')&Q(current=True)|Q(position='MPP')&Q(province_name=province_name)&Q(current=True)).filter(current=True).select_related('person').order_by('person')
    #         filter = 'all'
    #         title = "All Government Officials"
    #     elif chamber == 'House':
    #         roles = Role.objects.filter(position='Member of Parliament', current=True).select_related('person').order_by('person__last_name')
    #         filter = 'House'
    #         title = "All Members of Parliament"
    #     elif chamber == 'Senate':
    #         roles = Role.objects.filter(position='Senator', current=True).select_related('person').order_by('person')
    #         filter = 'Senators'
    #         title = "All Senators"
    #     elif chamber == 'Assembly':
    #         roles = Role.objects.filter(position='MPP', current=True, province_name=province_name).select_related('person').order_by('person__last_name', 'person__first_name')
    #         # roles = Role.objects.filter(position='MPP', current=True).select_related('person').order_by('person')
    #         filter = 'Assembly'
    #         title = "Ontario Members of Provincial Parliament"
    #         # print(roles.count())
    start_time = datetime.datetime.now()
    print('start', start_time)
    print('gov', gov)
    print('chamber', chambers)
    positions = ['Member of Parliament', 'Senator', 'Representative', 'MPP', 'Councillor']
    # updates = Update.objects.filter(Country_obj=country, data__icontains='"Current": true', Role_obj__Position='Member of Parliament').distinct('Role_obj__Person_obj')
    # updates = updates.order_by('Role_obj__Person_obj__LastName')

    # updates = Update.objects.filter(
    #     Country_obj=country, 
    #     data__icontains='"Current": true', 
    #     Role_obj__Position__in=positions,
    #     chamber__in=chambers
    # ).distinct('Role_obj__created').order_by('Role_obj__created', '-Role_obj__Person_obj__LastName')
        
    updates = Post.objects.filter(Country_obj=country, Update_obj__data__icontains='"Current": true', Update_obj__Role_obj__Position__in=positions, chamber__in=chambers).order_by('Update_obj__Role_obj__Person_obj__LastName')
    # updates = Post.objects.filter(Country_obj=country, Update_obj__data__icontains='"Current": true', Update_obj__Role_obj__Person_obj__FullName__icontains='Leo', chamber__in=chambers).order_by('Update_obj__Role_obj__Person_obj__LastName')
    # print(len(updates))
    # print(updates[0].Update_obj.Role_obj.Person_obj.FullName)
    # print(updates[0].Update_obj.Role_obj.id)
    # print(updates[0].Update_obj.data)
    # print()
    # up = Update.objects.filter(data__icontains='"Affiliation": "Non-affiliated"')
    # print('up', up)
    # up2 = Update.objects.filter(pointerId='d7c93021f1ab46a982d098d405f794a1')
    # print('up2', up2)
    # for u in up2:
    #     print(u.data)
    #     try:
    #         p = Post.objects.filter(Update_obj=u)[0]
    #         print(p)
    #     except Exception as e:
    #         print(str(e))
    # updates = updates.order_by('Role_obj__Person_obj','Role_obj__Person_obj__LastName')
    print()
    # print(updates)

    # people_ids = [u.Role_obj.Person_obj.id for u in updates]
    # print('people', people)
    # posts = Post.objects.filter(Person_obj__in=people)
    # print('updates', posts)
    # print(len(posts))
    # .select_related('Role_obj__Person_obj')
    # end 0:00:00.088560
    # end 0:00:00.448719
    # end 0:00:00.426202
    # print(page)
    setlist = paginate(updates, page, request)
    people_ids = [i.Update_obj.Role_obj.Person_obj.id for i in setlist]
    # print('people_ids', people_ids)
    personUpdates = Update.objects.filter(pointerId__in=people_ids).distinct('pointerId').order_by('pointerId', '-created')
    includedUpdates = {}
    for id in people_ids:
        includedUpdates[id] = personUpdates.filter(Person_obj__id=id)[0]
    # print(includedUpdates)

    end_time = datetime.datetime.now() - start_time
    print('end11', end_time)
    # end 0:00:00.247485
    # end 0:00:00.125219
    # includedUpdates = match_updates(setlist, personUpdates)
    # for s in setlist:
    #     print(s, s.person_name)
    # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s'%(page): '?page=', 'Search': 'search'}
    # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s'%(page): page, 'Sort: %s'%(sort):sort, 'Party: all':'all', 'Search': 'search'}
    nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), 
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), 
            # nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), 
            # nav_item('link', 'Recommended', '?view=Recommended'), 
            # nav_item('link', 'Trending', '?view=Trending'),
            nav_item('button', 'Search', 'subNavWidget("searchForm")'), 
            # nav_item('button', 'Date', 'subNavWidget("datePickerForm")')
            ]
    context = {
        # 'title': title,
        'cards': cards,
        'sort': sort,
        'view': view,
        'region': region,
        # 'filter': filter,
        'searchForm': searchform,
        'nav_bar': nav_options,
        'feed_list':setlist,
        'includedUpdates': includedUpdates,
    }
    return render_view(request, context, country=country)

def MP_view(request, iden, name):
    # start1 = datetime.datetime.now()
    print('Mp view')
    title = "Member of Parliament"
    cards = 'mp_view'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'new')
    if sort == 'old':
        ordering = 'DateTime'
        newSort = 'new'
    else:
        ordering = '-DateTime'
        newSort = 'old'
    page = request.GET.get('page', 1)
    view = request.GET.get('view', '')
    topic = request.GET.get('topic', '')
    follow = request.GET.get('follow', '')
    if follow and not request.user.is_authenticated:
        return render(request, "utils/dummy.html", {'result':'Please Login'})
    
    personUpdate = Update.objects.filter(Person_obj__id=iden).order_by('-created')[0]
    person = personUpdate.Person_obj

    user_data, user = get_user_data(request)
    country = person.Country_obj
    # country, provState, provState_name, municipality, municipality_name = get_regions(request, None, user)
    chamber, chambers = get_chambers(request, country)
    govs = get_gov(country, chamber)
    # print(person.parliamentary_position)
    if follow and follow != 'following' and follow != 'follow':
        fList = request.user.get_follow_topics()
        topic = follow
        if topic in fList:
            fList.remove(topic)
            response = 'Unfollow "%s"' %(topic)
            user = set_keywords(request.user, 'remove', topic)
        elif topic not in fList:
            fList.append(topic)
            response = 'Following "%s"' %(topic)
            user = set_keywords(request.user, 'add', topic)
        request.user.set_follow_topics(fList)
        request.user.save()
        return render(request, "utils/dummy.html", {"result": response})
    elif follow and follow == 'following' or follow and person in request.user.follow_Person_objs.all():
        request.user.follow_Person_objs.remove(person)
        request.user.save()
        return render(request, "utils/dummy.html", {'result':'Unfollow %s' %(person.FullName)})
    elif follow and follow == 'follow' or follow and person not in request.user.follow_Person_objs.all():
        request.user.follow_Person_objs.add(person)
        request.user.save()
        return render(request, "utils/dummy.html", {'result':'Following %s' %(person.FullName)})
    
    # if person.parliamentary_position:
    #     title = person.parliamentary_position  
    #     # print(title)
    #     if person.parliamentary_position == 'Member of Provincial Parliament':
    #         organization = person.province_name
    #         # print(organization)
    #         # organization = 'Ontario'
    #     else:
    #         organization = 'Federal'
    # else:
    #     organization = 'Federal'


    # updates = Update.objects.filter(pointerType='Role', Person_obj=person).distinct('Role_obj__created').order_by('-Role_obj__created', '-StartDate', '-EndDate')


    # if organization == 'Federal':
    #     r = Role.objects.filter(person=person, current=True).filter(Q(position='Member of Parliament')|Q(position='Senator'))[0]
    #     print(r)
    # else:
    #     r = Role.objects.filter(person=person, position='MPP', current=True)[0]
    r = Update.objects.filter(pointerType='Role', chamber__in=chambers, data__icontains='"Current": true', Role_obj__Person_obj=person).order_by('-created')[0]
    # if style == 'index':
    if request.user.is_authenticated and person in request.user.follow_Person_objs.all():
        follow = 'following'
    else:
        follow = 'follow'
    # if request.user.is_authenticated:
    #     try:
    #         match = Reaction.objects.filter(user=request.user, person=person).exclude(match=None)[0]
    #     except:
    #         match = Reaction(user=request.user, person=person)
    #     if not match.match or match.updated < datetime.datetime.now().replace(tzinfo=pytz.UTC) - datetime.timedelta(days=7):
    #         match_percentage, total_matches, vote_matches, my_votes, return_votes = get_matches(request, person, organization)
    #         match.match = match_percentage
    #         match.save()
    #     if match.match:
    #         match = str(match.match) + '%'
    #     else:
    #         match = 'None'
    # else:
    #     match = 'Login'
    # terms = Keyphrase.objects.filter(hansardItem__person=person)[:500]
    items = Statement.objects.filter(Person_obj=person).order_by('-DateTime')[:200]
    termsDic = {}
    for item in items:
        # item = p.hansardItem
        if item.Terms_array:
            for t in item.Terms_array:
                if t not in skipwords:
                    if t in termsDic:
                        termsDic[t] += 1
                    else:
                        termsDic[t] = 1
        if item.keyword_array:
            loweredTerms = []
            if item.Terms_array:
                loweredTerms = [x.lower() for x in item.Terms_array]  
            for t in item.keyword_array:
                if t not in skipwords and t not in loweredTerms:
                    if t in termsDic:
                        termsDic[t] += 1
                    else:
                        termsDic[t] = 1
    termsList = sorted(termsDic.items(), key=operator.itemgetter(1),reverse=True)
    # context = {
    #     'title': title,
    #     'nav_bar': list(options.items()),
    #     'person': person,
    #     'view': view,
    #     'cards': cards,
    #     'sort': sort,
    #     'personTerms': termsList
    # }
    #     return render_view(request, context)
    # else:
        # categories = []
        # for r in roles:
        #     if r.position not in categories:
                # categories.append(r.position = [])
            # categories[r.position] += r
        # for c in categories:
        # print('organization', organization)
    wordCloud = ''
    my_votes = {}
    vote_matches = 0
    total_matches = 0
    match_percentage = None
    if view == 'Match' or view == '':
        if request.user.is_authenticated:
            match_percentage, total_matches, vote_matches, my_votes, return_votes = get_matches(request, person, govs)
            posts = return_votes
            try:
                match = Interaction.objects.filter(User_obj=user, Person_obj=person).exclude(match=None)[0]
                match.match = match_percentage
                match.save()
            except:
                match = None
                print('fai11l')
                view = 'Votes'
        else:
            posts = ['Please login and start voting to see how you match']
            match_percentage = None
    if view == 'Roles':
        posts = Update.objects.filter(pointerType='Role', Role_obj__Person_obj=person).distinct('Role_obj__created').order_by('-Role_obj__created', '-Role_obj__StartDate')
        # posts = Role.objects.filter(person=person).select_related('person').order_by('-end_date', '-start_date', 'ordered')
    elif view == 'Votes':
        posts = Vote.objects.filter(Person_obj=person).order_by('-Motion_obj__DateTime')
        # posts = Vote.objects.filter(post_type='vote', vote__person=person).order_by('-date_time')
        # print(posts)
        if page == 1:
            match_percentage, total_matches, vote_matches, my_votes, return_votes = get_matches(request, person, govs)
        try:
            match = Interaction.objects.filter(User_obj=user, Person_obj=person).exclude(match=None)[0]
            match.match = match_percentage
            match.save()
        except:
            match = None
    elif view == 'Debates':
        posts = Post.objects.filter(Statement_obj__Person_obj=person).order_by(ordering)
    elif topic:
        # posts = Post.objects.filter(hansardItem__person=person, hansardItem__Terms__icontains=topic).select_related('hansardItem').order_by(ordering)
        search = ['%s'%(topic)]
        posts = Post.objects.filter(Statement_obj__Terms_array__overlap=search, Statement_obj__Person_obj=person).order_by(ordering)
        if posts.count() == 0:
            posts = Post.objects.filter(Statement_obj__keyword_array__icontains=topic, Statement_obj__Person_obj=person).order_by(ordering)
    elif view == 'Sponsorships':
        posts = Post.objects.filter(Q(Bill_obj__Person_obj=person)|Q(Bill_obj__CoSponsor_objs=person)).order_by(ordering)
        print(posts)
    # elif view == 'All':
    #     hansardItem, Vote, 
    # elif view == 'Word Cloud':
    #     try:
    #         hansards = HansardItem.objects.filter(person=person)
    #         print(hansards.count())
    #         cleantext = ''
    #         for h in hansards:
    #             cleantext = cleantext + ' ' + h.Content
    #         cleantext = BeautifulSoup(cleantext, "lxml").text
    #         wordCloud = get_wordCloud(request, cleantext)
    #         posts = []
    #     except:
    #         posts = []

    # options = {'Match: %s' %(match):'%s?view=Match'%(person.get_absolute_url()), 'Votes':'%s?view=Votes'%(person.get_absolute_url()), 
    #            'Debates':'%s?view=Debates'%(person.get_absolute_url()), 'Sponsorships':'%s?view=Sponsorships'%(person.get_absolute_url()), 'Roles':'%s?view=Roles'%(person.get_absolute_url())}
    # if topic:
    #     options['follow'] = '%s' %(topic)
    #     options['Sort: %s' %(sort)] = '%s?topic=%s&sort=%s' %(person.get_absolute_url(), topic, newSort)
    # elif view == 'Debates':
    #     options['follow'] = '?follow=%s' %(follow)
    #     options['Sort: %s' %(sort)] = '%s?view=Debates&sort=%s' %(person.get_absolute_url(), newSort)
    # else:
    #     options['follow'] = '?follow=%s' %(follow)
    nav_options = [
            nav_item('link', 'Match: %s' %('match'), '%s?view=Match'%(person.get_absolute_url())), 
            nav_item('link', 'Votes', '%s?view=Votes'%(person.get_absolute_url())), 
            nav_item('link', 'Debates', '%s?view=Debates'%(person.get_absolute_url())), 
            nav_item('link', 'Sponsorships', '%s?view=Sponsorships'%(person.get_absolute_url())), 
            nav_item('link', 'Roles', '%s?view=Roles'%(person.get_absolute_url())), 
            ]
    if topic:
        # nav_options['follow'] = '%s' %(topic)
        nav_options.append(nav_item('link', 'Sort: %s' %(sort), '%s?topic=%s&sort=%s' %(person.get_absolute_url(), topic, newSort))) 
        # ['Sort: %s' %(sort)] = '%s?topic=%s&sort=%s' %(person.get_absolute_url(), topic, newSort)
    elif view == 'Debates':
        # nav_options['follow'] = '?follow=%s' %(follow)
        # nav_options['Sort: %s' %(sort)] = '%s?view=Debates&sort=%s' %(person.get_absolute_url(), newSort)
        nav_options.append(nav_item('link', 'Sort: %s' %(sort), '%s?view=Debates&sort=%s' %(person.get_absolute_url(), newSort))) 
    # else:
    #     nav_options['follow'] = '?follow=%s' %(follow)
    # print(posts)
    setlist = paginate(posts, page, request)
    reactions = get_interactions(request, setlist)
    context = {
        'title': title,
        'nav_bar': nav_options,
        'updatedPerson': personUpdate,
        'view': view,
        'cards': cards,
        'sort': sort,
        'personTerms': termsList,
        # 'title': title,
        # 'cards': cards,
        # 'sort': sort,
        # 'view': view,
        'page': page,
        # 'filter': f,
        # 'nav_bar': list(options.items()),
        'feed_list':setlist,
        # 'mp': person,
        'updatedRole': r,
        'reactions': reactions,
        'match': match_percentage,
        'voteMatches': vote_matches,
        'totalMatches': total_matches,
        'myVotes': my_votes,
        # 'r' : Role.objects.filter(position="Member of Parliament", person=person)[0],
        'wordCloud': wordCloud,
        'topicList': [topic],
    }
    return render_view(request, context, country=country)


def senator_list(request):
    print('Senator list')
    title = "All Senators"
    cards = 'senator_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'position')
    page = request.GET.get('page', 1)
    # if style == 'index':
    #     page = 1
    roles = Role.objects.filter(position='Senator', current=True).select_related('person').order_by('ordered')
    setlist = paginate(roles, page, request)
    # options = ['Page: %s'%(page), 'Sort: %s'%(sort), 'Party: all']
    options = {'Page: %s' %(page):'page', 'Sort: %s' %(sort):'sort', 'Party: all': 'party'}
    context = {
        'title': title,
        'cards': cards,
        'sort': sort,
        'nav_bar': list(options.items()),
        'feed_list':setlist,
    }
    return render_view(request, context)


def user_set_region_view(request):
    print('profile')
    # username = username.replace('|', '')
    u = request.user
    
    title = 'My Region'
    cards = 'region_form'
    style = request.GET.get('style', 'index')
    # sort = request.GET.get('sort', 'alphabetical')
    # page = request.GET.get('page', 1)
    view = request.GET.get('view', 'constituency')
    address = request.POST.get('address')
   
    # from django.contrib.gis.utils import GeoIP
    # g = GeoIP()
    # ip = request.META.get('REMOTE_ADDR', None)
    # print(ip)
    # if ip:
    #     city = g.city(ip)['city']
    # else:
    #     city = 'Rome'
    # print('city: ', city)

    # import pygeoip
    # gi = pygeoip.GeoIP(GEOIP_DATABASE, pygeoip.GEOIP_STANDARD)
    # gi.record_by_addr(ip)

    # https://represent.opennorth.ca/boundaries/?contains=43.349130,-80.317020&format=apibrowser

    print(u.postal_code)
    form = RegionForm(initial={'address': u.address})
    if request.method == 'POST':
        # print(url)
        
        print('GOGO')
        if len(address) <= 7:
            address = address.upper().replace(' ', '')
            u.postal_code = address
            u.address_set_date = datetime.datetime.now()
            u = u.clear_region()
            url = 'https://represent.opennorth.ca/postcodes/%s/' %(address)
            form = u.get_data(url)
        else:
            url = 'http://dev.virtualearth.net/REST/v1/Locations/CA/%s?output=xml&key=AvYxl5kFcs1G1CKjpXM8atABzd_8Wb8shd8OJ2cG3-MtQjOa6Bg7rIOthHLGbDgA' %(address)
            r = requests.get(url)
            soup = BeautifulSoup(r.content, 'lxml')
            latitude = soup.find('latitude').text
            longitude = soup.find('longitude').text
            url = 'https://represent.opennorth.ca/boundaries/?contains=%s,%s' %(latitude, longitude)
            print(url)
            u = u.clear_region()
            form = u.get_data(url)
            url = 'https://represent.opennorth.ca/representatives/?point=%s,%s' %(latitude, longitude)
            print(url)
            print('----------------------------------------------------')
            form = u.get_data(url)
            u.address = address
            u.address_set_date = datetime.datetime.now()
        form = RegionForm(initial={'address': address})
        

        # options = {'All':'%s?view=all'%(u.get_absolute_url()), 'Yeas':'%s?view=yeas'%(u.get_absolute_url()), 'Nays':'%s?view=nays'%(u.get_absolute_url()), 'Comments':'%s?view=comments'%(u.get_absolute_url()), 'Saves': '%s?view=saves'%(u.get_absolute_url()), 'Constituency': '%s?view=constituency'%(u.get_absolute_url()), 'District': '%s?view=district'%(u.get_absolute_url()), 'Municipality': '%s?view=municipality'%(u.get_absolute_url())}
    # print(request.user.riding.name)
    # print(Person.objects.filter(riding=request.user.riding))
    # try:
    #     MP_role = Role.objects.filter(position='Member of Parliament', riding=request.user.riding, current=True)[0]
    # except:
    #     MP_role = 'Seat is vacant'
    # try:
    #     MPP_role = Role.objects.filter(position='MPP', district=request.user.district, current=True)[0]
    # except:
    #     MPP_role = None
    # try:
    #     Mayor_role = Role.objects.filter(position='Mayor', municipality=request.user.municipality, current=True)[0]
    # except:
    #     Mayor_role = None
    # try:
    #     Councillor_role =  Role.objects.filter(position='Councillor', ward=request.user.ward, current=True)[0]
    # except:
    #     Councillor_role = None
    reps = get_reps(request.user)
    # print(reps)
    context = {
        'u': u,
        'title': title,
        'cards': cards,
        'view': view,
        # 'nav_bar': list(options.items()),
        # 'feed_list':setlist,
        'form': form,
        # 'MP_role': MP_role,
        # 'MPP_role': MPP_role,
        # 'Mayor_role': Mayor_role,
        # 'Councillor_role': Councillor_role,
    }
    context = {**reps, **context}
    return render_view(request, context)


@csrf_exempt
def receive_interaction_data_view(request):
    print('receive_interaction_data_view')
    if request.method == 'POST':
        # print(request.body)
        # postData = json.loads(request.body)
        data = json.loads(request.POST.get('objData'))
        # print(data)
        # data = postData['objData']
        # print(received_json)
        # newPrivateKey = request.POST.get('new_private_key')
        # newPublicKey = request.POST.get('new_public_key')
        publicKey = data['publicKey']
        # transaction_data = request.POST.get('transactionData')
        signature = data['signature']
        # transaction_data = "Your transaction data here"
        # print('privateKey', newPrivateKey)
        # print()
        # print('pubkey', newPublicKey)
        print()
        print('publicKey', publicKey)
        # print()
        print('sig', signature)
        try:
            user = request.user
            print('user found', user)
            # if user.must_rename:
            #     if User.objects.filter(display_name=userData['display_name']).exclude(id=userData['id']).count() > 0:
            #         return JsonResponse({'message' : 'Username taken'})
            #     else:
            x = get_signing_data(data)
            # else:
            #     x = get_signing_data(user)
            # print(x)
            # user.delete()
            # for i in UserPubKey.objects.all():
            #     print(i.publicKey)
            #     print(i.User_obj.display_name)
            # print('--')
            
            try:
                upk = UserPubKey.objects.filter(User_obj=user, publicKey=publicKey)[0]
                print(upk)
                # print(signature)
                # print(x)
                is_valid = upk.verify(x, signature)
                print('is_valid',is_valid)
                if is_valid:
                    # json_data = json.loads(data)

                    xModel = get_or_create_model(data['object_type'], id=data['id'])
                    # print('xModel',xModel)
                    # xModel.User_obj = user
                    xModel, good = sync_and_share_object(xModel, data)
                    print('good',good)
                    if good:
                        response = JsonResponse({'message' : 'Success'})
                        # response.set_cookie(key='userData', value=json.dumps(x), expires=datetime.datetime.today()+datetime.timedelta(days=3650))
                        return response
                    else:
                        return JsonResponse({'message' : 'Sync failed'})
                else:
                    return JsonResponse({'message' : 'Verification failed'})
            except Exception as e:
                print(str(e))
                return JsonResponse({'message' : 'Invalid publicKey'})
        except Exception as e:
            return JsonResponse({'message' : f'Error {str(e)}'})

@csrf_exempt
def reaction_view(request, iden, item):
    print('reaction', iden, item)
    # add reaction to dataToShare


    userToken = None
    if not request.user.is_authenticated:
        # post = Post.objects.filter(id=iden)[0]
        # if item == 'None' or item == 'yea' or item == 'nay':
        #     try:
        #         userToken = request.COOKIES['userToken']
        #         if userToken:
        #             user = User.objects.filter(userToken=userToken)[0]
        #     except:
        #         userToken = uuid4()
        #         from random_username.generate import generate_username
        #         rand_username = generate_username(1)[0]
        #         user = User(username=rand_username, userToken=userToken, anon=True)
        #         user.slugger()
        #         user.save()
        # else:
        return render(request, "utils/dummy.html", {'result':'Login'})
        # user = User.objects.filter(username='Anon')[0]
    else:
        user = request.user
        # userOptions = UserOptions.objects.filter(pointerId=user.id)[0]
    if not 'person' in item:
        try:
            post = Post.objects.filter(id=iden)[0]
        except:
            post = Archive.objects.filter(id=iden)[0]
        # try:
            # if previous interaction has yet to be shared in dataPacket, reuse, otherwise create new
            # vote = 
            
            
            
        #     interaction = Interaction.objects.filter(User_obj=user, pointerId=post.pointerId).order_by('-created')[0]
        #     # dataPacket = get_latest_dataPacket()
        #     # packet_data = json.loads(dataPacket.data)
        #     # if interaction.id not in packet_data:
        #     #     fail
        #     # print(r.count())
        #     # post = r[0].post
        #     # try:
        #     #     r[1].delete()
        #     #     print('r[1].deleted')
        #     # except Exception as e:
        #     #     print(str(e))
        #     # interaction = r[0]
        # except Exception as e:
        #     print('create r', str(e))
        #     # post_pointer = post.pointer()
        #     interaction_id = hashlib.md5(str(user.id + post.id).encode('utf-8')).hexdigest()
        #     interaction = Interaction(id=interaction_id, created=now_utc(), User_obj=user, pointerId=post.pointerId, pointerType=post.pointerType, Region_obj=post.Region_obj)
        #     if post.object_type == 'Post':
        #         interaction.Post_obj=post
        #     elif post.object_type == 'Archive':
        #         interaction.Archive_obj=post
        #     interaction.save()
            
    # print(item)
    if item == 'None' or item == 'yea' or item == 'nay':
        # print('is vote')
        # interaction.isYea = False
        # interaction.isNay = False
        try:
            vote = UserVote.objects.filter(User_obj=user, postId=post.id)[0]
            reuse = check_dataPacket(vote)
            # print('reuse', reuse)
            if not reuse:
                fail
        except Exception as e:
            # print(str(e))
            vote = UserVote(User_obj=user, postId=post.id, pointerId=post.pointerId, id=uuid.uuid4().hex, created=now_utc())
            from blockchain.models import Blockchain
            blockchain = Blockchain.objects.filter(genesisId=post.Region_obj.id)[0]
            vote.blockchainId = blockchain.id
        # print(vote)
        # print('return')
        return JsonResponse({'message' : 'Please fill, sign and return', 'data' : get_signing_data(vote)})

    #     vote.vote = item
        

    #     if interaction.isYea == True:
    #         interaction.calculate_vote('yea', False)
    #     elif interaction.isNay == True:
    #         interaction.calculate_vote('nay', False)
    # elif item == 'yea':

    #     vote = interaction.get_or_create_object('Vote_obj', id=uuid.uuid4().hex, created=now_utc(), pointerId=post.id, Region_obj=post.Region_obj)
    #     vote.vote = 'yea'
    #     # vote = interaction.UserVote_obj
    #     # reuse = check_dataPacket(vote)
    #     # if reuse:
    #     #     vote.vote = 'yea'
    #     # else:
    #     #     vote = UserVote(id=uuid.uuid4().hex, created=now_utc(), pointerId=post.id, Region_obj=post.Region_obj)

    #     # interaction.isYea = True
    #     # interaction.isNay = False
    #     # r.viewed = True
    #     interaction.calculate_vote('yea', False)
    #     # if r.isYea:
    #     #     # print('1')
    #     #     r.isYea = False
    #     # else:
    #     #     print('2')
    #     #     r.isYea = True
    #     #     r.isNay = False
    # elif item == 'nay':

    #     vote = interaction.get_or_create_object('Vote_obj', id=uuid.uuid4().hex, created=now_utc(), pointerId=post.id, Region_obj=post.Region_obj)
    #     vote.vote = 'nay'

    #     interaction.isYea = False
    #     interaction.isNay = True
    #     # r.viewed = True
    #     interaction.calculate_vote('nay', False)
    #     # if r.isNay:
    #     #     r.isNay = False
    #     # else:
    #     #     r.isNay = True
    #     #     r.isYea = False
    elif item == 'saveButton':
        # if interaction.saved == True:
        #     interaction.saved = False
        # else:
        #     interaction.saved = True
        #     interaction.saved_time = now_utc()
        try:
            save = SavePost.objects.filter(User_obj=user, postId=post.id)[0]
            reuse = check_dataPacket(save)
            # print('reuse', reuse)
            if not reuse:
                fail
        except Exception as e:
            # print(str(e))
            save = SavePost(User_obj=user, postId=post.id, pointerId=post.pointerId, id=uuid.uuid4().hex, created=now_utc())
            
        return JsonResponse({'message' : 'Please fill, sign and return', 'data' : get_signing_data(save)})

    elif item == 'follow' or item == 'unfollow':
        print('follow')
        # r.viewed = True
        if not post:
            try:
                post = Post.objects.filter(id=iden)[0]
            except:
                post = Archive.objects.filter(id=iden)[0]

        # user.follow_Bill_objs.add(post.Bill_obj)
        # f = user.follow_Bill_obj_id_array.append(post.Bill_obj.id)
        # print(f)
        # user.save()
        # print(get_signing_data(user))
        return JsonResponse({'message' : 'Please fill, sign and return', 'data' : get_signing_data(user)})
        # print(post)
        # print(r.follow)
        # if r.follow == True:
        #     r.follow = False
        #     if post.bill:
        #         # print('bv')
        #         userOptions.follow_bill.remove(post.bill)
        #         text = 'Unfollow Bill %s' %(post.bill.NumberCode)
        #     elif post.committeeMeeting:
        #         # print(post.committeeMeeting.committee)
        #         userOptions.follow_committee.remove(post.committeeMeeting.committee)
        #         text = 'Unfollow Committee %s' %(post.committeeMeeting.committee.Title)
        #     elif post.committeeItem:
        #         userOptions.follow_person.remove(post.committeeItem.person)
        #         text = 'Unfollow %s' %(post.committeeItem.person.full_name)
        #     elif post.hansardItem:
        #         userOptions.follow_person.remove(post.hansardItem.person)
        #         text = 'Unfollow %s' %(post.hansardItem.person.full_name)
        # else:
        #     r.follow = True
        #     if post.bill:
        #         userOptions.follow_bill.add(post.bill)
        #         text = 'Following Bill %s' %(post.bill.NumberCode)
        #     elif post.committeeMeeting:
        #         userOptions.follow_committee.add(post.committeeMeeting.committee)
        #         text = 'Following Committee %s' %(post.committeeMeeting.committee.Title)
        #     elif post.committeeItem:
        #         userOptions.follow_person.add(post.committeeItem.person)
        #         text = 'Following %s' %(post.committeeItem.person.full_name)
        #     elif post.hansardItem:
        #         userOptions.follow_person.add(post.hansardItem.person)
        #         text = 'Following %s' %(post.hansardItem.person.full_name)
        # userOptions.save()
        # r.save()
        # text = 'n'
        # return render(request, "utils/dummy.html", {'result':text})
    elif item == 'follow-person':
        # print('follow person')
        # r.viewed = True
        person = Person.objects.filter(id=iden)[0]
        if person in userOptions.follow_person.all():
            userOptions.follow_person.remove(person)
        else:
            userOptions.follow_person.add(person)
        userOptions.save()
        # print(user.follow_person.all())
        return render(request, "utils/dummy.html", {'result':item})
    # r.save()
    # print(r)
    # context = {'result':item}
    # response =  render(request, "utils/dummy.html", context)
    # if userToken:
    #     response.set_cookie(key='userToken', value=userToken, expires=datetime.datetime.today()+datetime.timedelta(days=3650))
    # return response
    return JsonResponse({'message' : 'Please sign and return', 'userData' : get_signing_data(user)})
        
@csrf_exempt
def receive_test_data_view(request):
    print('recieive test')
    # print(request.body)
    # print()
    localData = json.loads(request.POST.get('localData'))
    print(localData)
    print()
    serverData = json.loads(request.POST.get('serverData'))
    print(serverData)
    # del serverData['signature']
    # del serverData['publicKey']
    print()
    # siglessData = json.loads(request.POST.get('siglessData'))
    # print(siglessData)

    print()
    if serverData == localData:
        print('its the same')
    else:
        print('no they are different')

    print()


    # publicKey = serverData['publicKey']
    # signature = serverData['signature']
    # # try:
    # user = request.user
    # # print('user found', user)
    # x = get_signing_data(serverData)
    #     # try:
    # upk = UserPubKey.objects.filter(User_obj=user, publicKey=publicKey)[0]
    
    # is_valid = upk.verify(x, signature)
    # print('serverData is_valid',is_valid)
    # print()

    publicKey = localData['publicKey']
    signature = localData['signature']
    # try:
    user = request.user
    # print('user found', user)
    x = get_signing_data(localData)
        # try:
    upk = UserPubKey.objects.filter(User_obj=user, publicKey=publicKey)[0]
    
    is_valid = upk.verify(x, signature)
    print('localData is_valid',is_valid)
    print()

    xModel, good = sync_and_share_object(user, localData)
    print('good',good)
    print()

@csrf_exempt
def set_sonet_view(request):
    print('set_sonet_view')
    try:
        if request.method == 'POST':
            try:
                existing_net = Sonet.objects.all()[0]
                sonet_exists = True
            except:
                sonet_exists = False
            sonetData = request.POST.get('sonetData')
            sonetData_json = json.loads(sonetData)

            sonet = get_or_create_model('Sonet', id=sonetData_json['id'])
            # upk.User_obj = user
            sonet, good = sync_model(sonet, sonetData_json)
            print('sonet-good',good)
            if good:
                if not sonet_exists:
                    earth = Region(id=uuid.uuid4().hex, created=now_utc(), func='super', nameType='Planet', Name='Earth', modelType='planet', is_supported=True)
                    return JsonResponse({'message' : 'Success', 'sonet' : get_signing_data(sonet), 'earth' : get_signing_data(earth)})
                else:
                    return JsonResponse({'message' : 'Success', 'sonet' : get_signing_data(sonet)})
            else:
                return JsonResponse({'message' : 'A problem occured'})
    except Exception as e:
        return JsonResponse({'message' : f'A problem occured, {str(e)}'})
        
