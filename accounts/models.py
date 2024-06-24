from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.db.models import Q, Value, F, Avg

# from django.contrib.postgres.fields import ArrayField
from posts.models import initial_save, superDelete, now_utc, sign_obj, share_with_network, find_or_create_chain_from_object, create_dynamic_model, get_point_value, set_keywords, Post, Archive
from blockchain.models import check_dataPacket
import re
import time
import datetime
import wikipedia
import random
import requests
from bs4 import BeautifulSoup
import json
import base64
import decimal
import pytz
import hashlib
import uuid

from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
# Create your models here.



class Sonet(models.Model):
    object_type = "Sonet"
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    title = models.CharField(max_length=200, default="x")
    subtitle = models.CharField(max_length=200, default="", blank=True, null=True)
    LogoLink = models.CharField(max_length=200, default="/static/img/logo_grey.png")
    coin_name = models.CharField(max_length=200, default="token")
    coin_name_plural = models.CharField(max_length=200, default="tokens")
    description = models.CharField(max_length=2000, default="", blank=True, null=True)
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")

    def __str__(self):
        return 'Sonet:%s' %(self.title)
    
    # def logo_link(self):
    #     return "static/img/%s" %(self.logoLink)

    def delete(self):
        pass

    def save(self):
        super(Sonet, self).save()
        try:
            exists = Sonet.objects.exclude(id=self.id)[0]
        except:
            if self.id == '0':
                self.id = uuid.uuid4().hex
            from blockchain.models import get_signing_data
            try:
                u = User.objects.filter(username='Sozed')[0]
                upks = UserPubKey.objects.filter(User_obj=u)
                for upk in upks:
                    is_valid = upk.verify(get_signing_data(self), self.signature)
                    if is_valid:
                        super(Sonet, self).save()
                        share_with_network(self)
                        break
            except:     
                pass



class BaseAccountModel(models.Model):
    blockchainId = models.CharField(max_length=50, default="")
    locked_to_chain = models.BooleanField(default=False)
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")

    class Meta:
        abstract = True

class User(AbstractUser):
    object_type = "User"
    # blockchainType = 'NoChain'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # user_id = models.CharField(max_length=50, default="0")
    signature = models.CharField(max_length=200, default="0")

    # salt = models.PositiveBigIntegerField(default=0)
    publicKey = models.CharField(max_length=200, default="0")
    display_name = models.CharField(max_length=50, default="0", blank=True, null=True)
    must_rename = models.BooleanField(default=False) # if network conflict occurs because display_name already taken on different node
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    slug = models.SlugField(unique=True)
    # userToken = models.CharField(max_length=500, default="", blank=True, null=True)
    appToken = models.CharField(max_length=500, default="", blank=True, null=True)
    # interest_array = ArrayField(models.CharField(max_length=100, blank=True, null=True, default='{default}'), size=1000, null=True, blank=True, default=list) #adjust size in reaction.set_keywords
    # longLat = ArrayField(models.CharField(max_length=25, blank=True, null=True, default='{default}'), size=1000, null=True, blank=True) #adjust size in reaction.set_keywords
    # postal_code = models.CharField(max_length=10, default="", blank=True, null=True)
    # address = models.CharField(max_length=100, default="", blank=True, null=True)
    region_set_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    
    # Person_obj = models.ForeignKey('posts.Person', default=None, blank=True, null=True, on_delete=models.SET_NULL)
    # person_position = models.CharField(max_length=20, default="", blank=True, null=True)
    
    Country_obj = models.ForeignKey('posts.Region', default=None, related_name='country', blank=True, null=True, on_delete=models.SET_NULL)
    Federal_District_obj = models.ForeignKey('posts.District', default=None, related_name='federal_district', blank=True, null=True, on_delete=models.SET_NULL)
    ProvState_obj = models.ForeignKey('posts.Region', default=None, related_name='provState', blank=True, null=True, on_delete=models.SET_NULL)
    ProvState_District_obj = models.ForeignKey('posts.District', default=None, related_name='provState_district', blank=True, null=True, on_delete=models.SET_NULL)
    Greater_Municipality_obj = models.ForeignKey('posts.Region', default=None, related_name='greater_municpality', blank=True, null=True, on_delete=models.SET_NULL)
    Greater_Municipal_District_obj = models.ForeignKey('posts.District', default=None, related_name='greater_municpality_district', blank=True, null=True, on_delete=models.SET_NULL)
    Municipality_obj = models.ForeignKey('posts.Region', default=None, related_name='municipality', blank=True, null=True, on_delete=models.SET_NULL)
    Municipal_District_obj = models.ForeignKey('posts.District', default=None, related_name='muncipality_district', blank=True, null=True, on_delete=models.SET_NULL)
    
    # follow_Person_objs = models.ManyToManyField('posts.Person', default=None, blank=True, related_name='accounts_person')
    # follow_Bill_objs = models.ManyToManyField('posts.Bill', default=None, blank=True, related_name='posts_bill')
    # follow_Committee_objs = models.ManyToManyField('posts.Committee', default=None, blank=True, related_name='posts_committee')
    # follow_topic_json = models.TextField(default='[]')
    # follow_Bill_obj_id_array = ArrayField(models.CharField(max_length=100, blank=True, null=True, default='{default}'), size=100, null=True, blank=True, default=list)
    # follow_Committee_obj_id_array = ArrayField(models.CharField(max_length=100, blank=True, null=True, default='{default}'), size=100, null=True, blank=True, default=list)
    
    # follow_post_id_array = ArrayField(models.CharField(max_length=100, blank=True, null=True, default='{default}'), size=100, null=True, blank=True, default=list)
    # follow_topic_array = ArrayField(models.CharField(max_length=100, blank=True, null=True, default='{default}'), size=100, null=True, blank=True, default=list)
    
    interest_array = models.TextField(default='[]', blank=True, null=True)
    follow_post_id_array = models.TextField(default='[]', blank=True, null=True)
    follow_topic_array = models.TextField(default='[]', blank=True, null=True)
    
    receiveNotifications = models.BooleanField(default=True)
    isVerified = models.BooleanField(default=False)
    # is_admin = models.BooleanField(default=False)
    # show_data = models.BooleanField(default=False)
    # nodeId = models.CharField(max_length=50, default="0")
    
    def __str__(self):
        return 'USER:%s' %(self.display_name)
    
    class Meta:
        ordering = ['created']

    def get_absolute_url(self):
        #return reverse("sub", kwargs={"subject": self.name})
        return "/so/%s" % (self.display_name)
    
    def get_userLink_html(self):
        return f'''<a href='{self.get_absolute_url()}'><span style='color:#b78e12'>V</span><span style='color:gray'>/</span>{ self.display_name }</a>'''

    # def get_display_name(self):
    #     return UserOptions.object.filter(user=self).order_by('-created')[0].display_name

    # def get_latest_options(self):
    #     return UserOptions.object.filter(user=self).order_by('-created')[0]

    def verify(self, data, signature_hex):
        pubKeys = UserPubKey.objects.filter(User_obj=self)
        for p in pubKeys:
            is_valid = p.verify(data, signature_hex)
            if is_valid:
                return True
        return False
    


    # def sign_transaction(self, private_key, transaction_data):
    #     # json.loads(get_latest_update(current_user.id).data)['public_key']
    #     # Hash the transaction data
    #     digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    #     digest.update(transaction_data.encode('utf-8'))
    #     hashed_transaction = digest.finalize()

    #     # Sign the hashed transaction with the private key
    #     signature = private_key.sign(hashed_transaction, ec.ECDSA(hashes.SHA256()))

    #     return signature

    # def verify_signature(self, transaction_data, signature):
    #     from posts.models import get_latest_update
    #     public_key = base64.b64decode(json.loads(get_latest_update(self.id).data)['public_key'])
    #     # Hash the transaction data
    #     digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    #     digest.update(transaction_data.encode('utf-8'))
    #     hashed_transaction = digest.finalize()

    #     # Verify the signature using the public key
    #     try:
    #         public_key.verify(signature, hashed_transaction, ec.ECDSA(hashes.SHA256()))
    #         return True  # Verification successful
    #     except Exception as e:
    #         print(f"Signature verification failed: {str(e)}")
    #         return False  # Verification failed


    def assess_verification(self):
        pass

    def alert(self, title, link, body, obj=None, share=True):
        # print('alert')
        if title == 'Yesterday in Government':
            x = link.find('?date=') + len('?date=')
            date = link[x:]
            workingTitle = date + ' in Government'
            # print(workingTitle)
        else:
            if body:
                if len(body) > 11:
                    b = body[:11] + '...'
                else:
                    b = body
                workingTitle = title + ' - ' + b
            else:
                workingTitle = title
        try:
            n = Notification.objects.filter(title=workingTitle, link=link, User_obj=self)[0]
        except:
            # pass
            n = Notification(title=workingTitle, link=link, User_obj=self)
            if obj:
                n.pointerType = obj.object_type
                n.pointerId = obj.id
            # else:
            #     n = Notification(title=title, link=link, user=self)
            n.save(share=share)
            try:
                from firebase_admin.messaging import Notification as fireNotification
                from firebase_admin.messaging import Message as fireMessage
                from fcm_django.models import FCMDevice
                if link:
                    link = link.replace('file://', '')
                    if link[0] == '/':
                        link = 'https://sovote.org' + link
                else:
                    link = 'https://sovote.org'
                fcm_devices = FCMDevice.objects.filter(user=self, active=True)
                for device in fcm_devices:
                    try:
                        print(device)
                        device.send_message(fireMessage(notification=fireNotification(title=title, body=body), data={"click_action" : "FLUTTER_NOTIFICATION_CLICK","link" : link}))
                        print('away')
                    except Exception as e:
                        print(str(e))
            except:
                pass
        # print(n)
    
    def clear_region(self):
        u = self
        # try:
        #     r = Role.objects.filter(Position='Member of Parliament', District=u.Federal_District)[0]
        #     u.follow_person.remove(r.Person)
        # except:
        #     pass
        # try:
        #     r = Role.objects.filter(Position='MPP', District=u.ProvState_District)[0]
        #     u.follow_person.remove(r.Person)
        # except:
        #     pass

        u.Country_obj = None
        u.Federal_District_obj = None
        u.ProvState_obj = None
        u.ProvState_District_obj = None
        u.Municipality_obj = None
        u.Municipal_District_obj = None
        u.Greater_Municipality_obj = None
        u.Greater_Municipal_District_obj = None
        return u

    def get_keys(self):
        return UserPubKey.objects.filter(User_obj=self)

    def slugger(self):
        # self.display_name = re.sub(r'[^a-zA-Z0-9+_-]', '', self.display_name)
        slug = slugify(re.sub(r'[^a-zA-Z0-9+_-]', '', self.display_name))
        unique = False
        while unique == False:
            try:
                u = User.objects.filter(slug=slug)[0]
                slug = slug + random.randint(100)
            except:
                # self.slug = slug
                unique = True
        return slug
    
    def set_follow_topics(self, x):
        self.follow_Topic_json = json.dumps(x)

    def get_follow_topics(self):
        return json.loads(self.follow_topic_json)
    
    def save(self, share=True, *args, **kwargs):
        # print('save user')
        if self.id == '0':
            self = initial_save(self, share=share)
            if not self.slug:
                self.slugger()
            # wallet = Wallet(pointerId=self.id)
            # wallet.save()
        # if not self.locked_to_chain:
        super(User, self).save(*args, **kwargs)
        # print('done save')

    def delete(self):
        # deletes only if username previously registered to different user or user created less than 10 seconds ago
        if not isinstance(self.created, datetime.datetime):
            created = datetime.datetime.fromisoformat(self.created)
        else:
            created = self.created
        if created >= now_utc()-datetime.timedelta(seconds=10): 
            super(User, self).delete()
        else:
            try:
                u = User.objects.filter(display_name=self.display_name).exclude(id=self.id)[0]
                if u.created < created:   
                    super(User, self).delete()
            except:
                pass

def generate_keyPair(password):
    print('gen keypair')
    get_keys = '''
    function createKeys(){   
    const curve = new elliptic.ec('secp256k1');
    let keyPair = curve.keyFromPrivate('%s');
    let privKey = keyPair.getPrivate("hex");
    const publicKey = keyPair.getPublic();
    const publicKeyHex = keyPair.getPublic().encode('hex');
    return [privKey, publickKeyHex];
    }
    createKeys()
    ''' %(password)

    from pythonmonkey import eval as js_eval
    with open("elliptic.js", "r") as file:
        elliptic_js_code = file.read()

    full_js_code = elliptic_js_code + "\n" + get_keys

    keys = js_eval(full_js_code)
    print('result', keys)
    return keys


def sign(private_key, data):
    private_key_bytes = bytes.fromhex(private_key)
    private_key = ec.derive_private_key(int.from_bytes(private_key_bytes, byteorder='big'), ec.SECP256K1())
    signature = private_key.sign(data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    signature_hex = signature.hex()
    # this should be included, not sure if func is being used
    # data = json.loads(data)
    # data['publicKey'] = pubKey
    # data['signature'] = signature_hex
    return signature_hex


def add_or_verify_pubkey(user, registeredPublicKey, newPublicKey, signature):
    # print('verify registeredpubkey', registeredPublicKey)
    # print('verify newpubkey', newPublicKey)
    upks = UserPubKey.objects.filter(User_obj=user)
    if upks.count() > 0:
        for u in upks:
            if u.publicKey == newPublicKey:
                return u
        for u in upks:
            # print('enxt')
            if registeredPublicKey and u.publicKey == registeredPublicKey:
                isValid = u.verify(signature, 'new public key')
                if isValid and newPublicKey:
                    upk = UserPubKey(User_obj=user, publicKey=newPublicKey)
                    upk.save()
                    return upk
        return None
    elif newPublicKey:
        # print('else')
        upk = UserPubKey(User_obj=user, publicKey=newPublicKey)
        upk.save()
        return upk
    else:
        return None

class UserPubKey(BaseAccountModel):
    object_type = "UserPubKey"
    blockchainType = 'Users'
    modelVersion = models.CharField(max_length=50, default="v1")
    # blockchainId = models.CharField(max_length=50, default="0")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.CASCADE)
    # signature = models.CharField(max_length=200, default="0")
    # publicKey = models.CharField(max_length=200, default="0")
    keyType = models.CharField(max_length=50, default="password") # password or biometrics
    

    def __str__(self):
        return 'USERPUBLICKEY:%s' %(self.id)
        
    class Meta:
        ordering = ['-created', 'id']

    def verify(self, data, signature_hex):
        signature_bytes = bytes.fromhex(signature_hex)
        # print(signature_bytes.hex())
        public_key_bytes = bytes.fromhex(self.publicKey)
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
        # print('pubkey loaded', publicKey)
        try:
            public_key.verify(signature_bytes, data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
            print("Signature is valid YAY IT WORKED!!!.")
            return True
        # except InvalidSignature:
        #     print("Invalid signature.")
        except Exception as e:
            print(str(e))
            return False

    def save(self, share=True, *args, **kwargs):
        if self.id == '0':
            self = initial_save(self, share=share)
            # if not self.slug:
            #     self.slugger()
        # add to dataToShare
        super(UserPubKey, self).save(*args, **kwargs)

    def delete(self, signature=None):
        if not isinstance(self.created, datetime.datetime):
            created = datetime.datetime.fromisoformat(self.created)
        else:
            created = self.created
        is_valid = None
        if signature:
            is_valid = self.verify('delete', signature)
        if is_valid:
            print('deleted upk')
            super(UserPubKey, self).delete()
        else:
            if created <= now_utc()-datetime.timedelta(seconds=10):
                super(UserPubKey, self).delete()
            # else:
            #     print('is more than 10')
            # print('failed to delete upk')

class Verification(BaseAccountModel):
    object_type = "Verification"
    blockchainType = 'Users'
    modelVersion = models.CharField(max_length=50, default="v1")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    pointerId = models.CharField(max_length=50, default="0")
    pointerType = 'User'
    Target_User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.CASCADE)
    isVerified = models.BooleanField(default=False)
    # signature = models.CharField(max_length=200, default="0")
    # publicKey = models.CharField(max_length=200, default="0")
    

    def __str__(self):
        return 'VERIFICATION:%s' %(self.id)
        
    class Meta:
        ordering = ['-created', 'id']

    def save(self, share=True, *args, **kwargs):
        if self.id == '0':
            self = initial_save(self, share=share)
            # broadcast changes immediatly
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            super(Verification, self).save(*args, **kwargs)

class Wallet(BaseAccountModel):
    object_type = "Wallet"
    blockchainType = 'Wallet'
    modelVersion = models.CharField(max_length=50, default="v1")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=False)
    pointerId = models.CharField(max_length=50, default="0")
    pointerType = 'User'
    User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.SET_NULL)
    coins = models.CharField(max_length=1000000, default="0")
    # private_key = models.CharField(max_length=500, default="", blank=True, null=True)
    # secret_key = models.CharField(max_length=500, default="", blank=True, null=True)
    

    def __str__(self):
        return 'WALLET:%s' %(self.id)
        
    class Meta:
        ordering = ['-created', 'id']

    def save(self, share=True, *args, **kwargs):
        if self.id == '0':
            self.pointerId = self.User_obj.id
            self = initial_save(self, share=share)
            # broadcast changes immediately
        if not self.locked_to_chain:
            super(Wallet, self).save(*args, **kwargs)

class Transaction(BaseAccountModel):
    object_type = "Transaction"
    blockchainType = 'Wallet'
    modelVersion = models.CharField(max_length=50, default="v1")
    # blockchainId = models.CharField(max_length=50, default="0")
    receiverChainId = models.CharField(max_length=50, default="0")
    locked_to_chain = models.BooleanField(default=False)
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=False)
    # pointerId = models.CharField(max_length=50, default="0")
    # pointerType = 'Wallet'
    SoDo_value = models.CharField(max_length=1000000, default="0")
    sender_wallet_obj = models.ForeignKey('accounts.Wallet', related_name='sender', on_delete=models.PROTECT)
    receiver_wallet_obj = models.ForeignKey('accounts.Wallet', related_name='receiver', on_delete=models.PROTECT)
    # sender_id = models.CharField(max_length=1000000, default="0")
    # receiver_id = models.CharField(max_length=1000000, default="0")
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")


    def __str__(self):
        return 'TRANASACTION:%s' %(self.id)
        
    class Meta:
        ordering = ['-created', 'id']

    def save(self, share=True, *args, **kwargs):
        if self.id == '0':
            self = initial_save(self, share=share)
            # broadcast changes immediatly
        if not self.locked_to_chain:
            super(Transaction, self).save(*args, **kwargs)

class Notification(BaseAccountModel):
    object_type = "Notification"
    blockchainType = 'Users'
    modelVersion = models.CharField(max_length=50, default="v1")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=True)
    Target_User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=400, blank=True, null=True, default="")
    link = models.CharField(max_length=500, blank=True, null=True, default="")
    Region_obj = models.ForeignKey('posts.Region', blank=True, null=True, on_delete=models.SET_NULL)
    new = models.BooleanField(default=True)
    pointerId = models.CharField(max_length=50, default="")
    pointerType = models.CharField(max_length=50, default="")
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
 
    class Meta:
        ordering = ["-created", '-id']
    
    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            super(Notification, self).save()

class UserVote(BaseAccountModel):
    object_type = "UserVote"
    blockchainType = 'Region'
    postId = models.CharField(max_length=50, default="0") 
    User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.SET_NULL)
    vote = models.CharField(max_length=20, default='none', blank=True, null=True)

    def __str__(self):
        return f'UserVote: username:{self.User_obj.display_name}, postId:{self.postId}'

    def create_post(self):
        # creates Interaction
        try:
            interaction = Interaction.objects.filter(User_obj=self.User_obj, Post_obj__id=self.postId)[0]
        except:
            post = Post.objects.filter(id=self.postId)[0]
            interaction = Interaction(User_obj=self.User_obj, Post_obj=post, created=self.created)
        interaction.UserVote_obj = self
        interaction.save()

    def save(self, share=True):
        # if self.id == '0':
        #     self = initial_save(self, share=share)
        if not self.blockchainId:
            chain, obj, receiverChain = find_or_create_chain_from_object(self)
            self.blockchainId = chain.id
        # if share:
        #     share_with_network(self)
        super(UserVote, self).save()
    
    def delete(self):
        super(UserVote, self).delete()

class SavePost(models.Model):
    object_type = "SavePost"
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")
    postId = models.CharField(max_length=50, default="0") 
    User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.SET_NULL)
    saved = models.BooleanField(default=False)

    def create_post(self):
        # creates Interaction
        try:
            interaction = Interaction.objects.filter(User_obj=self.User_obj, Post_obj__id=self.postId)[0]
        except:
            post = Post.objects.filter(id=self.postId)[0]
            interaction = Interaction(User_obj=self.User_obj, Post_obj=post, created=self.created)
        interaction.SavePost_obj = self
        interaction.save()
        previous_objs = SavePost.objects.filter(User_obj=self.User_obj, postId=self.postId).exclude(id=self.id)
        for obj in previous_objs:
            obj.delete()

    def save(self, share=True):
        # if self.id == '0':
        #     self = initial_save(self, share=share)
        # if share:
        #     share_with_network(self)
        super(SavePost, self).save()
    
    def delete(self):
        super(SavePost, self).delete()

# class Follow(models.Model):
#     object_type = "Follow"
#     id = models.CharField(max_length=50, default="0", primary_key=True)
#     created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
#     publicKey = models.CharField(max_length=200, default="0")
#     signature = models.CharField(max_length=200, default="0")
#     postId = models.CharField(max_length=50, default="0") 
#     User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.SET_NULL)
#     follow = models.BooleanField(default=False)

#     def create_post(self):
#         # creates Interaction
#         try:
#             interaction = Interaction.objects.filter(User_obj=self.User_obj, Post_obj__id=self.postId)[0]
#         except:
#             post = Post.objects.filter(id=self.postId)[0]
#             interaction = Interaction(User_obj=self.User_obj, Post_obj=post, created=self.created)
#         interaction.Follow_obj = self
#         interaction.save()
#         previous_objs = Follow.objects.filter(User_obj=self.User_obj, postId=self.postId).exclude(id=self.id)
#         for obj in previous_objs:
#             obj.delete()

#     def save(self, share=True):
#         # if self.id == '0':
#         #     self = initial_save(self, share=share)
#         if share:
#             share_with_network(self)
#         super(Follow, self).save()
    
#     def delete(self):
#         super(Follow, self).delete()


class Interaction(models.Model):
    object_type = "Interaction"
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=False)
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")

    Region_obj = models.ForeignKey('posts.Region', related_name='%(class)s_region_obj', blank=True, null=True, on_delete=models.CASCADE)
    User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.SET_NULL)
    Post_obj = models.ForeignKey(Post, blank=True, null=True, on_delete=models.SET_NULL)
    # Archive_obj = models.ForeignKey(Archive, blank=True, null=True, on_delete=models.SET_NULL)
    # post_id = models.IntegerField(null=True) 
    pointerId = models.CharField(max_length=50, default="0") # points to post_obj.pointer, not post
    pointerType = models.CharField(max_length=50, default="0")

    UserVote_obj = models.ForeignKey('accounts.UserVote', blank=True, null=True, on_delete=models.SET_NULL)
    SavePost_obj = models.ForeignKey('accounts.SavePost', blank=True, null=True, on_delete=models.SET_NULL)
    # Follow_obj = models.ForeignKey('accounts.Follow', blank=True, null=True, on_delete=models.SET_NULL)



    score = models.IntegerField(default=0)

    # Person_obj = models.ForeignKey('posts.Person', blank=True, null=True, on_delete=models.SET_NULL)
    match = models.IntegerField(default=None, blank=True, null=True)
    
    # saved = models.BooleanField(default=False)
    # saved_time = models.DateTimeField(auto_now_add=False, auto_now=False, null=True)
    # shared = models.BooleanField(default=False)
    # shared_time = models.DateTimeField(auto_now_add=False, auto_now=False, null=True)

    # voted_keywords_added = models.BooleanField(default=False)
    # viewed_keywords_added = models.BooleanField(default=False)
    shared_keywords_added = models.BooleanField(default=False)
    # followed_keywords_added = models.BooleanField(default=False)
    # viewed = models.BooleanField(default=False)
    # follow = models.BooleanField(default=False)

    def __str__(self):
        return f'Interaction: user:{self.User_obj.display_name}, pointerId:{self.pointerId}'
        # if self.post_id:
        #     return "post/%s/%s/%s" % (self.user, self.post_id, self.score)
        # elif self.comment_id:
        #     return "comment/%s/%s/%s" % (self.user, self.comment_id, self.score)
        # elif self.episode_link_id:
        #     return "eplink/%s/%s/%s" % (self.user, self.episode_link_id, self.score)
        # elif self.column:
        #     return "column/%s/%s/%s" % (self.user, self.column.name, self.score)

    class Meta:
        ordering = ["-created"]
    
    def get_or_create_object(self, obj_type, **kwargs):
        item = getattr(self, obj_type)
        reuse = check_dataPacket(item)
        if reuse:
            return item
        else:
            return create_dynamic_model(obj_type, **kwargs)

    def calculate_vote(self, vote, forceVote):
        if self.Post_obj:
            p = self.Post_obj
        elif self.Archive_obj:
            p = self.Archive_obj
        score = get_point_value(p)
        if vote == 'yea' or vote == 'Yea':
            if self.isYea == False or forceVote:
                if self.isYea == True:
                    p.total_yeas -= 1
                self.isYea = True
                if self.isNay == True:
                    p.total_nays -= 1
                self.isNay = False
                points = decimal.Decimal(score)
                p.rank += points
                p.total_yeas += 1
                if not forceVote:
                    p.total_votes += 1
                # self = set_keywords(self, 'add', None)
            elif self.isYea == True:
                self.isYea = False
                points = decimal.Decimal(score)
                p.rank -= points
                p.total_votes -= 1
                p.total_yeas -= 1
                # self = set_keywords(self, 'remove', None)
        elif vote == 'nay' or vote == 'Nay':
            # self.cast_vote = ''
            if self.isNay == False or forceVote:
                if self.isNay == True:
                    p.total_nays -= 1
                self.isNay = True
                if self.isYea == True:
                    self.isYea = False
                    points = decimal.Decimal(score)
                    p.rank -= points
                    p.total_yeas -= 1
                p.total_nays += 1
                if not forceVote:
                    p.total_votes += 1
            elif self.isNay == True:
                self.isNay = False
                p.rank += points
                # self = set_keywords(self, 'add', None)
                p.total_votes -= 1
                p.total_nays -= 1
        p.save()
        self.save()

    def save(self, share=False):
        if self.id == '0':
            if self.Post_obj:
                post = self.Post_obj
            elif self.Archive_obj:
                post = self.Archive_obj
            self.Region_obj = post.Region_obj
            pointer = post.get_pointer()
            self.pointerId = pointer.id
            self.pointerType = pointer.object_type
            # print(pointer, pointer.DateTime)
            # self.DateTime = now_utc()
            # print('self.pointerDateTime22', self.pointerDateTime)
            # pointer_obj = str(self.pointerType) + '_obj'
            # setattr(self, pointer_obj, pointer)
            # print('pointer.id', pointer.id)
            
            
            self.id = hashlib.md5(str(self.User_obj.id + post.id).encode('utf-8')).hexdigest()
            
            
            
            # self = initial_save(self, share=share)
            # try:
            #     p = Post.objects.filter(id=self.postId)[0]
            # except:
            #     p = Archive.objects.filter(id=self.postId)[0]
            # self.blockchainType = p.blockchainType
            # self.blockchainId = p.blockchainId
        # try:
        #     if self.saved and not self.saved_time:
        #         self.saved_time = now_utc()
        #     if self.viewed and not self.viewed_keywords_added:
        #         # print('viewed add')
        #         self = set_keywords(self, 'add', None)
        #         self.viewed_keywords_added = True
        #     # if not self.voted_keywords_added and self.isYea or not self.voted_keywords_added and self.isNay:
        #     #     print('voted add')
        #     #     self.voted_time = datetime.datetime.now()
        #     #     self = self.set_keywords('add')
        #     #     self.voted_keywords_added = True
        #     if self.shared and not self.shared_keywords_added:
        #         # print('shared add')
        #         self.shared_time = now_utc()
        #         self = set_keywords(self, 'add', None)
        #         self.shared_keywords_added = True
        #     if self.follow and not self.followed_keywords_added:
        #         # print('followed add')
        #         self = set_keywords(self, 'add', None)
        #         self.followed_keywords_added = True
        # except Exception as e:
        #     print(str(e))
        # if not self.locked_to_chain:
            # add to dataToShare
        super(Interaction, self).save()
    
    def delete(self):
        if not self.locked_to_chain:
            super(Interaction, self).delete()

# class SchoolBoard(models.Model):
#     # parlinfo_link = models.URLField(null=True, blank=True)
#     object_type = "SchoolBoard"
#     id = models.CharField(max_length=50, default="0", primary_key=True)
#     created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
#     last_updated = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
#     name = models.CharField(max_length=100, default="")
#     province_name = models.CharField(max_length=100, default="")
#     province = models.ForeignKey(Province, blank=True, null=True, on_delete=models.RESTRICT)
#     map_link = models.URLField(null=True, blank=True)
#     info = models.TextField(blank=True, null=True)
#     opennorthId = models.IntegerField(default=0, blank=True, null=True)
#     wikipedia = models.URLField(null=True, blank=True)

#     def __str__(self):
#         return 'SCHOOLBOARD:%s %s %s' %(self.name, self.province_name)

#     class Meta:
#         ordering = ["name"]

#     def save(self):
#         if self.id == '0':
#             self = initial_save(self)
#         super(SchoolBoard, self).save()
    
# class SchoolBoardRegion(models.Model):
#     # parlinfo_link = models.URLField(null=True, blank=True)
#     object_type = "SchoolBoardRegion"
#     id = models.CharField(max_length=50, default="0", primary_key=True)
#     created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
#     last_updated = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
#     name = models.CharField(max_length=100, default="")
#     province_name = models.CharField(max_length=100, default="")
#     schoolBoard_name = models.CharField(max_length=100, default="")
#     province = models.ForeignKey(Province, blank=True, null=True, on_delete=models.RESTRICT)
#     schoolBoard = models.ForeignKey(SchoolBoard, blank=True, null=True, on_delete=models.RESTRICT)
#     map_link = models.URLField(null=True, blank=True)
#     info = models.TextField(blank=True, null=True)
#     opennorthId = models.IntegerField(default=0, blank=True, null=True)
#     wikipedia = models.URLField(null=True, blank=True)

#     def __str__(self):
#         return 'SCHOOLBOARDREGION:%s %s %s' %(self.name, self.schoolBoard_name, self.province_name)

#     class Meta:
#         ordering = ["name"]
    
#     def save(self):
#         if self.id == '0':
#             self = initial_save(self)
#         super(SchoolBoardRegion, self).save()

