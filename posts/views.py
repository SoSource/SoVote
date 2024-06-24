
from django.shortcuts import render, redirect
from django.template.defaulttags import register
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from accounts.forms import *
from .forms import AgendaForm, SearchForm
from .utils import *
from .models import *
from accounts.models import Notification
from blockchain.models import get_signing_data

# from django.urls import resolve
from django.db.models import Q, Value, F, Avg
from django.db.models import Count
from collections import Counter
from operator import itemgetter as _itemgetter
from django_user_agents.utils import get_user_agent

# import auth_token
from uuid import uuid4
import datetime
from django.utils import timezone
from datetime import date
from bs4 import BeautifulSoup
import re
from django.http import JsonResponse
import unicodedata
from unidecode import unidecode
import string
# Create your views here.

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_updated_field(update, args):
    # print()
    # print('get_updated_field', update, args)

    # if args.startswith('"') or args.startswith("'"):
    #     print('has quoets')
    # else:
    #     args = '"' + args + '"'
    #     print(args)
    #     print('added quotes')
    fields = args.split(",")
    # print('subfield', fields)
    try:
        data = json.loads(update.data)
    except:
        data = None
    # print(data)
    if data and fields[0] in data:
        result = data[fields[0]]
    else:
        result = ''
        try:
            # try:
            # result = ''
            # obj_field = str(fields[0]) + '_obj'
            # print('obj_field', obj_field)
            obj = getattr(update, fields[0])
            # print('obj', obj)
            if obj != None:
                # fail
                result = obj
            else:
                # print(str(e))
                obj_field = str(update.pointerType) + '_obj'
                # print('obj_field', obj_field)
                obj = getattr(update, obj_field)
                # print('obj', obj)
                result = getattr(obj, fields[0])
                # print('result',result)



            if fields[1]:
                # print('yes', fields[1])
                subresult = getattr(result, fields[1])
                # print('subresult', subresult)
                return subresult
        except Exception as e:
            # print(str(e))
            pass
    return result

@register.filter
def dt_object(dt):
    try:
        return datetime.datetime.fromisoformat(dt)
    except Exception as e:
        print(str(e))
        return dt

@register.filter
def list_all_terms(update):
    # print('list all terms', update)
    # return {'a':'b'}
    try:
        d = json.loads(update.data)
        terms = d['Terms']
        # print(json.loads(terms).items())
        return json.loads(terms).items()
    except Exception as e:
        # print(str(e))
        return None

@register.filter
def list_75_terms(update):
    # print('list 75')
    try:
        d = json.loads(update.data)
        terms = d['Terms']
        l = []
        # print(list(d.items())[:5])
        # print()
        for key, value in list(json.loads(terms).items())[:75]:
            # print({key:value})
            if key not in skipwords:
                # print(key)
                # pass
                l.append((key, value))
        return l
    except:
        return None

@register.filter
def get_terms_overflow(update):
    # print('get overflow')
    try:
        d = json.loads(update.data)
        terms = d['Terms']
        total = len(json.loads(terms).items())
        # print(total)
        if total > 75:
            remaining = total - 75
        else:
            remaining = None
        # print(remaining)
        return remaining
    except:
        return None

@register.filter
def list_all_people(update):
    # print('list all people')
    # from accounts.models import Person
    try:
        d = json.loads(update.data)
        people_json = json.loads(d['People_json'])
        # print('people_json',people_json)
        # for key, value in people_json.items():
        #     print(key, value)
        # l = list(d.items())
        speakers = {}
        keys = []
        for key, value in people_json.items():
            keys.append(key)
        people = Person.objects.filter(id__in=keys)
        for p, value in [[p, value] for p in people for key, value in people_json.items() if p.id == key]:
            speakers[p] = value
        # for key, value in l:
        #     a = Person.objects.filter(id=key)[0]
        #     speakers[a] = value
        H_people = sorted(speakers.items(), key=operator.itemgetter(1),reverse=True)
        # print('people', H_people)
        return H_people
    except Exception as e:
        print(str(e))
        return None

@register.filter
def get_ordinal(num):
    # print('get ordinal', num)
    if num % 10 == 1:
        return str(num) + 'st'
    elif num % 10 == 2:
        return str(num) + 'nd'
    elif num % 10 == 3:
        return str(num) + 'rd'
    else:
        return str(num) + 'th'

@register.filter
def get_role_short(position):
    if position == 'President':
        return 'P'
    elif position == 'Representative':
        return 'R'
    elif position == 'Senator':
        return 'S'
    elif position == 'Prime Minister':
        return 'PM'
    elif position == 'Member of Parliament':
        return 'MP'
    elif position == 'MPP':
        return 'MPP'
    elif position == 'Mayor':
        return 'M'
    elif position == 'Councillor':
        return 'C'

@register.filter
def order_terms(terms, termList):
    order = []
    lowerTerms = [term.lower() for term in terms]
    if termList and terms:
        for t in termList:
            if t.lower() in lowerTerms:
                # print(t)
                order.append(t)
    if terms:
        for t in terms:
            if t not in order:
                order.append(t)
    return order

@register.filter
def html_json(text):
    return None
    try:
        return text.replace('"', "'").replace('\n', '').strip()
    except:
        return None
    text = ''.join(text.splitlines())
    return text.replace('"', "'").replace('\n', '').strip()
    text = unidecode(text)
    return text.replace('"', "'").replace(';','').replace('\n', '').strip()

@register.filter
def remove_tags(text):
    try:
        TAG_RE = re.compile(r'<[^>]+>')
        text = TAG_RE.sub('', text).replace('"', "'").replace('\n', '').strip()
        text = ''.join(text.splitlines())
        text = unidecode(text)
        return text
    except:
        return None

@register.filter
def convert_printable(text):
    # text = unidecode(text)
    # printable = set(string.printable)
    # return ''.join(filter(lambda x: x in printable, text))
    # return text.encode('ascii',errors='ignore')
    return text

@register.filter
def get_bill_term(hansard, bill):
    d = ''
    try:
        for key, value in hansard.list_all_terms():
            try:
                k = Keyphrase.objects.annotate(string=Value(key)).filter(string__icontains=F('text')).filter(bill=bill, hansardItem__hansard=hansard)[0]
                num = value + 1
                term = key
                return "<li><span>(" + str(num) + ")</span>&nbsp; <a href='" + hansard.get_absolute_url() + "/?topic=" + term + "' title='" + term + "'>" + term + " </a></li>"
            except Exception as e:
                # print(str(e))
                pass
    except:
        pass
    return d

@register.filter
def match_terms(terms, keywords):
    # print('match terms', terms, keywords)
    # print(terms)
    n = 0
    order = {}
    if terms and keywords:
        # print('1')
        for key, value in terms:
            # print(key, value)
            if n <= 5 and key in keywords:
                n += 1
                if key not in order:
                    order[key] = value
            elif n > 5:
                break
    if terms:
        # print('2')
        for key, value in terms:
            # print(key, value)
            if key not in order:
                order[key] = value
         
    return list(order.items())

def render_view(request, context, country=None):
    # print('renderview')
    style = request.GET.get('style', 'index')
    if style == 'feed':
        return render(request, "utils/feed.html", get_paginator_url(request, context))
    else:
        if not request.user.is_authenticated:
            try:
                appToken = request.COOKIES['appToken'] # for app users
                # user = User.objects.filter(appToken=appToken)[0]
            except Exception as e:
                # print(str(e))
                appToken = None
            # try:
            #     userToken = request.COOKIES['userToken'] # for anon users
            #     # print('userToken', userToken)
            #     # user = User.objects.filter(userToken=userToken)[0]
            # except Exception as e:
            #     # print(str(e))
            #     # userToken = None
            #     userToken = uuid4()

                # user_agent = get_user_agent(request)
                # if not user_agent.is_bot:
                #     from random_username.generate import generate_username
                #     rand_username = generate_username(1)[0]
                #     user = User(username=rand_username, userToken=userToken, appToken=appToken, anon=True)
                #     user.slugger()
                #     user.save()
        else:
            appToken = request.user.appToken
            if not appToken:
                request.user.appToken = uuid4()
                request.user.save()
            # userToken = request.user.userToken
            # if not userToken:
            #     request.user.userToken = uuid4()
            #     request.user.save()
        try:
            fcmDeviceId = request.GET.get('fcmDeviceId', '')
            if not fcmDeviceId:
                fcmDeviceId = request.COOKIES['fcmDeviceId']
            # print('dviceId', fcmDeviceId)
            if fcmDeviceId:
                from fcm_django.models import FCMDevice
                try:
                    fcm_device = FCMDevice.objects.filter(registration_id=fcmDeviceId)[0]
                except:
                    fcm_device = FCMDevice()
                    fcm_device.registration_id = fcmDeviceId
                fcm_device.user = request.user
                fcm_device.active = True
                fcm_device.save()
                # print('saved device')
        except Exception as e:
            # print(str(e))
            pass
        
        ctx = get_cookies(request,context,country=country)
        # print('ctx', ctx)
        response = render(request, "home.html", ctx)
        # print('render 1')
        width = request.GET.get('width', '')
        if width:
            response.set_cookie(key='deviceWidth', value=width, expires=datetime.datetime.today()+datetime.timedelta(days=3650))
        if fcmDeviceId:
            response.set_cookie(key='fcmDeviceId', value=fcmDeviceId, expires=datetime.datetime.today()+datetime.timedelta(days=3650))
        if appToken:
            response.set_cookie(key='appToken', value=appToken, expires=datetime.datetime.today()+datetime.timedelta(days=3650))
        # print('passed render')
        # if userToken:
        #     response.set_cookie(key='userToken', value=userToken, expires=datetime.datetime.today()+datetime.timedelta(days=3650))
        return response

def test_view(request):
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'recent')

    import numpy as np
    # import pandas as pd
    from os import path
    from PIL import Image
    from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
    import matplotlib.pyplot as plt
    # Start with one review:
    bill = Bill.objects.exclude(first_reading_html=None)[4]
    print(bill.NumberCode)
    print(bill.LongTitleEn)
    cleantext = BeautifulSoup(bill.first_reading_html, "lxml").text

    p = Person.objects.filter(first_name='Pierre', last_name='Poilievre')[1]
    print(p)
    hansards = HansardItem.objects.filter(person=p)
    print(hansards.count())
    cleantext = ''
    for h in hansards:
        cleantext = cleantext + ' ' + h.Content
    cleantext = BeautifulSoup(cleantext, "lxml").text
    
    # Create stopword list:
    stopwords = set(STOPWORDS)
    stopwords.update(["C", "Canada", "House", 'Commons', 'Parliament', 'Government', 'Speaker', 'Canadian', 'Canadians', 'Mr','Madam', 'Paragraph', 'Act', 'subsection', 'section'])
    # Create and generate a word cloud image:
    wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(cleantext)

    # Display the generated image:
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    # wordcloud = plt.show()

    import base64
    import io
    image = io.BytesIO()
    import urllib.parse
    plt.savefig(image, format="png")
    image.seek(0)
    string = base64.b64encode(image.read())
    image_64 = "data:image/png;base64," +   urllib.parse.quote_plus(string)


    context = {
        # 'title': title,
        # 'nav_bar': list(options.items()),
        # 'view': view,
        'wordcloud': image_64,
        'cards': 'test',
        'sort': sort,
        # 'feed_list':setlist,
        # 'interactions': interactions,
        "form": AgendaForm(request.POST),
    }
    return render_view(request, context)

def splash_view(request):
    # user_data, user = get_user_data(request)
    supported_regions = Region.objects.filter(is_supported=True)
    style = request.GET.get('style', 'index')
    context = {
        'title': 'Welcome',
        'cards': 'splash',
        'supported_regions': supported_regions,
    }
    return render_view(request, context)

def home_view(request, region):
    print()
    print()
    print('------------homeview')
    # print(request.user)
    print(region)
    
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    
    style = request.GET.get('style', 'index')

    sort = request.GET.get('sort', 'recent')
    if sort == 'trending':
        sort_link = '?sort=recent'
        sort_type = '-date_time'
    else:
        sort_link = '?sort=trending'
        sort_type = '-date_time'
    if user:
        view = request.GET.get('view', 'Recommended')
    else:
        view = request.GET.get('view', 'Trending')
    page = request.GET.get('page', 1)
    getDate = request.GET.get('date', None)
    # province, region = get_region(request)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    # chamber = get_chamber(request)
    if user:
        # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s' %(page): '?view=%s&page=' %(view), 'Recommended': '?view=Recommended', 'Trending': '?view=Trending'}
        nav_options = [nav_item('button', f'Chamber: {chamber}', 'subNavWidget("chamberForm")'), nav_item('button', f'Page: {page}','subNavWidget("pageForm")'), nav_item('link', 'Recommended',f'?view=Recommended'), nav_item('link', 'Trending',f'?view=Trending')]
    else:
        # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s' %(page): '?view=%s&page=' %(view), 'Trending': '?view=Trending'}
        nav_options = [nav_item('button', f'Chamber: {chamber}', 'subNavWidget("chamberForm")'), nav_item('button', f'Page: {page}','subNavWidget("pageForm")'),nav_item('link', 'Trending',f'?view=Trending')]
    # if request.user.is_authenticated and request.user.is_god:
    #     options['testNotify'] = '?test-notify=True'
    cards = 'home_view'
    title = 'The Government of %s' %(country.Name)
    # title = '%s' %(country.Name)
    if style == 'index' and page == 1:
        context = {
            'title': title,
            'nav_bar': nav_options,
            'view': view,
            # 'provState': provState,
            'cards': cards,
            'sort': sort,
            # 'country': country,
        }
        return render_view(request, context, country=country)
    else:
        # return render_view(request, {}, country=country)
        print('1 chamber', chamber)
    # hansardItems = None
        # if view == 'Recommended':
        #     posts = Post.objects.filter(post_type='bill').filter(Q(bill__NumberCode='C-18')|Q(bill__NumberCode='C-11')|Q(bill__NumberCode='C-22')).select_related('bill', 'bill__person').order_by('-rank','-date_time', '-id')
        if view == 'Recommended':
            include_list = ['Bill', 'Meeting']
            
            posts, view = algorithim(user, include_list, chamber, country, provState_name, view, page)

        else:   
            include_list = ['Bill','Meeting']
            # view = 'Trending'
            # trends = Post.objects.filter(organization__in=orgs).filter(Q(date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=1))|Q(date_time__gte=datetime.datetime.now() + datetime.timedelta(days=30))).filter(post_type__in=include_list).order_by('-rank', sort_type)[:200]
            # keys = []
            # for p in trends:
            #     if p.keywords:
            #         keys = keys + p.keywords   
            # posts = Post.objects.filter(organization__in=orgs).filter(Q(date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=1))|Q(date_time__gte=datetime.datetime.now() + datetime.timedelta(days=30))).filter(post_type__in=include_list).filter(keywords__overlap=keys).annotate(matches=Count('keywords')+F('rank')).order_by('-matches','-date_time')
                
            # posts, view = algorithim(request, include_list, chamber, region, view, page)
            cards = 'top_cards'
            # print(chamber, provState.Name)
            posts = getTrendingTop(chamber, country)
            if posts.count() == 0:
                posts, view = algorithim(user, include_list, chamber, country, provState_name, view, page)
                cards = 'home_view'
        setlist = paginate(posts, page, request)
        print('view',view)
        # for i in setlist:
        #     print(i.pointerType)
        #     print(i.keyword_array)
        #     try:
        #         print('b',i.Bill_obj.chamber)
        #     except:
        #         pass
        print('--------')
        # for i in setlist:
        #     print(i.Update_obj.keyword_array)
        if view == 'Recommended' and user:
            # counter = Counter(request.user.keywords)
            # userKeys = counter.most_common()[0]
            userKeys = [k for k, value in Counter(json.loads(user.interest_array)).most_common()]
        else:
            if chamber == 'House':
                orgs = ['House', 'House of Commons', 'Congress']
            elif chamber == 'Senate':
                orgs = ['Senate']
            elif chamber == 'All':
                orgs = ['Senate', 'House', 'House of Commons', 'Congress', '%s-Assembly'%(provState_name)]
            elif chamber == 'Assembly':
                orgs = ['%s-Assembly'%(provState_name)]
            try:
                dateQuery = Statement.objects.filter(meeting_type='Debate', chamber__in=orgs).order_by('-DateTime')[12].DateTime
                dt = datetime.datetime.now().replace(tzinfo=pytz.UTC) - dateQuery
            except:
                dt = datetime.datetime.now().replace(tzinfo=pytz.UTC) - datetime.datetime.now().replace(tzinfo=pytz.UTC)
            userKeys = get_trending_keys(dt, include_list, orgs)
            # print('!!!!!!!!!!!!!', userKeys)

        # interactions = get_interactions(user, setlist)  
        # my_rep = getMyRepVotes(user, setlist) 
        daily = None
        if page == 1:
            # daily = getDaily(request, province, getDate)
            pass
        try:
            isApp = request.COOKIES['fcmDeviceId']
        except:
            isApp = None
        # cards = 'home_view'
        # print('cards',cards)
        context = {
            'title': title,
            'nav_bar': nav_options,
            'isApp': isApp,
            'view': view,
            # 'provState': provState_name,
            'cards': cards,
            'dailyCard': daily,
            'sort': sort,
            'feed_list':setlist,
            'user_keywords': userKeys,
            # 'posts': setlist,
            'interactions': get_interactions(user, setlist),
            # 'updates': get_updates(setlist),
            'myRepVotes': getMyRepVotes(user, setlist),
        }
        return render_view(request, context)

def following_view(request):
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'recent')
    view = request.GET.get('view', 'Current')
    page = request.GET.get('page', 1)
    # u = request.user
    user_data, user = get_user_data(request)
    u = user
    country, provState, provState_name, municipality, municipality_name = get_regions(request, None, user)
    if not user:
        return redirect('/')
    # country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user_data, user)
    
    # chamber = get_chamber(request)
    # options = {'Current': '?view=Current', 'Upcoming': '?view=Upcoming', 'Following':'%s?view=Following' %(request.user.get_absolute_url())}
    nav_options = [nav_item('link', 'Current', '?view=Current'), nav_item('link', 'Upcoming','?view=Upcoming'),nav_item('link', 'Following','%s?view=Following' %(user.get_absolute_url()))]
    cards = 'home_list'
    title = 'Following'
    if style == 'index':
        context = {
            'title': title,
            'nav_bar': nav_options,
            'view': view,
            'cards': cards,
            'sort': sort,
            # 'country': country,    
        }
        return render_view(request, context)
    else:
        getList = []
        topicList = []
        for p in u.follow_Person.objs.all():
            getList.append(p.id)
        for p in u.follow_Bill_objs.all():
            getList.append('%s?current=True' %(p.NumberCode))
        for p in u.follow_Committee_objs.all():
            getList.append(p.code)
        for p in u.get_follow_topics():
            getList.append(p)
            topicList.append(p)
        # print(getList)
        posts = Post.objects.filter(Country_obj=country).filter(keyword_array__overlap=getList).filter(date_time__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')).select_related('Meeting', 'Statement','Bill').order_by('-date_time')
        setlist = paginate(posts, page, request)
        # interactions = get_interactions(request, setlist) 
        try:
            isApp = request.COOKIES['fcmDeviceId']
        except:
            isApp = None 
        context = {
            'isApp': isApp,
            'view': view,
            'cards': cards,
            'sort': sort,
            'feed_list':setlist,
            'interactions': get_interactions(user, setlist),
            # 'updates': get_updates(setlist),
            'topicList': topicList,
        }   
        return render_view(request, context, country=country)

def topic_view(request, region, keyword):
    print(keyword)
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'Newest')
    view = request.GET.get('view', 'Current')
    keyword = request.GET.get('keyword', keyword)
    keyword = keyword.lower()
    page = request.GET.get('page', 1)
    getDate = request.GET.get('date', None)
    # keyword = request.GET.get('keyword', '')
    # chamber = get_chamber(request)
    # province, region = get_region(request)
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, None, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    follow = request.GET.get('follow', '')
    ordering = get_sort_order(sort)
    if follow and keyword:
        # if request.user.is_authenticated:
        #     user = request.user
        # else:
        #     userToken = request.COOKIES['userToken']
        #     user = User.objects.filter(userToken=userToken)[0]
        print('follow')
        fList = user.get_follow_topics()
        if keyword in fList:
            fList.remove(keyword)
            user = set_keywords(user, 'remove', keyword)
            response = 'Unfollow "%s"' %(keyword)
        elif keyword not in fList:
            fList.append(keyword)
            user = set_keywords(user, 'add', keyword)
            response = 'Following "%s"' %(keyword)
        user.set_follow_topics(fList)
        user.save()
        print('done')
        return render(request, "utils/dummy.html", {"result": response})
    if user and keyword in user.get_follow_topics():
        f = 'following'
    else:
        f = 'follow'
    # options = {'Chamber: %s' %(chamber): 'chamber', 'follow':'%s?follow=%s' %(request.path, f), 'Sort: %s'%(sort):sort }
    nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), nav_item('button', 'follow',f'react("follow2", "{request.path}?keyword={keyword}&follow={f}")'), nav_item('link', f'Sort: {sort}', f'?keyword={keyword}&sort={sort}')]
    
    cards = 'home_list'
    title = 'Topic: %s' %(keyword)
    if style == 'index':
        try:
            # if request.user.is_authenticated:
            #     user = request.user
            # elif not user:
            #     userToken = request.COOKIES['userToken']
            #     user = User.objects.filter(userToken=userToken)[0]
            user = set_keywords(request.user, 'add', keyword)
            user.save()
        except:
            pass
        context = {
            'title': title,
            'nav_bar': nav_options,
            'view': view,
            'region': region,
            'cards': cards,
            'keyword': keyword,
            'sort': sort,
            'sortOptions': ['Oldest','Newest','Loudest','Random'],
        }
        return render_view(request, context, country=country)
    else:
        getList = [keyword]
        topicList = [keyword]
        if getDate:
            firstDate = datetime.datetime.strptime(getDate, '%Y-%m-%d')
            secondDate = firstDate + datetime.timedelta(days=1)
        else: 
            secondDate = datetime.datetime.now() + datetime.timedelta(hours=1)
            firstDate = secondDate - datetime.timedelta(days=1000)
        # chamber, chambers = get_chambers(request, country, provState, municipality)
        posts = Post.objects.filter(Country_obj=country, chamber__iexact__in=chambers).filter(keyword_array__overlap=getList).filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('Meeting', 'Statement','Bill').order_by(ordering,'-date_time')
        # if chamber == 'All':
        # else: 
        #     posts = Post.objects.filter(Country_obj=country, chamber__iexact=chamber).filter(keyword_array__overlap=getList).filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('Meeting', 'Statement','Bill').order_by(ordering,'-date_time')
        
        
        
        
        try:
            setlist = paginate(posts, page, request)
        except:
            setlist = []
        # interactions = get_interactions(request, setlist)  
        try:
            isApp = request.COOKIES['fcmDeviceId']
        except:
            isApp = None
        cards = 'home_list'
        context = {
            'isApp': isApp,
            'view': view,
            'cards': cards,
            'keyword': keyword,
            'sort': sort,
            'sortOptions': ['Oldest','Newest','Loudest','Random'],
            'feed_list':setlist,
            'interactions': get_interactions(user, setlist),
        # '   updates': get_updates(setlist),
            'topicList': topicList,
        }
        return render_view(request, context, country=country)

def search_view(request, keyword):
    style = request.GET.get('style', 'index')
    # sort = request.GET.get('sort', 'recent')
    view = request.GET.get('view', '')
    sort = request.GET.get('sort', 'Newest')
    keyword = request.GET.get('keyword', keyword)
    keyword = keyword.lower()
    page = request.GET.get('page', 1)
    search = request.POST.get('post_type', '')
    autoComplete = request.GET.get('search')
    follow = request.GET.get('follow', '')
    cards = 'home_list'
    ordering = get_sort_order(sort)
    title = 'Search: %s' %(search)    
    # province, region = get_region(request)
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, None, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    # options = {'Chamber: %s' %(chamber): 'chamber'}
    # nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")')]
    searchform = SearchForm(initial={'post_type': search})
    subtitle = ''
    if follow and follow != 'following' and follow != 'follow':
        # if request.user.is_authenticated:
        #     user = request.user
        # else:
        #     try:
        #         userToken = request.COOKIES['userToken']
        #         user = User.objects.filter(userToken=userToken)[0]
        #     except:
        #         pass
        if user:
            fList = user.get_follow_topics()
            topic = follow
            if topic in fList:
                fList.remove(topic)
                response = 'Unfollow "%s"' %(topic)
                user = set_keywords(user, 'remove', topic)
            elif topic not in fList:
                fList.append(topic)
                response = 'Following "%s"' %(topic)
                user = set_keywords(user, 'add', topic)
            user.set_follow_topics(fList)
            user.save()
        else:
            response = 'Please login'
        return render(request, "utils/dummy.html", {"result": response})
    if keyword:
        title = 'Search: %s' %(keyword)
        # options['follow'] = '%s' %(keyword)
        nav_options.append(nav_item('button', 'follow', f'react("follow2", "{keyword}")'))
        posts = Post.objects.filter(keyword_array__icontains=keyword).exclude(date_time=None).order_by(ordering,'-date_time')
        if posts.count() == 0:
            posts = Archive.objects.filter(keyword_array__icontains=keyword).exclude(date_time=None).order_by(ordering,'-date_time')
        if posts.count() == 1:
            response = redirect(posts[0].get_absolute_url())
            return response
    elif autoComplete:
        keyphrases = Keyphrase.objects.filter(chamber__iexact__in=chambers).filter(text__icontains=autoComplete)[:500]
        # if chamber == 'All':
        # else:
        #     keyphrases = Keyphrase.objects.filter(chamber__iexact=chamber).filter(text__icontains=autoComplete)[:500]

        # if chamber == 'All':
        #     if 
        #     keyphrases = Keyphrase.objects.filter(text__icontains=autoComplete)[:500]
        #     # print(keyphrases)
        # elif chamber == 'House':
        #     keyphrases = Keyphrase.objects.filter(chamber__iexact=chamber).filter(text__icontains=autoComplete)[:500]
        # elif chamber == 'Senate':
        #     keyphrases = Keyphrase.objects.filter(organization='Senate').filter(text__icontains=autoComplete)[:500]
        # elif chamber == 'Assembly':
        #     # org = get_province_name
        #     keyphrases = Keyphrase.objects.filter(organization='%s-Assembly'%(region)).filter(text__icontains=autoComplete)[:500]
        data = []
        for k in keyphrases:
            if k.text not in data:
                data.append(k.text)
        return JsonResponse({'status':200, 'data':data})
    else:
        posts = {}
    try:
        setlist = paginate(posts, page, request)
    except:
        setlist = []
    # interactions = get_interactions(request, setlist) 
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None 
    # my_rep = getMyRepVotes(request, setlist) 
    # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s' %(page): '?page=1', 'Sort: %s'%(sort): sort, 'Search': 'search', 'Date': 'date'}
    nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), 
                   nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'),
            # nav_item('link', 'Page: %s' %(page), '?view=%s&page=' %(view)), 
            nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), 
            # nav_item('link', 'Current', '?view=Current'), 
            # nav_item('link', 'Upcoming', '?view=Upcoming'),
            nav_item('button', 'Search', 'subNavWidget("searchForm")'), 
            nav_item('button', 'Date', 'subNavWidget("datePickerForm")')]
    context = {
        'isApp': isApp,
        'title': title,
        'subtitle': subtitle,
        'nav_bar': nav_options,
        'sort': sort,
        'sortOptions': ['OLdest','Newest','Loudest','Random'],
        'keyword': keyword,
        'view': view,
        # 'region': region,
        'searchForm': searchform,
        'cards': cards,
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        'myRepVotes': getMyRepVotes(user, setlist),
        'topicList': [keyword],
        # 'myRepVotes': my_rep,
        # 'country': Country.objects.all()[0],
    }
    return render_view(request, context, country=country)

def region_view(request):
    # style = request.GET.get('style', 'index')
    # sort = request.GET.get('sort', 'recent')
    # if sort == 'trending':
    #     sort_link = '?sort=recent'
    #     sort_type = '-date_time'
    # else:
    #     sort_link = '?sort=trending'
    #     sort_type = '-date_time'
    # view = request.GET.get('view', 'current')
    # if request.user.is_authenticated:
    #     if not request.user.postal_code: 
    #         response = redirect('/set-region')
    #         # print(response)
    #         return response

    title = 'Region'
    # if view == 'upcoming':
    #     posts = Post.objects.filter(Q(date_time__gte=datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(hours=1), '%Y-%m-%d-%H:%M'))).exclude(post_type='hansardItem').select_related('bill', 'bill__person', 'hansard_key', 'motion','motion__sponsor','committeeMeeting', 'committeeMeeting__committee__chair').order_by('date_time')
    # else:
    #     posts = Post.objects.filter(Q(date_time__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(hours=1), '%Y-%m-%d-%H:%M'))).exclude(post_type='hansardItem').select_related('bill', 'bill__person', 'hansard_key', 'motion','motion__sponsor','committeeMeeting', 'committeeMeeting__committee__chair').order_by(sort_type)
    # setlist = paginate(posts, page, request)
    # print(setlist[0])
    
    # interactions = get_interactions(request, setlist)  
    nav_options = [nav_item('button', 'Set Region', "modalPopUp('Select Region', '/accounts/get_country_modal')")]
    # options = [{'type':'button', 'text':'Set Region', 'target':'/set-region'}]
    cards = 'region_form'
    # try:
    #     MP = Role.objects.filter(position='Member of Parliament', riding=request.user.riding, current=True)[0]
    # except:
    #     MP = None
    user_data, user = get_user_data(request)
    print(user)
    # reps = {}
    # if user_data:
    if user:
        reps = get_reps(user)
    else:
        reps = {}
    # print(reps)
    # form = RegionForm(initial={'address': request.user.address})
    context = {
        'has_reps': True,
        # 'user': user,
        'title': title,
        'nav_bar': nav_options,
        # 'view': view,
        'cards': cards,
        # 'updates': get_updates(setlist),
        # 'sort': sort,
        # 'country': Country.objects.all()[0],
        # 'form': form,
        # 'feed_list':setlist,
        # 'interactions': interactions,
        # 'MP': MP,
    }
    context = {**reps, **context}
    return render_view(request, context)

def citizenry_view(request, region):
    style = request.GET.get('style', 'index')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    context = {
        'title': 'Citizenry',
        'cards': 'citizenry',
    }
    return render_view(request, context, country=country)

def citizen_debates_view(request, region):
    style = request.GET.get('style', 'index')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    context = {
        'title': 'Citizen Debates',
        'cards': 'citizenry',
    }
    return render_view(request, context, country=country)

def citizen_bills_view(request, region):
    style = request.GET.get('style', 'index')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    context = {
        'title': 'Citizen Bills',
        'cards': 'citizenry',
    }
    return render_view(request, context, country=country)

def polls_view(request, region):
    style = request.GET.get('style', 'index')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    context = {
        'title': 'Polls',
        'cards': 'citizenry',
    }
    return render_view(request, context, country=country)

def petitions_view(request, region):
    style = request.GET.get('style', 'index')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    context = {
        'title': 'Petitions',
        'cards': 'citizenry',
    }
    return render_view(request, context, country=country)

def someta_view(request):
    style = request.GET.get('style', 'index')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, None, user)
    context = {
        'title': 'SoMeta',
        'cards': 'citizenry',
    }
    return render_view(request, context, country=country)

def legislature_view(request, region):
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'recent')
    if sort == 'trending':
        sort_link = '?sort=recent'
        sort_type = '-DateTime'
    else:
        sort_link = '?sort=trending'
        sort_type = '-DateTime'
    view = request.GET.get('view', 'Current')
    page = request.GET.get('page', 1)
    getDate = request.GET.get('date', None)
    date = request.POST.get('date')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s' %(page): '?view=%s&page=' %(view), 'Current': '?view=Current', 'Recommended': '?view=Recommended', 'Trending': '?view=Trending'}
    nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), nav_item('link', 'Current', '?view=Current'), nav_item('link', 'Recommended', '?view=Recommended'), nav_item('link', 'Trending', '?view=Trending')]
    form = AgendaForm()
    title = f'{country.Name} Legislature'
    subtitle = ''
    cards = 'home_list'

    if style == 'index' and page == 1:
        context = {
            'title': title,
            'nav_bar': nav_options,
            'view': view,
            'region': region,
            'cards': cards,
            'sort': sort,
            # 'country': country,
        }
        return render_view(request, context, country=country)
    else:
        # exclude_list = ['person', 'party', 'district', 'riding', 'agendaTime', 'hansardItem', 'committeeItem', 'committee', 'agenda', 'vote', 'bill']
        if view == 'Upcoming':
            include_list = ['Bill','Meeting', 'Motion']
            posts = Post.objects.filter(Country_obj=country, DateTime__gte=datetime.datetime.now() - datetime.timedelta(hours=1)).filter(pointerType__in=include_list).exclude(BillVersion__Current=False).order_by('date_time', 'id')
        elif view == 'Current':
            include_list = ['Bill','Meeting', 'Motion']
            if getDate:
                firstDate = datetime.datetime.strptime(getDate, '%Y-%m-%d')
                secondDate = firstDate + datetime.timedelta(days=1)
            else: 
                secondDate = datetime.datetime.now() + datetime.timedelta(hours=1)
                firstDate = secondDate - datetime.timedelta(days=1000)
            
            posts = Post.objects.filter(Country_obj=country, chamber__in=chambers).filter(DateTime__gte=firstDate, DateTime__lt=secondDate).filter(pointerType__in=include_list).exclude(BillVersion_obj__Current=False).order_by(sort_type, 'id')
            
            # if chamber == 'All':
            #     # orgs = ['House', 'House of Commons', 'Congress']
            # else:
            #     posts = Post.objects.filter(Country_obj=country, chamber=chamber).filter(date_time__gte=firstDate, date_time__lt=secondDate).filter(pointerType__in=include_list).exclude(BillVersion__Current=False).order_by(sort_type, 'id')
            
            # elif chamber == 'Senate':
            #     posts = Post.objects.filter(Chamber='Senate').filter(date_time__gte=firstDate, date_time__lt=secondDate).filter(pointerType__in=include_list).exclude(BillVersion__Current=False).order_by(sort_type, 'id')
            # elif chamber == 'All':
            #     orgs = ['Senate', 'House', 'House of Commons', 'Congress', '%s-Assembly'%(provState_name)]
            #     posts = Post.objects.filter(Chamber__in=orgs).filter(date_time__gte=firstDate, date_time__lt=secondDate).filter(pointerType__in=include_list).exclude(BillVersion__Current=False).order_by(sort_type, 'id')
            # elif chamber == 'Assembly':
            #     posts = Post.objects.filter(Chamber='%s-Assembly'%(provState_name)).filter(date_time__gte=firstDate, date_time__lt=secondDate).filter(pointerType__in=include_list).exclude(BillVersion__Current=False).order_by(sort_type, 'id')        
        elif view == 'Recommended':
            include_list = ['Bill','Meeting']
            posts, view = algorithim(request, include_list, chamber, provState_name, view, page)
        elif view == 'Trending':
            include_list = ['Bill','Meeting']
            # posts, view = algorithim(request, include_list, chamber, region, view, page)
            posts = getTrendingTop(chamber, provState_name)
            cards = 'top_cards'

        # elif chamber == 'All':
        #     title = 'Canadian Legislature'
        #     if request.method == 'POST':
        #         date = datetime.datetime.strptime(date, '%Y-%m-%d')
        #         subtitle = date
        #         view = None
        #         posts = Post.objects.exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Q(post_type='agendaTime')|Q(bill__OriginatingChamberName='House of Commons')|Q(hansard_key__Organization='House')|Q(motion__OriginatingChamberName='House')|Q(committeeMeeting__Organization='House')).order_by('date_time')
        #     elif view == 'Upcoming':
        #         posts = Post.objects.exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__gte=datetime.datetime.now()).order_by('date_time')
        #     else:
        #         posts = Post.objects.exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=1)).order_by(sort_type)
        # elif chamber == 'House':
        #     title = 'The House of Commons'
        #     if request.method == 'POST':
        #         date = datetime.datetime.strptime(date, '%Y-%m-%d')
        #         subtitle = date
        #         view = None
        #         posts = Post.objects.filter(organization__icontains='House').exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Q(post_type='agendaTime')|Q(bill__OriginatingChamberName='House of Commons')|Q(hansard_key__Organization='House')|Q(motion__OriginatingChamberName='House')|Q(committeeMeeting__Organization='House')).order_by('date_time')
        #     elif view == 'Upcoming':
        #         posts = Post.objects.filter(organization__icontains='House').exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__gte=datetime.datetime.now()).order_by('date_time')
        #     else:
        #         posts = Post.objects.filter(organization='House').exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=1)).order_by(sort_type)
        # elif chamber == 'Senate':
        #     title = 'Canadian Senate'
        #     if request.method == 'POST':
        #         date = datetime.datetime.strptime(date, '%Y-%m-%d')
        #         subtitle = date
        #         view = None
        #         posts = Post.objects.filter(organization='Senate').exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Q(post_type='agendaTime')|Q(bill__OriginatingChamberName='House of Commons')|Q(hansard_key__Organization='House')|Q(motion__OriginatingChamberName='House')|Q(committeeMeeting__Organization='House')).order_by('date_time')
        #     elif view == 'upcoming':
        #         posts = Post.objects.filter(organization='Senate').exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d-%H:%M')).order_by('date_time')
        #     else:
        #         posts = Post.objects.filter(organization='Senate').exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(hours=1), '%Y-%m-%d-%H:%M')).order_by(sort_type)
        # elif chamber == 'Assembly':
        #     title = '%s Assembly' %(province.name)
        #     if request.method == 'POST':
        #         date = datetime.datetime.strptime(date, '%Y-%m-%d')
        #         subtitle = date
        #         view = None
        #         posts = Post.objects.filter(organization='%s-Assembly'%(region)).exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Q(post_type='agendaTime')|Q(bill__OriginatingChamberName='House of Commons')|Q(hansard_key__Organization='House')|Q(motion__OriginatingChamberName='House')|Q(committeeMeeting__Organization='House')).order_by('date_time')
        #     elif view == 'upcoming':
        #         posts = Post.objects.filter(organization='%s-Assembly'%(region)).exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d-%H:%M')).order_by('date_time')
        #     else:
        #         posts = Post.objects.filter(organization='%s-Assembly'%(region)).exclude(post_type__in=exclude_list).exclude(billVersion__current=False).filter(date_time__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(hours=1), '%Y-%m-%d-%H:%M')).order_by(sort_type)    
        
        if view != 'Trending' and user:
            userKeys = [k for k, value in Counter(json.loads(user.interest_array)).most_common()]
        else:
            # if chamber == 'House':
            #     orgs = ['House', 'House of Commons', 'Congress']
            # elif chamber == 'Senate':
            #     orgs = ['Senate']
            # elif chamber == 'All':
            #     orgs = ['Senate', 'House', 'House of Commons', 'Congress', '%s-Assembly'%(provState_name)]
            # elif chamber == 'Assembly':
            #     orgs = ['%s-Assembly'%(provState_name)]
            # dateQuery = Debate.objects.filter(Chamber__in=orgs).order_by('-PublicationDateTime')[12].PublicationDateTime
            # dt = datetime.datetime.now().replace(tzinfo=pytz.UTC) - dateQuery
            try:
                if chamber == 'All':
                    dateQuery = Meeting.objects.filter(meeting_type='Debate', Country_obj=country, chamber__in=chambers).order_by('-DateTime')[12].DateTime
                else:
                    dateQuery = Meeting.objects.filter(meeting_type='Debate', Country_obj=country, chamber=chamber).order_by('-DateTime')[12].DateTime
                dt = datetime.datetime.now().replace(tzinfo=pytz.UTC) - dateQuery
            except:
                dt = datetime.datetime.now().replace(tzinfo=pytz.UTC) - datetime.datetime.now().replace(tzinfo=pytz.UTC)
            userKeys = get_trending_keys(dt, include_list, chambers)
        setlist = paginate(posts, page, request)
        # my_rep = getMyRepVotes(request, setlist)   
        # interactions = get_interactions(user, setlist)
        daily = None
        if page == 1:
            pass
            # if getDate:
            #     daily = getDaily(request, provState, getDate)
            # else:
            #     daily = getDaily(request, provState, None)
        try:
            isApp = request.COOKIES['fcmDeviceId']
        except:
            isApp = None
        context = {
            'isApp': isApp,
            'title': title,
            'subtitle': subtitle,
            'nav_bar': nav_options,
            'view': view,
            'region': region,
            'dateForm': form,
            'user_keywords': userKeys,
            'dailyCard': daily,
            'cards': cards,
            'sort': sort,
            'filter': chamber,
            'feed_list':setlist,
            'interactions': get_interactions(user, setlist),
            # 'updates': get_updates(setlist),
            'myRepVotes': getMyRepVotes(user, setlist),
            # 'country': country,
            # 'xRequestr': request.headers.get('X-Requested-With')
        }
        return render_view(request, context, country=country)
        
# not used
def senate_view(request):
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'recent')
    if sort == 'trending':
        sort_link = '?sort=recent'
        sort_type = '-date_time'
    else:
        sort_link = '?sort=trending'
        sort_type = '-date_time'
    view = request.GET.get('view', 'current')
    page = request.GET.get('page', 1)
    # view = request.GET.get('view', 'past')
    date = request.POST.get('date')
    form = AgendaForm()
    subtitle = ''
    if request.method == 'POST':
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        subtitle = date
        view = None
        posts = Post.objects.filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Q(bill__OriginatingChamberName='Senate')|Q(hansard_key__Organization='Senate')|Q(motion__OriginatingChamberName='Senate')|Q(committeeMeeting__Organization='Senate')).select_related('bill', 'bill__person', 'hansard_key', 'motion','motion__sponsor','committeeMeeting', 'committeeMeeting__committee__chair').order_by('date_time')
    elif view == 'upcoming':
        posts = Post.objects.filter(Q(bill__OriginatingChamberName='Senate')|Q(hansard_key__Organization='Senate')|Q(motion__OriginatingChamberName='Senate')|Q(committeeMeeting__Organization='Senate')).filter(date_time__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d-%H:%M')).select_related('bill', 'bill__person', 'hansard_key', 'motion','motion__sponsor','committeeMeeting', 'committeeMeeting__committee__chair').order_by('date_time')
    else:
        posts = Post.objects.filter(Q(bill__OriginatingChamberName='Senate')|Q(hansard_key__Organization='Senate')|Q(motion__OriginatingChamberName='Senate')|Q(committeeMeeting__Organization='Senate')).filter(date_time__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(hours=1), '%Y-%m-%d-%H:%M')).select_related('bill', 'bill__person', 'hansard_key', 'motion','motion__sponsor','committeeMeeting', 'committeeMeeting__committee__chair').order_by(sort_type)
    title = 'The Senate'
    setlist = paginate(posts, page, request)
    # interactions = get_interactions(request, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    options = {'Current': '?view=current', 'Upcoming': '?view=upcoming', 'Page: %s' %(page): '?page=', 'Sort: %s' %(sort): sort_link, 'Date': 'date'}
    cards = 'home_list'
    context = {
        'isApp': isApp,
        'title': title,
        'subtitle': subtitle,
        'nav_bar': list(options.items()),
        'view': view,
        'dateForm': form,
        'cards': cards,
        'sort': sort,
        'feed_list':setlist,
        'interactions': interactions,
        'country': Country.objects.all()[0],
    }
    return render_view(request, context)

def agenda_watch_view(request, region, chamber, year, month, day, hour, minute):
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', '')
    page = request.GET.get('page', 1)
    view = request.GET.get('view', 'past')
    date = request.POST.get('date')
    form = AgendaForm()
    seconds = '00'
    subtitle = ''
    # user_data, user = get_user_data(request)
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    # chamber, chambers = get_chambers(request, country, provState, municipality)
    # country, provState, provState_name, municipality, municipality_name = get_regions(region, user_data)
    # posts = Post.objects.filter(hansard_key__Organization='House').select_related('hansard_key').order_by('-hansard_key__Publication_date_time')
    # agenda = Hansard.objects.filter(Organization=organization, Publication_date_time__gte=date, Publication_date_time__lt=date + datetime.timedelta(days=1))[0]
    if request.method == 'POST':
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        subtitle = date
        view = None
        # agenda = Agenda.objects.filter(organization=organization, date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1))[0]
        debate = Debate.objects.filter(Chamber=chamber, PublicationDateTime__gte=date, PublicationDateTime__lt=date + datetime.timedelta(days=1))[0]
    else:
        subtitle = '%s-%s-%s/%s:%s' %(year, month, day, hour, minute),
        # agenda = Agenda.objects.filter(organization=organization, Publication_date_time__year=year, Publication_date_time__month=month, Publication_date_time__day=day)[0]
        debate = Debate.objects.filter(Chamber=chamber, PublicationDateTime__year=year, PublicationDateTime__month=month, PublicationDateTime__day=day)[0]
    card = 'watch_video'
    title = '%s Agenda' %(chamber)
    if chamber == 'House':
        video_link = 'https://parlvu.parl.gc.ca/Harmony/en/PowerBrowser/PowerBrowserV2/%s%s%s/-1/%s?mediaStartTime=%s%s%s%s%s%s&viewMode=3&globalStreamId=29' %(year,month,day,Debate.Agenda.videoCode,year,month,day,hour,minute,seconds)
    elif chamber == 'Senate':
        video_link = Debate.Agenda.VideoURL
    posts = Post.objects.filter(Debate_key=debate)
    setlist = paginate(posts, page, request)
    # interactions = get_interactions(user, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    options = {'Date': 'date'}
    context = {
        'isApp': isApp,
        'title': title, 
        'subtitle': subtitle,
        'nav_bar': list(options.items()),
        'view': view,
        'dateForm': form,
        'cards': card,
        'video_link': video_link,
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        # 'myRepVotes': getMyRepVotes(user, setlist),
    }
    return render_view(request, context, country=country)

def agendas_view(request, region, chamber):
    print('agenda_view')
    cards = 'agenda_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'time')
    page = request.GET.get('page', 1)
    view = request.GET.get('view', 'past')
    date = request.POST.get('date')
    search = request.POST.get('post_type')
    dateform = AgendaForm()
    searchform = SearchForm()
    subtitle = ''
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality, chamber=chamber)
    if request.method == 'POST':
        if date:
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
            subtitle = date
            view = None
            posts = Post.objects.filter(Country_obj=country, Agenda__chamber__in=chambers, date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(pointerType='Agenda').order_by('-date_time')
            # if chamber == 'All':
            # else:
            #     posts = Post.objects.filter(Country_obj=country, Agenda__chamber=chamber, date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).order_by('-date_time')
        elif search:
            subtitle = search
            view = None
            agendaItems = AgendaItem.objects.filter(text__icontains=search)
            search_list = []
            for i in agendaItems:
                search_list.append(i.agendaTime)
            posts = Post.objects.filter(AgendaTime__in=search_list).select_related('AgendaTime').order_by('-date_time')
    else:
        posts = Post.objects.filter(pointerType='Agenda', Agenda__chamber__in=chambers).select_related('Agenda').order_by('-date_time')
        # if chamber == 'All':
        # # elif chamber == 'Senate':
        # #     posts = Post.objects.filter(pointerType='Agenda', Agenda__Chamber='Senate').select_related('Agenda').order_by('-date_time')
        # else:
        #     posts = Post.objects.filter(pointerType='Agenda', Agenda__chamber=chamber).select_related('Agenda').order_by('-date_time')
    if chamber == 'All':
        title = 'Agendas'
        h = '/House-agendas'
        s = '/Senate-agendas'
    elif chamber == 'House':
        title = '%s Agendas' %(chamber)
        h = '/agendas'
        s = '/Senate-agendas'
    elif chamber == 'Senate':
        title = '%s Agendas' %(chamber)
        h = '/House-agendas'
        s = '/agendas'
    setlist = paginate(posts, page, request)
    # interactions = get_interactions(user, setlist) 
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None   
    # options = {'House':h, 'Senate':s,'Page: %s' %(page): '?page=', 'Search':'search', 'Date': 'date'}
    nav_options = [nav_item('link', 'House', h), nav_item('link', 'Senate', s), nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), nav_item('button', 'Search', 'subNavWidget("searchForm")'), nav_item('button', 'Date', 'subNavWidget("datePickerForm")')]
    context = {
        'isApp': isApp,
        'title': title,
        'subtitle': subtitle,
        'nav_bar': nav_options,
        'view': view,
        'filter': chamber,
        'dateForm': dateform,
        'searchForm': searchform,
        'cards': cards,
        'sort': sort,
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
    }
    return render_view(request, context, country=country)

def bill_view(request, region, chamber, govNumber, session, numcode):
    print()
    print('bill_view')
    # cards = 'bill_view'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'new')
    view = request.GET.get('view', 'Overview')
    page = request.GET.get('page', 1)
    reading = request.GET.get('reading', '')
    getSpren = request.GET.get('getSpren', '')
    topicList = []
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    govs = get_gov(country, gov_levels, govNumber, session)
    if view == 'LatestText':
        reading = 'LatestText'
    if sort == 'old':
        changeSort = 'new'
        ordering = 'DateTime'
        order2 = 'id'
    else:
        changeSort = 'old'
        ordering = '-DateTime'
        order2 = '-id'
    # print(parliament, session, numcode)
    bill = Bill.objects.filter(Government_obj__in=govs, NumberCode=numcode)[0]
    print('bill', bill)
    billUpdate = Update.objects.filter(Bill_obj=bill)[0]
    # print('billUpdate',billUpdate)
    data = json.loads(billUpdate.data)
    # print('data', data['billVersions'])
    for v in data['billVersions']:
        if v['current'] == True:
            # print(v['status'])
            # print(v)
            currentVersion = v['version']
            # print('currentVersion', currentVersion)
            break
        # except:
        #     pass
    # updatedVersion = Update.objects.filter(BillVersion_obj__Bill_obj=bill, BillVersion_obj__Version=currentVersion)[0]
    # print('updatedVersion111', updatedVersion)
    # print(bill.get_absolute_url())
    # prov = Province.objects.filter(name='Ontario')[0]
    # n = Notification(user=request.user, title='%s %s has sponsored bill %s' %(bill.person.first_name, bill.person.last_name, bill.NumberCode), link=str(bill.get_absolute_url()))
    # n.save()
    try:
        billPost = Post.objects.filter(Bill_obj=bill)[0]
    except:
        billPost = Archive.objects.filter(Bill_obj=bill)[0]
    print()
    # xModel = globals()['Post'].objects.all()[0]
    # print(xModel)
    # rs = Reaction.objects.filter(post=billPost).exclude(person=None)
    # print(rs.count())
    updatedVersion = None
    if getSpren and user and user.is_superuser:
        print('runme')
        # bill.get_bill_keywords()
        bill.getSpren(False)
        # import django_rq
        # from rq import Queue
        # from worker import conn
        # queue = django_rq.get_queue('default')
        # queue.enqueue(bill.sprenBot, job_timeout=500)
    # print(bill.summarySpren)
    if view == 'Work':
        posts = Post.objects.filter(Meeting_obj__Bill_obj=bill).order_by(ordering)
    elif view == 'Debates':
        # posts = Post.objects.filter(hansard_key__agenda__bills=bill).order_by(ordering)
        posts = Post.objects.filter(Statement_obj__Bill_objs=bill).select_related('Statement_obj__Person_obj', 'Statement').order_by(ordering, order2)
        # print(posts.count())
        keys = Keyphrase.objects.filter(Bill_obj=bill)
        topicList = []
        for key in keys:
            if not key.text in topicList:
                topicList.append(key.text)
        print(topicList)
    elif view == 'Motions':
        posts = Post.objects.filter(Motion_obj__Bill_obj=bill).order_by(ordering)
    elif view == 'LatestText':
        updatedVersion = Update.objects.filter(BillVersion_obj__Bill_obj=bill, BillVersion_obj__Version=currentVersion)[0]
        print('updatedVersion', updatedVersion)
        posts = {}
    elif view == 'Overview' or not reading:
        posts = Post.objects.filter(Q(BillVersion_obj__Bill_obj=bill)|Q(Motion_obj__Bill_obj=bill)|Q(BillAction_obj__Bill_obj=bill)).order_by(ordering, order2)
        print('posts', posts)
    else:
        print('no posts')
        posts = {}
    # print("%s Bill" %(bill.chamber))
    # titl = "%s Bill" %(bill.chamber)
    if posts:
        setlist = paginate(posts, page, request)
    else:
        setlist = {}
    interactions = get_interactions(request, setlist) 
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    # my_rep = getMyRepVotes(request, setlist)   
    # print(my_rep)         
    try:
        r = Interaction.objects.filter(Post_obj=billPost, User_obj=user)[0]  
        if not r.viewed:
            r.viewed = True
            r.save()
        interactions[r.postId] = r
    except:
        try:
            r = Interaction(Post_obj=billPost, User_obj=user, viewed=True)
            r.save()
            interactions[r.postId] = r
        except:
            pass
    # latest_reading = bill.get_latest_reading 
    # options = {'Overview': '%s?view=Overview' %(bill.get_absolute_url()),  'LatestText': '%s?view=LatestText' %(bill.get_absolute_url()), 'Page: %s' %(page): '?view=%s&page=' %(view), 'Sort: %s' %(sort): '%s?view=%s&sort=%s' %(bill.get_absolute_url(), view, changeSort), 'Debates': '%s?view=Debates' %(bill.get_absolute_url()), 'Motions': '%s?view=Motions' %(bill.get_absolute_url()), 'Work': '%s?view=Work' %(bill.get_absolute_url())}
    nav_options = [nav_item('link', 'Overview', '%s?view=Overview' %(bill.get_absolute_url())), nav_item('link', 'LatestText', '%s?view=LatestText' %(bill.get_absolute_url())), nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), nav_item('button', 'Sort: %s' %(sort), 'subNavWidget("sortForm")'), nav_item('link', 'Debates', '%s?view=Debates' %(bill.get_absolute_url())), nav_item('link', 'Work', '%s?view=Work' %(bill.get_absolute_url()))]
    # if request.user.is_authenticated and request.user.is_god:
    #     # options['update'] = bill.get_update_url()
    #     options['getSpren'] = '%s?getSpren=True' %(bill.get_absolute_url())
    context = {
        'isApp': isApp,
        'title': "%s Bill" %(bill.chamber),
        'nav_bar': nav_options,
        'cards': 'bill_view',
        'page': page,
        'sort': sort,
        'view': view,
        'post': billPost,
        'updatedVersion': updatedVersion,
        'feed_list': setlist,
        'interactions': interactions,
        # 'updates': get_updates(setlist),
        # 'myRepVotes': getMyRepVotes(user, setlist),
        'reading': reading,  
        'topicList': topicList,   
        # 'country': Country.objects.all()[0],   
    }
    # if style == 'json':
    #     return render(request, "utils/feed.html", {**get_theme(request), **context})
    print('done bill view')
    return render_view(request, context, country=country)
    
def bills_view(request, region):
    print('bills_view')
    cards = 'bills_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'Newest')
    page = request.GET.get('page', 1)
    view = request.GET.get('view', 'Current')
    getDate = request.GET.get('date', None)
    date = request.POST.get('date')
    search = request.POST.get('post_type')
    # chamber = get_chamber(request)
    dateform = AgendaForm()    
    searchform = SearchForm()
    subtitle = ''
    # province, region = get_region(request)
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    # gov = get_gov(country, chamber, parliament, session)
    ordering = get_sort_order(sort)
    if request.method == 'POST':
        if date:
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
            subtitle = date
            view = None
            posts = Post.objects.filter(pointerType='Bill', date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Country_obj=country, Bill_obj__chamber__in=chambers).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-DateTime', 'id')
            if posts.count() == 0:
                posts = Archive.objects.filter(pointerType='Bill', date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Country_obj=country, Bill_obj__chamber__in=chambers).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-DateTime', 'id')
            if chamber.lower() == 'all':
                title = "Government Bills"
            else:
                title = '%s Bills' %(chamber.replace('-', ' '))
                # posts = Post.objects.filter(pointerType='Bill', date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Country_obj=country, Bill_obj__chamber=chamber).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-date_time', 'id')
                # if posts.count() == 0:
                #     posts = Archive.objects.filter(pointerType='Bill', date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Country_obj=country, Bill_obj__chamber=chamber).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-date_time', 'id')
                    
        elif search:
            subtitle = search
            view = None
            posts = Post.objects.filter(pointerType='Bill', date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Country_obj=country, Bill_obj__chamber__in=chambers).filter(Q(Bill_obj__amendedNumberCode__icontains=search)|Q(Bill_obj__NumberCode__icontains=search)|Q(Bill_obj__Title__icontains=search)|Q(Bill_obj__LongTitle__icontains=search)).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-DateTime', 'id')
            if posts.count() == 0:
                posts = Archive.objects.filter(pointerType='Bill', date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Country_obj=country, Bill_obj__chamber__in=chambers).filter(Q(Bill_obj__amendedNumberCode__icontains=search)|Q(Bill_obj__NumberCode__icontains=search)|Q(Bill_obj__Title__icontains=search)|Q(Bill_obj__LongTitle__icontains=search)).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-DateTime', 'id')
            if chamber.lower() == 'all':
                title = "Government Bills"
            else:
                title = '%s Bills' %(chamber.replace('-', ' '))
                # posts = Post.objects.filter(pointerType='Bill', date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Country_obj=country, Bill_obj__chamber=chamber).filter(Q(Bill_obj__amendedNumberCode__icontains=search)|Q(Bill_obj__NumberCode__icontains=search)|Q(Bill_obj__Title__icontains=search)|Q(Bill_obj__LongTitle__icontains=search)).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-date_time', 'id')
                # if posts.count() == 0:
                #     posts = Archive.objects.filter(pointerType='Bill', date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).filter(Country_obj=country, Bill_obj__chamber=chamber).filter(Q(Bill_obj__amendedNumberCode__icontains=search)|Q(Bill_obj__NumberCode__icontains=search)|Q(Bill_obj__Title__icontains=search)|Q(Bill_obj__LongTitle__icontains=search)).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-date_time', 'id')
                    


            # if chamber.lower() == 'all':
            #     print('issssalll')
            #     title = "Government Bills"
            #     # posts = Post.objects.filter(Q(bill__NumberCode__iexact=search)).select_related('bill', 'bill__person').order_by('-bill__LatestBillEventDateTime','-date_time', 'id')
            #     posts = Post.objects.filter(post_type='bill').filter(Q(bill__amendedNumberCode__icontains=search)|Q(bill__NumberCode__icontains=search)|Q(bill__ShortTitle__icontains=search)|Q(bill__LongTitleEn__icontains=search)).filter(Q(bill__OriginatingChamberName__icontains='House')|Q(bill__OriginatingChamberName='Senate')|Q(bill__province=province)).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            #     print(posts.count())
            #     if posts.count() == 0:
            #         print('is zero')
            #         posts = Archive.objects.filter(post_type='bill').filter(Q(bill__amendedNumberCode__icontains=search)|Q(bill__NumberCode__icontains=search)|Q(bill__ShortTitle__icontains=search)|Q(bill__LongTitleEn__icontains=search)).filter(Q(bill__OriginatingChamberName__icontains='House')|Q(bill__OriginatingChamberName='Senate')|Q(bill__province=province)).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            # elif chamber.lower() == 'house':
            #     print('isshouse')
            #     title = "House Bills"
            #     posts = Post.objects.filter(post_type='bill').filter(Q(bill__amendedNumberCode__icontains=search)|Q(bill__NumberCode__icontains=search)|Q(bill__ShortTitle__icontains=search)|Q(bill__LongTitleEn__icontains=search)).filter(bill__IsHouseBill='true', bill__province=None).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            #     if posts.count() == 0:
            #         posts = Archive.objects.filter(post_type='bill').filter(Q(bill__amendedNumberCode__icontains=search)|Q(bill__NumberCode__icontains=search)|Q(bill__ShortTitle__icontains=search)|Q(bill__LongTitleEn__icontains=search)).filter(bill__IsHouseBill='true', bill__province=None).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            # elif chamber.lower() == 'senate':
            #     title = "Senate Bills"
            #     posts = Post.objects.filter(post_type='bill').filter(Q(bill__amendedNumberCode__icontains=search)|Q(bill__NumberCode__icontains=search)|Q(bill__ShortTitle__icontains=search)|Q(bill__LongTitleEn__icontains=search)).filter(bill__IsSenateBill='true', bill__province=None).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            #     if posts.count() == 0:
            #         posts = Archive.objects.filter(post_type='bill').filter(Q(bill__amendedNumberCode__icontains=search)|Q(bill__NumberCode__icontains=search)|Q(bill__ShortTitle__icontains=search)|Q(bill__LongTitleEn__icontains=search)).filter(bill__IsSenateBill='true', bill__province=None).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            # elif chamber.lower() == 'assembly':
            #     title = "Assembly Bills"
            #     posts = Post.objects.filter(post_type='bill').filter(Q(bill__amendedNumberCode__icontains=search)|Q(bill__NumberCode__icontains=search)|Q(bill__ShortTitle__icontains=search)|Q(bill__LongTitleEn__icontains=search)).filter(bill__province=province).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            #     if posts.count() == 0:
            #         posts = Archive.objects.filter(post_type='bill').filter(Q(bill__amendedNumberCode__icontains=search)|Q(bill__NumberCode__icontains=search)|Q(bill__ShortTitle__icontains=search)|Q(bill__LongTitleEn__icontains=search)).filter(bill__province=province).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
    else:
        if chamber.lower() == 'all':
            title = "Government Bills"
        else:
            title = '%s Bills' %(chamber.replace('-', ' '))
        # if chamber.lower() == 'house':
        #     title = "House Bills"
        # elif chamber.lower() == 'senate':
        #     title = "Senate Bills"
        # elif 'Assembly' in chamber:
        #     title = 'Assembly Bills'
        # elif 'Council' in chamber:
        #     title = 'Coun Bills'
        if view == 'Current':
            if getDate:
                firstDate = datetime.datetime.strptime(getDate, '%Y-%m-%d')
                secondDate = firstDate + datetime.timedelta(days=1)
            else: 
                secondDate = datetime.datetime.now() + datetime.timedelta(hours=1)
                firstDate = secondDate - datetime.timedelta(days=1000)


            posts = Post.objects.filter(pointerType='Bill').filter(Country_obj=country, Bill_obj__chamber__in=chambers).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-DateTime', 'id')
            if posts.count() == 0:
                posts = Archive.objects.filter(pointerType='Bill').filter(Country_obj=country, Bill_obj__chamber__in=chambers).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-DateTime', 'id')
            if chamber.lower() == 'all':
                title = "Government Bills"
            else:
                title = '%s Bills' %(chamber.replace('-', ' '))
                # posts = Post.objects.filter(pointerType='Bill').filter(Country_obj=country, Bill_obj__chamber=chamber).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-date_time', 'id')
                # if posts.count() == 0:
                #     posts = Archive.objects.filter(pointerType='Bill').filter(Country_obj=country, Bill_obj__chamber=chamber).select_related('Bill_obj', 'Bill_obj__Person_obj').order_by(ordering, '-date_time', 'id')
                    


            # if chamber.lower() == 'all':
            #     posts = Post.objects.filter(post_type='bill').filter(Q(bill__IsHouseBill='true')|Q(bill__IsSenateBill='true')|Q(bill__province=province)).filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            # if chamber.lower() == 'house':
            #     posts = Post.objects.filter(post_type='bill').filter(bill__IsHouseBill='true', bill__province=None).filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            #     # posts = Post.objects.filter(bill__IsHouseBill='true', bill__ParliamentNumber=parliament, bill__SessionNumber=session).select_related('bill', 'bill__person').order_by('-date_time', 'id')
            # elif chamber.lower() == 'senate':
            #     posts = Post.objects.filter(post_type='bill').filter(bill__IsSenateBill='true').filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
            # elif 'Assembly' in chamber:
            #     posts = Post.objects.filter(post_type='bill').filter(bill__province=province).filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('bill', 'bill__person').order_by(ordering, '-date_time', '-id')
        elif view == 'Recommended':
            include_list = ['bill']
            posts, view = algorithim(user, include_list, chamber, country, provState_name, view, page)
        elif view == 'Trending':
            include_list = ['bill']
            posts, view = algorithim(user, include_list, chamber, country, provState_name, view, page)

    setlist = paginate(posts, page, request)
    # bills = [p.Bill_obj for p in setlist]
    # versionUpdates = Update.objects.filter(BillVersion_obj__Bill_obj__in=bills).distinct('pointerId').order_by('pointerId')
    # includedUpdates = {}
    # for b in bills:
    #     includedUpdates[b.id] = versionUpdates.filter(BillVersion_obj__Bill_obj=b)[0]
    # print(versionUpdates)
    # for i in setlist:
    #     print(i)
    #     print(i.date_time)
    #     print(i.billVersion.dateTime)
    #     print('')
    # interactions = get_interactions(request, setlist)  
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s' %(page): '?page=', 'Sort: %s'%(sort): sort, 'Recommended': '?view=Recommended', 'Trending': '?view=Trending', 'Search': 'search', 'Date': 'date'}
    nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), 
                   nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), 
                   nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), 
                   nav_item('link', 'Recommended', '?view=Recommended'), 
                   nav_item('link', 'Trending', '?view=Trending'),
                    nav_item('button', 'Search', 'subNavWidget("searchForm")'), 
                    nav_item('button', 'Date', 'subNavWidget("datePickerForm")')]
    


    # nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), nav_item('link', 'Page: %s' %(page), '?view=%s&page=' %(view)), nav_item('link', 'Current', '?view=Current'), nav_item('link', 'Recommended', '?view=Recommended'), nav_item('link', 'Trending', '?view=Trending')]
    # nav_options = [nav_item('link', 'Overview', '%s?view=Overview' %(bill.get_absolute_url())), nav_item('link', 'LatestText', '%s?view=LatestText' %(bill.get_absolute_url())), nav_item('link', 'Page: %s' %(page), '?view=%s&page=' %(view)), nav_item('button', 'Sort: %s' %(sort), 'subNavWidget("sortForm")'), nav_item('link', 'Debates', '%s?view=Debates' %(bill.get_absolute_url())), nav_item('link', 'Work', '%s?view=Work' %(bill.get_absolute_url()))]
    context = {
        'isApp': isApp,
        'title': title,
        'subtitle': subtitle,
        'nav_bar': nav_options,
        'view': view,
        # 'region': region,
        'dateForm': dateform,
        'searchForm': searchform,
        'cards': cards,
        'sort': sort,
        'sortOptions': ['Newest','Loudest'],
        'feed_list':setlist,
        # 'includedUpdates': includedUpdates,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        # 'myRepVotes': getMyRepVotes(user, setlist),
    }
    # print(setlist)
    # if style == 'json':
    #     return render(request, "json/json_feed.html", {**get_theme(request), **context},content_type="application/json")
    
    return render_view(request, context, country=country)
      
def elections_view(request, region):
    # print('elections view')
    title = "Upcoming Elections"
    # cards = 'elections_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', '')
    if request.user.is_authenticated:
        view = request.GET.get('view', 'My Elections')
    else:
        view = request.GET.get('view', 'All Elections')
    page = request.GET.get('page', 1)
    # province, region = get_region(request)
    # # chamber = get_chamber(request)
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality, chamber=None)

    # if style == 'index':
    #     page = 1
    if user and view == 'My Elections':
        posts = Post.objects.filter(pointerType='Election').filter(Election_obj__end_date__gte=datetime.datetime.now()-datetime.timedelta(days=30)).exclude(Election_obj__District_obj=None).filter(Q(Election_obj__District_obj=user.Federal_District_obj)|Q(Election_obj__District_obj=user.ProvState_District_obj)|Q(Election_obj__District_obj=user.Greater_Municipal_District_obj)|Q(Election_obj__District_obj=user.Municipal_District_obj)).order_by('DateTime')
        
        # if request.user.Federal_District_obj and request.user.ProvState_District_obj:
        #     posts = Post.objects.filter(post_type='election').filter(election__end_date__gte=datetime.datetime.now()-datetime.timedelta(days=30)).filter(Q(election__riding=request.user.riding)|Q(election__district=request.user.district)).order_by('date_time')
        # elif request.user.riding:
        #     posts = Post.objects.filter(post_type='election').filter(election__end_date__gte=datetime.datetime.now()-datetime.timedelta(days=30)).filter(election__riding=request.user.riding).order_by('date_time')
        # elif request.user.district:
        #     posts = Post.objects.filter(post_type='election').filter(election__end_date__gte=datetime.datetime.now()-datetime.timedelta(days=30)).filter(election__district=request.user.district).order_by('date_time')
        # else:
        #     posts = []
    elif view == 'My Elections':
        posts = []
    else:
        posts = []

        # if province:
        #     posts = Post.objects.filter(post_type='election').filter(election__end_date__gte=datetime.datetime.now()-datetime.timedelta(days=30)).filter(Q(election__level='Federal')|Q(election__province=province)).order_by('date_time')
        # else:
        #     posts = Post.objects.filter(post_type='election').filter(election__end_date__gte=datetime.datetime.now()-datetime.timedelta(days=30)).filter(election__level='Federal').order_by('date_time')
    
    # posts = Post.objects.filter(post_type='election').filter(Q(election__level='Federal')|Q(election__province=province)).order_by('date_time')
    # print(posts)
    if user:
        # options = {'My Elections': '?view=My Elections', 'All Elections': '?view=All Elections'}
        nav_options = [nav_item('link', 'My Elections', '?view=My Elections'),nav_item('link', 'All Elections', '?view=All Elections')]
    else:  
        # options = {'All Elections': '?view=All Elections'}
        nav_options = [nav_item('link', 'All Elections', '?view=All Elections')]


    setlist = paginate(posts, page, request) 
    # setlist = posts
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    context = {
        'isApp': isApp,
        'title': title,
        'view': view,
        'nav_bar': nav_options,
        'cards': 'elections_list',
        'sort': sort,
        'feed_list':setlist,
        # 'updates': get_updates(setlist),
        # 'country': Country.objects.all()[0],
    }
    return render_view(request, context, country=country)
        
def candidates_view(request, organization, region, iden):
    print('candidates view')
    cards = 'candidates_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', '')
    view = request.GET.get('view', '')
    page = request.GET.get('page', 1)
    # province, region = get_region(request)
    # chamber = get_chamber(request)
    election = Election.objects.filter(id=iden)[0]
    candidates = Role.objects.filter(election=election).order_by('?')
    if election.riding:
        title = "%s %s %s" %(election.province.name, election.riding.name, election.type)
    elif election.district:
        title = "%s %s %s" %(election.province.name, election.district.name, election.type)
    else:
        title = "%s %s %s" %(election.province.name, election.level, election.type)
    setlist = paginate(candidates, page, request)    
    # agenda, agendaItems = get_agenda()
    context = {
        'title': title,
        'view': view,
        # 'subtitle': '44th Parliament of Canada',
        # "agenda":agenda,
        # "agendaItems":agendaItems,
        'cards': cards,
        'sort': sort,
        'feed_list':setlist,
        'country': Country.objects.all()[0],
    }
    return render_view(request, context)
    
def house_or_senate_hansards_view(request, region):
    print('house/senate hansard view')
    
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'time')
    page = request.GET.get('page', 1)
    view = request.GET.get('view', 'Current')
    date = request.POST.get('date')
    form = AgendaForm()
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    # chamber = get_chamber(request)
    # province, region = get_region(request)
    # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s' %(page): '?page=',  'Date': 'date'}
    nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), 
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), 
            # nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), 
            # nav_item('link', 'Recommended', '?view=Recommended'), 
            # nav_item('link', 'Trending', '?view=Trending'),
            # nav_item('button', 'Search', 'subNavWidget("searchForm")'), 
            nav_item('button', 'Date', 'subNavWidget("datePickerForm")')]
    subtitle = ''
    if request.method == 'POST':
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        subtitle = date
        view = None
        if chamber == 'All':
            title = '%s Debates' %(country.Name)
        else:   
            title = '%s Debates' %(chamber)
        posts = Post.objects.filter(Country_obj=country, Meeting_obj__meeting_type='Debate', Meeting_obj__DateTime__gte=date, Meeting_obj__DateTime__lt=date + datetime.timedelta(days=1)).filter(Meeting_obj__chamber__in=chambers).select_related('Meeting_obj').order_by('-Meeting_obj__DateTime')

        # elif chamber == 'All':
        #     posts = Post.objects.filter(hansard_key__Publication_date_time__gte=date, hansard_key__Publication_date_time__lt=date + datetime.timedelta(days=1)).select_related('hansard_key').order_by('-hansard_key__Publication_date_time')
        #     title = 'House and Senate Debates'
        # elif 'Assembly' in chamber:
        #     title = 'Assembly Debates'
        #     posts = Post.objects.filter(hansard_key__Organization=region+'-Assembly', hansard_key__Publication_date_time__gte=date, hansard_key__Publication_date_time__lt=date + datetime.timedelta(days=1)).select_related('hansard_key').order_by('-date_time', 'id')
    # elif view == 'upcoming':
    #     posts = Post.objects.filter(committeeMeeting__date_time_start__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')).exclude(committeeMeeting=None).exclude(committeeMeeting__Organization='House').order_by('-committeeMeeting__date_time_start')
    else:
        # if chamber == 'Senate':
        #     title = 'Senate Debates'
        # elif chamber == 'House':    
        #     title = 'House of Commons Debates'
        # elif chamber == 'All':
        #     title = 'House and Senate Debates'
        # elif 'Assembly' in chamber:
        #     title = 'Assembly Debates'
        if view == 'Current':
            if chamber == 'All':
                title = '%s Debates' %(country.Name)
            else:   
                # posts = Post.objects.filter(Country_obj=country, Meeting_obj__meeting_type='Debate', date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=12)).filter(Meeting_obj__chamber=chamber).select_related('Meeting_obj').order_by('-Meeting_obj__PublicationDateTime')
                title = '%s Debates' %(chamber)
            # posts = Post.objects.filter(Country_obj=country, Meeting_obj__meeting_type__iexact='Debate', DateTime__lte=now_utc() + datetime.timedelta(hours=12)).filter(Meeting_obj__chamber__in=chambers).select_related('Meeting_obj').order_by('-Meeting_obj__DateTime')
            posts = Post.objects.filter(Country_obj=country, Meeting_obj__meeting_type__iexact='Debate').filter(Meeting_obj__chamber__in=chambers).select_related('Meeting_obj').order_by('-Meeting_obj__DateTime')
            print('posts', posts)
            for p in posts:
                print(p)
                print(p.DateTime)
                # print(p.Update_obj.Meeting_obj)
                
            # print('----')
            # for m in Meeting.objects.all():
            #     print(m.Title)
            # if chamber == 'Senate':
            #     posts = Post.objects.filter(date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=12)).filter(hansard_key__Organization='Senate').select_related('hansard_key').order_by('-hansard_key__Publication_date_time')
            # elif chamber == 'House':    
            #     posts = Post.objects.filter(date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=12)).filter(hansard_key__Organization='House').select_related('hansard_key').order_by('-hansard_key__Publication_date_time')
            # elif chamber == 'All':
            #     posts = Post.objects.filter(date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=12)).exclude(hansard_key=None).select_related('hansard_key').order_by('-date_time')
            # elif 'Assembly' in chamber:
            #     posts = Post.objects.filter(hansard_key__Organization=region+'-Assembly', date_time__lte=datetime.datetime.now() + datetime.timedelta(hours=12)).select_related('hansard_key').order_by('-date_time', 'id')
        elif view == 'Recommended':
            include_list = ['Statement']
            posts, view = algorithim(user, include_list, chamber, country, provState_name, view, page)
            # posts, view = algorithim(request, include_list, chamber, region, view, page)
        elif view == 'Trending':
            include_list = ['Meeting']
            posts, view = algorithim(user, include_list, chamber, country, provState_name, view, page)
            # posts, view = algorithim(request, include_list, chamber, region, view, page)
    
    
    if view != 'Trending' and user:
        userKeys = [k for k, value in Counter(user.interest_array).most_common()]
    else:
        # if chamber == 'House':
        #     orgs = ['House', 'House of Commons']
        # elif chamber == 'Senate':
        #     orgs = ['Senate']
        # elif chamber == 'All':
        #     orgs = ['Senate', 'House', 'House of Commons', '%s-Assembly'%(region)]
        # elif chamber == 'Assembly':
        #     orgs = ['%s-Assembly'%(region)]
        try:
            dateQuery = Meeting.objects.filter(Country_obj=country, meeting_type='Debate', chamber__in=chambers).order_by('-DateTime')[12].DateTime
        except:
            dateQuery = now_utc()
        dt = now_utc().replace(tzinfo=pytz.UTC) - dateQuery
        userKeys = get_trending_keys(dt, ['Meeting'], chambers)
    setlist = paginate(posts, page, request)
    # interactions = get_interactions(request, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    context = {
        'isApp': isApp,
        'title': title,
        'subtitle': subtitle,
        'nav_bar': nav_options,
        'view': view,
        # 'region': region,
        'dateForm': form,
        'cards': 'debates_list',
        'sort': sort,
        'feed_list':setlist,        
        'user_keywords': userKeys,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
    }
    return render_view(request, context, country=country)

def debate_view(request, region, chamber, govNumber, session, iden, year, month, day, hour, minute):
    print(' hansard _view')
    govNumber = re.sub("[^0-9]", "", govNumber)
    session = re.sub("[^0-9]", "", session)
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'Oldest')
    page = request.GET.get('page', 1)
    speaker_id = request.GET.get('speaker', '')
    topic = request.GET.get('topic', '')
    view = request.GET.get('view', '')
    id = request.GET.get('id', '')
    instruction = None
    userData = None
    ordering = get_sort_order(sort)
    print('ordering', ordering)
    # cards = 'debate_view'
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality, chamber=chamber)
    govs = get_gov(country, gov_levels, govNumber, session)
    sprenPost = None
    # # preview card
    # iden = 12167831
    # time = '03:00pm'
    video_link = None
    # print('region', region)
    # print('chamber', chamber)
    # print('govNumber', govNumber)
    # print('session', session)
    print('topic', topic)
    # m = Meeting.objects.filter(id=iden)[0]
    p = Post.objects.filter(Meeting_obj__id=iden)[0]
    m = p.Meeting_obj
    meetingUpdate = p.Update_obj
    title = '%s %s' %(chamber, str(m.Title))
    # print(m.__dict__)
    # print('meetingUpdate', json.loads(meetingUpdate.data)['Terms'])
    print('----------')


    # ttt = 'C-360, An Act to establish a national strategy to reduce the amount of wasted food in Canada'
    # # Keyphrase.objects.filter(text=trend.text, Country_obj=self.Country_obj, DateTime__gte=sevenDays, DateTime__lte=self.DateTime)
    # kxs = Keyphrase.objects.filter(text=ttt)
    # print('kxs', kxs)
    # kk = kxs[0]
    # kk.set_trend()
    # print(kk.KeyphraseTrend_obj)
    # print('done set trend')
    # if chamber == 'All':
    #     h = Meeting.objects.filter(chamber__in=chambers, Government_obj=gov, pub_iden=iden)[0]
    #     title = '%s %s' %(chamber, str(h.Title))
    # else:
    #     h = Meeting.objects.filter(chamber=chamber, Government_obj=gov, pub_iden=iden)[0]
    #     title = '%s %s' %(chamber, str(h.Title))
        
    # else:
    #     h = Hansard.objects.filter(ParliamentNumber=parliament, SessionNumber=session, id=iden)[0]
    #     title = '%s %s' %(str(h.Organization.replace('-',' ')), str(h.Title))
    if m.Region_obj.timezone:
        tz = m.Region_obj.timezone
    else:
        tz = 'US/Eastern'
    time = request.GET.get('time', '')
    # print('t1', time)
    # if not time:
    #     time = request.GET.get('time', m.DateTime.strftime("%I:%M%p"))
    subtitle = str(get_ordinal(m.Government_obj.GovernmentNumber)) + ' Parl. ' + str(get_ordinal(m.Government_obj.SessionNumber)) + ' Sess.'
    subtitle2 = '%s %s' %(datetime.datetime.strftime(m.DateTime, '%B %-d, %Y'), time)
    hasContext = True
    # print('topic',topic)
    if topic or speaker_id:
        hasContext = False
        if speaker_id:
            speaker = Person.objects.filter(id=speaker_id)[0]
    elif page == 1 and sort.lower() == 'oldest':
        seconds = '00'
        try:
            videoUrl = json.loads(meetingUpdate.data)['VideoUrl']
        except:
            try:
                agendaUpdate = Post.objects.filter(Agenda_obj=m.Agenda_obj)[0].Update_obj
                videoUrl = json.loads(agendaUpdate.data)['VideoUrl']
            except:
                videoUrl = None
        if videoUrl:
            if chamber == 'House' and country.Name == 'Canada':
                date = '%s-%s-%s' %(m.DateTime.year, m.DateTime.month, m.DateTime.day)
                dt = datetime.datetime.strptime(date + '/' + time, '%Y-%m-%d/%I:%M%p')
                # doesn't work on mac, needs leading zero
                video_link = 'https://parlvu.parl.gc.ca/Harmony/en/PowerBrowser/PowerBrowserV2/%s%s%s/-1/%s?mediaStartTime=%s%s%s%s%s%s&viewMode=3&globalStreamId=29' %(dt.year,dt.month,dt.day,videoUrl,dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second)
                # # preview video
                # video_link = 'https://parlvu.parl.gc.ca/Harmony/en/PowerBrowser/PowerBrowserV2/20221214/-1/38300?mediaStartTime=20221214150123&viewMode=3&globalStreamId=29'
            elif chamber == 'Senate' and country.Name == 'Canada':
                video_link = videoUrl
    follow = request.GET.get('follow', '')
    if follow and topic and request.user.is_authenticated:
        print('gogo')
        fList = request.user.follow_topic_array
        if topic in fList:
            # fList.remove(topic)
            # response = 'Unfollow "%s"' %(topic)
            # user = set_keywords(request.user, 'remove', topic)
            instruction = 'follow_topic_array remove "%s"' %(topic)
        elif topic not in fList:
            # fList.append(topic)
            # response = 'Following "%s"' %(topic)
            # user = set_keywords(request.user, 'add', topic)
            instruction = 'follow_topic_array add "%s"' %(topic)
        # user.set_follow_topics(fList)
        # request.user.save()
        # userData = get_user_signing_data(user)
        return render(request, "utils/dummy.html", {"result": 'success', 'userData': get_user_sending_data(user), 'instruction':instruction})
    wordCloud = None
    if topic:
        print(topic)
        # if request.user.is_authenticated:
        #     user = request.user
        # else:
        #     try:
        #         userToken = request.COOKIES['userToken'] # for anon users
        #         user = User.objects.filter(userToken=userToken)[0]
        #     except Exception as e:
        #         user = None
        if user:
            # user = set_keywords(user, 'add', topic)
            userData = get_user_sending_data(user)

            instruction = 'keyword_array add "%s"' %(topic)
    
        hasContext = False
        search = ['%s'%(topic)]
        print('searxh', search)
        # hansards = HansardItem.objects.filter(Terms__icontains=term, hansard=h).select_related('person')
        
        # states = Statement.objects.filter(Terms_array__icontains=topic)
        # print('states', states)
        # states2 = Statement.objects.filter(keyword_array__icontains=topic)
        # print('states2', states2)
        # x = '96fb2556f6954636b7e4981d61421ff5'
        # x = 'fd85105fc79949f09cd47fb179a8bdd8'
        # x = 'c1cd5df0e71246c0b4c3d0d2c0a3e7ca'
        # st = Statement.objects.filter(id=x)[0]
        # print(st)
        # print(st.keyword_array)
        # print(st.Terms_array)
        if speaker_id:
            posts = Post.objects.filter(Statement_obj__Person_obj=speaker, Statement_obj__Meeting_obj=m).filter(Q(Statement_obj__Terms_array__overlap=search)|Q(Statement_obj__keyword_array__overlap=search)).select_related('Statement_obj__Person_obj', 'Statement_obj').order_by(ordering,'-DateTime')
            # if posts.count() == 0:
            #     posts = Post.objects.filter(hansardItem__person=speaker, hansardItem__keywords__overlap=search, hansardItem__hansard=h).select_related('hansardItem__person', 'hansardItem').order_by(ordering,'-date_time')
        else:
            # s = Statement.objects.all().first()
            # print('h', h)
            # posts = Post.objects.filter(Statement_obj__Meeting_obj=h)
            posts = Post.objects.filter(Statement_obj__Meeting_obj=m).filter(Q(Statement_obj__Terms_array__overlap=search)|Q(Statement_obj__keyword_array__overlap=search)).order_by(ordering,'-DateTime')
            # print('posts1', posts)
            # if posts.count() == 0:
            #     posts = Post.objects.filter(hansardItem__keywords__overlap=search, hansardItem__hansard=h).select_related('hansardItem__person', 'hansardItem').order_by(ordering,'-date_time')
        # from posts.utils import summarize_topic, get_token_count
        # print('pstss',posts[0].keyword_array)
        try:
            spren = Spren.objects.filter(Meeting_obj=m, topic=topic).exclude(content='TBD')[0]
            sprenPost = spren.get_post()
        except Exception as e:
            print('spren error ', str(e))
    elif speaker_id:
        posts = Post.objects.filter(Statement_obj__Person_obj=speaker, Statement_obj__Meeting_obj=m).select_related('Statement_obj__Person_obj', 'Statement_obj').order_by(ordering,'-DateTime')
    
    elif time:
        print('time', time)
        if time == None:
            print('eys')
        else:
            print('no')
        date_time = '%s/%s/%s/%s' %(m.DateTime.year, m.DateTime.month, m.DateTime.day, time)
        print(date_time)
        dt = datetime.datetime.strptime(date_time, '%Y/%m/%d/%I:%M%p')
        posts = Post.objects.filter(Statement_obj__Meeting_obj=m, Statement_obj__DateTime__gte=dt).select_related('Statement_obj__Person_obj', 'Statement_obj').order_by(ordering,'-DateTime')
    else:
        print('eeeee')
        # hasContext = False
        posts = Post.objects.filter(Statement_obj__Meeting_obj=m).select_related('Statement_obj__Person_obj', 'Statement_obj').order_by('Statement_obj__created','-DateTime')
    if id:
        setlist = paginate(posts, 'id=%s' %(id), request)
        hasContext = setlist[0].Statement_obj.id
        id = id
        video_link = None
    else:
        setlist = paginate(posts, page, request)
        if not topic and not speaker_id:
            if page != 1 or time:
                try:
                    hasContext = setlist[0].Statement_obj.id
                except:
                    pass
    # interactions = get_interactions(request, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    # user.follow_topic_array = None
    # user.follow_topic_array.append('first')

    # user.follow_topic_array = user.keyword_array
    # if remove_oldest:
    #     user.keyword_array.pop(0)
    # user.follow_topic_array.append('x')
    print(request.user.follow_topic_array)
    # user.save()
    # userData = get_signing_data(user)
    # print(userData)
    # # print()/
    # instruction = 'follow_topic_array remove "Rex Murphy 11"'
    # instruction = 'follow_topic_array add "Rex Murphy 6"'
    # options = {'Page: %s'%(page): '?page=', 'Sort: %s'%(sort):sort, 'Transcript': h.GovPage}
    nav_options = [ 
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), 
            nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'),
            nav_item('link', 'Transcript', m.GovPage)]
    if topic:
        if user and topic in user.follow_topic_array:
            f = 'following'
        else:
            f = 'follow'
        # options = {'Page: %s'%(page): '?page=', 'Sort: %s' %(sort):sort, 'follow':'%s?topic=%s&follow=%s' %(h.get_absolute_url(), topic, f), 'Transcript': h.GovPage}
        nav_options = [ 
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), 
            nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), 
            nav_item('link', 'follow', '%s?topic=%s&follow=%s' %(m.get_absolute_url(), topic, f)), 
            nav_item('link', 'Transcript', m.GovPage),]
    context = {
        'isApp': isApp,
        'title': title,
        'subtitle': subtitle,
        'subtitle2': subtitle2,  
        'title_link': m.get_absolute_url(),      
        'nav_bar': nav_options,
        'cards': 'debate_view',
        'view': view,
        'sort': sort,
        # 'country': Country.objects.all()[0],
        'sortOptions': ['Oldest','Newest','Loudest','Random'],
        'topic': topic,
        'id': id,
        'time': time,
        'speaker_id': speaker_id,
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        'debate': m,
        'debateUpdate': meetingUpdate,
        'sprenPost': sprenPost,
        'video_link': video_link,
        'hasContext': hasContext,
        'wordCloud': wordCloud,
        'topicList': [topic],
        'userData':userData,
        'instruction':instruction
    }
    return render_view(request, context, country=country)


def motions_view(request, region):
    print('house/senate motions view')
    # cards = 'motions_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'time')
    page = request.GET.get('page', 1)
    view = request.GET.get('view', 'past')
    getDate = request.GET.get('date', None)
    date = request.POST.get('date')
    form = AgendaForm()
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    # gov = get_gov(country, chamber, parliament, session)
    # options = {'Chamber: %s' %(chamber): 'chamber', 'Page: %s' %(page): '?page=', 'Date': 'date'}
    nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), 
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), 
            # # nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), 
            # nav_item('link', 'Recommended', '?view=Recommended'), 
            # nav_item('link', 'Trending', '?view=Trending'),
            # nav_item('button', 'Search', 'subNavWidget("searchForm")'), 
            nav_item('button', 'Date', 'subNavWidget("datePickerForm")')]
    subtitle = ''
    if request.method == 'POST':
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        subtitle = date
        view = None
        posts = Post.objects.filter(Country_obj=country, chamber__in=chambers).filter(DateTime__gte=date, DateTime__lt=date + datetime.timedelta(days=1)).select_related('Motion_obj').order_by('-DateTime')
        if chamber.lower == 'all':
            title = 'Motions'
        else:
            title = f'{chamber} Motions'
        # if chamber == 'Senate':
        #     # posts = Post.objects.filter(motion__OriginatingChamberName='Senate').filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).select_related('motion').order_by('-date_time')
        #     title = 'Senate Motions'
        # elif chamber == 'House':    
        #     posts = Post.objects.filter(motion__OriginatingChamberName='House').filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).select_related('motion').order_by('-date_time')
        #     title = 'House of Commons Motions'
        # elif chamber == 'All':
        #     posts = Post.objects.filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1)).select_related('motion').order_by('-date_time')
        #     title = 'House and Senate Motions'
    # elif view == 'upcoming':
    #     posts = Post.objects.filter(committeeMeeting__date_time_start__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')).exclude(committeeMeeting=None).exclude(committeeMeeting__Organization='House').order_by('-committeeMeeting__date_time_start')
    else:
        # print('motion else')
        if getDate:
            # print('getdate')
            firstDate = datetime.datetime.strptime(getDate, '%Y-%m-%d')
            secondDate = firstDate + datetime.timedelta(days=1)
        else: 
            secondDate = now_utc() + datetime.timedelta(hours=1)
            firstDate = secondDate - datetime.timedelta(days=1000)
        # posts = Post.objects.filter(Country_obj=country, pointerType='Motion')
        posts = Post.objects.filter(Country_obj=country, pointerType='Motion', chamber__in=chambers).filter(DateTime__gte=firstDate, DateTime__lt=secondDate).select_related('Motion_obj').order_by('-DateTime')
        print('chambers', chambers)
        print('country', country)
        # posts = Post.objects.filter(Country_obj=country, pointerType='Motion', chamber__in=chambers).order_by('-pointerDateTime')
        print('posts',posts)
        if chamber.lower() == 'all':
            title = 'Motions'
        else:
            title = f'{chamber} Motions'
        # if chamber == 'Senate':
        #     posts = Post.objects.filter(motion__OriginatingChamberName='Senate').filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('motion').order_by('-date_time')
        #     title = 'Senate Motions'
        # elif chamber == 'House':    
        #     posts = Post.objects.filter(motion__OriginatingChamberName='House').filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('motion').order_by('-date_time')
        #     title = 'House of Commons Motions'
        # elif chamber == 'All':
        #     posts = Post.objects.exclude(motion=None).filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('motion').order_by('-date_time')
        #     title = 'House and Senate Motions'
        # elif 'Assembly' in chamber:
        #     title = 'Assembly Motions'
        #     posts = Post.objects.filter(motion__OriginatingChamberName=region+'-Assembly').filter(date_time__gte=firstDate, date_time__lt=secondDate).select_related('motion').order_by('-date_time', '-id')
    
    # if not subtitle:
    #     latest = posts[0]
    #     subtitle = str(latest.motion.ParliamentNumber) + 'th Parliament, ' + str(latest.hansard_key.SessionNumber) + 'st Session'
    setlist = paginate(posts, page, request)
    # interactions = get_interactions(request, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    # my_rep = getMyRepVotes(request, setlist)   
    # print(my_rep)         
    context = {
        'isApp': isApp,
        'title': title,
        'subtitle': subtitle,
        'nav_bar': nav_options,
        'view': view,
        # 'region': region,
        'dateForm': form,
        'cards': 'motions_list',
        'sort': sort,
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        'myRepVotes': getMyRepVotes(user, setlist),
    }
    return render_view(request, context, country=country)


def motion_view(request, region, chamber, govNumber, session, number):
    print('vote motion view')
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'Alphabetical')
    page = request.GET.get('page', 1)
    party = request.GET.get('party', 'All')
    view = request.GET.get('view', '')
    # print(party)
    vote = request.GET.get('vote', 'All')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality, chamber=chamber)
    # print('govNumber',govNumber)
    # print('session',session)
    # print('gov_levels',gov_levels)
    govs = get_gov(country, gov_levels, govNumber, session)
    # print('govs',govs)
    # print('chamber',chamber)
    # print('number', f'xx{number}aa')
    # motions = Motion.objects.filter(chamber__iexact=chamber, Government_obj__in=govs, VoteNumber=number)
    motions = Motion.objects.filter(chamber__iexact=chamber, Government_obj__in=govs, VoteNumber=number)
    # print('motions',motions)
    motion = motions[0]
    title = '%s Motion No. %s' %(motion.chamber.replace('-', ' '), motion.VoteNumber)
    # cards = 'vote_list'
    votes = Vote.objects.filter(Motion_obj=motion)
    if party != 'All':
        votes = votes.filter(Person_obj__Party_obj__Name__iexact=party)
    if vote != 'All':
        votes = votes.filter(VoteValueName__iexact=vote)
    # print(motion.partys)
    setlist = paginate(votes, page, request)
    # setlist = setlist[0:1]
    # interactions = get_interactions(request, setlist)
    # print('setlist', len(setlist))
    people_objs = [v.Person_obj for v in setlist]
    # print('people_objs', len(people_objs))
    personUpdates = Update.objects.filter(Person_obj__in=people_objs).order_by('Person_obj__id','-created').distinct('Person_obj__id')
    # print('personUpdates', len(personUpdates))
    # for p in personUpdates:
    #     print()
    #     fields = p._meta.fields
    #     data = []
    #     for f in fields:
    #         # data.append(str(f.name))
    #         # print(f.name, f)
    #         print(f.name, getattr(p, f.name))
        # print(data)
    
    updates = {}
    for v in setlist:
        try:
            p = [u for u in personUpdates if u.Person_obj == v.Person_obj][0]
            updates[v.id] = p
        except:
            pass
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    # my_rep = getMyRepVotes(request, motions)      
    # print(my_rep)      
    if setlist.paginator.num_pages < int(page):
        page = str(setlist.paginator.num_pages)
    # options = {'Page: %s'%(page): '?sort=%s&party=%s&vote=%s&page=' %(sort, party, vote), 'Party: %s' %(party):'?page=%s&sort=%s&vote=%s&party=' %(page, sort, vote), 'Vote: %s' %(vote): '?page=%s&sort=%s&party=%s&vote=' %(page, sort, party)}
    nav_options = [
        # nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), 
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), 
            nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), 
            nav_item('button', 'Party: %s' %(party), 'subNavWidget("partyForm")'), 
            nav_item('button', 'Vote: %s' %(vote), 'subNavWidget("voteForm")' )]
    context = {
        'isApp': isApp,
        'title': title,     
        'view': view,
        'nav_bar': nav_options,
        'cards': 'vote_list',
        'sort': sort,
        'feed_list':setlist,
        'personUpdates': updates,
        'm': motion,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        # 'myRepVotes': getMyRepVotes(user, setlist),
        'myRepVotes': {},
        'partyOptions': [party.Name for party in motion.Party_objs.all()],
        'sortOptions': ['Alphabetical'],
        'voteOptions': ['All', 'Yea', 'Nay', 'Paired']
    }
    return render_view(request, context, country=country)

def house_motion_view(request, govNumber, session, number):
    print('latest house motion view')
    # h = Hansard.objects.get(Parliament=parliament, Session=session, pub_iden=iden)
    # title = None
    # subtitle = str(motion.ParliamentNumber) + 'th Parliament, ' + str(motion.SessionNumber) + 'st Session'
    # subtitle2 = datetime.datetime.strftime(h.Publication_date_time, '%B %-d, %Y')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, None, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    govs = get_gov(country, gov_levels, govNumber, session)

    motion = Motion.objects.filter(Government_obj__in=govs, chamber=chamber, VoteNumber=number)[0]
    title = 'House Motion No. %s' %(motion.VoteNumber)

    cards = 'vote_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'alphabetical')
    view = request.GET.get('view', '')
    page = request.GET.get('page', 1)
    votes = Vote.objects.filter(Motion_obj=motion)
    setlist = paginate(votes, page, request)
    # interactions = get_interactions(user, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    # agenda, agendaItems = get_agenda()
    # options = {'Page: %s'%(page): page, 'Sort: %s'%(sort): sort, 'Party: All':'previous', 'Vote: All': 'all'}
    nav_options = [
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'), 
            nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'),  
            nav_item('button', 'Party: All', 'subNavWidget("partyForm")'), 
            nav_item('button', 'Vote: All', 'subNavWidget("voteForm")' )]
    # options = {'Roles':'%s?view=Roles'%(person.get_absolute_url()), 'Vote History':'%s?view=Vote History'%(person.get_absolute_url())}
    context = {
        'isApp': isApp,
        'title': title,
        'view': view,
        # 'subtitle': subtitle,
        # 'subtitle2': subtitle2,  
        # "agenda":agenda,
        # "agendaItems":agendaItems,      
        'nav_bar': nav_options,
        'cards': cards,
        'sort': sort,
        # 'country': Country.objects.all()[0],
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        'm': motion,
    }
    return render_view(request, context, country=country)


def senate_motion_view(request, govNumber, session, number):
    print('senate motion view')
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, None, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    govs = get_gov(country, gov_levels, govNumber, session)

    # h = Hansard.objects.get(Parliament=parliament, Session=session, pub_iden=iden)
    motion = Motion.objects.filter(Government_obj__in=govs, chamber__in=chambers, VoteNumber=number)[0]
    title = 'Senate Motion No. %s' %(motion.VoteNumber)
    # subtitle = str(motion.ParliamentNumber) + 'th Parliament, ' + str(motion.SessionNumber) + 'st Session'
    # subtitle2 = datetime.datetime.strftime(h.Publication_date_time, '%B %-d, %Y')
    cards = 'vote_list'
    style = request.GET.get('style', 'index')
    view = request.GET.get('view', '')
    sort = request.GET.get('sort', 'alphabetical')
    page = request.GET.get('page', 1)
    votes = Vote.objects.filter(motion=motion).order_by('person__last_name')
    setlist = paginate(votes, page, request)
    # interactions = get_interactions(user, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    # agenda, agendaItems = get_agenda()
    # options = {'Page: %s'%(page): page, 'Sort: %s'%(sort): sort, 'Party: All':'previous', 'Vote: All': 'all'}
    nav_options = [
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'),
            nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'),  
            nav_item('button', 'Party: All', 'subNavWidget("partyForm")'), 
            nav_item('button', 'Vote: All', 'subNavWidget("voteForm")' )]
    # options = {'Roles':'%s?view=Roles'%(person.get_absolute_url()), 'Vote History':'%s?view=Vote History'%(person.get_absolute_url())}
    context = {
        'isApp': isApp,
        'title': title,
        'view': view,
        # 'subtitle': subtitle,
        # 'subtitle2': subtitle2, 
        # "agenda":agenda,
        # "agendaItems":agendaItems,       
        'nav_bar': nav_options,
        'cards': cards,
        'sort': sort,
        # 'country': Country.objects.all()[0],
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        'm': motion,
    }
    return render_view(request, context, country=country)

    
def latest_committees_view(request, region, chamber):
    print('latest committees view')
    title = 'Latest Committee Events' 
    # subtitle = str(latest.ParliamentNumber) + 'th Parliament, ' + str(latest.SessionNumber) + 'st Session'
    # subtitle2 = datetime.datetime.strftime(latest.date_time_start, '%B %-d, %Y')
    cards = 'committeeMeeting_list'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'time')
    page = request.GET.get('page', 1)
    view = request.GET.get('view', 'Current')
    # filter = request.GET.get('filter', 'all')
    date = request.POST.get('date')
    form = AgendaForm()
    subtitle = ''
    # chamber = get_chamber(request)
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, region, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    govs = get_gov(country, gov_levels)

    # options = {'Chamber: %s' %(chamber): 'chamber', 'Current': '?view=Current', 'Upcoming': '?view=Upcoming', 'Date': 'date'}
    nav_options = [nav_item('button', f'Chamber:{chamber}', 'subNavWidget("chamberForm")'), 
            # nav_item('link', 'Page: %s' %(page), '?view=%s&page=' %(view)), 
            # nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), 
            nav_item('link', 'Current', '?view=Current'), 
            nav_item('link', 'Upcoming', '?view=Upcoming'),
            # nav_item('button', 'Search', 'subNavWidget("searchForm")'), 
            nav_item('button', 'Date', 'subNavWidget("datePickerForm")')]
    # parl = Parliament.objects.filter(organization='Federal').first()
    committeeList = Committee.objects.exclude(chamber__in=chamber).filter(Government_obj__in=govs).order_by('Title')
    # if chamber == 'House':
    #     committeeList = Committee.objects.exclude(chamber__in=chamber).filter(Government_obj__in=govs).order_by('Title')
    # elif chamber == 'Senate':
    #     committeeList = Committee.objects.exclude(Organization='House').filter(ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber).order_by('Title')
    # else:
    #     # print('else')
    #     committeeList = Committee.objects.filter(ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber).order_by('Title')
    if request.method == 'POST':
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        subtitle = date
        title = 'House Committees'
        view = None
        posts = Post.objects.filter(Meeting_obj__meeting_type='Commitee', Meeting_obj__date_time_start__gte=date, Meeting_obj__date_time_start__lt=date + datetime.timedelta(days=1)).exclude(Meeting_obj=None).order_by('-date_time')
    elif view == 'Upcoming':
        posts = Post.objects.filter(Meeting_obj__meeting_type='Commitee', Meeting_obj__date_time_start__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')).exclude(Meeting_obj=None).order_by('-date_time')
        if chamber.lower() == 'all':
            title = 'Upcoming Committee Events'
        else:
            title = f'Upcoming {chamber} Committee Events'

        # posts = Post.objects.filter(committeeMeeting__date_time_start__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')).exclude(committeeMeeting=None).exclude(committeeMeeting__Organization='Senate').order_by('-date_time')
        # if chamber == 'Senate':
        #     title = 'Upcoming Senate Committee Events' 
        #     # posts = Post.objects.filter(committeeMeeting__date_time_start__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')).exclude(committeeMeeting=None).exclude(committeeMeeting__Organization='House').order_by('date_time')
        # elif chamber == 'House':
        #     title = 'Upcoming House Committee Events' 
        #     posts = Post.objects.filter(committeeMeeting__date_time_start__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')).exclude(committeeMeeting=None).exclude(committeeMeeting__Organization='Senate').order_by('date_time')
        # else:
        #     title = 'Upcoming Committee Events' 
        #     posts = Post.objects.filter(committeeMeeting__date_time_start__gte=datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')).exclude(committeeMeeting=None).order_by('date_time')
    else:
        posts = Post.objects.filter(Meeting_obj__meeting_type='Commitee', Meeting_obj__chamber__in=chambers, Meeting_obj__date_time_start__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')).exclude(Meeting_obj=None).order_by('-date_time')
        if chamber.lower() == 'all':
            title = 'Latest Committee Events'
        else:
            title = f'Latest {chamber} Committee Events'

        # if chamber == 'Senate':
        #     title = 'Latest Senate Committee Events' 
        #     posts = Post.objects.filter(committeeMeeting__date_time_start__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')).exclude(committeeMeeting=None).exclude(committeeMeeting__Organization='House').order_by('-date_time')
        # elif chamber == 'House':
        #     title = 'Latest House Committee Events' 
        #     posts = Post.objects.filter(committeeMeeting__date_time_start__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')).exclude(committeeMeeting=None).exclude(committeeMeeting__Organization='Senate').order_by('-date_time')
        # else:
        #     title = 'Latest Committee Events' 
        #     posts = Post.objects.filter(committeeMeeting__date_time_start__lte=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')).exclude(committeeMeeting=None).order_by('-date_time')
    if not request.method == 'POST':
        setlist = paginate(posts, page, request)
    else:
        setlist = posts
    # interactions = get_interactions(user, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    context = {
        'isApp': isApp,
        'title': title,
        'subtitle': subtitle,
        'nav_bar': nav_options,
        'view': view,
        'dateForm': form,
        'cards': cards,
        'sort': sort,
        # 'country': Country.objects.all()[0],
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        'committeeList': committeeList,
    }
    return render_view(request, context, country=country)

def committee_view(request, organization, govNumber, session, iden):
    print('latest committee view')
    # organization = None
    user_data, user = get_user_data(request)
    country, provState, provState_name, municipality, municipality_name = get_regions(request, None, user)
    chamber, chambers, gov_levels = get_chambers(request, country, provState, municipality)
    govs = get_gov(country, gov_levels, govNumber, session)
    c = Meeting.objects.filter(id=iden, meeting_type='Committee', Government_obj__in=govs, chamber__in=chambers).select_related('Committee_obj', 'Committee_obj__Chair_obj')[0]
    if 'Subcommittee' in c.Committee_obj.Title:
        title = 'Senate Committee'
    else:
        title = f'{chamber} Committee'
    # if organization == 'senate':
    #     c = CommitteeMeeting.objects.exclude(committee__Organization='House').filter(ParliamentNumber=parliament, SessionNumber=session, id=iden).select_related('Committee_obj', 'Committee_obj__Chair_obj')[0]
        
    # else:
    #     c = CommitteeMeeting.objects.exclude(committee__Organization='Senate').filter(ParliamentNumber=parliament, SessionNumber=session, id=iden).select_related('committee', 'committee__chair__person')[0]
    #     title = 'House Committee'
    subtitle = str(get_ordinal(c.Government_obj__GovernmentNumber)) + ' Num. ' + str(get_ordinal(c.Government_obj__SessionNumber)) + ' Sess.'
    subtitle2 = datetime.datetime.strftime(c.date_time_start, '%B %-d, %Y')
    cards = 'committeeMeeting_view'
    style = request.GET.get('style', 'index')
    sort = request.GET.get('sort', 'time')
    view = request.GET.get('view', '')
    page = request.GET.get('page', 1)
    speaker_id = request.GET.get('speaker', '')
    topic = request.GET.get('topic', '')
    iden = request.GET.get('id', '')
    hasContext = True
    if topic:
        title = topic
        hasContext = False
    elif speaker_id:
        speaker = Person.objects.filter(id=speaker_id)[0]
        title = speaker.get_name()
        hasContext = False
    follow = request.GET.get('follow', '')
    if follow and topic:
        fList = user.get_follow_topics()
        if topic in fList:
            fList.remove(topic)
        elif topic not in fList:
            fList.append(topic)
        user.set_follow_topics(fList)
        user.save()
        # print(request.user.get_follow_topics())
        return render(request, "utils/dummy.html", {"result": 'Success'}, country=country)
    # print(request.user.get_follow_topics())
    if speaker_id:
        # print(speaker)
        # hansards = HansardItem.objects.filter(person=speaker, hansard=h).select_related('person')
        posts = Post.objects.filter(Statement_obj__Person_obj=speaker, Statement_obj__Meeting_obj=c).select_related('Statement_obj__Person_obj', 'Statement_obj').order_by('Statement_obj__DateTime', 'created')
    elif topic:
        # hansards = HansardItem.objects.filter(Terms__icontains=term, hansard=h).select_related('person')
        posts = Post.objects.filter(Statement_obj__Terms_array__icontains=topic, Statement_obj__Meeting_obj=c).select_related('Statement_obj__Person_obj', 'Statement_obj').order_by('Statement_obj__DateTime', 'created')
        # posts = Post.objects.filter(committeeItem__Terms__icontains=topic, committeeItem__committeeMeeting=c).select_related('committeeItem__person', 'committeeItem').order_by('committeeItem__Item_date_time', 'created')
    else:
        # hansards = HansardItem.objects.filter(hansard=h).select_related('person')
        posts = Post.objects.filter(Statement_obj__Meeting_obj=c).select_related('Statement_obj__Person_obj', 'Statement_obj').order_by('Statement_obj__DateTime', 'created')
        # posts = Post.objects.filter(committeeItem__committeeMeeting=c).select_related('committeeItem__person', 'committeeItem').order_by('committeeItem__Item_date_time', 'created')
        # print('found posts')
    # print(posts[0])
    if iden:
        # print('iden:',iden)
        setlist = paginate(posts, 'id=%s' %(iden), request)
        hasContext = setlist[0].Statement_obj.id
        iden = int(iden)
    else:
        setlist = paginate(posts, page, request)
        if page != 1:
            hasContext = setlist[0].Statement_obj.id
    # setlist = paginate(posts, page, request)
    # interactions = get_interactions(user, setlist)
    try:
        isApp = request.COOKIES['fcmDeviceId']
    except:
        isApp = None
    # options = {'Page: %s'%(page): page, 'Sort: %s'%(sort): sort}
    nav_options = [
            nav_item('button', 'Page: %s' %(page), 'subNavWidget("pageForm")'),
            nav_item('button', 'Sort: %s'%(sort), 'subNavWidget("sortForm")'), ]
    if topic:
        if user and topic in user.get_follow_topics():
            f = 'following'
        else:
            f = 'follow'
        follow_link = '%s?topic=%s&follow=%s' %(c.get_absolute_url(), topic, f)
        nav_options.append(nav_item('button', 'follow', f'react("follow2", "{follow_link}")'))
    # if request.user.is_god:
    #     options['reprocess'] = '/utils/reprocess%s' %(c.get_absolute_url())

 # options = {'Roles':'%s?view=Roles'%(person.get_absolute_url()), 'Vote History':'%s?view=Vote History'%(person.get_absolute_url())}
    context = {
        'isApp': isApp,
        'title': title,
        'title_link': c.get_absolute_url(),
        'subtitle': subtitle,
        'subtitle2': subtitle2,        
        'nav_bar': nav_options,
        'view': view,
        'cards': cards,
        'sort': sort,
        'topic': topic,
        'id': iden,
        'hasContext': hasContext,
        'feed_list':setlist,
        'interactions': get_interactions(user, setlist),
        # 'updates': get_updates(setlist),
        'committee': c,
        'topicList': [topic],
        # 'country': Country.objects.all()[0],
    }
    return render_view(request, context, country=country)

