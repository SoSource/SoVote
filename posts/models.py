from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q

from accounts.models import *

from django.forms.models import model_to_dict

import uuid
import base64
import re
import random
import json
import pytz
import datetime
import time
from dateutil import tz
from django.utils import timezone
import decimal
import operator
from nltk.corpus import stopwords
import hashlib
import ast
# from collections import Counter, OrderedDict
# from operator import itemgetter

skipwords = [
    "shouldn't", 'needn', 'before', 'we', 'are', 'after', 'because', 'haven', 'and', 'itself', 'all', 'o', 'but', 'any', 'again', 'aren', 'she', "you'll", 
    'himself', 'didn', 'under', 'wasn', 's', 'yours', 'very', "aren't", "won't", 'don', 'how', 'him', "mustn't", 'more', 't', 'off', 'ours', "it's", 'into', 
    'same', 'myself', 'at', "wouldn't", 'they', 'only', 'so', 'down', 'yourselves', 'both', 'each', 'who', 'themselves', 'yourself', 'as', 'up', 'not', 'above', 
    'this', 'will', 'was', 'here', 'does', 'for', 'such', 'there', 'should', 'by', 'mustn', 're', 'is', "isn't", "she's", "weren't", 'y', 'he', 'between', 
    'where', 'on', 'am', 'other', 'now', 'too', "haven't", 'some', 'd', 'being', 'then', 'hasn', "hadn't", 'in', 'having', 'i', 'which', "mightn't", 'were', 
    'wouldn', 'our', 'to', 'until', 'with', 'most', 'if', 'those', 'their', 'nor', 'of', 'doesn', "wasn't", 'do', 'that', 'once', 'than', 'ain', 'isn', 'its', 
    'these', 'had', 'your', 'can', 'you', 'shouldn', "you're", 'doing', 'it', 'while', 'the', 'll', 'or', 'hadn', "doesn't", 'his', 've', 'about', 'through', 'own', 
    'mightn', 'further', 'hers', "didn't", 'm', "that'll", "hasn't", "you'd", 'me', 'have', 'what', 'did', 'over', 'whom', "you've", 'has', 'why', "needn't", 
    'couldn', 'below', "don't", 'an', 'no', 'ourselves', 'out', 'won', 'her', 'be', 'from', "shan't", 'been', 'herself', "should've", 'just', 'ma', 'when', 'shan', 
    "couldn't", 'few', 'during', 'against', 'a', 'them', 'weren', 'theirs', 'my', 'statement',
    'SENATORS’ STATEMENTS','Orders of the Day', 'Question Period', 'Petitions', "Members' Statements", 'ORDERS OF THE DAY', 'SENATORS’ STATEMENTS', 'ROUTINE PROCEEDINGS', 
    'Oral questions', 'QUESTION PERIOD','QUESTION PERIOD', 'Government bills', 'Oral Questions', 'Adjournment Proceedings', 'Adjournment',
    'Oral questions', 'Statements by Members', 'Government bills','ORDERS OF THE DAY', 'QUESTION PERIOD', 'ROUTINE PROCEEDINGS','Opposition motions',  
    'act', 'acts', 'statutes', 'legislature', 'schedule', 'tax','taxes','taxation','taxable','taxation','taxapyer','taxed','taxing','income','incomes',
    'bill amends the', 'enactment grants', 'enactment grants the', 'Opposition motions','declaration',
    'this enactment grants', 'enactment amends the','this enactment amends','Royal Assent','unanimous','consent','motion','move','issues',
    'this acts amends', 'act amends the', 'act amends', 'amends','amendment','political',
    'enactment', 'enactment amends', 'provisions', 'intermediary', 'Introduction of Visitors',
    'intermediaries', 'regulation', 'regulations', 'regulations to', 'Members’ Statements',
    'also amends', 'consequential amendments', 'amendments to', 'amendments', 'Business of the Senate',
    'amends', 'makes consequential amendments', 'enactment provides', 'Visitor in the Gallery',
    'provides', 'canada', 'council', 'councils', 'government','hon', 'Points of order',
    'senators','agreed','committee','senate','report','reports','presented', 'Report stage',
    'canadians','sector','legislation','bill','province','canadian','member', 'Visitors in the Gallery',
    'minister','ministers','madam','speaker','house','senator','statements','Third reading and adoption',
    'question','mr','mrs','ms','colleague','conservative','conservatives','liberal',
    'liberals','ndp','mp','mps','chair','members','canada bill','proceedings','parliament',
    'canada bill','canada enacts','department','is amended','canada act','amended'
    'district','electoral','the province','province of','amend','amended','canadian bill',
    'parliamentary','commons','legislative','federal','provincial','sencanada','repealed',
    'ca','exemption','pursuant','provinces','repeal','commencement','day','laws','canada obligations',
    'ontario','ontario enacts','ontario regulation','schedule ontario','ontario act','enacted','policies','issued','agreements','documents','code','may',
    'amends the','agreement','exempt','law','federal provincial','provision','month','canadian charter',
    'amending','consultations','is repealed','comply','parliamentarians','municiapl','the parliament',
    'act canada','an assault','parliamentarians act','parliament of','of parliament',
    'canada implementation','insertion','canada official','provincial legislation','section',
    'to canada','of parliamentarians','to amend','act canadian','parliament report','proceeding',
    'canada council','municipal act','statutes of','amend the','province will','province law',
    'canadian council', 'implement', 'stage',
    'order','debate','opposition','leader','party','honourable','questions','vote','policy','secratary',
    'honour','representative','governments','bills','please','thank','municipalities','colleagues',
    'national','committees','official','third','second','parliamentarian','assent','politicians','Second reading',
    'representatives','parliaments','oh','None','none','points of order','The Senate',"Private Members' Bills",
    ]


class BaseModel(models.Model):
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    func = models.CharField(max_length=50, default="")
    blockchainId = models.CharField(max_length=50, default="")
    locked_to_chain = models.BooleanField(default=False)
    publicKey = models.CharField(max_length=200, default="")
    signature = models.CharField(max_length=200, default="")
    chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    Region_obj = models.ForeignKey('posts.Region', related_name='%(class)s_region_obj', blank=True, null=True, on_delete=models.CASCADE)
    Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    Government_obj = models.ForeignKey('posts.Government', related_name='%(class)s_government_obj', blank=True, null=True, on_delete=models.SET_NULL)
    DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    
    class Meta:
        abstract = True

class Government(models.Model):
    object_type = 'Government'
    blockchainType = 'Region'
    modelVersion = models.CharField(max_length=50, default="v1")
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    func = models.CharField(max_length=50, default="")
    blockchainId = models.CharField(max_length=50, default="")
    locked_to_chain = models.BooleanField(default=False)
    publicKey = models.CharField(max_length=200, default="")
    signature = models.CharField(max_length=200, default="")
    Region_obj = models.ForeignKey('posts.Region', related_name='%(class)s_region_obj', blank=True, null=True, on_delete=models.CASCADE)
    Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    GovernmentNumber = models.IntegerField(default=0)
    SessionNumber = models.IntegerField(default=1)
    StartDate = models.DateTimeField(auto_now=False, auto_now_add=False, blank=False, null=True)
    gov_level = models.CharField(max_length=100, default="", blank=True, null=True) # Federal, Provincial, State, Greater Municipal, Municipal
    gov_type = models.CharField(max_length=100, default="Parliament", blank=True, null=True) # Parliament or Government
    
    # update fields
    # EndDate = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    
    def __str__(self):
        return 'GOVERNMENT:(%s-%s)' %(self.GovernmentNumber, self.SessionNumber)
    
    class Meta:
        ordering = ['-StartDate', '-GovernmentNumber','-SessionNumber']

    def end_previous(self, func):
        # dt = datetime.date.today()
        dt_now = now_utc()
        today = dt_now - datetime.timedelta(hours=dt_now.hour, minutes=dt_now.minute, seconds=dt_now.second, microseconds=dt_now.microsecond)
        try:
            previousCongress = Government.objects.filter(Country_obj=self.Country_obj, gov_level=self.gov_level, EndDate=None).exclude(id=self.id)[0]
            obj, update, updateData, is_new = get_model_and_update(self.object_type, obj=previousCongress)
            
            updateData['EndDate'] = today - datetime.timedelta(days=1)
            update.data = json.dumps(updateData)
            update.func = func
            update, u_is_new = update.save_if_new()
            if u_is_new:
                return [update]
        except:
            return []

    def version_v1_fields(self):
        fields = ['blockchainId', 'locked_to_chain', 'modelVersion', 'id', 'created', 'publicKey', 'signature', 'chamber', 'Region', 'GovernmentNumber', 'SessionNumber', 'StartDate', 'EndDate', 'gov_level']
        return fields
    
    def save(self, share=True):
        if self.id == '0':
            self.DateTime = self.StartDate
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Government, self).save()
    

    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        p = new_post(self)
        p.save(share=share)
        return p

class Keyphrase(BaseModel):
    object_type = "Keyphrase"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True

    pointerId = models.CharField(max_length=50, db_index=True, default="0")
    pointerType = models.CharField(max_length=50, default="0")
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='keyphrase_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    KeyphraseTrend_obj = models.ForeignKey('posts.KeyphraseTrend', blank=True, null=True, on_delete=models.SET_NULL)
    
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    Statement_obj = models.ForeignKey('posts.Statement', blank=True, null=True, on_delete=models.CASCADE)
    # DebateItem = models.ForeignKey('posts.DebateItem', blank=True, null=True, on_delete=models.CASCADE)
    # CommitteeItem = models.ForeignKey('posts.CommitteeItem', blank=True, null=True, on_delete=models.CASCADE)
    Bill_obj = models.ForeignKey('posts.Bill', blank=True, null=True, on_delete=models.SET_NULL)
    
    text = models.CharField(max_length=1000, default="", blank=True, null=True)

    # date_time = models.DateTimeField(auto_now=False, auto_now_add=False, blank=False, null=True)
    # gov_level = models.CharField(max_length=250, default="", blank=True, null=True)
    # chamber = models.CharField(max_length=250, default="", blank=True, null=True)
    # last_occured = models.DateTimeField(auto_now=False, auto_now_add=False, blank=False, null=True)
    # numberOfOccurences = models.IntegerField(default=0, blank=True, null=True)

    class Meta:
        ordering = ['-DateTime']
    
    def __str__(self):
        return 'KEYPHRASE:(%s/%s)' %(self.chamber, self.text)
    
    def set_chamber(self):
        if not self.chamber:
            if self.Statement_obj:

                self.chamber = self.Statement_obj.chamber
                # self.gov_level = self.DebatedItem.Debate.gov_level
                # if 'House' in self.DebateItem.Debate.Government.gov_level:
                #     self.chamber = 'House'
                # elif self.DebateItem.Debate.gov_level == 'Senate':
                #     self.chamber = 'Senate'
                # elif 'Assembly' in self.DebateItem.Debate.Government.gov_level:
                #     self.chamber = self.DebateItem.Debate.gov_level
                # elif self.DebateItem.Debate.gov_level == 'All':
                #     self.chamber = 'All'
            # elif self.CommitteeItem:
            #     self.chamber = self.CommitteeItem.chamber
                # self.gov_level = self.CommitteeItem.CommitteeMeeting.gov_level
                # if 'House' in self.CommitteeItem.CommitteeMeeting.gov_level:
                #     self.chamber = 'House'
                # elif self.CommitteeItem.CommitteeMeeting.gov_level == 'Senate':
                #     self.chamber = 'Senate'
                # elif 'Assembly' in self.CommitteeItem.CommitteeMeeting.gov_level:
                #     self.chamber = self.CommitteeItem.CommitteeMeeting.gov_level
                # elif self.CommitteeItem.CommitteeMeeting.gov_level == 'All':
                #     self.chamber = 'All'
            elif self.Bill_obj:
                self.chamber = self.Bill_obj.chamber
            self.save()

    def set_score(self, trend):
        # print('set_score')

        # print('trend.text', trend.text)
        # print('self.chamber', trend.chamber)
        # print('self.Country_obj', trend.Country_obj)
        # print('self.Region_obj', trend.Region_obj)
        # print('trend.DateTime', trend.DateTime)
        trend.last_occured = self.DateTime
        # print(trend.last_occured)
        trend.total_occurences += 1
        start_date = '%s-%s-%s' %(trend.last_occured.year, trend.last_occured.month, trend.last_occured.day)
        day = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        dayRange = datetime.datetime.strftime(day - datetime.timedelta(days=7), '%Y-%m-%d')
        sevenDays = datetime.datetime.strptime(dayRange, '%Y-%m-%d')
        # print('set score22')
        if trend.chamber == 'All':
            # print('a')
            # trend.recent_occurences = Statement.objects.filter(Country_obj=self.Country_obj, DateTime__gte=sevenDays, DateTime__lte=self.DateTime).filter(Q(Terms_array__icontains=trend.text)|Q(keyword_array__icontains=trend.text)).count()
            trend.recent_occurences = Keyphrase.objects.filter(text=self.text, Country_obj=self.Country_obj, DateTime__gte=sevenDays, DateTime__lte=self.DateTime).count()
        else:
            # print('else')
            # trend.recent_occurences = Statement.objects.filter(chamber=trend.chamber, Country_obj=self.Country_obj, DateTime__gte=sevenDays, DateTime__lte=self.DateTime).filter(Q(Terms_array__icontains=trend.text)|Q(keyword_array__icontains=trend.text)).count()
            trend.recent_occurences = Keyphrase.objects.filter(KeyphraseTrend_obj=trend, Region_obj=self.Region_obj, Country_obj=self.Country_obj, DateTime__gte=sevenDays, DateTime__lte=self.DateTime).count()
        # print('trend.recent_occurences', trend.recent_occurences)
        # print('set score 33')
        settime = datetime.datetime(2022, 10, 23, 1, 0).replace(tzinfo=pytz.UTC)
        t = trend.last_occured.replace(tzinfo=pytz.UTC) - settime
        secs = t.seconds * (100 / 86400) # converts 24hrs in seconds to 100
        r = ((t.days * 100) + secs) #1 day == 100
        trend.trend_score = r + trend.recent_occurences
        trend.save()
        # print('rend saved')
        # print('ro:', trend.recent_occurences)

    def set_trend(self):
        if self.text not in skipwords and len(self.text) >= 4:
            if not self.KeyphraseTrend_obj:
                # print()
                # print('--------')
                # print('set trend', self.text)
                # # if self.text.lower() == 'budget':
                #     # print('--------------------------------budget')
                # print('self.chamber', self.chamber)
                # print('self.Country_obj', self.Country_obj)
                # print('self.Region_obj', self.Region_obj)
                #     time.sleep(6)
                try:
                    trend = KeyphraseTrend.objects.filter(chamber=self.chamber, Country_obj=self.Country_obj, text__iexact=self.text[:100])[0]
                    # print('found trednd')
                except Exception as e:
                    # print(str(e))
                    # print()
                    # print('created trend')
                    trend = KeyphraseTrend(chamber=self.chamber, Region_obj=self.Region_obj, Country_obj=self.Country_obj, text=self.text[:100])
                    trend.first_occured = self.DateTime
                    trend.save()
                # if self.text.lower() == 'budget':
                #     tr = KeyphraseTrend.objects.filter(chamber=self.chamber,text='budget').count()
                    # print('budgetes111', tr)
                    # time.sleep(10)
                self.KeyphraseTrend_obj = trend
                # print('self.keyphraseTrend_obj', self.KeyphraseTrend_obj)
                self.save()
                # if self.text.lower() == 'budget':
                #     tr = KeyphraseTrend.objects.filter(chamber=self.chamber,text='budget').count()
                #     print('budgetes222', tr)
                    # time.sleep(10)
            # print('seta')
            self.set_score(self.KeyphraseTrend_obj)
            # print('self.keyphraseTrend_obj', self.KeyphraseTrend_obj)
            if 'Assembly' not in self.chamber:
                # print('all trend')
                try:
                    trend = KeyphraseTrend.objects.filter(Region_obj=self.Region_obj, Country_obj=self.Country_obj, chamber='All', text=self.text[:100])[0]
                    # print('trend found')
                except Exception as e:
                    # print(str(e))
                    trend = KeyphraseTrend(Region_obj=self.Region_obj, Country_obj=self.Country_obj, chamber='All', text=self.text[:100])
                    trend.first_occured = self.DateTime
                    trend.save()
                # print('setb')
                self.set_score(trend)
                # if self.text.lower() == 'budget':
                #     tr = KeyphraseTrend.objects.filter(text='budget').count()
                #     print('budgetes33', tr)
                #     time.sleep(15)
        # print('done done self.keyphraseTrend_obj', self.KeyphraseTrend_obj)

    def version_v1_fields(self):
        fields = ['blockchainId', 'locked_to_chain', 'modelVersion', 'id', 'created', 'publicKey', 'signature', 'Region', 'KeyphraseTrend', 'Government', 'DebateItem', 'CommitteeItem', 'Bill', 'text', 'DateTime', 'gov_level', 'chamber']
        return fields
    
    def save(self, share=False):
        # print('start save', self.locked_to_chain)
        if self.id == '0':
            # if not self.Region_obj:
            pointer = get_dynamic_model(self.pointerType, list=False, id=self.pointerId)
            self.Region_obj = pointer.Region_obj
            self.Country_obj = pointer.Country_obj
            self.Government_obj = pointer.Government_obj
            self.chamber = pointer.chamber
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Keyphrase, self).save()
        #     print('object saved')
        #     print('111self.keyphraseTrend_obj', self.KeyphraseTrend_obj)
        # else:
        #     print('not saved')
    

    def delete(self):
        superDelete(self)


class KeyphraseTrend(BaseModel):
    object_type = "KeyphraseTrend"
    blockchainType = 'NoChain'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    pointerId = models.CharField(max_length=50, db_index=True, default="0")
    pointerType = models.CharField(max_length=50, default="0")
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='keyphrasetrend_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    text = models.CharField(max_length=300, default="", blank=True, null=True)
    total_occurences = models.IntegerField(default=0, blank=True, null=True)
    recent_occurences = models.IntegerField(default=0, blank=True, null=True)
    first_occured = models.DateTimeField(auto_now=False, auto_now_add=False, blank=False, null=True)
    last_occured = models.DateTimeField(auto_now=False, auto_now_add=False, blank=False, null=True)
    # trendScore = models.BigIntegerField(default=0, blank=True, null=True)
    trend_score = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    # gov_level = models.CharField(max_length=250, default="", blank=True, null=True)
    # chamber = models.CharField(max_length=250, default="", blank=True, null=True)

    class Meta:
        ordering = ['-trend_score', '-last_occured','recent_occurences', 'total_occurences']
    
    def __str__(self):
        return 'KEYPHRASETREND:(%s/%s)' %(self.chamber, self.text)

    def get_absolute_url(self):
        # return 'xxx'
        return "%s/topic/%s" %(self.Country_obj.Name, self.text)

    def version_v1_fields(self):
        fields = ['blockchainId', 'locked_to_chain', 'modelVersion', 'id', 'created', 'Government', 'publicKey', 'signature', 'Region', 'text', 'total_occurences', 'recent_occurences', 'first_occured', 'last_occured', 'trend_score', 'gov_level', 'chamber']
        return fields

    def save(self, share=False):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(KeyphraseTrend, self).save()
    

    def delete(self):
        for k in Keyphrase.objects.filter(KeyphraseTrend_obj=self):
            k.delete()
        superDelete(self)


class Agenda(BaseModel):
    object_type = "Agenda"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='agenda_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # gov_level = models.CharField(max_length=250, default="", blank=True, null=True)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    # province = models.ForeignKey('accounts.Province', blank=True, null=True, on_delete=models.SET_NULL)
    # gov_level = models.CharField(max_length=250, default="", blank=True, null=True)

    # ---updates
    # EndDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # Bill_objs = models.ManyToManyField('posts.Bill', blank=True, related_name='agenda_bills')
    # current_status = models.CharField(max_length=250, default="", blank=True, null=True)
    # NextDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # PreviousDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # VideoCode = models.IntegerField(default=0, blank=True, null=True)
    # VideoURL = models.URLField(null=True, blank=True)

    def __str__(self):
        return 'AGENDA:%s-%s' %(self.DateTime, self.chamber)

    class Meta:
        ordering = ['-DateTime']

    def get_absolute_url(self):
        est = pytz.timezone('US/Eastern')
        return "/agenda-item/%s/%s" %(self.chamber, self.DateTime.astimezone(est).strftime("%Y-%m-%d/%H:%M"))
        # return "/agenda-item/%s-%s-%s/%s:%s" %(self.date_time.astimezone(est).year, self.date_time.astimezone(est).month, self.date_time.astimezone(est).day, self.date_time.astimezone(est).hour, self.date_time.astimezone(est).minute)

    @property
    def is_today(self):
        def convert_to_localtime(utctime):
            fmt = '%Y-%m-%d'
            utc = utctime.replace(tzinfo=pytz.UTC)
            localtz = utc.astimezone(timezone.get_current_timezone())
            return localtz.strftime(fmt)
        return str(datetime.date.today()) == convert_to_localtime(self.DateTime)
        
    def is_last(self):
        a = Agenda.objects.first()
        if self == a:
            return True
        else:
            return False


    def get_item(self, bill):
        print('get_item')
        a = AgendaItem.objects.filter(Agenda_obj=self, Bill_obj=bill)
        h = Debate.objects.filter(Agenda_obj=self)
        for key, value in h.list_all_terms:
            if key == a.text:
                break
        return key

    def version_v1_fields(self):
        fields = ['blockchainId', 'locked_to_chain', 'modelVersion', 'id', 'created', 'publicKey', 'signature', 'chamber', 'Region', 'DateTime', 'EndDateTime', 'Organization', 'Government', 'gov_level', 'VideoURL', 'VideoCode', 'current_status', 'NextDateTime', 'PreviousDateTime']
        return fields
    
    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Agenda, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        p = new_post(self)
        p.save(share=share)
        return p

class AgendaTime(BaseModel):
    object_type = "AgendaTime"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='agendatime_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    Agenda_obj = models.ForeignKey(Agenda, blank=True, null=True, on_delete=models.CASCADE)
    
    # updates
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    Bill_objs = models.ManyToManyField('posts.Bill', blank=True, related_name='agendaTime_bills')
    
    def __str__(self):
        return 'AGENDATIME:%s' %(self.DateTime)

    def get_absolute_url(self):
        est = pytz.timezone('US/Eastern')
        return "/agenda-item/%s" %(self.DateTime.astimezone(est).strftime("%Y-%m-%d/%H:%M"))
        # return "/agenda-item/%s-%s-%s/%s:%s" %(self.date_time.astimezone(est).year, self.date_time.astimezone(est).month, self.date_time.astimezone(est).day, self.date_time.astimezone(est).hour, self.date_time.astimezone(est).minute)

    class Meta:
        ordering = ['-DateTime']

    def version_v1_fields(self):
        fields = ['blockchainId', 'locked_to_chain', 'modelVersion', 'id', 'created', 'publicKey', 'signature', 'chamber', 'Region', 'DateTime', 'EndDateTime', 'Organization', 'Government', 'gov_level', 'VideoURL', 'VideoCode', 'current_status', 'NextDateTime', 'PreviousDateTime']
        return fields
    
    def save(self, share=True):
        if self.id == '0':
            self.Government_obj = self.Agenda_obj.Government_obj
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(AgendaTime, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        p = new_post(self)
        # if self.agenda.gov_level == 'Senate':
        #     p.organization = 'Senate'
        # else:
        #     p.organization = 'House'
        p.save(share=share)
        return p

class AgendaItem(BaseModel):
    object_type = "AgendaItem"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='agendaitem_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    Agenda_obj = models.ForeignKey(Agenda, blank=True, null=True, on_delete=models.CASCADE)
    AgendaTime_obj = models.ForeignKey(AgendaTime, blank=True, null=True, on_delete=models.CASCADE)
    Bill_obj = models.ForeignKey('posts.Bill', blank=True, null=True, on_delete=models.SET_NULL)
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    Text = models.CharField(max_length=250, default="", blank=True, null=True)
    
    # organization = models.CharField(max_length=250, default="", blank=True, null=True)
    # gov_level = models.CharField(max_length=250, default="", blank=True, null=True)
    
    position = models.IntegerField(default=0, blank=True, null=True)
    
    has_post = models.BooleanField(default=False)

    def __str__(self):
        return 'AGENDAITEM:%s-%s' %(self.Text, self.position)

    def get_absolute_url(self):
        est = pytz.timezone('US/Eastern')
        return "/agenda-item/%s/%s" %(self.chamber, self.DateTime.astimezone(est).strftime("%Y-%m-%d/%H:%M"))
        # return "/agenda-item/%s-%s-%s/%s:%s" %(self.date_time.astimezone(est).year, self.date_time.astimezone(est).month, self.date_time.astimezone(est).day, self.date_time.astimezone(est).hour, self.date_time.astimezone(est).minute)

    class Meta:
        ordering = ['position','DateTime', 'created',] #required ordering for agenda_card

    def save(self, share=True):
        if self.id == '0':
            self.Government_obj = self.Agenda_obj.Government_obj
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(AgendaItem, self).save()
    

    def delete(self):
        superDelete(self)

class Bill(BaseModel):
    object_type = "Bill"
    blockchainType = 'Region'
    modelVersion = models.CharField(max_length=50, default="v1")
    # automated = True
    Person_obj = models.ForeignKey('posts.Person', blank=True, null=True, on_delete=models.CASCADE) #sponsor
    CoSponsor_objs = models.ManyToManyField('posts.Person', blank=True, related_name='co_sponsors')
    GovIden = models.IntegerField(default=0, blank=True, null=True)
    LegisLink = models.URLField(null=True, blank=True) #official link to text of bill
    Started = models.DateTimeField(auto_now=False, auto_now_add=True, blank=True, null=True)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    # province = models.ForeignKey('accounts.Province', blank=True, null=True, on_delete=models.SET_NULL)
    absolute_url = models.CharField(max_length=50, default="", blank=True, null=True)
    type = models.CharField(max_length=30, default="Bill", blank=True, null=True) # bill or resolution
    
    has_senate = models.BooleanField(default=True)
    
    NumberCode = models.CharField(max_length=20, default="", blank=True, null=True)
    amendedNumberCode = models.CharField(max_length=20, default="", blank=True, null=True) #removes dash for search
    NumberPrefix = models.CharField(max_length=20, default="", blank=True, null=True)
    Number = models.IntegerField(default=0, blank=True, null=True)
    
    # LongTitleEn = models.CharField(max_length=1000, default="", blank=True, null=True)
    # LongTitleFr = models.CharField(max_length=1000, default="", blank=True, null=True)
    # ShortTitle = models.CharField(max_length=1000, default="", blank=True, null=True)
    
    Title = models.CharField(max_length=1000, default="", blank=True, null=True)
    LongTitle = models.CharField(max_length=1000, default="", blank=True, null=True)
    # StatusId = models.IntegerField(default=0, blank=True, null=True)
    # StatusNameFr = models.CharField(max_length=1000, default="", blank=True, null=True)
    # LatestCompletedMajorStageName = models.CharField(max_length=70, default="", blank=True, null=True)
    # LatestCompletedMajorStagechamberName = models.CharField(max_length=71, default="", blank=True, null=True)
    # GovernmentNumber = models.IntegerField(default=0, blank=True, null=True)
    # SessionNumber = models.IntegerField(default=0, blank=True, null=True)
    BillDocumentTypeName = models.CharField(max_length=56, default="", blank=True, null=True)
    IsGovernmentBill = models.CharField(max_length=10, default="", blank=True, null=True)
    # OriginatingchamberName = models.CharField(max_length=30, default="", blank=True, null=True)
    IsHouseBill = models.CharField(max_length=10, default="", blank=True, null=True)
    IsSenateBill = models.CharField(max_length=10, default="", blank=True, null=True)
    IsVoterBill = models.CharField(max_length=10, default="", blank=True, null=True)
    # SponsorSenateSystemAffiliationId = models.IntegerField(default=0, blank=True, null=True) #not used
    SponsorPersonId = models.IntegerField(default=0, blank=True, null=True) #not used
    # SponsorPersonOfficialFirstName = models.CharField(max_length=100, default="", blank=True, null=True) #not used
    # SponsorPersonOfficialLastName = models.CharField(max_length=100, default="", blank=True, null=True) #not used
    # SponsorPersonName = models.CharField(max_length=100, default="", blank=True, null=True) 
    # SponsorPersonShortHonorific = models.CharField(max_length=10, default="", blank=True, null=True) #not used
    # SponsorAffiliationTitle = models.CharField(max_length=255, default="", blank=True, null=True) #not used
    # SponsorAffiliationRoleName = models.CharField(max_length=154, default="", blank=True, null=True) #not used
    # SponsorConstituencyName = models.CharField(max_length=153, default="", blank=True, null=True) #not used
    
    # --updates
    # keyword_array = ArrayField(models.CharField(max_length=50, blank=True, null=True, default=[]), size=20, null=True, blank=True)
    # Status = models.CharField(max_length=1000, default="", blank=True, null=True)
    # # LatestCompletedMajorStageId = models.IntegerField(default=0, blank=True, null=True)
    # # OngoingStageId = models.IntegerField(default=0, blank=True, null=True)
    # OngoingStageName = models.CharField(max_length=72, default="", blank=True, null=True)
    # # LatestCompletedBillStageId = models.IntegerField(default=0, blank=True, null=True)
    # LatestCompletedBillStageName = models.CharField(max_length=73, default="", blank=True, null=True)
    # LatestCompletedBillStageNameWithChamberSuffix = models.CharField(max_length=113, default="", blank=True, null=True)
    # LatestCompletedBillStageChamberName = models.CharField(max_length=74, default="", blank=True, null=True)
    # LatestCompletedBillStageDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # # inCommittee_objs = models.ManyToManyField('posts.Committee', blank=True, related_name='committees')
    # LatestBillEventDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # LatestBillEventNumberOfAmendments = models.IntegerField(default=0, blank=True, null=True)
    # LatestBillEventChamberName = models.IntegerField(default=0, blank=True, null=True)
    # # # LatestBillEventAdditionalInformationEn = models.TextField(blank=True, null=True)
    # # # LatestBillEventAdditionalInformationFr = models.TextField(blank=True, null=True)
    # # EndDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    
    
    # BillFormName = models.CharField(max_length=100, default="", blank=True, null=True)
    # IsSessionOngoing = models.CharField(max_length=100, default="", blank=True, null=True)
    # summary = models.TextField(blank=True, null=True)
    # first_reading_html = models.TextField(blank=True, null=True)
    # first_reading_nav = models.TextField(blank=True, null=True)
    # second_reading_html = models.TextField(blank=True, null=True)
    # second_reading_nav = models.TextField(blank=True, null=True)
    # third_reading_html = models.TextField(blank=True, null=True)
    # third_reading_nav = models.TextField(blank=True, null=True)
    # royal_assent_html = models.TextField(blank=True, null=True)
    # royal_assent_nav = models.TextField(blank=True, null=True)
    # bill_text_html = models.TextField(blank=True, null=True)
    # bill_text_nav = models.TextField(blank=True, null=True)
    # bill_text_version = models.CharField(max_length=10, default="", blank=True, null=True)
    # summarySpren = models.CharField(max_length=1000, default="", blank=True, null=True)
    # steelmanSprenFor = models.CharField(max_length=1000, default="", blank=True, null=True)
    # steelmanSprenAgainst = models.CharField(max_length=1000, default="", blank=True, null=True)
    # spren_version = models.CharField(max_length=10, default="", blank=True, null=True)
    # mark_for_deletion = models.BooleanField(default=False)

    def __str__(self):
        return 'BILL:(%s-%s) %s' %(self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.NumberCode)

    class Meta:
        ordering = ['-created', "-NumberCode"]

    def get_absolute_url(self):
        return "/bill/%s/%s/%s/%s/%s" %(self.Country_obj.Name, self.chamber, self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.NumberCode)
    
    def get_update_url(self):
        return "/utils/update_bill/%s" %(self.id)

    def get_fields(self):
        return ['%s: %s' %(field.name, field.value_to_string(self)) for field in Bill._meta.fields[:61]]
    
    def choose_nav(self, nav):
        # print(nav)
        try:
            d = json.loads(nav)
            return list(d.items())
        except Exception as e:
            print(str(e))
            return None

    def get_nav(self):
        # if self.royal_assent_nav:
        #     result = self.choose_nav(self.royal_assent_nav)
        # elif self.third_reading_nav:
        #     result = self.choose_nav(self.third_reading_nav)
        # elif self.second_reading_nav:
        #     result = self.choose_nav(self.second_reading_nav)
        # elif self.first_reading_nav:
        #     result = self.choose_nav(self.first_reading_nav)
        # # print(result)
        if self.bill_text_nav:
            d = json.loads(self.bill_text_nav)
            result = list(d.items())
        else:
            result = None
        return result

    def remove_tags(text):
        TAG_RE = re.compile(r'<[^>]+>')
        return TAG_RE.sub('', text)

    def get_latest_version(self):
        # v = BillVersion.objects.filter(Bill_obj=self, current=True)[0]
        return Post.objects.filter(BillVersion_obj__Bill_obj=self, BillVersion_obj__current=True)[0]

    def get_bill_keywords(self, p):
        #not running after text is received because it takes too long, keywords is title and sponsor only
        def strip_tags(text):
            TAG_RE = re.compile(r'<[^>]+>')
            return TAG_RE.sub('', text)
        if self.bill_text_html:
            text = self.bill_text_html.replace(self.bill_text_nav, '')
            text = strip_tags(text)
            self, p = get_keywords(self, p, text)

            # stop_words = set(stopwords.words('english'))
            # stop_words_french = set(stopwords.words('french'))
            # kw_model = KeyBERT()
            # stop_w = []
            # for i in stop_words:
            #     stop_w.append(i)
            # # keywords = kw_model.extract_keywords(text)
            # # skipwords = ['act', 'acts', 'statutes', 'legislature', 'schedule', 'bill amends the', 'enactment grants', 'enactment grants the', 'this enactment grants', 'enactment amends the','this enactment amends', 'this acts amends', 'act amends the', 'act amends', 'enactment', 'enactment amends', 'provisions', 'intermediary', 'intermediaries', 'regulation', 'regulations', 'regulations to', 'also amends', 'consequential amendments', 'amendments to', 'amendments', 'amends', 'makes consequential amendments', 'enactment provides', 'provides']
            # self.keywords = []
            # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(1, 1), stop_words=stop_w)
            # n = 0
            # for i, r in x:
            #     if i not in skipwords and i not in stop_words and i not in stop_words_french and i not in self.keywords and n <= 10:
            #         self.keywords.append(i)
            #         p.keywords.append(i)
            #         stop_w.append(i)
            #         n += 1
            #         # print(i, r)
            # print('get bill keywords', datetime.datetime.now())
            # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(2, 2), stop_words=stop_w)
            # print('finish bill keywords', datetime.datetime.now())
            # n = 0
            # for i, r in x:
            #     if i not in skipwords and i not in self.keywords and n <= 5:
            #         self.keywords.append(i)
            #         p.keywords.append(i)
            #         n += 1
                    # print(i, r)
            # print()
            # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(3, 3), stop_words=None)
            # n = 0
            # for i, r in x:
            #     if i not in skipwords and i not in self.keywords and n <= 5:
            #         self.keywords.append(i)
            #         n += 1
            #         print(i)
            # print()
            self.save()
            p.save()
        return p

    def update_keywords(self, p, share=True):
        # p.keywords = []
        if self.Person_obj and self.Person_obj not in p.keyword_array:
            p.keyword_array.append(self.Person_obj.FullName)
            try:
                keyphrase = Keyphrase.objects.filter(text=self.Person_obj.FullName)[0]
                keyphrase.DateTime = self.DateTime
                keyphrase.Bill_obj = self
                keyphrase.save(share=share)
            except:
                print('creating key1')
                keyphrase = Keyphrase(pointerType=self.Person_obj.object_type, pointerId=self.Person_obj.id, text=self.Person_obj.FullName, DateTime=self.DateTime) 
                keyphrase.chamber = self.chamber
                keyphrase.Bill_obj = self
                keyphrase.save(share=share)
        if self.Title and self.Title not in p.keyword_array:
            title = '*%s Bill %s (%s-%s): %s' %(self.chamber.replace('-Assembly', ''), self.amendedNumberCode, self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.Title)
            p.keyword_array.append(title)
            # print(title)
            try:
                keyphrase = Keyphrase.objects.filter(pointerType=self.object_type, pointerId=self.id, chamber=self.chamber, text=title[:300])[0]
                keyphrase.DateTime = self.DateTime
                keyphrase.Bill_obj = self
                keyphrase.save(share=share)
                # print('key found')
            except:
                print('creating key2')
                keyphrase = Keyphrase(pointerType=self.object_type, pointerId=self.id, chamber=self.chamber, text=title[:300], DateTime=self.DateTime) 
                keyphrase.Bill_obj = self
                keyphrase.save(share=share)
                print('key created')
        elif self.LongTitle not in p.keyword_array:
            if len(self.LongTitle) > 980:
                title = self.LongTitle[:977] + '...'
            else:
                title = self.LongTitle
            title = '*%s Bill %s (%s-%s): %s' %(self.chamber.replace('-Assembly', ''), self.amendedNumberCode, self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, title[:300])
            p.keyword_array.append(title)
            try:
                keyphrase = Keyphrase.objects.filter(pointerType=self.object_type, pointerId=self.id, chamber=self.chamber, text=title[:300])[0]
                keyphrase.DateTime = self.DateTime
                keyphrase.Bill_obj = self
                keyphrase.save(share=share)
            except:
                print('creating key3')
                keyphrase = Keyphrase(pointerType=self.object_type, pointerId=self.id, chamber=self.chamber, text=title[:300], DateTime=self.DateTime) 
                keyphrase.Bill_obj = self
                keyphrase.save(share=share)
        p.save()
        # p = self.get_bill_keywords(p)

    def save(self, share=False):
        if self.id == '0':
            self.amendedNumberCode = self.NumberCode.replace('-', '')
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Bill, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=False):
        p = new_post(self)
        # p.chamber = self.chamber
        # p.gov_level = self.Government_obj.gov_level
        # self.absolute_url = self.get_absolute_url()
        # self.save()
        p.save(share=share)
        self.update_keywords(p, share=share)
        return p
    
    def update_post_time(self):
        # print('running update time')
        p = find_post(self)
        # if p.date_time != self.LatestBillEventDateTime:
        #     users = User.objects.filter(follow_bill=self)
        #     for u in users:
        #         if self.ShortTitle:
        #             title = 'Bill %s, %s' %(self.NumberCode, self.ShortTitle)
        #         else:
        #             title = 'Bill %s, %s' %(self.NumberCode, self.LongTitleEn)
        #         u.alert(title, str(self.get_absolute_url()), None)
        p.DateTime = self.DateTime
        # p.chamber = self.chamber
        p.set_score()
        # p.save(share=share)
        if not self.keyword_array:
            self.update_keywords(p)
        # p.save()
        versions = Post.objects.filter(BillVersion_obj__Bill_obj=self, BillVersion_obj__empty=False)
        for v in versions:
            v.BillVersion_obj.create_post()

    def hasSummarySpren(self):
        try:
            return Spren.objects.filter(Bill_obj=self, type='summary')[0]
        except:
            return None
    def hasSteelForSpren(self):
        try:
            return Spren.objects.filter(Bill_obj=self, type='steelfor')[0]
        except:
            return None
    def hasSteelAgainstSpren(self):
        try:
            return Spren.objects.filter(Bill_obj=self, type='steelagainst')[0]
        except:
            return None

    def getSpren(self, force):
        print('start getSpren')
        from posts.utils import get_chatgpt_model, get_token_count
        def strip_tags(text):
            TAG_RE = re.compile(r'<[^>]+>')
            return TAG_RE.sub('', text)
        try:
            text = self.bill_text_html.replace(self.bill_text_nav, '')
            text = strip_tags(text)
            model, text = get_chatgpt_model(text)
            num_tokens = get_token_count(text, "cl100k_base")
            print('tokens:', num_tokens)
            print(model)
            import os
            from openai import OpenAI   
            import time
            api_key = ""
            print('summary')
            try:
                spren = Spren.objects.filter(bill=self, type='summary')[0]
                new = False
            except:
                spren = Spren(bill=self, type='summary')
                new = True
            if new or force:
                client = OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                model = model,
                temperature=0.1,
                max_tokens=500,
                # stream=True,
                messages=[
                    {"role": "system", "content": "You are a non-conversational computer assistant."},
                    {"role": "user", "content": "summarize this to an 18 year old: " + text}
                
                    # {"role": "user", "content": "provide a steelman argument in favor of this: " + text}
                    # {"role": "user", "content": "provide a steelman argument opposing this and use right wing anti-government talking points: " + text}
                ]
                )
                print(completion.choices[0].message.content)
                print(len(completion.choices[0].message.content))
                spren.content = completion.choices[0].message.content[:3000]
                spren.save()
                time.sleep(2)


            print('steelfor')
            try:
                spren = Spren.objects.filter(bill=self, type='steelfor')[0]
                new = False
            except:
                spren = Spren(bill=self, type='steelfor')
                new = True
            if new or force:
                client = OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                model = model,
                temperature=0.1,
                max_tokens=500,
                # stream=True,
                messages=[
                    {"role": "system", "content": "You are a non-conversational computer assistant."},
                    # {"role": "user", "content": "summarize this to an 18 year old: " + text}
                
                    {"role": "user", "content": "provide a steelman argument in favor of this: " + text}
                    # {"role": "user", "content": "provide a steelman argument opposing this and use right wing anti-government talking points: " + text}
                ]
                )
                print(completion.choices[0].message.content)
                print(len(completion.choices[0].message.content))
                spren.content = completion.choices[0].message.content[:3000]
                spren.save()
                time.sleep(2)
            print('steel against')
            try:
                spren = Spren.objects.filter(bill=self, type='steelagainst')[0]
                new = False
            except:
                spren = Spren(bill=self, type='steelagainst')
                new = True
            if new or force:
                client = OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                model = model,
                temperature=0.1,
                max_tokens=500,
                # stream=True,
                messages=[
                    {"role": "system", "content": "You are a non-conversational computer assistant."},
                    # {"role": "user", "content": "summarize this to an 18 year old: " + text}
                
                    # {"role": "user", "content": "provide a steelman argument in favor of this: " + text}
                    {"role": "user", "content": "provide a steelman argument opposing this and use right wing anti-government talking points: " + text}
                ]
                )
                print(completion.choices[0].message.content)
                print(len(completion.choices[0].message.content))
                spren.content = completion.choices[0].message.content[:3000]
                spren.save()
            print('saved')
            # u = User.objects.filter(username='Sozed')[0]
            # title = 'Bill %s Spren available' %(self.NumberCode)
            # u.alert(title, str(self.get_absolute_url()), None)
        except Exception as e:
            print(str(e))

class BillVersion(BaseModel):
    object_type = "BillVersion"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='billversion_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    Bill_obj = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.CASCADE)
    NumberCode = models.CharField(max_length=100, default="", blank=True, null=True)
    # province = models.ForeignKey('accounts.Province', blank=True, null=True, on_delete=models.SET_NULL)
    # GovernmentNumber = models.IntegerField(default=0, blank=True, null=True)
    # SessionNumber = models.IntegerField(default=0, blank=True, null=True)
    Version = models.CharField(max_length=100, default="", blank=True, null=True)
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    Summary = models.TextField(blank=True, null=True)
    TextHtml = models.TextField(blank=True, null=True)
    TextNav = models.TextField(blank=True, null=True)
    Current = models.BooleanField(default=False)
    empty = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['empty', '-DateTime']

    def __str__(self):
        return 'BILLVERSION:(%s-%s) %s-%s' %(self.Bill_obj.Government_obj.GovernmentNumber, self.Bill_obj.Government_obj.SessionNumber, self.NumberCode, self.Version)

    def get_absolute_url(self):
        return '%s?reading=LatestReading' %(self.Bill_obj.get_absolute_url())


    def get_nav(self):
        print('get nav')
        if self.TextNav:
            d = json.loads(self.TextNav)
            result = list(d.items())
        else:
            result = None
        return result
    
    def get_bill_keywords(self, p):
        #not running after text is received because it takes too long, keywords is title and sponsor only
        def strip_tags(text):
            TAG_RE = re.compile(r'<[^>]+>')
            return TAG_RE.sub('', text)
        if self.TextHtml:
            text = self.TextHtml.replace(self.TextNav, '')
            text = strip_tags(text)
            self, p = get_keywords(self, p, text)

            self.save()
            # p.save()
        return self, p

    def save(self, share=True):
        if self.id == '0':
            if not self.DateTime:
                self.DateTime = self.Bill_obj.DateTime
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(BillVersion, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        p = new_post(self)
        print(p)
        # p.chamber = self.Bill_obj.chamber
        # p.gov_level = self.Government_obj.gov_level
        if self.DateTime:
            p.DateTime = self.DateTime
            # print(self.dateTime)
        elif self.Bill_obj.Started:
            p.DateTime = self.Bill_obj.Started
            # print(self.bill.started)
        else:
            try:
                if self.bill.PassedFirstchamberFirstReadingDateTime < self.bill.PassedSecondchamberFirstReadingDateTime:
                    self.bill.Started = self.bill.PassedFirstchamberFirstReadingDateTime
                    self.bill.save()
                    p.DateTime = self.bill.Started
                    # print(self.bill.started)
                elif self.bill.PassedSecondchamberFirstReadingDateTime < self.bill.PassedFirstchamberFirstReadingDateTime:
                    self.bill.Started = self.bill.PassedSecondchamberFirstReadingDateTime
                    self.bill.save()
                    p.DateTime = self.bill.started
            except Exception as e:
                print(str(e))
                self.Bill_obj.Started = now_utc()
                self.Bill_obj.save()
                p.DateTime = self.Bill_obj.Started
            # print(self.bill.started)
        print('p.keywords', p.keyword_array)
        p.keyword_array = []
        # self, p = self.get_bill_keywords(p):
        # if p.keyword_array:
        #     p.keyword_array.clear()
        # p.keyword_array.append('%s?current=%s' %(self.Bill_obj.NumberCode, str(self.Current)))
        p.save(share=share)
        return p

class BillAction(BaseModel):
    object_type = "BillAction"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='billaction_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    Bill_obj = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.CASCADE)
    Code = models.CharField(max_length=100, default="", blank=True, null=True)
    # province = models.ForeignKey('accounts.Province', blank=True, null=True, on_delete=models.SET_NULL)
    # ParliamentNumber = models.IntegerField(default=0, blank=True, null=True)
    # SessionNumber = models.IntegerField(default=0, blank=True, null=True)
    # version = models.CharField(max_length=100, default="", blank=True, null=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    Text = models.TextField(blank=True, null=True)
    # reading_html = models.TextField(blank=True, null=True)
    # reading_nav = models.TextField(blank=True, null=True)
    # current = models.BooleanField(default=False)
    # empty = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-Code', '-DateTime']

    def __str__(self):
        return 'BILLACTION:(%s-%s) %s-%s' %(self.Bill_obj.GovernmentNumber, self.Bill_obj.SessionNumber, self.Code)

    # def get_absolute_url(self):
    #     return '%s?reading=LatestReading' %(self.bill.get_absolute_url())

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(BillAction, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        p = new_post(self)
        # p.chamber = self.Bill.chamber
        # p.gov_level = self.Government.gov_level
        if self.DateTime:
            p.DateTime = self.DateTime
            # print(self.dateTime)
        elif self.Bill_obj.Started:
            p.DateTime = self.Bill_obj.Started
            # print(self.bill.started)
        else:
            try:
                if self.bill.PassedFirstchamberFirstReadingDateTime < self.bill.PassedSecondchamberFirstReadingDateTime:
                    self.bill.started = self.bill.PassedFirstchamberFirstReadingDateTime
                    self.bill.save()
                    p.DateTime = self.bill.started
                    # print(self.bill.started)
                elif self.bill.PassedSecondchamberFirstReadingDateTime < self.bill.PassedFirstchamberFirstReadingDateTime:
                    self.bill.started = self.bill.PassedSecondchamberFirstReadingDateTime
                    self.bill.save()
                    p.DateTime = self.bill.started
            except:
                self.bill.started = datetime.datetime.now()
                self.bill.save()
                p.DateTime = self.bill.started
            # print(self.bill.started)
        p.save(share=share)
        return p

class Meeting(BaseModel):
    object_type = "Meeting"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='meeting_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)  
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    meeting_type = models.CharField(max_length=100, default="", blank=True, null=True) # Debate, Committee
    Agenda_obj = models.ForeignKey(Agenda, blank=True, null=True, on_delete=models.SET_NULL)
    PubIden = models.IntegerField(default=0, blank=True, null=True)
    GovPage = models.URLField(null=True, blank=True)
    Title = models.CharField(max_length=50, default="", blank=True, null=True)
    


    # GovernmentNumber = models.IntegerField(default=0, blank=True, null=True)
    # SessionNumber = models.IntegerField(default=0, blank=True, null=True)
    PublicationId = models.IntegerField(default=0, blank=True, null=True)
    # gov_level = models.CharField(max_length=100, default="", blank=True, null=True)
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # PdfURL = models.URLField(null=True, blank=True)
    IsTelevised = models.IntegerField(default=0, blank=True, null=True)
    IsAudioOnly = models.IntegerField(default=0, blank=True, null=True)
    TypeId = models.IntegerField(default=0, blank=True, null=True)
    HtmlURL = models.URLField(null=True, blank=True)
    MeetingIsForSenateOrganization = models.CharField(max_length=100, default="", blank=True, null=True)
    # keyword_array = ArrayField(models.CharField(max_length=50, blank=True, null=True, default=[]), size=20, null=True, blank=True)
    
    # PublicationDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    
    # --updates
    # VideoURL = models.URLField(null=True, blank=True)
    # has_transcript = models.BooleanField(default=False)
    # PdfURL = models.CharField(max_length=200, default="", blank=True, null=True)
    
    
    # Subjects_array = ArrayField(models.CharField(max_length=100, blank=True, null=True, default='[]'), size=100, null=True, blank=True)
    # Terms_array = ArrayField(models.CharField(max_length=1000, blank=True, null=True, default='[]'), size=100, null=True, blank=True)
    # Terms_json = models.TextField(default='', blank=True, null=True)
    # # people = ArrayField(models.ForeignKey(Person, blank=True, null=True, on_delete=models.SET_NULL), size=100, null=True, blank=True)
    # People_objs = models.ManyToManyField('accounts.Person', blank=True, related_name='debate_people')
    # People_json = models.TextField(default='', blank=True, null=True)
    # completed_model = models.BooleanField(default=False)

    # Bill_obj = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.SET_NULL)
    # Committee_obj = models.ForeignKey('posts.Committee', blank=True, null=True, on_delete=models.CASCADE)
    # CurrentChair_obj = models.ForeignKey('accounts.Person', related_name='current_chair', blank=True, null=True, on_delete=models.CASCADE)
    # PubIden = models.IntegerField(default=0, blank=True, null=True)
    # GovPage = models.URLField(null=True, blank=True)
    # # Title = models.CharField(max_length=1000, default="", blank=True, null=True)
    # Code = models.CharField(max_length=50, default="", blank=True, null=True)
    # # ItemId = models.IntegerField(default=0, blank=True, null=True)
    # StartDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # EndDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)

    # EvidenceLink = models.URLField(null=True, blank=True)
    # StudiesLink = models.URLField(null=True, blank=True)
    # Minutes = models.URLField(null=True, blank=True)
    # EmbedURL = models.URLField(null=True, blank=True)
    # previewURL = models.CharField(max_length=450, default="", blank=True, null=True)
    # TimeRange = models.CharField(max_length=251, default="", blank=True, null=True)
    # Location = models.CharField(max_length=252, default="", blank=True, null=True)
    # GovURL = models.CharField(max_length=253, default="", blank=True, null=True)
    # TranscriptURL = models.URLField(null=True, blank=True)

    # Event = models.CharField(max_length=102, default="", blank=True, null=True)
    # Report = models.TextField(blank=True, null=True)
    # ReportLink = models.URLField(null=True, blank=True)


    def __str__(self):
        return 'MEETING:(%s-%s) %s' %(self.id, self.id, self.Title)
    
    class Meta:
        ordering = ['-DateTime']

    def get_absolute_url(self):
        # if 'House' in self.chamber:
        #     return "/%s-debate/%s/%s/%s" %(self.chamber, self.GovernmentNumber, self.SessionNumber, self.PublicationId)
        # else:
        return "/%s/%s-meeting/%s/%s/%s" %(self.Government_obj.Region_obj.Name, self.chamber, self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.id)

    def apply_terms(self, meeting_terms, meetingData):
        # print('apply meeting terms')
        # self.Terms = []
        try:
            data = meetingData['Terms']
        except:
            data = []
        meeting_terms = sorted(meeting_terms.items(), key=operator.itemgetter(1),reverse=True)
        x = len(data)
        for t in meeting_terms:
            x += 1
            if t[0] not in data and t[0] not in skipwords:
                data.append(t)
                # print(t)
        # print(data)
        # meeting_data = {k: my_dict[k] for k in list(my_dict.keys())[:10]}
        meeting_data = {key: value for key, value in data[:150]}
        meetingData['Terms'] = json.dumps(meeting_data)
        # self.Terms_json = json.dumps(meeting_data)
        # self.save()
        p = Post.objects.filter(pointerId=self.id)[0]
        p.keyword_array = [key for key, value in data[:20]]
        p.save(share=False)
        return meetingData

    def version_v1_fields(self):
        fields = [
            "object_type",
            "blockchainType",
            "blockchainId",
            "locked_to_chain",
            "modelVersion",
            "id",
            "created",
            "automated",
            "publicKey",
            "signature",
            "chamber",
            "Region",
            "Government",
            "Agenda",
            "PubIden",
            "GovPage",
            "Title",
            "PublicationDateTime",
            "GovernmentNumber",
            "SessionNumber",
            "PublicationId",
            "Organization",
            "PdfURL",
            "IsTelevised",
            "IsAudioOnly",
            "TypeId",
            "HtmlURL",
            "MeetingIsForSenateOrganization",
            "VideoURL",
            "has_transcript",
            "Subjects",
            "Terms",
            "TermsText",
            "People",
            "PeopleText",
            "completed_model",
        ]
        return fields

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Meeting, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        isLatest = True #turn off when building database
        # self.set_chamber()
        p = new_post(self)
        # p.chamber = self.chamber
        # p.gov_level = self.Government.gov_level
        # if isLatest and self.has_transcript:
        #     date = '%s-%s-%s/%s:%s' %(self.created.year, self.created.month, self.created.day, self.Publication_date_time.hour, self.Publication_date_time.minute)
        #     dt = datetime.datetime.strptime(date, '%Y-%m-%d/%H:%M')
        #     p.date_time = dt
        # else:
        p.DateTime = self.DateTime
        p.save(share=share)
        return p

    # def list_ten_terms(self):
    #     try:
    #         d = json.loads(self.Terms_json)
    #         return list(d.items())[:10]
    #     except:
    #         return None
    # def list_matching_terms(self, user_keywords):
    #     print('match terms')
    #     try:
    #         from collections import Counter
    #         counter = Counter(user_keywords)
    #         CommonKeys = counter.most_common(500)
    #         print('keylen', len(CommonKeys))
    #         d = json.loads(self.TermsText)
    #         l = []
    #         # print(list(d.items())[:5])
    #         # print()
    #         for key, value in list(d.items())[:75]:
    #             if key not in skipwords:
    #                 # print(key)
    #                 # pass
    #                 # print({key:value})
    #                 l.append((key, value))
    #         return l
    #     except Exception as e:
    #         print(str(e))
    #         return None
    # def list_75_terms(self):
    #     try:
    #         d = json.loads(self.Terms_json)
    #         l = []
    #         # print(list(d.items())[:5])
    #         # print()
    #         for key, value in list(d.items())[:75]:
    #             if key not in skipwords:
    #                 # print(key)
    #                 # pass
    #                 # print({key:value})
    #                 l.append((key, value))
    #         return l
    #     except:
    #         return None
    # def get_terms_overflow(self):
    #     try:
    #         d = json.loads(self.Terms_json)
    #         total = len(d.items())
    #         if total > 75:
    #             remaining = total - 75
    #         else:
    #             remaining = None
    #         return remaining
    #     except:
    #         return None
    # def list_all_terms(self):
    #     # print('list all terms')
    #     try:
    #         d = json.loads(self.Terms_json)
    #         return list(d.items())
    #     except:
    #         return None
    
    def list_people(self):
        # print('list peiple')
        from accounts.models import Person
        try:
            d = json.loads(self.People_json)
            l = list(d.items())[:10]
            speakers = {}
            keys = []
            for key, value in l:
                keys.append(key)
            people = Person.objects.filter(id__in=keys)
            for p, value in [[p, value] for p in people for key, value in l if p.id == key]:
                speakers[p] = value
            # for key, value in l:
            #     a = Person.objects.filter(id=key)[0]
            #     speakers[a] = value
            return list(speakers.items())
        except Exception as e:
            print(str(e))
            return None

    # def list_all_people(self):
    #     # print('list all people')
    #     from accounts.models import Person
    #     try:
    #         d = json.loads(self.People_json)
    #         l = list(d.items())
    #         speakers = {}
    #         keys = []
    #         for key, value in l:
    #             keys.append(key)
    #         people = Person.objects.filter(id__in=keys)
    #         for p, value in [[p, value] for p in people for key, value in l if p.id == key]:
    #             speakers[p] = value
    #         # for key, value in l:
    #         #     a = Person.objects.filter(id=key)[0]
    #         #     speakers[a] = value
    #         return list(speakers.items())
    #     except Exception as e:
    #         print(str(e))
    #         return None
        
    # from django import template
    # register = template.Library()
    # @register.simple_tag
    # def get_bill_term(self, bill):
    #     d = []
    #     for key, value in self.list_all_terms():
    #         try:
    #             k = Keyphrase.objects.filter(bill=bill, text=key, hansardItem__hansard=self)[0]
    #             print(key)
    #             d.key = value
    #             return key, value
    #         except:
    #             pass
    #     return d

class Statement(BaseModel):
    object_type = "Statement"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='statement_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    Meeting_obj = models.ForeignKey('posts.Meeting', blank=True, null=True, related_name='debate_key', on_delete=models.CASCADE)
    # Committee_obj = models.ForeignKey('posts.Committee', blank=True, null=True, on_delete=models.CASCADE)
    # CommitteeMeeting_obj = models.ForeignKey('posts.CommitteeMeeting', blank=True, null=True, related_name='committee_meeting_key', on_delete=models.CASCADE)
    
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    # hansardId = models.CharField(max_length=250, default="", blank=True, null=True)
    Person_obj = models.ForeignKey('posts.Person', blank=True, null=True, on_delete=models.SET_NULL)
    PersonName = models.CharField(max_length=250, default="", blank=True, null=True)
    keyword_array = ArrayField(models.CharField(max_length=50, blank=True, null=True, default='{default}'), size=15, null=True, blank=True, default=list)
    Bill_objs = models.ManyToManyField('posts.Bill', blank=True, related_name='debateItem_bills')
    ItemId = models.IntegerField(default=0, blank=True, null=True)
    EventId = models.IntegerField(default=0, blank=True, null=True)
    VideoURL = models.URLField(null=True, blank=True)
    # Sequence = models.IntegerField(default=0, blank=True, null=True)
    Page = models.IntegerField(default=0, blank=True, null=True)
    PdfPage = models.IntegerField(default=0, blank=True, null=True)
    TypeId = models.IntegerField(default=0, blank=True, null=True)
    PublicationId = models.IntegerField(default=0, blank=True, null=True)
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    FacebookLink = models.URLField(null=True, blank=True)
    XTwitterLink = models.URLField(null=True, blank=True)

    OrderOfBusiness = models.CharField(max_length=255, default="", blank=True, null=True)
    SubjectOfBusiness = models.CharField(max_length=450, default="", blank=True, null=True)
    EventType = models.CharField(max_length=52, default="", blank=True, null=True)

    Type = models.CharField(max_length=53, default="", blank=True, null=True)
    Language = models.CharField(max_length=54, default="", blank=True, null=True)

    Content = models.TextField(default='', blank=True, null=True)
    word_count = models.PositiveIntegerField(blank=True, null=True)
    Terms_array = ArrayField(models.CharField(max_length=300, blank=True, null=True, default=[]), size=20, null=True, blank=True, default=list)
    
    
    MeetingTitle = models.CharField(max_length=1000, default="", blank=True, null=True)
    
    # question = models.ForeignKey(Question, blank=True, null=True, on_delete=models.SET_NULL)
    # questions = ArrayField(models.ForeignKey(Question, blank=True, null=True, on_delete=models.SET_NULL), size=10, null=True, blank=True)
    # questions = models.ManyToManyField(Question, blank=True, related_name='hansard_questions')

    def __str__(self):
        return 'STATEMENT:%s(%s-%s)' %(self.PersonName, self.id, self.DateTime)

    def get_absolute_url(self):
        # if self.Debate_obj:
        return '%s?id=%s' %(self.Meeting_obj.get_absolute_url(), self.id)
        # elif self.CommitteeMeeting_obj:
        #     return '%s?id=%s' %(self.CommitteeMeeting_obj.get_absolute_url(), self.id)

    def remove_tags(self):
        return re.sub('<[^<]+?>', '', self.Content)

    class Meta:
        ordering = ['-DateTime', 'created']

    def create_keyphrases(self, term, bill, share=False):
        print('create keyphrase')
        try:
            keyphrase = Keyphrase.objects.filter(pointerType=self.object_type, pointerId=self.id, Statement_obj=self, text=term[:300])[0]
            if bill:
                if keyphrase.Bill_obj != bill:
                    keyphrase.Bill_obj = bill
                    keyphrase.save(share=share)
                self.Bill_objs.add(bill)
                if self.Meeting_obj.Agenda_obj:
                    self.Meeting_obj.Agenda_obj.Bill_objs.add(bill)
                    self.Meeting_obj.Agenda_obj.save()
                if not self.DateTime:
                    self.DateTime = self.Meeting_obj.DateTime
            keyphrase.DateTime = self.DateTime
            keyphrase.save(share=share)
        except Exception as e:
            # print(str(e))
            # print('creating phrase', self.Region_obj)
            keyphrase = Keyphrase(pointerType=self.object_type, pointerId=self.id, Region_obj=self.Region_obj, Statement_obj=self, Country_obj=self.Country_obj, chamber=self.chamber, text=term[:300])
            # print('new prhase')
            # keyphrase.set_chamber() 
            if bill:
                keyphrase.Bill_obj = bill
                if self.Meeting_obj.Agenda_obj:
                    self.Meeting_obj.Agenda_obj.Bill_objs.add(bill)
                    self.Meeting_obj.Agenda_obj.save()
                if not self.DateTime:
                    self.DateTime = self.Meeting_obj.DateTime
            keyphrase.DateTime = self.DateTime
            # print('save', keyphrase)
            # keyphrase.chamber = self.Debate.chamber
            keyphrase.save(share=share)
            # print('set trend')
            keyphrase.set_trend() 
            # print('done set trend')

    def add_term(self, term, bill, share=False):
        if not self.Terms_array:
            self.Terms_array = []
        if term and term not in self.Terms_array:
            self.Terms_array.append(term)
        if bill and bill not in self.Terms_array:
            self.Terms_array.append(bill)
        # if not self.hansard.Terms:
        #     self.hansard.Terms = []
        # if term not in self.hansard.Terms:
        #     self.hansard.Terms.append(term)
        #     self.hansard.save()
        self.save(share=False)
        # print('add term:', term, self.Region_obj)
        self.create_keyphrases(term, bill, share=share)
        return self

    
    def get_item_keywords(self, p, share=False):
        def strip_tags(text):
            TAG_RE = re.compile(r'<[^>]+>')
            return TAG_RE.sub('', text)
        text = strip_tags(self.Content)
        print('get keywords 111')
        self, p = get_keywords(self, p, text)
        print('done get keywords 111')
        for k in self.keyword_array:
            self.create_keyphrases(k, None, share=share)
        # stop_words = set(stopwords.words('english'))
        # stop_words_french = set(stopwords.words('french'))
        # kw_model = KeyBERT()
        # stop_w = []
        # for i in stop_words:
        #     stop_w.append(i)
        # # keywords = kw_model.extract_keywords(text)
        # # skipwords = ['act', 'acts', 'statutes', 'legislature', 'schedule', 'bill amends the', 'enactment grants', 'enactment grants the', 'this enactment grants', 'enactment amends the','this enactment amends', 'this acts amends', 'act amends the', 'act amends', 'enactment', 'enactment amends', 'provisions', 'intermediary', 'intermediaries', 'regulation', 'regulations', 'regulations to', 'also amends', 'consequential amendments', 'amendments to', 'amendments', 'amends', 'makes consequential amendments', 'enactment provides', 'provides']
        # self.keywords = []
        # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(1, 1), stop_words=stop_w)
        # n = 0
        # for i, r in x:
        #     if i not in skipwords and i not in stop_words and i not in stop_words_french and i not in self.keywords and n <= 10:
        #         self.keywords.append(i)
        #         p.keywords.append(i)
        #         stop_w.append(i)
        #         n += 1
        #         # print(i, r)
        # print('get bill keywords', datetime.datetime.now())
        # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(2, 2), stop_words=stop_w)
        # print('finish bill keywords', datetime.datetime.now())
        # n = 0
        # for i, r in x:
        #     if i not in skipwords and i not in self.keywords and n <= 5:
        #         self.keywords.append(i)
        #         p.keywords.append(i)
        #         n += 1
                # print(i, r)
        # stop_words = set(stopwords.words('english'))
        # stop_words_french = set(stopwords.words('french'))
        # kw_model = KeyBERT()
        # # keywords = kw_model.extract_keywords(text)
        # self.keywords = []
        # # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(2, 2), stop_words=None)
        # # n = 0
        # # for i, r in x:
        # #     if i not in skipwords and i not in self.keywords and n <= 5:
        # #         self.keywords.append(i)
        # #         n += 1
        # #         print(i)
        # # print()
        # x = kw_model.extract_keywords(text, top_n=5, keyphrase_ngram_range=(1, 1), stop_words=None)
        # n = 0
        # for i, r in x:
        #     if i not in skipwords and i not in stop_words and i not in stop_words_french and i not in self.keywords and n <= 5:
        #         if self.Terms and i.lower() not in [x.lower() for x in self.Terms] or not self.Terms:
        #             n += 1
        #             self.keywords.append(i)
        #             p.keywords.append(i)
        #             # print(i, r)
        # print()
        # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(3, 3), stop_words=None)
        # n = 0
        # for i, r in x:
        #     if i not in skipwords and i not in self.keywords and n <= 5:
        #         self.keywords.append(i)
        #         n += 1
        #         print(i)
        # print()
        self.save()
        p.save()
        return p

    def save(self, share=False):
        if self.id == '0':
            if not self.chamber:
                if self.Meeting_obj:
                    self.chamber = self.Meeting_obj.chamber
                # elif self.Debate_obj:
                #     self.chamber = self.Debate_obj.chamber
            if not self.Country_obj:
                self.Country_obj = self.Government_obj.Country_obj
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Statement, self).save()
        

    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        # print('--statement create post')
        p = new_post(self)  
        # p.chamber = self.chamber
        # p.gov_level = self.Government.gov_level
        p.keyword_array = []
        # print('--1')
        # print('self.Person_obj', self.Person_obj)
        # print('self.Person_obj.FullName', self.Person_obj.FullName)
        # print('p.keyword_array', p.keyword_array)
        if self.Person_obj and self.Person_obj.FullName not in p.keyword_array:
            # print('--1a')
            p.keyword_array.append(self.Person_obj.FullName)
        # print('---1b')
        if self.Terms_array:
            for t in self.Terms_array:
                if t not in p.keyword_array and t not in skipwords:
                    p.keyword_array.append(t)   
        # print('---1c')
        # p.organization = self.Debate.Organization
        try:
            personPost = Post.objects.filter(Person_obj=self.Person_obj)[0]
            personPost.DateTime = p.DateTime
            # personPost.DateTime = p.pointerDateTime
            personPost.save()
        except:
            pass
        # print('---2')
        if not self.DateTime:
            # if self.CommitteeMeeting_obj:
            self.DateTime = self.Meeting_obj.DateTime
            # elif self.Debate_obj:
            #     self.ItemDateTime = self.Debate_obj.PublicationDateTime
            self.save()
            p.DateTime = self.DateTime
            p.save()
        else:
            p.DateTime = self.DateTime
            p.save()
        # print('--3')
        # p.save(share=share)
        print('--get keywords')
        p = self.get_item_keywords(p, share=share)
        print('--done get keywords')
        return p

class Spren(models.Model):
    object_type = "Spren"
    blockchainType = models.CharField(max_length=50, default="0")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='spren_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # date_time = models.DateTimeField(auto_now=False, auto_now_add=False, blank=False, null=True)
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    func = models.CharField(max_length=50, default="")
    blockchainId = models.CharField(max_length=50, default="")
    locked_to_chain = models.BooleanField(default=False)
    # modelVersion = models.CharField(max_length=50, default="v1")
    publicKey = models.CharField(max_length=200, default="")
    signature = models.CharField(max_length=200, default="")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('posts.Region', related_name='%(class)s_region_obj', blank=True, null=True, on_delete=models.CASCADE)
    # Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    # Government_obj = models.ForeignKey('posts.Government', related_name='%(class)s_government_obj', blank=True, null=True, on_delete=models.SET_NULL)
    DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    
    
    pointerId = models.CharField(max_length=50, default="0")
    pointerType = models.CharField(max_length=50, default="0")
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    
    Statement_obj = models.ForeignKey(Statement, blank=True, null=True, related_name='spren_statement_key', on_delete=models.CASCADE)
    Meeting_obj = models.ForeignKey(Meeting, blank=True, null=True, related_name='spren_meeting_key', on_delete=models.CASCADE)
    debateId = models.CharField(max_length=250, default="", blank=True, null=True)
    
    topic = models.CharField(max_length=500, default="", blank=True, null=True)
    type = models.CharField(max_length=250, default="", blank=True, null=True)
    
    Bill_obj = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.CASCADE)
    
    content = models.CharField(max_length=3000, default="", blank=True, null=True)
    # steelmanFor = models.CharField(max_length=1000, default="", blank=True, null=True)
    # steelmanAgainst = models.CharField(max_length=1000, default="", blank=True, null=True)
    version = models.CharField(max_length=10, default="", blank=True, null=True)
    
    def __str__(self):
        return 'SPREN:%s, %s' %(self.type, self.DateTime)

    class Meta:
        ordering = ["-DateTime"]

    def get_post(self):
        p = Post.objects.filter(Spren_obj=self)[0]
        return p

    def save(self, share=False):
        print('start save spren')
        if self.id == '0':
            if self.Statement_obj:
                self.blockchainType = self.Statement_obj.blockchainType
                self.chamber = self.Statement_obj.chamber
                self.Region_obj = self.Statement_obj.Region_obj
                self.Country_obj = self.Statement_obj.Country_obj
                self.Government_obj = self.Statement_obj.Government_obj
            elif self.Meeting_obj:
                self.blockchainType = self.Meeting_obj.blockchainType
                self.chamber = self.Meeting_obj.chamber
                self.Region_obj = self.Meeting_obj.Region_obj
                self.Country_obj = self.Meeting_obj.Country_obj
                self.Government_obj = self.Meeting_obj.Government_obj
            elif self.Bill_obj:
                self.blockchainType = self.Bill_obj.blockchainType
                self.chamber = self.Bill_obj.chamber
                self.Region_obj = self.Bill_obj.Region_obj
                self.Country_obj = self.Bill_obj.Country_obj
                self.Government_obj = self.Bill_obj.Government_obj
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Spren, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=False):
        if not self.DateTime:
            if self.Statement_obj:
                self.DateTime = self.Statement_obj.DateTime
            elif self.Meeting_obj:
                self.DateTime = self.Meeting_obj.DateTime
            elif self.Bill_obj:
                self.DateTime = self.Bill_obj.DateTime
            else:
                self.DateTime = self.created
        self.save()
        p = new_post(self)
        # p.chamber = self.chamber
        # p.gov_level = self.Government.gov_level
                # # def strip_tags(text):
                # #     TAG_RE = re.compile(r'<[^>]+>')
                # #     return TAG_RE.sub('', text)
                # # if self.bill_text_html:
                # text = self.content
                # # text = strip_tags(text)
                # stop_words = set(stopwords.words('english'))
                # stop_words_french = set(stopwords.words('french'))
                # kw_model = KeyBERT()
                # # keywords = kw_model.extract_keywords(text)
                # # skipwords = ['act', 'acts', 'statutes', 'legislature', 'schedule', 'bill amends the', 'enactment grants', 'enactment grants the', 'this enactment grants', 'enactment amends the','this enactment amends', 'this acts amends', 'act amends the', 'act amends', 'enactment', 'enactment amends', 'provisions', 'intermediary', 'intermediaries', 'regulation', 'regulations', 'regulations to', 'also amends', 'consequential amendments', 'amendments to', 'amendments', 'amends', 'makes consequential amendments', 'enactment provides', 'provides']
                # p.keywords = []
                # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(1, 1), stop_words=None)
                # n = 0
                # for i, r in x:
                #     if i not in skipwords and i not in stop_words and i not in stop_words_french and i not in p.keywords and n <= 10:
                #         # self.keywords.append(i)
                #         p.keywords.append(i)
                #         n += 1
                #         # print(i, r)
                # # print('get bill keywords', datetime.datetime.now())
                # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(2, 2), stop_words=None)
                # # print('finish bill keywords', datetime.datetime.now())
                # n = 0
                # for i, r in x:
                #     if i not in skipwords and i not in p.keywords and n <= 5:
                #         # self.keywords.append(i)
                #         p.keywords.append(i)
                #         n += 1
                #         # print(i, r)
                # # print()
                # # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(3, 3), stop_words=None)
                # # n = 0
                # # for i, r in x:
                # #     if i not in skipwords and i not in self.keywords and n <= 5:
                # #         self.keywords.append(i)
                # #         n += 1
                # #         print(i)
                # # print()
                # # self.save()
                # # p.save()
        # p.set_score()
        print('done create sprenPost')
        print('p',p)
        p.save(share=share)
        print('saved spren post')
            # return p
                # p.keywords = []
                # p.keywords.append(self.subject)
            # try:
            #     keyphrase = Keyphrase.objects.filter(organization=self.OriginatingchamberName, text=self.subject)[0]
                
            # except:
            #     keyphrase = Keyphrase(organization=self.OriginatingchamberName, text=self.subject) 
            #     keyphrase.save()
        # p.set_score()
        return p

class SprenItem(models.Model):
    object_type = "SprenItem"
    blockchainType = models.CharField(max_length=50, default="0")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='sprenitem_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    func = models.CharField(max_length=50, default="")
    blockchainId = models.CharField(max_length=50, default="")
    locked_to_chain = models.BooleanField(default=False)
    # modelVersion = models.CharField(max_length=50, default="v1")
    publicKey = models.CharField(max_length=200, default="")
    signature = models.CharField(max_length=200, default="")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('posts.Region', related_name='%(class)s_region_obj', blank=True, null=True, on_delete=models.CASCADE)
    # Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    # Government_obj = models.ForeignKey('posts.Government', related_name='%(class)s_government_obj', blank=True, null=True, on_delete=models.SET_NULL)
    DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    
    
    Spren_obj = models.ForeignKey(Spren, blank=True, null=True, on_delete=models.CASCADE)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    Statement_obj = models.ForeignKey(Statement, blank=True, null=True, related_name='sprenItem_statement_key', on_delete=models.CASCADE)
    
    refrenceType = models.CharField(max_length=50, default="0")
    referenceId = models.CharField(max_length=50, default="0")
    

    # hansardItem = models.ForeignKey(HansardItem, blank=True, null=True, related_name='sprenItem_hansardItem', on_delete=models.CASCADE)
    
    content = models.CharField(max_length=3000, default="", blank=True, null=True)

    def __str__(self):
        return 'SPRENITEM:%s' %(self.created)

    class Meta:
        ordering = ["created"]

    def get_absolute_url(self):
        try:
            return self.Statement_obj.get_absolute_url()
        except:
            return ''
    
    def save(self, share=True):
        if self.id == '0':
            self.blockchainType = self.Spren_obj.blockchainType
            self.chamber = self.Spren_obj.chamber
            self.Region_obj = self.Spren_obj.Region_obj
            self.Country_obj = self.Spren_obj.Country_obj
            self.Government_obj = self.Spren_obj.Government_obj
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(SprenItem, self).save()


    def delete(self):
        superDelete(self)

class Daily(BaseModel):
    object_type = "Daily"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='daily_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', related_name='daily_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    # # Region_obj = models.ForeignKey('accounts.Region', related_name='daily_region_obj', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    User_obj = models.ForeignKey('accounts.User', blank=True, null=True, on_delete=models.SET_NULL)
    # date_time = models.DateTimeField(auto_now=False, auto_now_add=False, blank=False, null=True)
    
    # organization = models.CharField(max_length=250, default="", blank=True, null=True)
    
    content = models.CharField(max_length=2000, default="", blank=True, null=True)
    
    def __str__(self):
        return 'DAILY:%s, %s' %(self.chamber, self.DateTime)

    class Meta:
        ordering = ["-DateTime"]

    def get_absolute_url(self):
        return '/legislature?date=%s-%s-%s' %(self.DateTime.year, self.DateTime.month, self.DateTime.day)

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Daily, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        # self.save()
        # try:
        #     p = Post.objects.filter(daily=self)[0]
        # except:
        #     try:
        #         p = Archive.objects.filter(daily=self)[0]
        #     except:
        #         p = Post()
        #         p.daily = self
        #         p.date_time = self.date_time
        #         p.post_type = 'daily'
        p = new_post(self)
        # p.chamber = self.chamber
        # p.gov_level = self.Government.gov_level
                # text = self.content
                # stop_words = set(stopwords.words('english'))
                # stop_words_french = set(stopwords.words('french'))
                # kw_model = KeyBERT()
                # p.keywords = []
                # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(1, 1), stop_words=None)
                # n = 0
                # for i, r in x:
                #     if i not in skipwords and i not in stop_words and i not in stop_words_french and i not in p.keywords and n <= 10:
                #         p.keywords.append(i)
                #         n += 1
                # x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(2, 2), stop_words=None)
                # n = 0
                # for i, r in x:
                #     if i not in skipwords and i not in p.keywords and n <= 5:
                #         p.keywords.append(i)
                #         n += 1
        p.save(share=share)
        # print('done create dailyPost')
        return p

class Committee(BaseModel):
    object_type = "Committee"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='committee_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)   
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    Chair_obj = models.ForeignKey('posts.Role', related_name='committee_chair', blank=True, null=True, on_delete=models.CASCADE)
    Member_objs = models.ManyToManyField('posts.Role', blank=True)
    Code = models.CharField(max_length=50, default="", blank=True, null=True)
    Title = models.CharField(max_length=251, default="", blank=True, null=True)
    # GovernmentNumber = models.IntegerField(default=0, blank=True, null=True)
    # SessionNumber = models.IntegerField(default=0, blank=True, null=True)
    GovURL = models.CharField(max_length=250, default="", blank=True, null=True)
    
    # Organization = models.CharField(max_length=1000, default="", blank=True, null=True)
    
    def __str__(self):
        return 'COMMITTEE:(%s-%s) %s' %(self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.Title)
    
    class Meta:
        ordering = ['-created', 'Code']

    def get_absolute_url(self):
        if self.chamber == 'Senate':
            return "/senate-committee/%s/%s/%s" %(self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.Code)
        elif self.chamber == 'House of Commons' or self.chamber == 'House':
            return "/house-committee/%s/%s/%s" %(self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.Code)
        else:   
            # print(self.Organization)
            return "/committee/%s/%s/%s" %(self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.Code)

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Committee, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        
        p = new_post(self)
        # p.chamber = self.chamber
        # p.gov_level = self.Government.gov_level
        # if self.Organization == 'Senate':
        #     p.organization = 'Senate'
        # else:
        #     p.organization = 'House'
        p.save(share=share)
        return p

class Motion(BaseModel):
    object_type = "Motion"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='motion_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    Bill_obj = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.SET_NULL)
    billCode = models.CharField(max_length=30, default="", blank=True, null=True)
    Sponsor_obj = models.ForeignKey('posts.Person', blank=True, null=True, on_delete=models.SET_NULL)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    # province = models.ForeignKey('accounts.Province', blank=True, null=True, on_delete=models.SET_NULL)
    Party_objs = models.ManyToManyField('posts.Party', blank=True, related_name='motion_party')
    GovUrl = models.URLField(null=True, blank=True)
    # sponsor_gov_id = models.CharField(max_length=30, default="", blank=True, null=True)
    VoteNumber = models.IntegerField(default=0, blank=True, null=True) #DecisionDivisionNumber
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # respecting = models.CharField(max_length=30, default="", blank=True, null=True)
    # # OriginatingchamberName = models.CharField(max_length=30, default="House", blank=True, null=True)
    # GovernmentNumber = models.IntegerField(default=0, blank=True, null=True)
    # SessionNumber = models.IntegerField(default=0, blank=True, null=True)
    Subject = models.CharField(max_length=500, default="", blank=True, null=True)
    MotionText = models.TextField(blank=True, null=True)
    DecisionDivisionDocumentTypeName = models.CharField(max_length=500, default="", blank=True, null=True)
    DecisionDivisionDocumentTypeId = models.CharField(max_length=500, default="", blank=True, null=True)
    Yeas = models.IntegerField(default=0, blank=True, null=True)
    Nays = models.IntegerField(default=0, blank=True, null=True)
    Pairs = models.IntegerField(default=0, blank=True, null=True)
    Absentations = models.IntegerField(default=0, blank=True, null=True)
    TotalVotes = models.IntegerField(default=0, blank=True, null=True)
    Result = models.CharField(max_length=200, default="", blank=True, null=True) #DecisionResultName
    # sitting = models.IntegerField(default=0, blank=True, null=True)
    is_offical = models.BooleanField(default=False)
    
    def __str__(self):
        return 'MOTION:(%s-%s) %s/%s' %(self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.VoteNumber, self.Result)

    def get_absolute_url(self):
        # if self.OriginatingchamberName == 'Senate':
        #     return "/senate-motion/%s/%s/%s" %(self.ParliamentNumber, self.SessionNumber, self.vote_number)
        # elif self.OriginatingchamberName == 'House' or self.OriginatingchamberName == 'House of Commons':
        #     return "/house-motion/%s/%s/%s" %(self.ParliamentNumber, self.SessionNumber, self.vote_number)
        return "/%s/%s-motion/%s/%s/%s" %(self.Country_obj.Name.lower(), self.chamber.lower(), self.Government_obj.GovernmentNumber, self.Government_obj.SessionNumber, self.VoteNumber)
        # else:
        #     return "/motion/%s/%s/%s" %(self.ParliamentNumber, self.SessionNumber, self.vote_number)

    class Meta:
        ordering = ["-DateTime", '-VoteNumber', 'created']

    def save(self, share=False):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Motion, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=False):
        p = new_post(self)
        # p.chamber = self.chamber
        # p.gov_level = self.Government.gov_level
            # if self.OriginatingchamberName == 'Senate':
            #     p.organization = 'Senate'
            # else:
            #     p.organization = 'House'
        # p.organization = self.OriginatingchamberName
        p.keyword_array = []
        p.keyword_array.append(self.Subject)
        # try:
        #     keyphrase = Keyphrase.objects.filter(pointerType=self.object_type, pointerId=self.id, Region_obj=self.Region_obj, chamber=self.chamber, text=self.Subject)[0]
            
        # except:
        #     keyphrase = Keyphrase(Region_obj=self.Region_obj, Country_obj=self.Country_obj, chamber=self.chamber, text=self.Subject) 
        #     keyphrase.save(share=share)
        p.save(share=share)
        return p

class Vote(BaseModel):
    # mp = models.CharField(max_length=100, default="", blank=True, null=True)
    # motion = models.ForeignKey(Motion, blank=True, null=True, on_delete=models.CASCADE)
    object_type = "Vote"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='vote_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    Motion_obj = models.ForeignKey(Motion, blank=True, null=True, on_delete=models.CASCADE)
    Person_obj = models.ForeignKey('posts.Person', blank=True, null=True, on_delete=models.SET_NULL)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    # post_id = models.IntegerField(default=0, blank=True, null=True)
    # motion_id = models.IntegerField(default=0, blank=True, null=True)
    # bill_id = models.IntegerField(default=0, blank=True, null=True)
    # person_id = models.IntegerField(default=0, blank=True, null=True)
    # voter_id = models.IntegerField(default=0, blank=True, null=True)
    # GovernmentNumber = models.CharField(max_length=10, default="", blank=True, null=True)
    # SessionNumber = models.CharField(max_length=10, default="", blank=True, null=True)
    DecisionEventDateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True) # might not be working
    vote_number = models.CharField(max_length=100, default="", blank=True, null=True) #DecisionDivisionNumber
    PersonShortSalutation = models.CharField(max_length=10, default="", blank=True, null=True)
    ConstituencyName = models.CharField(max_length=150, default="", blank=True, null=True)
    VoteValueName = models.CharField(max_length=20, default="", blank=True, null=True)
    # PersonOfficialFirstName = models.CharField(max_length=100, default="", blank=True, null=True)
    # PersonOfficialLastName = models.CharField(max_length=100, default="", blank=True, null=True)
    PersonOfficialFullName = models.CharField(max_length=100, default="", blank=True, null=True)
    ConstituencyProvinceTerritoryName = models.CharField(max_length=100, default="", blank=True, null=True)
    CaucusShortName = models.CharField(max_length=50, default="", blank=True, null=True)
    IsVoteYea = models.CharField(max_length=10, default="", blank=True, null=True)
    IsVoteNay = models.CharField(max_length=10, default="", blank=True, null=True)
    IsVotePaired = models.CharField(max_length=10, default="", blank=True, null=True)
    IsVoteAbsentation = models.CharField(max_length=10, default="", blank=True, null=True)
    DecisionResultName = models.CharField(max_length=50, default="", blank=True, null=True)
    PersonId = models.CharField(max_length=20, default="", blank=True, null=True)

    def __str__(self):
        if self.Person_obj:
            return 'VOTE:person-%s: %s' %(self.Person_obj.id, self.VoteValueName)
        else:
            return 'VOTE:voter-%s' %(self.VoteValueName)

    class Meta:
        ordering = ["-created"]
    
    def save(self, share=False):
        print()
        print('start save vote')
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Vote, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=False):
        print()
        print('vote create post')
        p = new_post(self)
        try:
            print(self.Person_obj)
            print(self.Person_obj.Party_obj)
            personU = Update.objects.filter(Person_obj=self.Person_obj)[0]
            print(personU.Party_obj)
            self.Motion_obj.Party_objs.add(personU.Party_obj)
            self.Motion_obj.save()
        except Exception as e:
            print(str(e))
            pass
        p.save(share=share)
        return p

class Election(BaseModel):
    object_type = "Election"
    blockchainType = 'Region'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # automated = True
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='election_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    start_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    end_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # Government_obj = models.ForeignKey(Government, blank=True, null=True, on_delete=models.SET_NULL)
    # country = models.ForeignKey('posts.Country', blank=True, null=True, on_delete=models.SET_NULL)
    # province = models.ForeignKey('accounts.Province', blank=True, null=True, on_delete=models.SET_NULL)
    # organization = models.CharField(max_length=55, default="", blank=True, null=True)
    # level = models.CharField(max_length=25, default="", blank=True, null=True)
    type = models.CharField(max_length=25, default="", blank=True, null=True)
    # riding = models.ForeignKey('accounts.Riding', blank=True, null=True, on_delete=models.SET_NULL)
    District_obj = models.ForeignKey('posts.District', blank=True, null=True, on_delete=models.SET_NULL)
    total_votes = models.IntegerField(default=0, blank=True, null=True)
    total_valid_votes = models.IntegerField(default=0, blank=True, null=True)
    rejected_votes = models.IntegerField(default=0, blank=True, null=True)
    # Parliament = models.IntegerField(default=0, blank=True, null=True)
    # government = models.ForeignKey('posts.Government', blank=True, null=True, on_delete=models.SET_NULL)
    ongoing = models.BooleanField(default=False)

    def __str__(self):
        return 'ELECTION:%s %s' %(self.chamber, self.type)

    class Meta:
        ordering = ["-end_date"]

    def get_absolute_url(self):
        # if self.Riding:
        #     return '/election/%s/%s/%s' %(self.chamber, self.Riding.Name, self.id)
        # if self.District_obj:
        #     return '/election/%s/%s/%s' %(self.chamber, self.District_obj.Name, self.id)
        # else:
        return '/election/%s/%s/%s' %(self.chamber, self.Government_obj.Country.Name, self.id)

    # def send_alerts(self):
    #     from accounts.models import User
    #     name = self.District.Name
    #     User.objects.filter(username='Sozed')[0].alert('%s in %s on %s' %(self.type, name, self.end_date), self.get_absolute_url(), "See who's running")
    #     users = User.objects.filter(district=self.district)
    #     for u in users:
    #         u.alert('%s in %s on %s' %(self.type, name, self.end_date), self.get_absolute_url(), "See who's running")

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Election, self).save()


    def delete(self):
        superDelete(self)

    def create_post(self, share=True):
        p = new_post(self)
        # p.set_score()
        p.save(share=share)
        return p

class Update(BaseModel):
    object_type = "Update"
    blockchainType = models.CharField(max_length=50, default="0")
    modelVersion = models.CharField(max_length=50, default="v1")
    # automated = True
    pointerId = models.CharField(max_length=50, db_index=True, default="0")
    pointerType = models.CharField(max_length=50, default="0")

    # region, country, government in baseModel
    Interaction_obj = models.ForeignKey('accounts.Interaction', blank=True, null=True, on_delete=models.CASCADE)
    Daily_obj = models.ForeignKey(Daily, blank=True, null=True, on_delete=models.CASCADE)
    Spren_obj = models.ForeignKey(Spren, blank=True, null=True, on_delete=models.CASCADE)
    Agenda_obj = models.ForeignKey(Agenda, blank=True, null=True, on_delete=models.CASCADE)
    AgendaTime_obj = models.ForeignKey(AgendaTime, blank=True, null=True, on_delete=models.CASCADE)
    AgendaItem_obj = models.ForeignKey(AgendaItem, blank=True, null=True, on_delete=models.CASCADE)
    Bill_obj = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.CASCADE)
    BillVersion_obj = models.ForeignKey(BillVersion, blank=True, null=True, on_delete=models.CASCADE)
    BillAction_obj = models.ForeignKey(BillAction, blank=True, null=True, on_delete=models.CASCADE)
    Meeting_obj = models.ForeignKey(Meeting, related_name='%(class)s_meeting_obj', blank=True, null=True, on_delete=models.CASCADE)
    Statement_obj = models.ForeignKey(Statement, blank=True, null=True, on_delete=models.CASCADE)
    Committee_obj = models.ForeignKey(Committee, related_name='%(class)s_committee_obj', blank=True, null=True, on_delete=models.CASCADE)
    Motion_obj = models.ForeignKey(Motion, blank=True, null=True, on_delete=models.CASCADE)
    Vote_obj = models.ForeignKey(Vote, blank=True, null=True, on_delete=models.CASCADE)
    Election_obj = models.ForeignKey(Election, blank=True, null=True, on_delete=models.CASCADE)
    Person_obj = models.ForeignKey('posts.Person', blank=True, null=True, on_delete=models.CASCADE)
    Party_obj = models.ForeignKey('posts.Party', blank=True, null=True, on_delete=models.CASCADE)
    District_obj = models.ForeignKey('posts.District', blank=True, null=True, on_delete=models.CASCADE)
    Role_obj = models.ForeignKey('posts.Role', blank=True, null=True, on_delete=models.CASCADE)
    ProvState_obj = models.ForeignKey('posts.Region', related_name='%(class)s_provstate_obj', blank=True, null=True, on_delete=models.CASCADE)

    
    data = models.TextField(default='{}', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)


    def __str__(self):
        return 'UPDATE:%s-%s' %(self.pointerType, self.pointerId)

    class Meta:
        ordering = ["-created"]

    skipFields = ['id', 'func', 'locked_to_chain', 'created', 'last_updated', 'publicKey', 'signature']

    def create_next_version(self, obj=None):
        # print('create_next_version', obj)
        if obj:
            try:
                current = Update.objects.filter(pointerId=obj.id)[0]
            except:
                current = None
            # print('current', current)
            new = Update(pointerId=obj.id, pointerType=obj.object_type)
            if current:
                fields = current._meta.fields
                for f in fields:
                    if f.name not in self.skipFields:
                        attr = getattr(current, f.name)
                        setattr(new, f.name, attr)
        else:
            # print('else')
            try:
                current = Update.objects.filter(pointerId=self.id)[0]
            except:
                current = self
            new = Update(pointerId=self.id, pointerType=self.object_type)
            fields = current._meta.fields
            for f in fields:
                if f.name not in self.skipFields:
                    attr = getattr(current, f.name)
                    setattr(new, f.name, attr)
        # print('new update', new.__dict__)
        return new
    
    def get_pointer(self):
        # print('get pointer', self.pointerType, self.pointerId)
        return get_dynamic_model(self.pointerType, id=self.pointerId)
        # return globals()[self.pointerType].objects.filter(id=self.pointerId)[0]
        
    def save_if_new(self, share=True):
        # print('save update if new')
        if not self.data:
            return None, False
        field_names = [field.name for field in self._meta.fields if field.name not in self.skipFields]
        # print(field_names)
        query_kwargs = {field: getattr(self, field) for field in field_names}
        # print(query_kwargs)
        try:
            match = Update.objects.filter(**query_kwargs)[0]
            # print('match', match)
            return match, False
        except:
            # try:
            #     previous_updates = Update.objects.filter(pointeriId=self.pointerId).exclude(id=self.id)
            #     for u in previous_updates:
            #         u.delete()
            # except:
            #     pass
            # print('self', self)
            self.save(share=share)
            previous_updates = Update.objects.filter(pointerId=self.pointerId).exclude(id=self.id)
            for u in previous_updates:
                u.delete()
            return self, True

    def update_post(self):
        # print('update _post')
        try:
            # if self.DateTime:
            #     p = Post.objects.filter(pointerId=self.pointerId)[0]
            #     p.DateTime = self.DateTime
            #     if not self.signature:
            # sign_obj(self)
            # super(Post, p).save()
            
            post = Post.objects.filter(pointerId=self.pointerId)[0]
            post.Update_obj = self
            # post.updateId = self.id
            post.DateTime = self.DateTime
            post.save(share=False)
        except:
            pass

    def save(self, share=True):
        if self.id == '0':
            print('update first save')
            pointer = self.get_pointer()
            self.DateTime = pointer.DateTime
            try:
                self.Government_obj = pointer.Government_obj
            except:
                pass
            try:
                self.chamber = pointer.chamber
            except:
                pass
            try:
                self.Country_obj = pointer.Country_obj
            except:
                pass
            try:
                self.Region_obj = pointer.Region_obj
            except:
                pass
            self.blockchainType = pointer.blockchainType
            field = str(self.pointerType) + '_obj'
            # print(field, pointer)
            setattr(self, field, pointer)
            self = initial_save(self, share=share)
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Update, self).save()
            self.update_post()
        elif not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Update, self).save()
    

    def delete(self):
        super(Update, self).delete()



def now_utc():
    return datetime.datetime.now().astimezone(pytz.utc)    

def get_latest_update(pointerId):
    return Update.objects.filter(pointerId=pointerId).order_by('-created')[0]

def get_keywords(obj, post, text):
    # print('get keyowrds')
    # stop_words = set(stopwords.words('english'))
    # stop_words_french = set(stopwords.words('french'))
    if not post:
        try:
            post = Post.objects.filter(pointerId=obj.id)[0]
        except:
            pass
    try:
        from keybert import KeyBERT
        kw_model = KeyBERT()
        # end_time = datetime.datetime.now() - start_time
        # print('time1', end_time)
        stop_w = []
        # for i in stop_words:
        #     stop_w.append(i)
        for i in skipwords:
            stop_w.append(i)
        obj.keyword_array = []
        x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(2, 2), stop_words=stop_w)
        n = 0
        # print(x)
        # end_time = datetime.datetime.now() - start_time
        # print('time2', end_time)
        terms = ''
        for i, r in x:
            if i not in stop_w and i not in obj.keyword_array and n <= 7 and not i.isnumeric():
                obj.keyword_array.append(i)
                if post:
                    post.keyword_array.append(i)
                n += 1
                terms = terms + i + ' '
                # print(i, r)
        # end_time = datetime.datetime.now() - start_time
        # print('time3', end_time)
        x = kw_model.extract_keywords(text, top_n=10, keyphrase_ngram_range=(1, 1), stop_words=stop_w)
        n = 0
        # print(x)
        # end_time = datetime.datetime.now() - start_time
        # print('time4', end_time)
        for i, r in x:
            if i not in stop_w and i not in terms and n <= 7 and not i.isnumeric():
                obj.keyword_array.append(i)
                if post:
                    post.keyword_array.append(i)
                stop_w.append(i)
                n += 1
                # print(i, r)
        # end_time = datetime.datetime.now() - start_time
        # print('time5', end_time)
    except Exception as e:
        print('get_keywords fail', str(e))
    return obj, post

def get_point_value(post):
    if post.total_yeas > 1000:
        score = 0.042 # ~1hr per 1000 upvotes
    elif post.total_yeas > 500:
        score = 0.417 # ~1hr per 100 upvotes
    elif post.total_yeas > 75:
        score = 1.04 # ~1hr per 40 upvotes
    elif post.total_yeas > 10:
        score = 4.166 # ~1hr per 10 upvotes
    else:
        score = 41.66 # ~1hr added to rank per upvote for first 10 votes
    return score

def baseline_time():
    return datetime.datetime(1985, 10, 23, 0, 0)

def scoreMe(post):
    # print('scoreme', post)
    if post.randomizer == 0:
        post.randomizer = random.randint(1,333) #used in algorithim to reduce number of hansardItems and mix up content by up to 8hrs -- not used anymore
    baseline = baseline_time()
    # print(post.pointerDateTime)
    try:
        t = post.DateTime - baseline
    except Exception as e:
        # print(str(e))
        t = post.DateTime - baseline.replace(tzinfo=pytz.UTC)
    secs = t.seconds * (1000 / 86400) # converts 24hrs in seconds to 1000, so there isnt' a big jump in rank numbers at the end of the day
    r = ((t.days * 1000) + secs)  #1000 - 1 day == 1000 on rank scale, 1 minute = 0.694 rank score
    # print('scoreme step2')
    from accounts.models import Interaction
    post.total_yeas = Interaction.objects.filter(Post_obj=post).filter(UserVote_obj__vote='yea').count()
    post.total_nays = Interaction.objects.filter(Post_obj=post).filter(UserVote_obj__vote='nay').count()
    post.total_votes = post.total_yeas + post.total_nays
    score = get_point_value(post)
    # print('score', score)
    post.rank = decimal.Decimal(r) + decimal.Decimal((post.total_yeas*score)+post.randomizer)
    # print('self.pointerDateTimexxx', post.pointerDateTime)
    post.save(share=False)
    # print('self.pointerDateTimexx22', post.pointerDateTime)
    # print('scoreme done')


def to_megabytes(instance):
    from django.core.serializers import serialize
    import sys
    serialized_data = serialize('json', [instance])
    size_in_bytes = sys.getsizeof(serialized_data)
    size_in_kilobytes = size_in_bytes / 1024 
    size_in_megabytes = size_in_kilobytes / 1024
    return size_in_megabytes

def send_for_validation(items, gov, func):
    from blockchain.models import get_scrape_duty, get_scraperScripts, downstream_broadcast, get_self_node, number_of_scrapers
    print('send_for_validation()', func, gov)
    print(items)
    items_to_get = [item for sublist in items for item in sublist]
    print('length', len(items_to_get))
    dt = None
    for i in items_to_get:
        try:
            dt = i.created
            break
        except:
            pass
    if func == 'get_user_region':
        # get_user_region is initiated by user and scraping_order does not apply
        # send as background process, user is waiting for result of scraper
        downstream_broadcast
    elif dt:
        region = gov.Region_obj
        print(region)
        # convert to local timezone
        # dt_now = datetime.datetime.now().astimezone(pytz.utc)
        today = dt - datetime.timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond)
        to_zone = tz.gettz(region.timezone)
        today = today.astimezone(to_zone)
        dt = dt.astimezone(to_zone)
        dayOfWeek = today.weekday()
        # # import functions
        # r = gov.Region_obj
        # x = '%s as %s' %(gov.gov_level, r.Name)
        # while r.modelType != 'country':
        #     x = r.Name + '.' + x 
        #     r = r.ParentRegion_obj
        # x = 'import scrapers.' + x
        # print(x)
        # exec(x)
        # runTimes = exec(f'{region.Name}.runTimes')
        # functions = exec(f'{region.Name}.functions')
        f = ''
        for i in items_to_get:
            if not f or i.func == f:
                f = i.func
        scraperScripts = get_scraperScripts(gov)
        print('will fail here')
        # scraper_list, approved_models = get_scrape_duty(gov, dt)
        approved_models = scraperScripts.approved_models
        model_types = []
        exceptions = ['Update'] # these do not need to be stated in scraper approved_models
        for i in items_to_get:
            if i.object_type not in exceptions and i.object_type not in model_types:
                model_types.append(i.object_type)
        print('model_types', model_types)
        # mb_size = 0
        # for i in items_to_get:
        #     mb_size += to_megabytes(i)
        # print('mb_size1', mb_size)
        approved_funcs = []
        for key, value in approved_models.items():
            # print(key, value)
            result = all(item in value for item in model_types)
            # print(result)
            if result:
                approved_funcs.append(key)
        print('func', func)
        print('approved funcs', approved_funcs)
        data, not_found = get_data(items_to_get)
        # mb_size = 0
        # for i in data:
        #     mb_size += to_megabytes(i)
        # print('mb_size2', mb_size)
        if f == func and func in approved_funcs:
            try:
                self_node = get_self_node()
                print('self_node', self_node)
                # scraping_order = get_scraping_order(iden=region.id, func_name=func, dt=dt)
                # print('order', scraping_order)

                # for script, models in approved_models:
                    # if xModel.func == script and xModel.object_type in models:
                for i in scraper_list:
                    if self_node.id in i['scraping_order'][:number_of_scrapers]:
                        # good = True
                        # break
                # break
                    # elif xModel.func == script and xModel.object_type == 'Validator':
                    #     pass


                    # scrape_list = get_scrape_duty(gov, items[0].created)
                    # for v in scrape_list:
                    # if self_node.id in scraping_order[:number_of_scrapers]:

                        # if func in v['function']:
                        # for n in v['scrapers']:
                        validator_node = i['scraping_order'][-1]

                        broadcast_list = {self_node.id : [validator_node]}
                        
                        data, not_found = get_data(items_to_get)
                        # mb_size = 0
                        # for i in data:
                        #     mb_size += to_megabytes(i)
                        # print('mb_size2', mb_size)
                        json_data = {'type':'for_validation', 'function':func, 'gov_id':gov.id, 'content': data}
                        downstream_broadcast(broadcast_list, 'blockchain/receive_posts_for_validating', json_data)
            except Exception as e:
                print(str(e))

def share_all_with_network(items):
    from blockchain.models import get_latest_dataPacket
    datapacket = get_latest_dataPacket()
    for i in items:
        for x in i:
            share_with_network(x, datapacket=datapacket)

def share_with_network(item, post=None, datapacket=None):
    print('share with network')
    from blockchain.models import get_operatorData, get_latest_dataPacket, Node
    # print(item.object_type)
    # print(Node.objects.all().count())
    if item.object_type != 'DataPacket': 
        if item.object_type != 'Node' or item.object_type == 'Node' and Node.objects.all().count() > 1:
            # get item.region
            # may need to get INteraction.Region_obj
            try:
                if not item.blockchainType == 'NoChain':
                    # print('chain')
                    chain, obj, receiverChain = find_or_create_chain_from_object(item)
                    # print(chain)
                    chain.add_item_to_data(item)
                    # print('added1')
                    chainId = chain.id
            except Exception as e:
                print('nochain', str(e))
                chainId = None
            # print('get datatotsharfe')
            if not datapacket:
                datapacket = get_latest_dataPacket(chainId)
            if datapacket:
                # print('datapacket')
                # print(datapacket)
                datapacket.add_item_to_data(item)
                print('shared')
            # if item.object_type != 'Update' and post != False:
            #     try:
            #         if post == None:
            #             post = Post.objects.filter(pointerId=item.id)[0]
            #         datapacket.add_item_to_data(post)
            #     except:
            #         post = None
            #     print('done p')

def sign_obj(item):
    try:
        # print('try sign', item.signature, item.publicKey)
        from blockchain.models import get_signing_data, get_operatorData
        from accounts.models import sign
        data = get_operatorData()
        # print(data)
        # user = User.objects.filter()
        sig = sign(data['privKey'], get_signing_data(item))
        # print('newsig', sig)
        item.signature = sig
        item.publicKey = data['pubKey']
    except Exception as e:
        print(str(e))
    return item

def get_operator_pubKey():
    from blockchain.models import get_operatorData
    data = get_operatorData()
    return data['pubKey']

def initial_save(item, share=True):
    print()
    print('initial save')
    # print(item.object_type)
    # print(item)
    if item.id == '0':
        item.id = uuid.uuid4().hex
    if not item.created:
        item.created = now_utc()
    try:
        if not item.DateTime:
            item.DateTime = now_utc()
    except:
        pass
    # try:
    #     if not item.signature and not item.publicKey or item.signature == '0' and item.publicKey == '0':
    #         item = sign_obj(item)
    # except:
    #     pass
    try:
        if not item.blockchainType == 'NoChain':
            # print('chain')
            # print(item.blockchainId)
            chain, obj, secondChain = find_or_create_chain_from_object(item)
            # print(chain)
            item.blockchainId = chain.id
    except Exception as e:
        print('NoChain', str(e))
    try:
        print('try create post', item)
        model_name = item.object_type
        app_name = get_app_name(model_name)
        from django.apps import apps
        # print('app_name initial save', app_name)
        model = apps.get_model(app_name, model_name)
        # print(model)
        super(model, item).save()
        p = item.create_post(share=share)
        # print('created p, back to initial save, - pointerDateTime', p.pointerDateTime)
    except Exception as e:
        print('create post fail', str(e))
        p = False
        # time.sleep(5)
    

    # if not item.signature: # user content needs to come with signature, node scrapings, blocks, dataPackets and validators are signed by node
    #     from blockchain.models import private_key, get_user, get_signature_data
    #     item.signature = get_user().sign_transaction(base64.b64decode(private_key), str(get_signature_data(item)))
    #     # else:
    #     #     # this shouldn't be used
    #     #     user = get_user()
    #     #     if user.id == item.user_id:
    #     #         item.signature = user.sign_transaction(base64.b64decode(private_key), get_validation_data(item))
    #     #         item.save()
    # if share:
    #     share_with_network(item)
    print('done initial save')
    # time.sleep(0.25)
    
    
    # no_chains = ['Blockchain', 'Block', 'DataPacket', 'Validator', 'posttotals]
    # if item.signature and item.object_type not in no_chains:

    #     from blockchain.models import DataPacket, get_self_node
    #     dataPacket = DataPacket.objects.filter(creator_node_id=get_self_node().id)[0]
    #     dataPacket.add_item_to_data(item)
    #     if not item.automated:
    #         blockchain, item, receiverChain = find_or_create_chain_from_object(item)
    #         blockchain.add_item_to_data(item)
    #         if receiverChain:
    #             receiverChain.add_item_to_chain(item)
    return item

def new_post(obj):
    print('new_post()')
    try:
        p = Post.objects.filter(pointerId=obj.id)[0]
    except:
        p = Post(pointerId=obj.id)
    # is_valid = p.get_validator()
    is_valid = True
    if is_valid:
        # p.DateTime = obj.created
        p.DateTime = obj.DateTime
        # print('p.pointerDateTime', p.pointerDateTime)
        p.pointerId = obj.id
        p.pointerType = obj.object_type
        # p.blockchainType = obj.blockchainType
        # p.blockchainId = obj.blockchainId
        # p.pointerPublicKey = obj.publicKey
        p.keyword_array = []
        try:
            pointer_obj = obj.object_type + '_obj'
            setattr(p, pointer_obj, obj)
        except Exception as e:
            print(str(e))
        try:
            update = Update.objects.filter(pointerId=obj.id)[0]
            # print(update)
            p.Update_obj = update
            # p.updateId = update.id
        except:
            pass
        try:
            p.Country_obj = obj.Country_obj
        except:
            pass
        try:
            p.gov_level = obj.Government_obj.gov_level
        except:
            pass
        try:
            p.Government_obj = obj.Government_obj
        except:
            pass
        try:
            p.chamber = obj.chamber
        except:
            pass
        try:
            p.Region_obj = obj.Region_obj
        except:
            pass
        return p
    else:
        p.delete()
        return None

def find_post(obj):
    try:
        p = Post.objects.filter(pointerId=obj.id)[0]
    except:
        try:
            p = Archive.objects.filter(pointerId=obj.id)[0]
        except:
            p = None
    return p

def set_keywords(obj, direction, topic):
    #this is now done in javascript edit_user_array()
    from posts.models import skipwords
    if obj and obj.object_type == 'Interaction':
        if obj.Post:
            p = obj.Post
        elif obj.Archive:
            p = obj.Archive
        if obj.User:
            user = obj.User
        else:
            user = None
        keywords = p.keyword_array # topic == None
    elif obj and obj.object_type == 'User':
        user = obj
        keywords = ['%s' %(topic)]
    if user and user.interest_array and len(user.interest_array) >= 980: 
        remove_oldest = True
    else:
        remove_oldest = False
    if user:
        for k in keywords:
            if k not in skipwords and user.interest_array[-1] != k:
                try:
                    if remove_oldest:
                        user.interest_array.pop(0)
                    if direction == 'add':
                        user.interest_array.append(k[:100])
                    elif direction == 'remove':
                        user.interest_array.remove(k[:100])
                except Exception as e:
                    if direction == 'add':
                        user.interest_array = []
                        if remove_oldest:
                            user.interest_array.pop(0)
                        user.interest_array.append(k[:100])
    if user:
        user.save()
    return obj

def sync_model(xModel, jsonContent):
    from blockchain.models import get_user, get_node, get_signing_data, get_scrape_duty, number_of_scrapers
    from accounts.models import verify_obj_to_data
    print('sync model**')
    good = False
    try:
        # data may or not be json
        data = json.loads(jsonContent)
    except:
        data = jsonContent
    # print(xModel.__dict__)
    # print(data)
    try:
        if xModel.last_updated > datetime.datetime.fromisoformat(data['last_updated']):
            return xModel, good
    except:
        pass
    # user = None
    # # if xModel.id == jsonContent['id']:
    # try:
    #     user = xModel.User_obj
    #     if not user:
    #         fail
    # except:
    #     try:
    #         user = xModel.Node_obj.User_obj
    #         if not user:
    #             fail
    #     except:
    #         try:
    #             user = xModel.CreatorNode_obj.User_obj
    #             if not user:
    #                 fail
    #         except:
    #             try:
    #                 user = get_user(user_id=data['id'])
    #                 if not user:
    #                     fail
    #             except Exception as e:
    #                 user = get_user(public_key=data['publicKey'])
    #                 print()
    #                 print("data['publicKey']",data['publicKey'])
    #                 from accounts.models import UserPubKey
    #                 for u in UserPubKey.objects.all():
    #                     print('u', u.User_obj.display_name, u.publicKey)
    # print('user',user)
    # print()
    # print('data1:', str(get_signing_data(user)))
    # print()
    # print('data2:', str(get_signing_data(data)))
    # print()
    # is_valid = user.verify(get_signing_data(data), data['signature'])
    is_valid, user = verify_obj_to_data(xModel, data, return_user=True)
    userTypes = ['User', 'UserPubKey', 'Wallet', 'Transaction', 'UserVote', 'SavePost', 'Follow']
    if is_valid:  
        # print('xModel.object_type',xModel.object_type)
        if user.username == 'd704bb87a7444b0ab304fd1566ee7aba' or user.display_name == 'Sozed':
            good = True
        elif user.is_superuser:
            # check for a validator from a current superuser
            # good = True
            pass
        elif xModel.object_type == 'Spren' or xModel.object_type == 'SprenItem':
            # get list of Nodes with ai_capable, xModel.publicKey should match node.User_obj.get_keys()
            pass
        elif xModel.object_type in userTypes:
            try:
                if xModel.object_type == 'User':
                    print('xmodel is user')
                    user = xModel
                    try:
                        from accounts.models import User
                        current_user_data = User.objects.filter(id=user.id)[0]
                        if datetime.datetime.fromisoformat(data['last_updated']) < current_user_data.last_updated:
                            print("datetime.datetime.fromisoformat(data['last_updated']) < current_user_data.last_updated")
                            return xModel, good
                    except Exception as e:
                        print("sync user pass 1235", str(e))
                        pass
                # elif xModel.object_type == 'Transaction':
                #     user = xModel.sender_wallet_obj.User_obj
                # else:
                #     user = xModel.User_obj
                #     print('else user')
                if data['publicKey'] in [key.publicKey for key in user.get_keys()]:
                    good = True
            except Exception as e:
                print(str(e))
                pass
        if not good:
            print('x2')
            # verfiy which nodes were assigned to scrape and validate this data
            node = get_node(publicKey=data['publicKey'])
            scraper_list, approved_models = get_scrape_duty(data['Government_obj'], data['created'])
            for script, models in approved_models:
                if data['func'] == script and xModel.object_type in models:
                    for i in scraper_list:
                        if i['function_name'] == data['func'] and node.id in i['scraping_order'][:number_of_scrapers]:
                            good = True
                            break
                    break
                elif data['func'] == script and xModel.object_type == 'Validator':
                    for i in scraper_list:
                        if i['function_name'] == data['func'] and xModel.Node_obj.id == i['scraping_order'][-1]:
                            good = True
                            break
                    break

        if good:
            # print('is good')
            # print(xModel.__dict__['_wrapped'].__dict__)
            fields = xModel._meta.fields
            # print(fields)
            # print()
            superFields = ['is_supported', 'isVerified', 'is_superuser', 'is_staff', 'is_admin', 'ai_validated']
            for f in fields:
                # print(f.name)
                try:
                    # print(data[f.name])
                    if f.name in superFields:
                        if user.username == 'd704bb87a7444b0ab304fd1566ee7aba':
                            setattr(xModel, f.name, data[f.name])
                        else:
                            # print('sync pass 95684')
                            # check for a validator from a current superuser
                            # in cases of granting new superuser privilege
                            pass
                        
                    else:
                        # if xModel.object_type == 'User' and '_array' in f.name:
                        #     print('TARGET',f.name,data[f.name])
                        #     # setattr(xModel, f.name, data[f.name].replace("'", '"'))
                        #     setattr(xModel, f.name, ["test"])
                        if data[f.name] == 'None':
                            setattr(xModel, f.name, None)
                        else:
                            if str(f.name) == 'True' or str(f.name) == 'False':
                                setattr(xModel, f.name, data[f.name])
                            elif '_obj' in str(f.name):
                                id_field = str(f.name) + '_id'
                                setattr(xModel, id_field, data[f.name][:10000000])
                            else:
                                setattr(xModel, f.name, data[f.name][:10000000])
                except Exception as e:
                    print(str(e))
                # print()
            xModel.locked_to_chain = False
            xModel.save()
            # print(xModel.__dict__['_wrapped'].__dict__)
            try:
                if xModel.blockchainType != 'NoChain' and xModel.object_type != 'Region':
                    chain, obj, receiverChain = find_or_create_chain_from_object(xModel)
                    chain.add_item_to_data(xModel)
            except:
                pass
            try:
                xModel.create_post()
            except:
                pass
            try:
                xModel.update_post() # for Update_objs only
            except:
                pass
            # should also update interaction data (UserVotes)
            # should also update post_totals (interactions)
    return xModel, good

def sync_and_share_object(obj, received_json):
    # sync and share user created objs. ie: User, UserVote, SavePost, Node
    try:
        # data may or not be json
        data = json.loads(received_json)
    except:
        data = received_json
    # print('sync and share', data)
    # dataToShare = DataToShare.objects.filter(creator_node_id=get_self_node(IpAddr).id)[0]
    obj, good = sync_model(obj, data)
    if good:
        try:
            if not obj.blockchainType == 'NoChain':
                print('chain')
                chain, item, receiverChain = find_or_create_chain_from_object(obj)
                # print(chain)
                # chain.add_item_to_data(item)
                # print('added1')
                chainId = chain.id
        except Exception as e:
            print('nochain', str(e))
            chainId = None
        from blockchain.models import get_operatorData, get_latest_dataPacket
        dataToShare = get_latest_dataPacket(chainId)
        if dataToShare:
            dataToShare.add_item_to_data(obj)
    return obj, good

def search_and_sync_object(received_json, lock=None):
    from blockchain.models import find_or_create_chain_from_json, get_self_node
    databaseUpdated = False
    # return_data_to_sender = False
    postType = received_json['object_type']
    obj_data = received_json
    # dataToShare = DataToShare.objects.filter(creator_node_id=get_self_node(IpAddr).id)[0]
    # dataToShare_json = json.loads(dataToShare.data)
    # blockchain = Blockchain.objects.filter(genesisType=object_data['object_dict']['blockchainType'], genesisId=object_data['object_dict']['blockchainId'])[0]
    blockchain = find_or_create_chain_from_json(obj_data)
    
    if blockchain and blockchain.chainType == 'Region' and not blockchain.regionId in json.loads(get_latest_update(get_self_node().id).data):
        return None, False
    else:
        try:
            # look for model based on id
            obj = globals()[postType].objects.filter(id=obj_data['id'])[0]

        except:
            # user = get_user(user_id=obj_data['obj_dict']['user_id'])
            # signature_verified = user.verify_signature(get_expanded_data(obj_data['obj_dict']), obj_data['signature'])
            # if signature_verified:
            try:
                # get rid of this
                # look for model based on predefined fields for if multiple nodes are scraping the same thing
                filters = {}
                fields = [[fields for key, fields in item if key == postType] for item in correlate_items]
                for field in fields[0][0]:
                    filters[field] = obj[field]
                obj = globals[postType].objects.filter(**filters)[0]
                if json_dt > obj.last_updated:
                    obj = sync_model(obj, obj_data)
                elif obj.data_updated_time > json_dt:
                    return_data_to_sender = True
            except:
                # create model
                obj = globals()[postType]()
                # signature_verified = get_user(user_id=obj_data['obj_dict']['user_id']).verify_signature(obj_data['obj_dict'], obj_data['obj_dict']['signature'])
                obj, signature_verified = sync_model(obj, obj_data)
                if signature_verified:
                    # dataToShare.add_item_to_data(xModel)
                    blockchain.add_item_to_data(obj)
                # if xModel.id not in dataToShare_json:
                #     dataToShare_json.append([xModel.object_type, xModel.id])
                # if not xModel.locked_to_chain and xModel.id not in blockchain_data_json:
                #     blockchain_data_json.append([xModel.object_type, xModel.id])
                    databaseUpdated = True

        
        return obj, databaseUpdated

def find_or_create_chain_from_object(obj):
    print('find_or_create_chain_from_object')
    from blockchain.models import Blockchain, NodeChain_genesisId
    blockchain = None
    secondChain = None
    if obj.blockchainId:
        return Blockchain.objects.filter(id=obj.blockchainId)[0], obj, None
    ChainTypes = ['Region', 'Wallet', 'Nodes', 'SoMeta', 'Users']
    print('get blockchainType', obj.blockchainType)
    if obj.blockchainType == 'NoChain':
        return blockchain, obj, secondChain
    elif obj.blockchainType in ChainTypes:
        # print('yes')
        if obj.blockchainType == obj.object_type:
            blockchain = Blockchain(genesisId=obj.id, genesisType=obj.object_type, created=obj.DateTime)
            blockchain.save()
        elif obj.blockchainType == 'Region':
            
            try:
                region = obj.Region_obj
            except:
                # is Interaction._obj, might not be being used
                from accounts.models import Interaction
                region = Interaction.objects.filter(User_obj=obj.User_obj, Post_obj__id=obj.pointerId)[0].Region_obj
            try:
                blockchain = Blockchain.objects.filter(genesisId=region.id)[0]
            except Exception as e:
                blockchain = Blockchain(genesisId=region.id, genesisType='Region', created=region.DateTime)
                blockchain.save()
                # secondChain = Blockchain(validatesPointerId=blockchain.id, genesisId=region.id, genesisType='Region', created=region.DateTime)
                # secondChain.save()
        elif obj.blockchainType == 'Nodes':
            try:
                blockchain = Blockchain.objects.filter(genesisId=NodeChain_genesisId)[0]
            except:
                blockchain = Blockchain(genesisId=NodeChain_genesisId, genesisType='Nodes', created=baseline_time())
        # elif obj.blockchainType == 'Validators':
        #     try:



        #         blockchain = Blockchain.objects.filter(genesisId=obj.blockchainId)[0]
        #     except:
        #         blockchain = Blockchain(genesisId=ValidatorChain_genesisId, genesisType='Validators', created=baseline_time())
        #         blockchain.save()
        # elif obj.blockchainType == 'Users':
        #     try:
        #         blockchain = Blockchain.objects.filter(genesisId=UserChain_genesisId)[0]
        #     except:
        #         blockchain = Blockchain(genesisId=UserChain_genesisId, genesisType='Users', created=baseline_time())
        #         blockchain.save()
        elif obj.object_type == 'Transaction': # wallet chain
            blockchain = Blockchain.objects.filter(id=obj.sender_wallet.blockchainId)[0]
            secondChain = Blockchain.objects.filter(id=obj.receiver_wallet.blockchainId)[0]
            if not obj.blockchainId:
                obj.blockchainId = obj.sender_wallet.blockchainId
            if not obj.receiverChainId:
                obj.receiverChainId = obj.receiver_wallet.blockchainId
        elif obj.object_type == 'Wallet':
            try:
                blockchain = Blockchain.objects.filter(genesisId=obj.id)[0]
            except Exception as e:
                print(str(e))
                blockchain = Blockchain(genesisId=obj.id, genesisType='Wallet', created=obj.created)
                blockchain.save()

    return blockchain, obj, secondChain


def get_data(items):
    print('get data sgtart')
    from blockchain.models import Validator
    mb_size = 0
    posts_size = 0
        # for i in items_to_get:
    obj_types = {}
    iden_list = []
    not_found = []
    for i in items:
        # print(i)
        if isinstance(i, dict):
            try:
                obj_types[i['object_type']].append(i['obj_id'])
            except:
                obj_types[i['object_type']] = [i['obj_id']]
            iden_list.append(i['obj_id'])
        else:
            try:
                obj_types[i.object_type].append(i.id)
            except:
                obj_types[i.object_type] = [i.id]

            iden_list.append(i.id)
    # data = {'objects' : [], 'posts' : [], 'updates' : [], 'references' : []}
    data = []
    validators = Validator.objects.filter(data__overlap=iden_list).exclude(id__in=iden_list)
    for obj in validators:
        is_valid = verify_obj_to_data(obj, obj)
        if is_valid:
            data.append(model_to_dict(obj))
            mb_size += to_megabytes(obj)
    for obj_type, idList in obj_types.items():
        objs = get_dynamic_model(obj_type, list=True, id__in=idList)
        for obj in objs:
            is_valid = verify_obj_to_data(obj, obj)
            if is_valid:
                data.append(model_to_dict(obj))
                mb_size += to_megabytes(obj)
            # if o.object_type == 'Post':
            #     posts_size += to_megabytes(o)
    updates = Update.objects.filter(pointerId__in=iden_list).exclude(id__in=iden_list)
    for obj in updates:
        is_valid = verify_obj_to_data(obj, obj)
        if is_valid:
            data.append(model_to_dict(obj))
            mb_size += to_megabytes(obj)
    keyphrases = get_dynamic_model('Keyphrase', list=True, pointerId__in=iden_list)
    for obj in keyphrases:
        is_valid = verify_obj_to_data(obj, obj)
        if is_valid:
            data.append(model_to_dict(obj))
            mb_size += to_megabytes(obj)
    notifications = get_dynamic_model('Notification', list=True, pointerId__in=iden_list)
    for obj in notifications:
        is_valid = verify_obj_to_data(obj, obj)
        if is_valid:
            data.append(model_to_dict(obj))
            mb_size += to_megabytes(obj)
    # try:
    #     posts = Post.objects.filter(pointerId__in=iden_list).exclude(id__in=iden_list)
    #     for p in posts:
    #         data.append(p.__dict__)
    #         mb_size += to_megabytes(p)
    #         posts_size += to_megabytes(o)
    # except Exception as e:
    #     print(str(e))
    for i in items:
        if isinstance(i, dict):
            iden = i['obj_id']
        else:
            iden = i.id
        if iden not in data:
            not_found.append(i)
    print('mb_size', mb_size)
    print('posts_size', posts_size)
    return data, not_found
             
# not used
def get_data_with_relationships(items):
    obj_types = {}
    iden_list = []
    post_idens = []
    not_found = []
    for i in items:
        try:
            obj_types[i[0]].append(i[1])
        except:
            obj_types[i[0]] = [i[1]]
        iden_list.append(i[1])
        post_idens.append(i[1])
    data = {'objs' : [], 'posts' : [], 'updates' : [], 'references' : []}
    for t in obj_types:
        objs = globals()[t].objects.filter(id__in=obj_types[t])
        for o in objs:
            data['objs'].append(o.__dict__)

        try:
            if o.referenceId:
                p = globals()[o.referenceType].objects.filter(id=o.referenceId)[0]
                data['references'].append(p.__dict__)
                post_idens.append(p.id)
        except Exception as e:
            print(str(e))
    for i in items:
        if i[1] not in data['objects']:
            not_found.append(i)
    try:
        updates = Update.objects.filter(pointerId__in=iden_list).order_by('-created')[0]
        for u in updates:
            data['updates'].append(u.__dict__)
            post_idens.append(u.id)
    except Exception as e:
        print(str(e))
        try:
            from accounts.models import UserOptions
            updates = UserOptions.objects.filter(pointerId__in=iden_list).order_by('-created')[0]
            for u in updates:
                data['updates'].append(u.__dict__)
                post_idens.append(u.id)
        except Exception as e:
            print(str(e))
    try:
        # get posts for any xmodel, update, reference
        posts = Post.objects.filter(pointerId__in=post_idens)
        for p in posts:
            data['posts'].append(p.__dict__)
    except Exception as e:
        print(str(e))

    return data, not_found

def get_app_name(model_name):
    accounts_models = ['Sonet', 'User', 'UserPubKey', 'Verification', 'Wallet', 'Transaction','Notification','Interactions','UserVote','SavePost']
    blockchain_models = ['DataPacket','Node','NodeUpdate','Block','Validator','Blockchain']

    if model_name in accounts_models:
        app_name = 'accounts'
    elif model_name in blockchain_models:
        app_name = 'blockchain'
    else:
        app_name = 'posts'
    return app_name

def get_dynamic_model(model_name, list=False, **kwargs):
    # print('get dynamic model', model_name)
    app_name = get_app_name(model_name)
    from django.apps import apps
    # print('app_name', app_name)
    model = apps.get_model(app_name, model_name)
    # print(model)
    # print(kwargs)
    if not model:
        return None
    if list:
        if list == True:
            try:
                return model.objects.filter(**kwargs)
            except model.DoesNotExist:
                return None
        else:
            try:
                return model.objects.filter(**kwargs)[list[0]:list[1]]
            except model.DoesNotExist:
                return None
            
    else:
        try:
            return model.objects.filter(**kwargs).first()
        except Exception as e:
            print(str(e))
            return None

def create_dynamic_model(model_name, **kwargs):
    # print('create_dynamic_model')
    app_name = get_app_name(model_name)
    from django.apps import apps
    model = apps.get_model(app_name, model_name)
    obj = model(**kwargs)
    # print(obj.__dict__)
    if not obj.created:
        obj.created = now_utc()
    if not obj.id:
        obj.id = uuid.uuid4().hex
    # print(obj.__dict__)
    return obj

def get_or_create_model(model_name, **kwargs):
    # print('get_or_create_model')
    obj = get_dynamic_model(model_name, **kwargs)
    # print(obj)
    if not obj:
        obj = create_dynamic_model(model_name, **kwargs)
        # print(obj)
    return obj

def get_model_and_update(model_name, obj=None, new_model=False, **kwargs):
    print('get model and update', model_name)
    # print(model_name)
    # print(kwargs)
    if not obj:
        if not new_model:
            obj = get_dynamic_model(model_name, **kwargs)
            # obj = globals()['Meeting'].objects.filter(**kwargs)[0]
            new_model = False
        if not obj:
            obj = create_dynamic_model(model_name, **kwargs)
            # obj.save(share=False)
            new_model = True
    else:
        new_model = new_model
    # print('new_model',new_model)
    # print(obj)
    # skipUpdate = ['Region', 'District']
    # if obj.object_type in skipUpdate:
    #     update = None
    #     update_data = {}
    # else:
    u = Update(pointerId=obj.id, pointerType=obj.object_type)
    update = u.create_next_version(obj=obj)
    update_data = json.loads(update.data)
    return obj, update, update_data, new_model

def save_and_return(obj, update, updateData, obj_is_new, shareData, func):
    print()
    print('-----')
    print('save and return, obj_is_new:', obj_is_new)
    result = []

    # if not self.data:
    #         return None, False
    field_names = [field.name for field in obj._meta.fields]
    # print(field_names)
    query_kwargs = {field: getattr(obj, field) for field in field_names}
    # print(query_kwargs)
    match = get_dynamic_model(obj.object_type, list=False, **query_kwargs)
    if not match:

        obj_is_new = True
        obj.func = func
        obj.save(share=False)
        if update:
            update.pointerId = obj.id 
            update.pointerType = obj.object_type
        result.append(obj)
        # print('saved new object')
        # try:
        #     p = Post.objects.filter(pointerId=obj.id)[0]
        #     result.append(p)
        # except:
        #     pass
    # print(updateData)
    skipUpdate = ['Region', 'District']
    if obj.object_type not in skipUpdate:
        update.func = func
        update.data = json.dumps(updateData)
        update, u_is_new = update.save_if_new(share=False)
        if u_is_new:
            result.append(update)
    if result:
        shareData.append(result)
    print('----done save and return')
    return obj, update, updateData, obj_is_new, shareData

# dont use
def save_obj_and_update(obj, update, updateData, obj_is_new, share=False):
    print('save obj and update', obj)
    # print(obj)
    result = []
    if obj_is_new:
        print('obj_is_new')
        # obj.id = '0'
        # obj = sign_obj(obj)
        obj.save(share=share)
        update.pointerId=obj.id 
        update.pointerType=obj.object_type
        result.append(obj)
        # try:
        #     p = Post.objects.filter(pointerId=obj.id)[0]
        #     result.append(p)
        # except:
        #     pass
    print(updateData)
    update.data = json.dumps(updateData)
    update, u_is_new = update.save_if_new(share=share)
    print('u_is_new', u_is_new)
    if u_is_new:
        result.append(update)
    print('done save obj and update', result)
    return result

def superDelete(obj):
    if not obj.locked_to_chain:
        try:
            updates = Update.objects.filter(pointerId=obj.id)
            for u in updates:
                u.delete()
        except:
            pass
        try:
            p = Post.objects.filter(pointerId=obj.id)[0]
            p.delete()
        except:
            pass
        try:
            keys = Keyphrase.objects.filter(pointerId=obj.id)
            for k in keys:
                k.delete()
        except:
            pass
        # print('try create post', item)
        model_name = obj.object_type
        app_name = get_app_name(model_name)
        from django.apps import apps
        # print('app_name', app_name)
        model = apps.get_model(app_name, model_name)
        # if not self.signature:
        # sign_obj(self)
        # super(model, item).save()
        super(model, obj).delete()


class Person(BaseModel):
    object_type = "Person"
    blockchainType = 'Region'
    modelVersion = models.CharField(max_length=50, default="v1")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=True)
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    Honorific = models.CharField(max_length=100, blank=True, null=True, default="")
    FirstName = models.CharField(max_length=100, blank=True, null=True, default="")
    LastName = models.CharField(max_length=100, blank=True, null=True, default="")
    FullName = models.CharField(max_length=200, default="")
    # Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    # Region_obj = models.ForeignKey('posts.Region', blank=True, null=True, on_delete=models.SET_NULL)
    Party_obj = models.ForeignKey('posts.Party', blank=True, null=True, on_delete=models.SET_NULL)
    District_obj = models.ForeignKey('posts.District', blank=True, null=True, on_delete=models.SET_NULL)
    # party_name = models.CharField(max_length=100, blank=True, null=True, default="")
    # province_name = models.CharField(max_length=100, blank=True, null=True, default="")
    # constituency_name = models.CharField(max_length=152, blank=True, null=True, default="")
    GovernmentPosition = models.CharField(max_length=1000, blank=True, null=True)
    GovProfilePage = models.CharField(max_length=500, blank=True, null=True)
    Website = models.URLField(null=True, blank=True)
    AvatarLink = models.CharField(max_length=400, blank=True, null=True)
    SmallAvatarLink = models.URLField(null=True, blank=True)
    Gender = models.CharField(max_length=15, blank=True, null=True)
    Email = models.EmailField(blank=True, null=True)
    Telephone = models.CharField(max_length=15, blank=True, null=True)
    XTwitter = models.URLField(null=True, blank=True)
    Wikipedia = models.URLField(null=True, blank=True)
    Bio = models.TextField(blank=True, null=True)
    GovIden = models.IntegerField(default=0)

    def __str__(self):
        return 'PERSON:%s %s' %(self.FirstName, self.LastName)

    def first_last(self):
        return '%s %s' %(self.FirstName, self.LastName)

    def get_name(self):
        if self.Honorific:
            return '%s %s %s' %(self.Honorific, self.FirstName, self.LastName)
        else:
            return '%s %s' %(self.FirstName, self.LastName)
        
    class Meta:
        ordering = ["LastName", 'FirstName', 'id']

    def get_absolute_url(self):
        #return reverse("sub", kwargs={"subject": self.name})
        return "/profile/%s/%s_%s" % (self.id, self.FirstName.replace(' ', '_'), self.LastName.replace(' ', '_'))
    
    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
            if not self.FullName:
                self.FullName = self.first_last()
            # self.create_post()
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Person, self).save()

    def create_post(self, share=False):
        from posts.models import Post, Archive, Keyphrase
        p = new_post(self)
        # self.FullName = self.first_last()
        # self.save()
        p.keyword_array = []
        p.keyword_array.append(self.first_last()) 
        # try:
        #     keyphrase = Keyphrase.objects.filter(pointerType=self.object_type, pointerId=self.id)[0]
        # except:
        #     keyphrase = Keyphrase(pointerType=self.object_type, pointerId=self.id, text=self.first_last()) 
        #     keyphrase.save(share=share)
        p.save(share=share)

    def delete(self):
        superDelete(self)
        # if not self.locked_to_chain:
        #     try:
        #         p = Post.objects.filter(pointerId=self.id)[0]
        #         p.delete()
        #     except:
        #         pass
        #     keys = Keyphrase.objects.filter(pointerId=self.id)
        #     for k in keys:
        #         k.delete()
        #     if not self.signature:
        # sign_obj(self)
            # super(Person, self).delete()



class Region(models.Model):
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    func = models.CharField(max_length=50, default="")
    object_type = "Region"
    blockchainType = 'Region'
    modelVersion = models.CharField(max_length=50, default="v1")
    publicKey = models.CharField(max_length=200, default="")
    signature = models.CharField(max_length=200, default="")
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    ParentRegion_obj = models.ForeignKey('posts.Region', blank=True, null=True, on_delete=models.SET_NULL)
    nameType = models.CharField(max_length=100, default="State") # Continent, Country, Province, State, City, Ward
    Name = models.CharField(max_length=100, default="")
    AbbrName = models.CharField(max_length=100, default="", blank=True, null=True)
    # Logo = models.FileField(upload_to='static_cdn/img/provinces/', null=True, blank=True)
    LogoLink = models.CharField(max_length=100, default="/static/img/default_region.jpg", null=True, blank=True)
    # getAiSummary = models.BooleanField(default=False)
    Wikipedia = models.URLField(default='', null=True, blank=True)
    modelType = models.CharField(max_length=100, default="provState", null=True, blank=True) # provState/country/city
    timezone = models.CharField(max_length=100, default="US/Eastern", null=True, blank=True)
    menuItems = models.CharField(max_length=100, default="[]", null=True, blank=True)
    is_supported = models.BooleanField(default=False)

    def __str__(self):
        return 'REGION:%s' %(self.Name)

    # def logo_link(self):
    #     return "static/img/%s" %(self.LogoLink)

    class Meta:
        ordering = ["created"]

    def lowerName(self):
        return self.Name.lower()

    def return_menu_items(self):
        # x = ['Debates','Bills','Motions','Officials','Elections']
        # self.menuItems = json.dumps(x)
        # self.save()
        try:
            return json.loads(self.menuItems)
        except Exception as e:
            print(str(e))
            return None

    def save(self, share=False):

        # FIX THIS
        if self.is_supported:
            # only super user can add/remove is_supported
            support = True
        else:
            support = False
        if self.id == '0':
            self = initial_save(self, share=share)
            # self.create_post()
        else:
            from accounts.models import User, UserPubKey
            for u in User.objects.filter(is_superuser=True):
                for upk in UserPubKey.objects.filter(User_obj=u):
                    if upk.publicKey == self.publicKey:
                        from blockchain.models import get_signing_data
                        is_valid = upk.verify(get_signing_data(self), self.signature)
                        if is_valid:
                            super(Region, self).save()
                            break
            # if not self.signature:
            #     sign_obj(self)
            # elif self.publicKey == get_operator_pubKey():
            #     sign_obj(self)
        super(Region, self).save()

    def create_post(self, share=False):
        # from posts.models import Post
        p = new_post(self)
        p.save(share=share)


    def delete(self):
        superDelete(self)

class District(BaseModel):
    object_type = "District"
    # blockchainType = 'Region'
    modelVersion = models.CharField(max_length=50, default="v1")
    
    # Government_obj = models.ForeignKey('posts.Government', blank=True, null=True, on_delete=models.RESTRICT)
    modelType = models.CharField(max_length=100, default="") #federal, provState, municipal
    nameType = models.CharField(max_length=100, default="") # Riding, District, Ward
    Name = models.CharField(max_length=100, default="")
    AltName = models.CharField(max_length=100, default="")
    gov_level = models.CharField(max_length=100, default="", blank=True, null=True) # Federal, Provincial, State, Greater Municipal, Municipal
    # province_name = models.CharField(max_length=100, default="")
    # Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    ProvState_obj = models.ForeignKey(Region, related_name='%(class)s_provstate_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Region_obj = models.ForeignKey(Region, related_name='%(class)s_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    Population = models.IntegerField(default=0, blank=True, null=True)
    StartDate = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    MapLink = models.URLField(null=True, blank=True)
    InfoLink = models.URLField(null=True, blank=True)
    Info = models.TextField(blank=True, null=True)
    # opennorthId = models.IntegerField(default=0, blank=True, null=True)
    Wikipedia = models.URLField(null=True, blank=True)


    def __str__(self):
        return 'DISTRICT:%s %s' %(self.Name, '1')

    class Meta:
        ordering = ["Name"]

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
            # self.create_post()
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(District, self).save()

    def create_post(self, share=False):
        p = new_post(self)
        p.save(share=share)



    def delete(self):
        superDelete(self)

    def fillout(self):
        print('fillout - Riding: %s' %(self.Name))
        try:
            if not self.map_link:
                chrome_options = Options()
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument("--headless")
                driver = webdriver.Chrome(options=chrome_options)
                caps = DesiredCapabilities().CHROME
                caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
                # caps["pageLoadStrategy"] = "eager"   # Do not wait for full page load
                driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
                print(self.parlinfo_link)
                driver.get(self.parlinfo_link)
                element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="RidingPic"]'))
                WebDriverWait(driver, 10).until(element_present)
                div = driver.find_element(By.ID, 'RidingPic')
                img = div.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                self.map_link = img
                div = driver.find_element(By.ID, 'RidingInfo')
                h = div.find_element(By.CSS_SELECTOR, 'h2').text
                a = h.find('(')
                b = h[a:].find(' - ')
                date = h[a:a+b]
                try:
                    date_time = datetime.datetime.strptime(date, '(%Y-%m-%d')
                    self.StartDate = date_time
                except:
                    try:
                        date_time = datetime.datetime.strptime(date, '(%Y-%m')
                        self.StartDate = date_time
                    except:
                        pass
                text = driver.find_element(By.ID, 'RidingNotes').text
                self.info = text
                driver.close()
                # wikipedia
            if not self.wikipedia:
                name = '%s %s federal electoral district' %(self.Name, self.Region_obj.Name)
                title = wikipedia.search(name)[0].replace(' ', '_')
                self.wikipedia = 'https://en.wikipedia.org/wiki/' + title
                # if not self.img_link:
                #     r = requests.get('https://en.wikipedia.org/wiki/' + title)
                #     soup = BeautifulSoup(r.content, 'html.parser')
                #     td = soup.find('td', {'class':'logo'})
                #     img = td.find('img')['src']
                #     self.img_link = img

                    # name = '%s Canada' %(self.name)
                    # print(name)
                    # driver.get("https://en.wikipedia.org/wiki/Main_Page")
                    # element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="searchInput"]'))
                    # WebDriverWait(driver, 15).until(element_present)
                    # # time.sleep(1)
                    # searchbox = driver.find_element(By.XPATH, '//*[@id="searchInput"]')
                    # searchbox.send_keys(name)
                    # time.sleep(1)
                    # search_enter = driver.find_element(By.XPATH, '//*[@id="searchform"]/div/button')
                    # # searchbox.send_keys(Keys.RETURN)
                    # search_enter.click()
                    # # time.sleep(1)
                    # element_present = EC.presence_of_element_located((By.CLASS_NAME, 'mw-search-results-container'))
                    # WebDriverWait(driver, 10).until(element_present)
                    # # time.sleep(1)
                    # div = driver.find_element(By.CLASS_NAME, 'mw-search-results-container')
                    # li = div.find_element(By.CSS_SELECTOR, 'li')
                    # d = li.find_element(By.CLASS_NAME, 'mw-search-result-heading')
                    # a = d.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    # self.wikipedia = a
                    # if not self.map_link: 
                    #     driver.get(a)
                    #     td = driver.find_element(By.CLASS_NAME, 'infobox-image')
                    #     img = td.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                    #     self.map_link = img
            self.save()
        except Exception as e:
            print(str(e))
            self.save()



class Party(BaseModel):
    object_type = "Party"
    blockchainType = 'Region'
    modelVersion = models.CharField(max_length=50, default="v1")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=True)
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    Name = models.CharField(max_length=100, default="", blank=True, null=True)
    AltName = models.CharField(max_length=100, default="", blank=True, null=True)
    gov_level = models.CharField(max_length=20, default="", blank=True, null=True)
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    # province_name = models.CharField(max_length=100, default="", blank=True, null=True)
    # Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    # Region_obj = models.ForeignKey(Region, blank=True, null=True, on_delete=models.RESTRICT)
    Leader = models.CharField(max_length=30, default="", blank=True, null=True)
    Colour = models.CharField(max_length=30, default="#C0C0C0")
    InfoLink = models.URLField(null=True, blank=True)
    LogoLink = models.URLField(null=True, blank=True)
    StartDate = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    EndDate = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    Website = models.URLField(null=True, blank=True)
    Wikipedia = models.URLField(null=True, blank=True)

    def __str__(self):
        return 'PARTY:%s-%s' %(self.Name, self.gov_level)

    class Meta:
        ordering = ["Name"]

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
            # self.create_post()
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Party, self).save()

    def create_post(self, share=False):
        from posts.models import Post, Archive, Keyphrase
        p = new_post(self)
        p.keyword_array = []
        p.keyword_array.append(self.Name)
        # if self.level == 'Federal':
        #     organization = 'House'
        # else:
        #     organization = self.province_name
        # try:
        #     keyphrase = Keyphrase.objects.filter(pointerType=self.object_type, pointerId=self.id, text=self.Name)[0]
        # except:
        #     keyphrase = Keyphrase(pointerType=self.object_type, pointerId=self.id, chamber=self.chamber, text=self.Name) 
        #     keyphrase.save(share=share)
        if self.AltName:
            p.keyword_array.append(self.AltName) 
            # try:
            #     keyphrase = Keyphrase.objects.filter(pointerType=self.object_type, pointerId=self.id, text=self.AltName)[0]
            # except:
            #     keyphrase = Keyphrase(pointerType=self.object_type, pointerId=self.id, chamber=self.chamber, text=self.AltName) 
            #     keyphrase.save(share=share)
        p.save(share=share)



    def delete(self):
        superDelete(self)

    def fillout(self):
        #for federal only
        print('fillout - party: %s' %(self.Name))
        try:
            if not self.Leader:
                print('opening browser')
                chrome_options = Options()
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument("--headless")
                driver = webdriver.Chrome(options=chrome_options)
                caps = DesiredCapabilities().CHROME
                caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
                # caps["pageLoadStrategy"] = "eager"   # Do not wait for full page load
                driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
                # url= 'https://lop.parl.ca/sites/ParlInfo/default/en_CA/Parties/Profile?partyId=15161'
                print(self.InfoLink)
                driver.get(self.InfoLink)
                element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="gridPartyLeaders"]/div/div[5]'))
                WebDriverWait(driver, 15).until(element_present)
                # time.sleep(1)
                try:
                    div = driver.find_element(By.ID, 'PartyPic')
                    try:
                        img = div.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                        if 'LogoNA' not in img:
                            self.LogoLink = img
                    except:
                        self.LogoLink = None
                    try:
                        div = driver.find_element(By.ID, 'PartyInfo')
                        h = div.find_element(By.CSS_SELECTOR, 'h2').text
                        a = h.find('(')
                        b = h[a:].find(' - ')
                        date = h[a:a+b]
                        date_time = datetime.datetime.strptime(date, '(%Y-%m-%d')
                        self.start_date = date_time
                    except:
                        pass
                    info = div.find_elements(By.CSS_SELECTOR, 'p')
                    for i in info:
                        if 'Last Official Leader' in i.text:
                            print(i.text)
                            try:
                                l = i.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                                role = Role.objects.filter(GovPage=l)[0]
                                p = role.Person_obj
                                self.Leader = '%s, %s' %(p.LastName, p.FirstName)
                                try:
                                    r = Role.objects.get(Person_obj=p, Position='Party Leader')
                                except:
                                    r = Role(Person_obj=p, Current=True, Position='Party Leader')
                                r.Current = True
                                r.save()
                            except Exception as e:
                                print(str(e))
                                self.Leader = i.text.replace('Last Official Leader: ', '')
                    website = div.find_element(By.CSS_SELECTOR, 'tr').find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    self.Website = website
                except Exception as e:
                    print(str(e))
                driver.close()
                # wikipedia
            if not self.Wikipedia:
                name = '%s Canada' %(self.Name)
                title = wikipedia.search(name)[0].replace(' ', '_')
                self.Wikipedia = 'https://en.wikipedia.org/wiki/' + title
                if not self.LogoLink:
                    r = requests.get('https://en.wikipedia.org/wiki/' + title)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    td = soup.find('td', {'class':'logo'})
                    img = td.find('img')['src']
                    self.LogoLink = img
                    # print(name)
                    # driver.get("https://en.wikipedia.org/wiki/Main_Page")
                    # element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="searchInput"]'))
                    # WebDriverWait(driver, 15).until(element_present)
                    # # time.sleep(1)
                    # searchbox = driver.find_element(By.XPATH, '//*[@id="searchInput"]')
                    # searchbox.send_keys(name)
                    # time.sleep(1)
                    # search_enter = driver.find_element(By.XPATH, '//*[@id="searchform"]/div/button')
                    # # searchbox.send_keys(Keys.RETURN)
                    # search_enter.click()
                    # # time.sleep(1)
                    # element_present = EC.presence_of_element_located((By.CLASS_NAME, 'mw-search-results-container'))
                    # WebDriverWait(driver, 10).until(element_present)
                    # # time.sleep(1)
                    # div = driver.find_element(By.CLASS_NAME, 'mw-search-results-container')
                    # li = div.find_element(By.CSS_SELECTOR, 'li')
                    # d = li.find_element(By.CLASS_NAME, 'mw-search-result-heading')
                    # a = d.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    # self.wikipedia = a
                    # if not self.img_link: 
                    #     driver.get(a)
                    #     td = driver.find_element(By.CLASS_NAME, 'infobox-image')
                    #     img = td.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
                    #     self.img_link = img
            self.save()
        except Exception as e:
            print(str(e))
            self.save()

class Role(BaseModel):
    object_type = "Role"
    blockchainType = 'Region'
    modelVersion = models.CharField(max_length=50, default="v1")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # automated = models.BooleanField(default=True)
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    Person_obj = models.ForeignKey(Person, blank=True, null=True, on_delete=models.CASCADE)
    # Government_obj = models.ForeignKey('posts.Government', blank=True, null=True, on_delete=models.SET_NULL)
    # Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    # riding = models.ForeignKey(Riding, blank=True, null=True, on_delete=models.SET_NULL)
    District_obj = models.ForeignKey(District, related_name='%(class)s_district_obj', blank=True, null=True, on_delete=models.SET_NULL)
    ProvState_obj = models.ForeignKey(Region, blank=True, related_name='%(class)s_provstate_obj', null=True, on_delete=models.RESTRICT)
    # Region_obj = models.ForeignKey(Region, blank=True, related_name='%(class)s_region_obj', null=True, on_delete=models.RESTRICT)
    # municipality = models.ForeignKey(Municipality, blank=True, null=True, on_delete=models.SET_NULL)
    # ward = models.ForeignKey(Ward, blank=True, null=True, on_delete=models.SET_NULL)
    # schoolBoardRegion = models.ForeignKey(SchoolBoardRegion, blank=True, null=True, on_delete=models.SET_NULL)
    Party_obj = models.ForeignKey(Party, blank=True, null=True, on_delete=models.SET_NULL)
    Committee_obj = models.ForeignKey('posts.Committee', related_name='%(class)s_committee_obj',  blank=True, null=True, on_delete=models.CASCADE)
    Election_obj = models.ForeignKey('posts.Election', blank=True, null=True, on_delete=models.SET_NULL)
    StartDate = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    EndDate = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    LogoLink = models.CharField(max_length=400, blank=True, null=True)
    Title = models.CharField(max_length=200, default="", blank=True, null=True) #exmaple chair or member
    GovernmentNumber = models.CharField(max_length=10, default="", blank=True, null=True)
    gov_level = models.CharField(max_length=100, default="", blank=True, null=True) # Federal, Provincial, State, Greater Municipal, Municipal
    # person_name = models.CharField(max_length=101, default="", blank=True, null=True)
    # party_name = models.CharField(max_length=102, default="", blank=True, null=True)
    # riding_name = models.CharField(max_length=103, default="", blank=True, null=True)
    # district_name = models.CharField(max_length=152, default="", blank=True, null=True)
    # municipality_name = models.CharField(max_length=104, default="", blank=True, null=True)
    # ward_name = models.CharField(max_length=105, default="", blank=True, null=True)
    Position = models.CharField(max_length=200, default="", blank=True, null=True) #example MP or committee member
    # constituency_name = models.CharField(max_length=106, default="", blank=True, null=True)
    # province_name = models.CharField(max_length=50, default="", blank=True, null=True)
    # attendanceCount = models.IntegerField(default=None, blank=True, null=True)
    # attendancePercent = models.IntegerField(default=None, blank=True, null=True)
    # quarterlyExpenseReport = models.FloatField(default=None, blank=True, null=True)
    Result = models.CharField(max_length=40, default="", blank=True, null=True)
    Group = models.CharField(max_length=300, default="", blank=True, null=True)
    ordered = models.IntegerField(default=0) # for ourcommons/roles and senator list page scrape
    # vote_count = models.IntegerField(default=0)
    # vote_percent = models.IntegerField(default=0)
    # occupation = ArrayField(models.CharField(max_length=20, blank=True, null=True, default='{default}'), size=6, null=True, blank=True)
    # Current = models.BooleanField(default=False)
    Affiliation = models.CharField(max_length=100, default="", blank=True, null=True)
    Occupation = models.CharField(max_length=100, default="", blank=True, null=True)
    GovPage = models.URLField(null=True, blank=True)
    # commons_page = models.URLField(null=True, blank=True)
    # commons_image = models.URLField(null=True, blank=True)
    # parlinfo_link = models.URLField(null=True, blank=True)
    Website = models.URLField(null=True, blank=True)
    Email = models.EmailField(blank=True, null=True)
    Fax = models.CharField(max_length=26, blank=True, null=True)
    Telephone = models.CharField(max_length=25, blank=True, null=True)
    Address = models.CharField(max_length=250, default="", blank=True, null=True)
    OfficeName = models.CharField(max_length=250, default="", blank=True, null=True)
    XTwitter = models.URLField(null=True, blank=True)

    def __str__(self):
        return 'ROLE:%s-%s: %s' %(self.Position, self.Title, self.Person_obj.FullName)

    class Meta:
        ordering = ["ordered","Position","-StartDate","-EndDate","Title",'created']
    
    def create_post(self, share=False):
        p = new_post(self)
        p.save(share=share)

    def save(self, share=True):
        if self.id == '0':
            self = initial_save(self, share=share)
        if not self.locked_to_chain:
            if not self.signature:
                sign_obj(self)
            elif self.publicKey == get_operator_pubKey():
                sign_obj(self)
            super(Role, self).save()


    def delete(self):
        superDelete(self)


class Post(models.Model):
    # posts will fail verification after receiving updates, still needs signature upon initial share, must be shared for common post.id
    object_type = "Post"
    # blockchainType = 'NoChain'
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    # modelVersion = models.CharField(max_length=50, default="v1")
    publicKey = models.CharField(max_length=200, default="0")
    signature = models.CharField(max_length=200, default="0")
    chamber = models.CharField(max_length=100, default="", db_index=True, blank=True, null=True)
    Region_obj = models.ForeignKey('posts.Region', related_name='%(class)s_region_obj', db_index=True, blank=True, null=True, on_delete=models.RESTRICT)
    Country_obj = models.ForeignKey('posts.Region', related_name='%(class)s_country_obj', db_index=True, blank=True, null=True, on_delete=models.CASCADE)
    Government_obj = models.ForeignKey('posts.Government', related_name='%(class)s_government_obj', blank=True, null=True, on_delete=models.SET_NULL)
    # DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    DateTime = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    modelVersion = models.CharField(max_length=50, default="v1")
    # validated = models.BooleanField(default=False) # is validated by validator nodes
    # ai_approved = models.BooleanField(default=False)
    gov_level = models.CharField(max_length=250, default="", blank=True, null=True)
    pointerId = models.CharField(max_length=50, default="")
    pointerType = models.CharField(max_length=50, default="")
    # updateId = models.CharField(max_length=50, default="")
    # pointerPublicKey = models.CharField(max_length=200, default="")
    Update_obj = models.ForeignKey('posts.Update', blank=True, null=True, on_delete=models.CASCADE)
    # History_obj = models.ForeignKey('posts.History', blank=True, null=True, on_delete=models.CASCADE)

    # Interaction_obj = models.ForeignKey('accounts.Interaction', blank=True, null=True, on_delete=models.CASCADE)
    Daily_obj = models.ForeignKey(Daily, blank=True, null=True, on_delete=models.CASCADE)
    Spren_obj = models.ForeignKey(Spren, blank=True, null=True, on_delete=models.CASCADE)
    Agenda_obj = models.ForeignKey(Agenda, blank=True, null=True, on_delete=models.CASCADE)
    AgendaTime_obj = models.ForeignKey(AgendaTime, blank=True, null=True, on_delete=models.CASCADE)
    Bill_obj = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.CASCADE)
    BillVersion_obj = models.ForeignKey(BillVersion, blank=True, null=True, on_delete=models.CASCADE)
    BillAction_obj = models.ForeignKey(BillAction, blank=True, null=True, on_delete=models.CASCADE)
    Meeting_obj = models.ForeignKey(Meeting, related_name='%(class)s_meeting_obj', blank=True, null=True, on_delete=models.CASCADE)
    Statement_obj = models.ForeignKey(Statement, blank=True, null=True, on_delete=models.CASCADE)
    Committee_obj = models.ForeignKey(Committee, related_name='%(class)s_committee_obj', blank=True, null=True, on_delete=models.CASCADE)
    Motion_obj = models.ForeignKey(Motion, blank=True, null=True, on_delete=models.CASCADE)
    Vote_obj = models.ForeignKey(Vote, blank=True, null=True, on_delete=models.CASCADE)
    Election_obj = models.ForeignKey(Election, blank=True, null=True, on_delete=models.CASCADE)
    Person_obj = models.ForeignKey('posts.Person', blank=True, null=True, on_delete=models.CASCADE)
    Party_obj = models.ForeignKey('posts.Party', blank=True, null=True, on_delete=models.CASCADE)
    District_obj = models.ForeignKey('posts.District', blank=True, null=True, on_delete=models.CASCADE)
    Role_obj = models.ForeignKey('posts.Role', blank=True, null=True, on_delete=models.CASCADE)



    rank = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    randomizer = models.IntegerField(default=0, null=True) 
    keyword_array = ArrayField(models.CharField(max_length=200, default='{default}'), size=20, blank=True, null=True, default=list)
    total_votes = models.IntegerField(default=0, null=True) 
    total_yeas = models.IntegerField(default=0, null=True) 
    total_nays = models.IntegerField(default=0, null=True) 
    total_voter_votes = models.IntegerField(default=0, null=True) 
    total_voter_yeas = models.IntegerField(default=0, null=True) 
    total_voter_nays = models.IntegerField(default=0, null=True) 
    total_comments = models.IntegerField(default=0, null=True) 
    total_saves = models.IntegerField(default=0, null=True) 
    total_shares = models.IntegerField(default=0, null=True) 

    def __str__(self):
        # for i in correlate_items_items:
        #     z = getattr(self, i)
        #     if z:
        #         return 'POST-%s' %(z)
        return 'POST-%s-%s' %(self.pointerType, self.id)     
    
    # def get_absolute_url(self):
    #     for item in post_items:
    #         for key, value in item:
    #             z = getattr(self, key)
    #             if z:
    #                 return z.get_absolute_url()

    
    def get_title(self):
        if self.Agenda_obj:
            return '%s agenda %s' %(self.Agenda_obj.chamber, datetime.datetime.strftime(self.Agenda_obj.DateTime, '%d/%m/%Y'))
        # elif self.agendaTime:
        #     return self.agendaTime.get_absolute_url()
        elif self.Bill_obj and self.Bill_obj.Title:
            return 'Bill %s %s' %(self.Bill_obj.NumberCode, self.Bill_obj.Title)
        elif self.Bill_obj and self.Bill_obj.LongTitle:
            return 'Bill %s %s' %(self.Bill_obj.NumberCode, self.Bill_obj.LongTitle)
        # elif self.billVersion:
        #     return self.billVersion.get_absolute_url()
        elif self.Meeting_obj:
            return '%s %s %s' %(self.Meeting_obj.chamber, self.Meeting_obj.meeting_type, self.Meeting_obj.DateTime)
        elif self.Statement_obj:
            if self.Statement_obj.Person_obj:
                return '%s Stated %s' %(self.Statement_obj.Person_obj.FullName, self.Statement_obj.DateTime)
            else:
                return '%s Stated %s' %(self.Statement_obj.PersonName, self.Statement_obj.DateTime)
        # elif self.committee:
        #     return '%s Debated %s' %(self.hansardItem.person_name, self.hansardItem.Item_date_time)
        # elif self.CommitteeMeeting_obj:
        #     return 'Committee %s %s' %(self.CommitteeMeeting_obj.Code, self.CommitteeMeeting_obj.DateTimeStart)
        # elif self.CommitteeItem:
        #     return '%s In Committee %s' %(self.CommitteeItem.Person.FullName, self.CommitteeItem.ItemDateTime)
        elif self.Motion_obj:
            return 'Bill %s Motion %s' %(self.Motion_obj.billCode, self.Motion_obj.DateTime)
        else:
            return '%s' %(self.pointerType)
        # elif self.vote:
        #     return self.vote.get_absolute_url()
        # elif self.person:
        #     return self.person.get_absolute_url()
        # elif self.party:
        #     return self.party.get_absolute_url()
        # elif self.district:
        #     return self.district.get_absolute_url()
        # elif self.riding:
        #     return self.riding.get_absolute_url()

    def tally_votes(self):
        try:
            return PostTotals.objects.filter(pointerId=self.id, created__gte=datetime.datetime.now() - datetime.timedelta(minutes=10))[0]
        except:
            totals = PostTotals(pointerId=self.id)
            totals.tally_totals()
            return totals

    def get_validator(self):
        from blockchain.models import Validator, get_signing_data
        try:
            v = Validator.objects.filter(pointerId=self.pointerId)[0]
            is_valid = v.Node_obj.User_obj.verify(str(get_signing_data(v)), v.signature)
        except:
            return False
        if is_valid:
            return True
        else:
            return False

    def get_pointer(self):
        # print('post get pointer')
        return get_dynamic_model(self.pointerType, id=self.pointerId)
        # return globals()[self.pointerType].objects.filter(id=self.pointerId)[0]

    def set_score(self):
        scoreMe(self)

    def save(self, share=False):
        print('save post')
        # print(self.__dict__)
        if self.id == '0':
            pointer = self.get_pointer()
            # print(pointer, pointer.DateTime)
            self.DateTime = pointer.DateTime
            # print('self.pointerDateTime22', self.pointerDateTime)
            pointer_obj = str(self.pointerType) + '_obj'
            setattr(self, pointer_obj, pointer)
            # print('pointer.id', pointer.id)
            post_id = hashlib.md5(str(pointer.object_type + pointer.id).encode('utf-8')).hexdigest()
            # print('post_id', post_id)
            self.id = post_id
            try:
                self.Government_obj = pointer.Government_obj
            except:
                pass
            try:
                self.chamber = pointer.chamber
            except:
                pass
            try:
                self.Country_obj = pointer.Country_obj
            except:
                pass
            try:
                self.Region_obj = pointer.Region_obj
            except:
                pass
            # if not pointer.automated:
            #     self.validated = True
            # self = initial_save(self, share=share)
        # print('self.pointerDateTime22aa', self.pointerDateTime)
        if self.rank == 0:
            self.set_score()
        # if not self.locked_to_chain:
            # if not self.signature:
            #     sign_obj(self)
            # elif self.publicKey == get_operator_pubKey():
            #     sign_obj(self)
        print('done save post')
        # print('self.pointerDateTime33', self.pointerDateTime)
        super(Post, self).save()

class PostHistory(models.Model):
    object_type = "PostHistory"
    blockchainType = 'NoChain'
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    data = models.TextField(default='{}', blank=True, null=True)

    def save(self, share=False):
        if self.id == '0':
            self = initial_save(self, share=share)
        super(PostHistory, self).save()

class PostTotals(BaseModel):
    # not saved to blockchain
    object_type = "PostTotals"
    blockchainType = 'NoChain'
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    gov_level = models.CharField(max_length=250, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='posttotals_region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    pointerId = models.CharField(max_length=50, default="0")
    pointerType = models.CharField(max_length=50, default="Post") # post or archive
    
    total_votes = models.IntegerField(default=0, null=True) 
    total_yeas = models.IntegerField(default=0, null=True) 
    total_nays = models.IntegerField(default=0, null=True) 
    total_voter_votes = models.IntegerField(default=0, null=True) 
    total_voter_yeas = models.IntegerField(default=0, null=True) 
    total_voter_nays = models.IntegerField(default=0, null=True) 
    total_comments = models.IntegerField(default=0, null=True) 
    total_saves = models.IntegerField(default=0, null=True) 
    total_shares = models.IntegerField(default=0, null=True) 

    def tally_totals(self):
        Interactions = Interaction.objects.filter(pointerId=self.pointerId).distinct('User_obj')
        self.total_votes = Interactions.count()
        self.total_yeas = len([r for r in Interactions if r.isYea])
        self.total_nays = len([r for r in Interactions if r.isNay])
        self.total_voter_votes = len([r for r in Interactions if r.User_obj.isVerified])
        self.total_voter_yeas = len([r for r in Interactions if r.isYea and r.User_obj.isVerified])
        self.total_voter_nays = len([r for r in Interactions if r.isNay and r.User_obj.isVerified])
        self.save()
        return self

    def save(self, share=False):
        if self.id == '0':
            self = initial_save(self, share=share)
        # if self.rank == 0:
        #     self.set_score()
        # if not self.locked_to_chain:
        #     if not self.signature:
        #         sign_obj(self)
        #     elif self.publicKey == get_operator_pubKey():
        #         sign_obj(self)
        super(PostTotals, self).save()

class Archive(BaseModel):
    object_type = "Archive"
    blockchainType = models.CharField(max_length=50, default="0")
    # blockchainId = models.CharField(max_length=50, default="0")
    # locked_to_chain = models.BooleanField(default=False)
    modelVersion = models.CharField(max_length=50, default="v1")
    # id = models.CharField(max_length=50, default="0", primary_key=True)
    # created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    validated = models.BooleanField(default=False) # is validated by validator nodes
    ai_approved = models.BooleanField(default=False)
    # publicKey = models.CharField(max_length=200, default="0")
    # signature = models.CharField(max_length=200, default="0")
    # chamber = models.CharField(max_length=100, default="", blank=True, null=True)
    gov_level = models.CharField(max_length=250, default="", blank=True, null=True)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='region_obj', blank=True, null=True, on_delete=models.RESTRICT)
    # Country_obj = models.ForeignKey('accounts.Region', related_name='archive_country_obj', blank=True, null=True, on_delete=models.CASCADE)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='archive_region_obj', blank=True, null=True, on_delete=models.CASCADE)
    # last_updated = models.DateTimeField(auto_now=True, auto_now_add=False, blank=True, null=True)
    pointerId = models.CharField(max_length=50, default="0")
    pointerType = models.CharField(max_length=50, default="0")
    pointerPublicKey = models.CharField(max_length=200, default="0")
    # date_time = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)


    Interaction_obj = models.ForeignKey('accounts.Interaction', blank=True, null=True, on_delete=models.CASCADE)
    Daily_obj = models.ForeignKey(Daily, blank=True, null=True, on_delete=models.CASCADE)
    Spren_obj = models.ForeignKey(Spren, blank=True, null=True, on_delete=models.CASCADE)
    Agenda_obj = models.ForeignKey(Agenda, blank=True, null=True, on_delete=models.CASCADE)
    AgendaTime_obj = models.ForeignKey(AgendaTime, blank=True, null=True, on_delete=models.CASCADE)
    Bill_obj = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.CASCADE)
    BillVersion_obj = models.ForeignKey(BillVersion, blank=True, null=True, on_delete=models.CASCADE)
    BillAction_obj = models.ForeignKey(BillAction, blank=True, null=True, on_delete=models.CASCADE)
    Meeting_obj = models.ForeignKey(Meeting, related_name='archive_meeting_obj', blank=True, null=True, on_delete=models.CASCADE)
    Statement_obj = models.ForeignKey(Statement, blank=True, null=True, on_delete=models.CASCADE)
    Committee_obj = models.ForeignKey(Committee, related_name='archive_committee_obj', blank=True, null=True, on_delete=models.CASCADE)
    # CommitteeMeeting_obj = models.ForeignKey(CommitteeMeeting, blank=True, null=True, on_delete=models.CASCADE)
    # CommitteeItem = models.ForeignKey(CommitteeItem, blank=True, null=True, on_delete=models.CASCADE)
    Motion_obj = models.ForeignKey(Motion, blank=True, null=True, on_delete=models.CASCADE)
    Vote_obj = models.ForeignKey(Vote, blank=True, null=True, on_delete=models.CASCADE)
    Election_obj = models.ForeignKey(Election, blank=True, null=True, on_delete=models.CASCADE)
    Person_obj = models.ForeignKey('posts.Person', blank=True, null=True, on_delete=models.CASCADE)
    Party_obj = models.ForeignKey('posts.Party', blank=True, null=True, on_delete=models.CASCADE)
    District_obj = models.ForeignKey('posts.District', blank=True, null=True, on_delete=models.CASCADE)
    # Region_obj = models.ForeignKey('accounts.Region', related_name='archive_region_obj', blank=True, null=True, on_delete=models.CASCADE)



    rank = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    randomizer = models.IntegerField(default=0, null=True) 
    keyword_array = ArrayField(models.CharField(max_length=200, blank=True, null=True, default='{default}'), size=20, null=True, blank=True, default=list)
    total_votes = models.IntegerField(default=0, null=True) 
    total_yeas = models.IntegerField(default=0, null=True) 
    total_nays = models.IntegerField(default=0, null=True) 
    total_voter_votes = models.IntegerField(default=0, null=True) 
    total_voter_yeas = models.IntegerField(default=0, null=True) 
    total_voter_nays = models.IntegerField(default=0, null=True) 
    total_comments = models.IntegerField(default=0, null=True) 
    total_saves = models.IntegerField(default=0, null=True) 
    total_shares = models.IntegerField(default=0, null=True) 

    def __str__(self):
        for i in post_items:
            z = getattr(self, i)
            if z:
                return 'ARCHIVEDPOST-%s' %(z)
        return 'ARCHIVEDPOST-%s' %(self.id) 
    
        # if self.daily:
        #     return 'Archive-%s' %(self.daily)
        # elif self.spren:
        #     return 'Archive-%s' %(self.spren)
        # elif self.agenda:
        #     return 'Archive-%s' %(self.agenda)
        # elif self.agendaTime:
        #     return 'Archive-%s' %(self.agendaTime)
        # elif self.bill:
        #     return 'Archive-%s' %(self.bill)
        # elif self.billVersion:
        #     return 'Archive-%s' %(self.billVersion)
        # elif self.billAction:
        #     return 'Archive-%s' %(self.billAction)
        # elif self.hansard_key:
        #     return 'Archive-%s' %(self.hansard_key)
        # elif self.hansardItem:
        #     return 'Archive-%s' %(self.hansardItem)
        # elif self.committee:
        #     return 'Archive-%s' %(self.committee)
        # elif self.committeeMeeting:
        #     return 'Archive-%s' %(self.committeeMeeting)
        # elif self.committeeItem:
        #     return 'Archive-%s' %(self.committeeItem)
        # elif self.motion:
        #     return 'Archive-%s' %(self.motion)
        # elif self.vote:
        #     return 'Archive-%s' %(self.vote)
        # elif self.election:
        #     return 'Archive-%s' %(self.election)
        # else:
        #     return 'Archive---%s' %(self.id)

    def createArchive(self, post):
        # self.id = post.id
        # self.created = post.created
        self.last_updated = post.last_updated
        # self.date_time = post.date_time
        # self.post_type = post.post_type
        # self.organization = post.organization
        # self.rank = post.rank
        # self.randomizer = post.randomizer
        # for k in post.keywords:
        #     self.keywords.append(k)
        # self.daily = post.daily
        # self.spren = post.spren
        # self.agenda = post.agenda
        # self.agendaTime = post.agendaTime
        # self.bill = post.bill
        # self.billVersion = post.billVersion
        # self.billAction = post.billAction
        # self.hansard_key = post.hansard_key
        # self.hansardItem = post.hansardItem
        # self.committee = post.committee
        # self.committeeMeeting = post.committeeMeeting
        # self.committeeItem = post.committeeItem
        # self.motion = post.motion
        # self.vote = post.vote
        # self.election = post.election
        # self.person = post.person
        # self.party = post.party
        # self.district = post.district
        # self.riding = post.riding
        # self.total_votes = post.total_votes
        # self.total_yeas = post.total_yeas
        # self.total_nays = post.total_nays
        # self.total_voter_votes = post.total_voter_votes
        # self.total_voter_yeas = post.total_voter_yeas
        # self.total_voter_nays = post.total_voter_nays
        # self.total_comments = post.total_comments
        # self.total_saves = post.total_saves
        # self.total_shares = post.total_shares
        fields = post._meta.get_fields(include_hidden=True)
        for f in fields:
            if str(f) != 'keyword_array':
                value = getattr(post, f)
                setattr(self, f, value)
        for k in post.keyword_arraay:
            self.keyword_array.append(k)
        self.save()
        Interactions = Interaction.objects.filter(post=post)
        for r in Interactions:
            r.archive = self
            r.save()

    def set_score(self):
        scoreMe(self)

class TopPost(models.Model):
    object_type = "TopPost"
    blockchain_type = 'Government'
    id = models.CharField(max_length=50, default="0", primary_key=True)
    created = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    post = models.ForeignKey(Post, blank=True, null=True, on_delete=models.SET_NULL)
    cycle = models.IntegerField(default=None, blank=True, null=True)
    chamber = models.CharField(max_length=20, default='', blank=True, null=True)
    country = models.CharField(max_length=20, default='', blank=True, null=True)
    
    def __str__(self):
        return 'TOPPOST:(%s-%s) %s/%s' %(self.created, self.cycle, self.chamber, self.country)
    
    class Meta:
        ordering = ['created']

    def save(self, share=False):
        if self.id == '0':
            self = initial_save(self, share=share)
        # if not self.locked_to_chain:
        # if not self.signature:
        # sign_obj(self)
        super(TopPost, self).save()


class MonitorPageForChange(models.Model):
    id = models.CharField(max_length=50, default="0", primary_key=True)
    link = models.URLField(null=True, blank=True)
    text = models.TextField(blank=True, null=True)
    new_text = models.TextField(blank=True, null=True)
    Region = models.ForeignKey('posts.Region', blank=True, null=True, on_delete=models.SET_NULL)

    def monitor(self):
        if self.new_text != self.text:
            from accounts.models import User
            User.objects.filter(username='Sozed')[0].alert('Page Monitor Alert', self.link, self.province.name)
    
    def save(self, share=False):
        if self.id == '0':
            self = initial_save(self, share=share)
        # if not self.signature:
        # sign_obj(self)
        super(MonitorPageForChange, self).save()


