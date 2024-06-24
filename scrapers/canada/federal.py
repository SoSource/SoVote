
# from unittest.result import failfast
from django.db import models
from django.db.models import Q, Avg

import django_rq
from rq import Queue
from worker import conn

from accounts.models import *
from posts.models import *
from posts.views import get_ordinal
from posts.utils import sprenderize


# from firebase_admin.messaging import Notification as fireNotification
# from firebase_admin.messaging import Message as fireMessage
# from fcm_django.models import FCMDevice
import sys
import gc
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import pytz
import time
import re
import random
import json
# from collections import OrderedDict
# from operator import itemgetter
import operator

from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys



runTimes = {'get_bills' : 1000, 'get_senate_bills' : 1000, 'get_house_bills' : 1000, 'get_all_bills' : 7200, 
            'get_house_agendas' : 200, 'get_house_debates' : 1000, 'get_senate_debates' : 200,
     'get_house_persons' : 2000, 'get_senate_persons' : 2000, 'get_senate_agendas' : 200,
     'get_house_motions' : 200, 'get_senate_motions' : 200, 'get_senate_committees' : 200, 'get_house_expenses' : 600,
     'get_todays_xml_agenda' : 1000, 'get_house_committees' : 1000, 'get_upcoming_senate_committees' : 200,
     }

typical = ['get_house_agendas', 'get_senate_agendas', 'get_todays_xml_agenda',
         'get_house_committees', 'get_senate_committees',
         ]

functions = [
     # first of the month
     {'date' : [1], 'dayOfWeek' : ['x'], 'hour' : [1], 'cmds' : ['get_house_expenses']},
     # saturday 1 am
     {'date' : ['x'], 'dayOfWeek' : [5], 'hour' : [1], 'cmds' : ['get_house_persons', 'get_senate_persons', 'get_all_bills']},
     # mon - sat
     {'date' : ['x'], 'dayOfWeek' : [1,2,3,4,5,6], 'hour' : [9, 12, 18, 23], 'cmds' : typical },
    # get_debates and get_motions run automatically after debate object created during get_agendas
     {'date' : ['x'], 'dayOfWeek' : ['x'], 'hour' : ['x'], 'cmds' : ['get_house_debates', 'get_house_motions', 'get_senate_debates', 'get_senate_motions']},
     ]

approved_models = {'get_house_agendas' : ['Government', 'Agenda', 'AgendaTime', 'AgendaItem'],
                   'get_house_persons' : ['Person', 'Role', 'Party', 'District', 'Region'],
                   'get_senate_persons' : ['Person', 'Role', 'Party', 'Region'],
                   'get_house_bills' : ['Bill', 'BillVersion', 'Role', 'Person'],
                   'get_senate_bills' : ['Bill', 'BillVersion', 'Role', 'Person'],
                   'get_house_debates' : ['Meeting', 'Statement', 'Agenda', 'Government', 'Person', 'Bill'],
                   'get_senate_debates' : ['Meeting', 'Statement', 'Bill'],
                   'get_house_motions' : ['Government', 'Motion', 'Vote', 'Interaction', 'Person'],
                   'get_senate_motions' : ['Government', 'Motion', 'Vote', 'Interaction'],
                   'get_user_region' : ['District', 'Region', 'Role', 'Party', 'Person'],
                   }


def get_house_agendas(url='https://www.ourcommons.ca/en/parliamentary-business/'):
    func = 'get_house_agendas'
    # try:
    # url = 'https://www.ourcommons.ca/en/parliamentary-business/2022-12-14'

    # print(soup)
    shareData = []
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    dt_now = now_utc()
    today = dt_now - datetime.timedelta(hours=dt_now.hour, minutes=dt_now.minute, seconds=dt_now.second, microseconds=dt_now.microsecond)
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    session = soup.find('span', {'class':'session-subtitle'})
    print(session)
    '(44th Parliament, 1st Session)'
    t = session.text.replace('(', '').replace(')','')
    a = t.find(' Parliament, ')
    b = t.find(' Session')
    p = t[:a].replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
    s = t[a+len(' Parliament, '):b].replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
    try:
        today = soup.find('span', {'class':'session-title'}).text
        # print(today)
        # 'Sunday, June 25, 2023'
        d = today.rfind(',')
        e = today[d-2:d]
        if e[0] == ' ':
            e = '0' + e[1]
            today = today[:d-1] + e + today[d:]
        dt = datetime.datetime.strptime(today, '%A, %B %d, %Y')
        print(dt)
    except Exception as e:
        print(str(e))
        dt = today
    gov, govU, govData, gov_is_new = get_model_and_update('Government', Country_obj=country, gov_level='Federal', GovernmentNumber=p, SessionNumber=s, Region_obj=country)
    if gov_is_new:
        shareData.append(gov.end_previous(func))
        gov, govU, govData, gov_is_new, shareData = save_and_return(gov, govU, govData, gov_is_new, shareData, func)

    # try:
    #     gov = Government.objects.filter(Country_obj=country, gov_level='Federal', GovernmentNumber=p, SessionNumber=s, Region_obj=country)[0]
    # except:
    #     gov = Government(Country_obj=country, gov_level='Federal', GovernmentNumber=p, SessionNumber=s, Region_obj=country)
    #     gov.save()
    #     oldGovU = gov.end_previous()

    section = soup.find('section', {'class':'block-in-the-chamber'})
    watch = section.find('div', {'class':'watch-previous'})
    watch_link = watch.find('a')['href']
    # print(watch_link)
    try:
        status = soup.find('p', {'class':'chamber-status'})
        print(status.text.replace('.','').replace('\r','').replace('\n','').strip())
        'The House is adjourned until Monday, December 5, 2022 at 11:00 a.m. (EST).'
        try:
            date_time = datetime.datetime.strptime(status.text.replace('.','').replace('\r','').replace('\n','').strip(), 'The House is adjourned until %A, %B %d, %Y at %H:%M %p (EST)')
        except:
            date_time = datetime.datetime.strptime(status.text.replace('.','').replace('\r','').replace('\n','').strip(), 'The House is adjourned until %A, %B %d, %Y at %H:%M %p (EDT)')
    except Exception as e:
        print(str(e))
        # date_time = datetime.datetime.strptime(url, 'https://www.ourcommons.ca/en/parliamentary-business/%Y-%m-%d')
    try:
        widget = section.find('div', {'class':'agenda-widget-content-wrapper'})
        date = widget.find('div').text.strip()
        print(date)
        'Agenda for Monday, November 28, 2022'
        date_time = datetime.datetime.strptime(date, 'Agenda for %A, %B %d, %Y')
    except Exception as e:
        print(str(e))
    def get_video_code():
        r = requests.get('http:' + watch_link, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        iden = str(soup).find('contentEntityId')+len('contentEntityId')
        # print(str(soup)[iden:iden+20])
        a = str(soup)[iden:].find(' = ')+len(' = ')
        b = str(soup)[iden+a:].find(';')
        special = str(soup)[iden+a:iden+a+b]
        # if isinstance(special, int):
        #     A.videoCode = special
        # try:
        #     A.VideoCode = int(special)
        # except Exception as e:
        #     print(str(e))
        return int(special)
    try:
        A = Agenda.objects.filter(DateTime__gte=date_time, DateTime__lt=date_time + datetime.timedelta(days=1), chamber='House', Government_obj=gov, Country_obj=country, Region_obj=country, func=func)[0]
        A, Au, AData, A_is_new = get_model_and_update('Agenda', obj=A)
        # print('agenda found')
        # if A.VideoURL != watch_link:
        #     A.VideoURL = watch_link
        #     try:
        #         a = Agenda.objects.filter(VideoURL=A.VideoURL).exclude(id=A.id)[0]
        #     except:
        #         A = get_video_code(A)
        #     A.save()
    except:
        # print('create agenda')
        # A = Agenda(DateTime=date_time, chamber='House', Government_obj=gov, Country_obj=country, VideoURL=watch_link, Region_obj=country)
        # A = get_video_code(A)
        # A.save()
        # A.create_post()
        
        A, Au, AData, A_is_new = get_model_and_update('Agenda', DateTime=date_time, chamber='House', Government_obj=gov, Country_obj=country, Region_obj=country)
    
    A, Au, AData, A_is_new, shareData = save_and_return(A, Au, AData, A_is_new, shareData, func)
    # if A_is_new:
    #     VideoURL = get_video_code(A)
    #     A.VideoURL = VideoURL
        # A.save()
        # A.create_post()
    if not 'VideoURL' in AData or Au['VideoURL'] != watch_link:
    # if watch_link not in AData:
        # A.VideoURL = watch_link
        # try:
        #     a = Agenda.objects.filter(VideoURL=A.VideoURL).exclude(id=A.id)[0]
        # except:
        # VideoURL = get_video_code()
        AData['VideoURL'] = get_video_code()
        # A.save()
    # H, Hu, HData, H_is_new = get_model_and_update('Meeting', meeting_type='Debate', Agenda_obj=A, Government_obj=gov, Country_obj=country, DateTime=date_time, chamber='House', Region_obj=country)
    
    # H, Hu, HData, H_is_new, shareData = save_and_return(H, Hu, HData, H_is_new, shareData)
    # # try:
    #     H = Meeting.objects.filter(meeting_type='Debate', Agenda_obj=A, Region_obj=country)[0]
    # except:
    #     H = Meeting(meeting_type='Debate', Agenda_obj=A, Government_obj=gov, Country_obj=country, PublicationDateTime=date_time, chamber='House', Region_obj=country)
    #     H.save()
    #     H.create_post() datetime.datetime.fromisoformat(i['created']):
    # x = datetime.datetime.isoformat
    try:
        if 'adjourned' in status.text:
            try:
                nextDt = datetime.datetime.strptime(status.text.strip().replace('.', ''), 'The House is adjourned until %A, %B %d, %Y at %I:%M %p (%Z)')
            except:
                nextDt = datetime.datetime.strptime(status.text.strip().replace('.', ''), 'The House is adjourned until %A, %B %d, %Y at %I:%M %p (%Z)')
            # print(A.NextDateTime)
            AData['NextDateTime'] = nextDt.isoformat()
        AData['current_status'] = status.text.strip()
        # print(A.current_status)
    except Exception as e:
        print(str(e))
        AData['current_status'] = 'Adjourned'
        print('adj')
    # A.save()
    if widget:
        agenda = widget.find('div', {'class':'agenda-items'})
        divs = agenda.find_all('div', {'class':'row'})
        position = 0
        start_time = None
        agendaTime = None
        for div in divs:
            position += 1
            try:
                hour = div.find('span', {'class':'the-time'}).text.strip()
                # print('\n', hour)
                item_time = datetime.datetime.strptime(date + ' / ' + hour.replace('.',''), 'Agenda for %A, %B %d, %Y / %I:%M %p')
                print(item_time)
                if not start_time:
                    start_time = item_time
                    # H.DateTime = item_time
                    # H.save()
                    A.DateTime = item_time
                    # A.save()
                agendaTime, agendaTimeU, agendaTimeData, agendaTime_is_new = get_model_and_update('AgendaTime', DateTime=item_time, Agenda_obj=A, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)
                agendaTime, agendaTimeU, agendaTimeData, agendaTime_is_new, shareData = save_and_return(agendaTime, agendaTimeU, agendaTimeData, agendaTime_is_new, shareData, func)

                # shareData.append([agendaTime, agendaTimeU, agendaTimeData, agendaTime_is_new])
                # try:
                #     agendaTime = AgendaTime.objects.filter(Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)[0]
                # except Exception as e:
                #     # print(str(e))
                #     agendaTime = AgendaTime(Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)
                #     agendaTime.save()
                    # agendaTime.create_post()
                agendaItem, agendaItemU, agendaItemData, agendaItem_is_new = get_model_and_update('AgendaItem', AgendaTime_obj=agendaTime, position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)
                # try:
                #     agendaItem = AgendaItem.objects.filter(agendaTime=agendaTime, position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)[0]
                # except Exception as e:
                #     # print(str(e))
                #     agendaItem = AgendaItem(agendaTime=agendaTime, position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)
                #     agendaItem.save()
                    # print('item created')
                    # agendaItem.check_for_post()
            except Exception as e:
                print('agendattime', str(e))
                if agendaTime:
                    agendaItem, agendaItemU, agendaItemData, agendaItem_is_new = get_model_and_update('AgendaItem', AgendaTime_obj=agendaTime, position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)
                    
                    # try:
                    #     agendaItem = AgendaItem.objects.filter(agendaTime=agendaTime, position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)[0]
                    # except:
                    #     agendaItem = AgendaItem(agendaTime=agendaTime, position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)
                    #     agendaItem.save()
                        # agendaItem.check_for_post()
                else:
                    agendaItem, agendaItemU, agendaItemData, agendaItem_is_new = get_model_and_update('AgendaItem', position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)

                    # try:
                    #     agendaItem = AgendaItem.objects.filter(position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)[0]
                    # except:
                    #     agendaItem = AgendaItem(position=position, Agenda_obj=A, DateTime=item_time, Country_obj=country, Government_obj=gov, chamber=A.chamber, Region_obj=country)
                    #     agendaItem.save()
            try:
                title = div.find('div', {'class':'agenda-item-title'}).text.strip()
                print(title)
                agendaItem.Text = title
                if ' ╼ ' in title:
                    a = title.find(' ╼ ')
                    try:
                        # sozed.alert('%s-STEP ONE' %(title[:a]), None)
                        # parl = Parliament.objects.first()
                        # bill, billU, billData, bill_is_new = get_model_and_update('Bill', NumberCode=title[:a], Government_obj=gov, Country_obj=country, Region_obj=country)

                        bill = Bill.objects.filter(NumberCode=title[:a], Government_obj=gov, Country_obj=country, Region_obj=country)[0]
                        agendaItem.Bill_obj = bill
                        # agendaItem.Agenda_obj.Bill_objs.add(bill)
                        # agendaItem.Agenda_obj.save()
                        # sozed.alert('%s-STEP TWO' %(bill.NumberCode), None)
                        # try:
                        #     billData['DateTime'] = start_time
                        #     # print(bill.LatestBillEventDateTime)
                        #     # bill.save()
                        #     bill, billU = save_obj_and_update(bill, billU, billData, bill_is_new)
                        #     # bill.update_post_time()
                        #     # sozed.alert('%s-||-%s-||-%s' %(bill.NumberCode, start_time, bill.LatestBillEventDateTime), None)
                        #     # print('done bill')
                        # except Exception as e:
                        #     print(str(e))
                            # sozed.alert('%s-%s' %(bill.NumberCode, str(e)), None, 'get_agenda')
                        print('BIll', bill)
                    except Exception as e:
                        print('111aa',str(e))
                        # sozed.alert('%s-FAIL TWO-%s' %(title[:a], str(e)), None, 'get_agenda')
                # agendaItem.save()
                # agendaItem.check_for_post()
            except:
                pass
            # shareData.append([agendaItem, agendaItemU, agendaItemData, agendaItem_is_new])
            # agendaItemU.data = json.dumps(agendaItemData)
            # A, AU = save_obj_and_update(A, Au, A_is_new)
            # H, HU = save_obj_and_update(H, Hu, H_is_new)
            if agendaTime:
                # shareData.append(save_obj_and_update(agendaTime, agendaTimeU, agendaTimeData, agendaTime_is_new))
                agendaTime, agendaTimeU, agendaTimeData, agendaTime_is_new, shareData = save_and_return(agendaTime, agendaTimeU, agendaTimeData, agendaTime_is_new, shareData, func)
            # shareData.append([agendaTime, agendaTimeU])
            # shareData.append(save_obj_and_update(agendaItem, agendaItemU, agendaItemData, agendaItem_is_new))
            agendaItem, agendaItemU, agendaItemData, agendaItem_is_new, shareData = save_and_return(agendaItem, agendaItemU, agendaItemData, agendaItem_is_new, shareData, func)
            # try:
            #     a = div.find('a')['href']
            #     print(a)
            # except:
            #     pass
    
    # shareData.append(save_obj_and_update(A, Au, AData, A_is_new))
    A, Au, AData, A_is_new, shareData = save_and_return(A, Au, AData, A_is_new, shareData, func)
    # shareData.append(save_obj_and_update(H, Hu, HData, H_is_new))
    send_for_validation(shareData, gov, func)
    # except Exception as e:
    #     print(str(e))

def get_house_bills():
    func = 'get_house_bills'
    shareData, gov = get_bills(func)
    # print('sharedata:', shareData)
    send_for_validation(shareData, gov, func)

def get_senate_bills():
    func = 'get_senate_bills'
    shareData, gov = get_bills()
    send_for_validation(shareData, gov, func)

def get_house_persons(value='current'):
    print('start gather mps')
    func = 'get_house_persons'
    shareData = []
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    gov = Government.objects.filter(Country_obj=country, gov_level='Federal', Region_obj=country)[0]
    def get_data(url, shareData):
        current_mps = []
        r = requests.get(url, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        m_list = []
        members = soup.find_all('div', {'class':'ce-mip-mp-tile-container'})
        for member in members:
            a = member.find('a',{'class':'ce-mip-mp-tile'})
            page = 'https://www.ourcommons.ca' + a['href']
            img = a.find(['img'])
            logo = 'https://www.ourcommons.ca' + img['src']
            name = a.find('div', {'class':'ce-mip-mp-name'}).text
            # print(name)
            party = a.find('div', {'class':'ce-mip-mp-party'}).text
            con = a.find('div', {'class':'ce-mip-mp-constituency'}).text
            prov = a.find('div', {'class':'ce-mip-mp-province'}).text
            a = page.find('(')+1
            b = page[a:].find(')')
            iden = page[a:a+b]
            # try:
            #     mp = Person.objects.get(gov_profile_page=page)
            #     # print(mp)
            #     # print('mp found')
            # except:
            #     mp = Person()
            #     # print('creating mp')
            # # mp.first_name = first
            # # mp.last_name = last
            # mp.gov_profile_page = page
            # mp.logo = logo
            # # mp.party = m['party']
            # # mp.constituency = m['con']
            # # mp.province = m['prov']
            # # mp.elected_date = elecdate
            # mp.gov_iden = iden
            # mp.save()
            # # print('saved')
            # get_MP(mp)
            m = {}
            m['name'] = name
            # m['party'] = party
            # m['con'] = con
            # m['prov'] = prov
            m['logo'] = logo
            m['link'] = page
            m['iden'] = iden
            m_list.append(m)
        
        url = 'https://www.ourcommons.ca/Members/en/search/XML'
        r = requests.get(url, verify=False)
        root = ET.fromstring(r.content)
        members = root.findall('MemberOfParliament')
        # q = len(m_list)
        # w = 1
        for member in members:
            first = member.find('PersonOfficialFirstName').text
            last = member.find('PersonOfficialLastName').text
            # print(first, last)
            elected = member.find('FromDateTime').text
            elecdate = datetime.datetime.strptime(elected, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.UTC)
            # print(elecdate)
            for m in m_list:
                if first in m['name'] and last in m['name']:
                    # print(m)
                    # print('%s/%s' %(w, q))
                    # w += 1
                    # try:
                    #     mp = Person.objects.filter(GovProfilePage=m['link'])[0]
                    #     print('%s/%s' %(w, q), 'mp found1', first, last)
                    # except:
                    #     try:
                    #         mp = Person.objects.filter(FirstName=first, LastName=last)[0]
                    #         # print(mp)
                    #         print('%s/%s' %(w, q), 'mp found2', first, last)

                    #     except:
                    #         mp = Person()
                    #         # p.Region_obj = 
                    #         print('%s/%s' %(w, q), 'creating mp', first, last)
                    person, personU, personData, person_is_new = get_model_and_update('Person', GovProfilePage=m['link'], Country_obj=country, Region_obj=country)
                    personData['GovProfilePage'] = m['link']
                    if person_is_new:
                        person.FirstName = first
                        person.LastName = last
                        # mp.gov_profile_page = m['link']
                        person.AvatarLink = m['logo']
                        # mp.party = m['party']
                        # mp.constituency = m['con']
                        # mp.province = m['prov']
                        # mp.elected_date = elecdate
                        person.GovIden = m['iden']
                        # must save person before profile info can be assigned
                        person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
                        # shareData.append(save_obj_and_update(person, personU, personData, person_is_new))
                        # person, personU, personData, person_is_new = get_model_and_update('Person', GovProfilePage=m['link'], Country_obj=country, Region_obj=country)
                    # print('personData', personData)
                    # print(personData['GovProfilePage'])
                    # mp.save()
                    # mp.create_post()
                    time.sleep(2)
                    # if 'http' not in personData['GovProfilePage']:
                    #     url = 'https:%s/roles' %(personData['GovProfilePage'])
                    # else:
                    #     url = '%s/roles' %(personData['GovProfilePage'])
                    # print(url)
                    mpData = get_MP(person, personU, personData, person_is_new, country, func)
                    for d in mpData:
                        shareData.append(d)
                    current_mps.append(person.id)
                    # print('saved')
                    # role = Role.objects.filter(position='Member of Parliament', person=mp).order_by('-start_date')
                    break
            # break
            # print('')
        return current_mps, shareData
    if value == 'alltime':
        parliaments = ['44', '43', '42', '41', '40', '39', '38', '37', '36']
        for p in parliaments:
            url = 'https://www.ourcommons.ca/Members/en/search/xml?parliament=%s&caucusId=all&province=all&gender=all' %(p)
            current_mps, shareData = get_data(url, shareData)
    elif value == 'current':
        url = 'https://www.ourcommons.ca/Members/en/search'
        current_mps, shareData = get_data(url, shareData)
        print('len:', len(current_mps))
        if len(current_mps) > 300:
            # print(current_mps)
            # print('updating current')
            # print()
            updates = Update.objects.filter(pointerType='Role', data__icontains='"Current": true', Role_obj__Position='Member of Parliament').exclude(Role_obj__Person_obj__id__in=current_mps).select_related('Role_obj', 'Role_obj__Person_obj')
            # roles = Role.objects.filter(Position='Member of Parliament', current=True).order_by('Person_obj__LastName', 'Person_obj__FirstName')
            for u in updates:
                print(u.Role_obj.Person_obj)
                if u.Role_obj.Person_obj.id not in current_mps:
                    # print('not listed')
                    # time.sleep(2)
                    # r.current = False
                    # r.save()
                    update = u.create_next_version(obj=u.Role_obj)
                    updateData = json.loads(update.data)
                    updateData['Current'] = False
                    update.data = json.dumps(updateData)
                    update, u_is_new = update.save_if_new(share=False)
                    if u_is_new:
                        shareData.append(update)
                # else:
                    # print('found')
    
    print('done gather mps')
    send_for_validation(shareData, gov, func)

def get_senate_persons():
    func = 'get_senate_persons'
    shareData = []
    
    print('bill saved')

    # if bill_is_new:
    #     bill, billU, billData, bill_is_new = get_model_and_update('Bill', Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin, GovIden=gov_iden, NumberCode=numCode)
    #     billV.Bill_obj = bill
    # print('save billv')
    # shareData.append(save_obj_and_update(billV, billVU, billVData, billV_is_new))

    # dt_now = now_utc()
    # today = dt_now - datetime.timedelta(hours=dt_now.hour, minutes=dt_now.minute, seconds=dt_now.second, microseconds=dt_now.microsecond)
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    # ParliamentNumber = b.find('ParliamentNumber').text
    # SessionNumber = b.find('SessionNumber').text
    # try:
    #     gov = Government.objects.filter(Country_obj=country, gov_level='Federal', GovernmentNumber=ParliamentNumber, SessionNumber=SessionNumber, Region_obj=country)[0]
    # except:
    #     gov = Government(Country_obj=country, gov_level='Federal', GovernmentNumber=ParliamentNumber, SessionNumber=SessionNumber, Region_obj=country)
    #     gov.save()
    #     gov.end_previous()
    gov = Government.objects.filter(Country_obj=country, gov_level='Federal', Region_obj=country)[0]
    
    # gov, govU, govData, gov_is_new = get_model_and_update('Government', Country_obj=country, gov_level='Federal', GovernmentNumber=ParliamentNumber, SessionNumber=SessionNumber, Region_obj=country)
    # if gov_is_new:
    #     shareData.append(gov.end_previous())
    #     shareData.append(save_obj_and_update(gov, govU, govData, gov_is_new))
    chamber = 'Senate'
    current_senators = Update.objects.filter(Role_obj__Position='Senator', data__icontains='"Current": true', Role_obj__gov_level='Federal', Country_obj=country)


    url = 'https://sencanada.ca/en/senators/'
    print("opening browser")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
    driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
    driver.get(url)
    # time.sleep(5)
    element_present = EC.presence_of_element_located((By.CLASS_NAME, 'sc-senators-political-card'))
    WebDriverWait(driver, 10).until(element_present)
    s_cards = driver.find_elements(By.CLASS_NAME, 'sc-senators-political-card')
    # senators = Role.objects.filter(position='Senator', current=True)
    # for s in senators:
    #     s.current = False
    #     s.save()
    updated_senators = []
    order_num = 0
    first_batch = []
    for c in s_cards:
        a = c.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
        src = c.find_element(By.CSS_SELECTOR, "img").get_attribute('src')
        try:
            title = c.find_element(By.CLASS_NAME, 'sc-senators-political-card-title').text
            # print(title)
        except Exception as e:
            print(str(e))
            title = None
        print(title)
        h = c.find_element(By.CSS_SELECTOR, 'h5').text
        h1 = h.find(', ')
        last_name = h[:h1]
        first_name = h[h1+2:]
        print(first_name)
        print(last_name)
        p = c.find_element(By.CSS_SELECTOR, "p").text
        p1 = p.find(' - ')
        p2 = p[p1+3:]
        # print(p2)
        try:
            p3 = p2.find(' (')
            provName = p2[:p3]
        except:
            provName = p2
        print('')
        person, personU, personData, person_is_new = get_model_and_update('Person', FirstName=first_name, LastName=last_name, Country_obj=country, Region_obj=country, chamber=chamber)
        person.AvatarLink = src
        person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
        # if person_is_new:
        #     shareData.append(save_obj_and_update(person, personU, personData, person_is_new))
        #     person, personU, personData, person_is_new = get_model_and_update('Person', FirstName=first_name, LastName=last_name, Country_obj=country, Region_obj=country, chamber=chamber)

        # try:
        #     person = Person.objects.filter(first_name=first_name, last_name=last_name)[0]
        # except:
        #     person = Person(first_name=first_name, last_name=last_name)
        #     # p.Region_obj = 
        #     person.save()
        #     person.create_post()
        order_num += 1
        first_batch.append(person)
        role, roleU, roleData, role_is_new = get_model_and_update('Role', Person_obj=person, Position='Senator', gov_level='Federal', Country_obj=country, Region_obj=country, chamber=chamber)
        # if role_is_new:
        prov, provU, provData, prov_is_new = get_model_and_update('Region', Name=provName, nameType='Province', modelType='provState', ParentRegion_obj=country)
        prov, provU, provData, prov_is_new, shareData = save_and_return(prov, provU, provData, prov_is_new, shareData, func)
        
        # if prov_is_new:
        #     shareData.append(save_obj_and_update(prov, provU, provData, prov_is_new))
        #     prov, provU, provData, prov_is_new = get_model_and_update('Region', Name=p2, nameType='Province', modelType='provState', ParentRegion_obj=country)
        personU.ProvState_obj = prov
        role.ProvState_obj = prov
        roleU.ProvState_obj = prov
        role.Title = title
        role.ordered = order_num
        role.LogoLink = src
        role.GovPage = a
        roleData['Current'] = True
        role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)
        
        # shareData.append(save_obj_and_update(role, roleU, roleData, role_is_new))
        updated_senators.append(role)
        # try:
        #     role = Role.objects.filter(person=person, position='Senator')[0]
        # except:
        #     role = Role(person=person, position='Senator')
            # r.Region_obj =
        # role.person_name = '%s %s' %(person.first_name, person.last_name)
        # role.province_name = p2
        # print('order:', role.ordered)
        # person.province_name = p2
        # person.save()
        # role.save()
        
    # title = None
    print('-------second list-------')
    s_cards = driver.find_elements(By.CLASS_NAME, 'sc-senators-senator-card')
    for c in s_cards:
        a = c.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
        src = c.find_element(By.CSS_SELECTOR, "img").get_attribute('src')
        h = c.find_element(By.CLASS_NAME, 'sc-senators-senator-card-text-name').text
        h1 = h.find(', ')
        last_name = h[:h1]
        first_name = h[h1+2:]
        print(first_name)
        print(last_name)
        p = c.find_element(By.CSS_SELECTOR, "p").text
        p1 = p.find(' - ')
        p2 = p[p1+3:]
        try:
            p3 = p2.find(' (')
            provName = p2[:p3]
        except:
            provName = p2
        print('')
        person, personU, personData, person_is_new = get_model_and_update('Person', FirstName=first_name, LastName=last_name, Country_obj=country, Region_obj=country, chamber=chamber)
        person.AvatarLink = src
        # if person_is_new:
        #     person.AvatarLink = src
        #     shareData.append(save_obj_and_update(person, personU, personData, person_is_new))
        #     person, personU, personData, person_is_new = get_model_and_update('Person', FirstName=first_name, LastName=last_name, Country_obj=country, Region_obj=country, chamber=chamber)
        person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)

        # try:
        # try:
        #     person = Person.objects.filter(first_name=first_name, last_name=last_name)[0]
        # except:
        #     person = Person(first_name=first_name, last_name=last_name)
        #     # p.Region_obj = 
        #     person.save()
        #     person.create_post()
        if person not in first_batch:
            order_num += 1
            role, roleU, roleData, role_is_new = get_model_and_update('Role', Person_obj=person, Position='Senator', gov_level='Federal', Country_obj=country, Region_obj=country, chamber=chamber)
            # if role_is_new:
            prov, provU, provData, prov_is_new = get_model_and_update('Region', Name=provName, nameType='Province', modelType='provState', ParentRegion_obj=country)
            prov, provU, provData, prov_is_new, shareData = save_and_return(prov, provU, provData, prov_is_new, shareData, func)
            
            # if prov_is_new:
            #     shareData.append(save_obj_and_update(prov, provU, provData, prov_is_new))
            #     prov, provU, provData, prov_is_new = get_model_and_update('Region', Name=p2, nameType='Province', modelType='provState', ParentRegion_obj=country)
            personU.ProvState_obj = prov
            role.ProvState_obj = prov
            roleU.ProvState_obj = prov
            role.Title = title
            role.ordered = order_num
            role.LogoLink = src
            role.GovPage = a
            roleData['Current'] = True
            # shareData.append(save_obj_and_update(person, personU, personData, person_is_new))
            role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)
            # shareData.append(save_obj_and_update(role, roleU, roleData, role_is_new))
            updated_senators.append(role)
            # try:
            #     role = Role.objects.filter(person=person, position='Senator')[0]
            # except:
            #     role = Role(person=person, position='Senator')
                # r.Region_obj =
            # role.person_name = '%s %s' %(person.first_name, person.last_name)
            # role.province_name = p2
            # role.ordered = order_num
            # print('order:', role.ordered)
            # person.logo = src
            # person.province_name = p2
            # person.save()
            # role.logo = src
            # role.gov_page = a
            # role.current = True
            # role.save()

    print('get details')
    # current_senators = Role.objects.filter(position='Senator', current=True).select_related('person')
    # updated_senators = Update.objects.filter(Role_obj__Position='Senator', data__icontains='"Current": true', Role_obj__gov_level='Federal', Country_obj=country)
    for u in current_senators:
        if u.Role_obj not in updated_senators:
            role, roleU, roleData, role_is_new = get_model_and_update('Role', obj=u.Role_obj)
            roleData['Current'] = False
            # shareData.append(save_obj_and_update(role, roleU, roleData, role_is_new))
            role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)

    for r in updated_senators:
        role, roleU, roleData, role_is_new = get_model_and_update('Role', obj=r)
        person, personU, personData, person_is_new = get_model_and_update('Person', obj=role.Person_obj)

        # r = u.Role_obj
        # uData = json.loads(u.data)
        print(role.GovPage)
        try:
            driver.get(role.GovPage)
            print('retreived')
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'senatorbiography'))
            WebDriverWait(driver, 20).until(element_present)
            items = driver.find_elements(By.CLASS_NAME, 'sc-senator-bio-senatorheader-content-card-list-item')
            for item in items:
                # print(item.text)
                if 'Affiliation' in item.text:
                    roleData['Affiliation'] = item.text.replace('Affiliation: ', '')
                    # r.person.party_name = r.affiliation
                    party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=roleData['Affiliation'], chamber=chamber, Country_obj=country, Region_obj=country, gov_level='Federal')
                    party, partyU, partyData, party_is_new, shareData = save_and_return(party, partyU, partyData, party_is_new, shareData, func)
                    
                    # if party_is_new:
                    #     shareData.append(save_obj_and_update(party, partyU, partyData, party_is_new))
                    #     party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=roleData['Affiliation'], chamber=chamber, Country_obj=country, Region_obj=country, gov_level='Federal')

                    personU.Party_obj = party
                    # roleU.Party_obj = party
                    # try:
                    #     party = Party.objects.filter(Name=uData['Affiliation'], gov_level='Federal', chamber=chamber)[0]
                    # except:
                    #     print('creating party')
                    #     print(r.affiliation)
                    #     party = Party(name=r.affiliation, level='Senate')
                    #     party.save()
                    #     party.create_post()
                    # r.party = party
                    # r.person.party = party
                elif 'Personal Website' in item.text:
                    # r.person.website = item.text.replace('Personal Website: ', '')
                    roleData['Website'] = item.text.replace('Personal Website: ', '')
                elif 'Email' in item.text:
                    # r.person.email = item.text.replace('Email: ', '').replace('Electronic card', '').replace('&nbsp;', '')
                    roleData['Email'] = item.text.replace('Email: ', '').replace('Electronic card', '').replace('&nbsp;', '')
                elif 'Telephone' in item.text:
                    # r.person.telephone = item.text.replace('Telephone: ', '')
                    roleData['Telephone'] = item.text.replace('Telephone: ', '')
                elif 'Follow' in item.text:
                    links = item.find_elements(By.CSS_SELECTOR, 'a')
                    for l in links:
                        if 'twitter' in l.get_attribute('href'):
                            # r.person.twitter = l.get_attribute('href')
                            roleData['XTwitter'] = l.get_attribute('href')

            print('')
            bio = driver.find_element(By.CLASS_NAME, 'senatorbiography').text
        except Exception as e:
            print(str(e))
            time.sleep(5)
        personData['Bio'] = bio
        # print('1111')
        try:
            print('retrieve2')
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="pills-votes-tab"]'))
            WebDriverWait(driver, 20).until(element_present)
            # time.sleep(2)
            votes_button = driver.find_element(By.XPATH, '//*[@id="pills-votes-tab"]')
            # print(votes_button.text)
            votes_button.click()
            time.sleep(1)
            votes_link = driver.find_element(By.XPATH, '//*[@id="pills-votes"]/div/div[2]/p/a').get_attribute('href')
            # print(votes_link)
            a = votes_link.find('/senator/')+len('/senator/')
            b = votes_link[a:].find('/')
            iden = votes_link[a:a+b]
            # print(iden)
            personData['GovIden'] = iden
        except Exception as e:
            print(str(e))
        print('roleData', roleData)
        # r.person.save()
        # r.save()
        # print('save obj and update')
        person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
        role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)

        # shareData.append(save_obj_and_update(person, personU, personData, person_is_new))
        # shareData.append(save_obj_and_update(role, roleU, roleData, role_is_new))

        print('saved')
        time.sleep(2)
    driver.quit()
    send_for_validation(shareData, gov, func)

    # sys.modules[__name__].__dict__.clear()
    # gc.collect()

def get_house_debates(object_type='hansard', value='latest'):
    func = 'get_house_debates'
    shareData, gov = get_house_hansard_or_committee(object_type, value, func)
    print('get house debates step 2')
    send_for_validation(shareData, gov, func)
    print('done done')

def get_senate_debates(time='latest'):
    # print('start senate hansards', time)
    func = 'get_senate_debates'
    shareData = []
    if time == 'latest':
        print('---------------------senate hansards')
        debate = 'https://sencanada.ca/en/in-the-chamber/debates/'
        r = requests.get(debate)
        soup = BeautifulSoup(r.content, 'html.parser')
        links = soup.find_all('a')
        for a in reversed(links[:5]):
            if '\content' in a['href'] and '\debates' in a['href']:
                link = 'https://sencanada.ca' + a['href'].replace('\\','/')
                data, gov = add_senate_hansard(link, False, func)
                for d in data:
                    shareData.append(d)
                break
    elif time == 'alltime':
        sessions = ['44-1', '43-2', '43-1', '42-1', '41-2', '41-1', '40-3', '40-2', '40-1', '39-2','39-1','38-1', '37-3','37-2','37-1','36-2','36-1','35-2']
        for s in sessions:
            debate = 'https://sencanada.ca/en/in-the-chamber/debates/%s' %(s)
            r = requests.get(debate)
            soup = BeautifulSoup(r.content, 'html.parser')
            links = soup.find_all('a')
            for a in reversed(links):
                if '\content' in a['href'] and '\debates' in a['href']:
                    link = 'https://sencanada.ca' + a['href'].replace('\\','/')
                    print('')
                    print(link)
                    data, gov = add_senate_hansard(link, False, func)
                    for d in data:
                        shareData.append(d)
                    time.sleep(2)
    send_for_validation(shareData, gov, func)

def get_todays_xml_agenda():
    print('---------------------xml agenda')
    func = 'get_todays_xml_agenda'
    shareData = []
    url = 'https://www.parl.ca/LegisInfo/en/overview/xml/onagenda'
    r = requests.get(url, verify=False)
    root = ET.fromstring(r.content)
    bills = root.findall('Bill')
    for b in bills:
        ShortTitle = b.find('ShortTitle').text
        print(ShortTitle)
        data, gov = get_bill(b, func)
        for d in data:
            shareData.append(d)
    send_for_validation(shareData, gov, func)
        # break

def get_house_motions():
    print('---------------------house motions')
    shareData = []
    func = 'get_house_motions'
    # print('-----get latest house motions')
    vote1 = 'https://www.ourcommons.ca/members/en/votes/xml'
    # print(vote1)
    r = requests.get(vote1, verify=False)
    root = ET.fromstring(r.content)
    motions = root.findall('Vote')
    # count = 0
    motion_list = []
    for motion in reversed(motions[:10]):
        m, gov, shareData = add_motion(motion, shareData, func)
        motion_list.append(m)
        print('-----------')
        # break
    
    # parl = Parliament.objects.filter(country='Canada', organization='Federal')[0]
    # total_motions = Motion.objects.filter(Q(OriginatingChamberName='House')|Q(OriginatingChamberName='House of Commons')).filter(ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber).count()
    # roles = Role.objects.filter(position='Member of Parliament', current=True).order_by('person')
    # mps = {}
    # for r in roles:
    #     # print(r.person)
    #     mps[r.person] = 0
    # for m in motion_list:
    #     # print(m)
    #     votes = Vote.objects.filter(motion=m)
    #     for v in votes:
    #         try:
    #             if v.person:
    #                 mps[v.person] += 1
    #         except Exception as e:
    #             # print(str(e))
    #             pass
    # for r in roles:
    #     # print(r.person)
    #     try:
    #         r.attendanceCount += mps[r.person]
    #         # print(r.attendanceCount, total, str((r.attendanceCount/total)*100))
    #         r.attendancePercent = int((r.attendanceCount/total_motions)*100)
    #         r.save()
    #         # print(r.attendancePercent)
    #     except Exception as e:
    #         print(str(e))
    send_for_validation(shareData, gov, func)
    
def get_senate_motions(time='latest'):    
    print('---------------------senate motions')
    func = 'get_senate_motions'
    shareData = []
    if time == 'latest':
        url = 'https://sencanada.ca/en/in-the-chamber/votes/'
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        section = soup.find('section', {'class':'votes-page'})
        tbody = section.find('tbody')
        trs = tbody.find_all('tr')
        m_num = 0
        for tr in reversed(trs):
            gov, shareData = add_senate_motion(tr, shareData, func)
            break
    elif time == 'alltime':
        sessions = ['43-2', '43-1', '42-1']
        for s in reversed(sessions):
            url = 'https://sencanada.ca/en/in-the-chamber/votes/%s' %(s)
            print(url)
            r = requests.get(url)
            soup = BeautifulSoup(r.content, 'html.parser')
            section = soup.find('section', {'class':'votes-page'})
            tbody = section.find('tbody')
            trs = tbody.find_all('tr')
            m_num = 0
            for tr in reversed(trs):
                gov, shareData = add_senate_motion(tr, shareData, func)

                # print('----')
        # m_num += 1
        # print('m_num:', m_num)
        # if m_num >= 6:
        #     break
    send_for_validation(shareData, gov, func)

def get_user_region(u, url):
    func = 'get_user_region'
    shareData = []

    # u = user
    # items = []
    result = {}
    result['greaterMunicipality_name'] = ''
    result['greaterMunicipality_id'] = ''
    result['greaterMunicipalityDistrict_name'] = ''
    result['greaterMunicipalityDistrict_id'] = ''

    country = Region.objects.filter(Name='Canada', modelType='country')[0]
    # u.Country_obj = country
    result['country_name'] = country.Name
    result['country_id'] = country.id
    # should not use verify=False but opennorth is giving ssl error
    r = requests.get(url, verify=False)
    data = json.loads(r.content)
    print(data)
    # responseData = {}
    try:
        prov = data['province']
        city = data['city']
        # u.city_name = city
        root = data['boundaries_centroid']
    except:
        root = data['objects']
    second_list = []
    try:
        for d in root:
            print('')
            # print(d)
            iden = d['external_id']
            name = d['name']
            type = d['boundary_set_name']
            print(type)
            if d['related']['boundary_set_url'] == '/boundary-sets/federal-electoral-districts/':
                print('riding,,,')
                try:
                    print('aa')
                    riding = District.objects.filter(Q(Name=name)&Q(Country_obj=country)&Q(modelType='riding'))[0]
                    # riding, ridingu, ridingData, riding_is_new = get_model_and_update('District', obj=riding)
                except Exception as e:
                    print(str(e))
                    riding = District(Name=name, Country_obj=country, Region_obj=country, AltName=name.replace('—', ''), gov_level='Federal', modelType='riding', nameType='Riding')
                    print('bb')
                    riding.save()
                    shareData.append(riding)
                    print('cc')
                
                    # riding, ridingu, ridingData, riding_is_new = get_model_and_update('District', Name=name, gov_level='Federal', AltName=name.replace('—', ''), modelType='riding', nameType='Riding', Country_obj=country, Region_obj=country)
    
                    # riding, ridingu, ridingData, riding_is_new, shareData = save_and_return(riding, ridingu, ridingData, riding_is_new, shareData, func)
                # if not riding.opennorthId:
                #     riding.opennorthId = iden
                #     riding.save()
                print(riding)
                # u.Federal_District_obj = riding
                # responseData['Federal_District_obj_id'] = riding.id
                print('done riding')
                result['federalDistrict_name'] = riding.Name
                result['federalDistrict_id'] = riding.id
                # u.riding_name = name
                # if not riding in items:
                #     items.append(riding)
            elif 'electoral district' in type and '2005' not in d['url'] and 'Federal' not in type:
                # print(type)
                provState_name = type.replace(' electoral district', '')
                print(provState_name)
                try:
                    provState = Region.objects.filter(Name=provState_name, ParentRegion_obj=country, nameType='Province', modelType='provState')[0]
                except:
                    provState = Region(Name=provState_name, ParentRegion_obj=country, nameType='Province', modelType='provState')
                    provState.save()
                    shareData.append(provState)

                # provState, provStateU, provStateData, provState_is_new = get_model_and_update('Region', Name=provState_name, ParentRegion_obj=country, nameType='Province', modelType='provState')

            
                # u.ProvState_obj = provState
                # responseData['ProvState_obj_id'] = provState.id
                # u.province_name = province_name
                result['provState_id'] = provState.id
                result['provState_name'] = provState.Name
                if not provState.AbbrName:
                    provState.AbbrName = prov
                    # provStateU['AbbrName'] = prov
                    provState.save()
                # provState, provStateU, provStateData, provState_is_new, shareData = save_and_return(provState, provStateU, provStateData, provState_is_new, shareData, func)
                
                try:
                    district = District.objects.filter(Name=name, Region_obj=provState, gov_level='Provincial', modelType='district', nameType='District')[0]
                except:
                    district = District(Name=name, Country_obj=country, Region_obj=provState, gov_level='Provincial', modelType='district', nameType='District')
                    district.save()
                    shareData.append(district)

                # district, districtU, districtData, district_is_new = get_model_and_update('District', Name=name, Country_obj=country, Region_obj=provState, gov_level='Provincial', modelType='district', nameType='District')

                # district, districtU, districtData, district_is_new, shareData = save_and_return(district, districtU, districtData, district_is_new, shareData, func)
            
                # if not district.opennorthId:
                #     district.province = province
                #     district.province_name = province_name
                #     district.opennorthId = iden
                #     district.save()
                # u.ProvState_District_obj = district
                # responseData['ProvState_District_obj_id'] = district.id
                # u.district_name = name
                result['provStateDistrict_name'] = district.Name
                result['provStateDistrict_id'] = district.id
                # if not district in items:
                #     items.append(district)
            elif 'ward' in type:
                second_list.append(d)
            elif 'School' in type:
                second_list.append(d)
        for m in second_list:
            iden = m['external_id']
            name = m['name']
            type = m['boundary_set_name']
            if 'ward' in type:
                # print('WARD')
                mun_name = type.replace(' ward', '')
                try:
                    municipality = Region.objects.filter(Name=mun_name, nameType='Municipality', modelType='municipality')[0]
                    # municipality, municipalityU, municipalityData, municipality_is_new = get_model_and_update('Region', obj=municipality)
                except:
                    municipality = Region(Name=mun_name, ParentRegion_obj=provState, nameType='Municipality', modelType='municipality')
                    municipality.save()
                    shareData.append(municipality)

                    # ParentRegion_obj may be changed below
                    # municipality, municipalityU, municipalityData, municipality_is_new = get_model_and_update('Region', Name=mun_name, ParentRegion_obj=provState, nameType='Municipality', modelType='municipality')

                # municipality, municipalityU, municipalityData, municipality_is_new, shareData = save_and_return(municipality, municipalityU, municipalityData, municipality_is_new, shareData, func)
            
                # if not district.o
                # try:
                #     municipality = District.objects.filter(Name=mun_name, Region=city, Type='Municipality')[0]
                # except:
                #     municipality = District(Name=mun_name, Region=city, Type='Municipality')
                #     municipality.save()
                # u.Municipality_obj = municipality
                # responseData['Municipality_obj_id'] = municipality.id
                # u.municipality_name = mun_name
                result['municipality_name'] = municipality.Name
                result['municipality_id'] = municipality.id
                # print(municipality)
                try:
                    ward = District.objects.filter(Name=name, Country_obj=country, Region_obj=municipality, gov_level='Municipal', modelType='ward', nameType='Ward')[0]
                except:
                    ward = District(Name=name, Country_obj=country, Region_obj=municipality, gov_level='Municipal', modelType='ward', nameType='Ward')
                    ward.save()
                    shareData.append(ward)

                # ward, wardU, wardData, ward_is_new = get_model_and_update('District', Name=name, Country_obj=country, Region_obj=municipality, gov_level='Municipal', modelType='ward', nameType='Ward')

                # ward, wardU, wardData, ward_is_new, shareData = save_and_return(ward, wardU, wardData, ward_is_new, shareData, func)
            
                # if not district.o
                # if not ward in items:
                #     items.append(ward)
                # u.Municipal_District_obj = ward
                # responseData['Municipal_District_obj_id'] = ward.id
                # u.ward_name = name
                result['ward_name'] = ward.Name
                result['ward_id'] = ward.id
            elif 'School' in type:
                # print('school')
                pass
    except Exception as e:
        print(str(e))
        pass
            # print('PASS')
            # print(type)
            # board_name = type.replace(' boundry', '')
            # print(board_name)
            # try:
            #     schoolBoard = SchoolBoard.objects.filter(name=board_name)[0]
            # except:
            #     schoolBoard = SchoolBoard(name=board_name, province=province, province_name=province_name)
            #     schoolBoard.save()
            # try:
            #     schoolRegion = SchoolBoardRegion.objects.filter(schoolBoard=schoolBoard, name=name)[0]
            # except:
            #     schoolRegion = SchoolBoardRegion(schoolBoard=schoolBoard, name=name, province=province, province_name=province_name)
            #     schoolRegion.save()
            # # if not schoolRegion in items:
            # #     items.append(schoolRegion)
            # # print(schoolRegion)
            # schoolRegion.schoolBoard_name = board_name
            # schoolRegion.save()
            # u.schoolBoardRegion = schoolRegion
            # u.schoolBoardRegion_name = name
    # u.save()
    try:
        print('-------------representatives')
        try:
            root = data['representatives_centroid']
        except:
            root = data['objects']
        region = None
        # if not province:
        #     province = u.ProvState
        for d in root:
            print('-----------')
            print('provstate',provState)
            url = d['url']
            last_name = d['last_name']
            first_name = d['first_name']
            name = d['name']
            # print(name)
            type = d['representative_set_name']
            personal_url = d['personal_url']
            elected_office = d['elected_office']
            gender = d['gender']
            district_name = d['district_name']
            email = ['email']
            for i in d['offices']:
                try:
                    postal = i['postal']
                except:
                    postal = None
                try:
                    fax = i['fax']
                except:
                    fax = None
                try:
                    tel = i['tel']
                except:
                    tel = None
            photo_url = d['photo_url']
            try:
                twitter = d['extra']['twitter']
            except:
                twitter = None
            party_name = d['party_name']
            if 'Assembly' in type:
                try:
                    role = Role.objects.filter(Position=elected_office, District_obj=district, Region_obj=provState, Person_obj__LastName__icontains=last_name, Person_obj__FirstName__icontains=first_name)[0]
                    role, roleU, roleData, role_is_new = get_model_and_update('Role', obj=role)
                except:
                    # try:
                    #     party = Party.objects.filter(Name=party_name, gov_level='Provincial', Region_obj=provState)[0]
                    # except:
                    #     print('create party')
                    #     party = Party(Name=party_name, gov_level='Provincial', Region_obj=provState)
                    #     party.save()
                    party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=party_name, gov_level='Provincial', Region_obj=provState)
                    party, partyU, partyData, party_is_new, shareData = save_and_return(party, partyU, partyData, party_is_new, shareData, func)
            
                    # try:
                    #     p = Person.objects.filter(Region_obj=provState, FirstName=first_name, LastName=last_name)[0]
                    # except:
                    #     print('create person')
                    #     p = Person(Region_obj=provState, FirstName=first_name, LastName=last_name, Gender=gender)
                    #     p.save()
                    person, personU, personData, person_is_new = get_model_and_update('Person', Region_obj=provState, FirstName=first_name, LastName=last_name)
                    if photo_url and not person.AvatarLink:
                        person.AvatarLink = photo_url
                        personData['AvatarLink'] = photo_url
                        # p.save()
                    person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
                    # r = Role(Position=elected_office, Person_obj=p, District_obj=district, Region_obj=provState, Party_obj=party, Current=True)
            
                    role, roleU, roleData, role_is_new = get_model_and_update('Role', Position=elected_office, Person_obj=p, District_obj=district, Region_obj=provState, Party_obj=party)
            
                roleData['Current'] = True
                role.Telephone = tel
                role.Fax = fax
                role.Address = postal
                role.Email = email
                role.LogoLink = photo_url
                role.Website = personal_url
                
                roleData['Telephone'] = tel
                roleData['Fax'] = fax
                roleData['Address'] = postal
                roleData['Email'] = email
                roleData['LogoLink'] = photo_url
                roleData['Website'] = personal_url
                if twitter:
                    role.XTwitter = twitter
                    roleData['XTwitter'] = twitter
                role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)
                
                # r.save()
                # u.follow_person.add(r.Person)
            elif 'Commons' in type:
            
                try:
                    role = Role.objects.filter(Position='Member of Parliament', District_obj=riding, Region_obj=country, Person_obj__LastName__icontains=last_name, Person_obj__FirstName__icontains=first_name)[0]
                    role, roleU, roleData, role_is_new = get_model_and_update('Role', obj=role)
                except:
                    party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=party_name, gov_level='Federal', Region_obj=country)
                    party, partyU, partyData, party_is_new, shareData = save_and_return(party, partyU, partyData, party_is_new, shareData, func)
                    person, personU, personData, person_is_new = get_model_and_update('Person', Region_obj=country, FirstName=first_name, LastName=last_name)
                    if photo_url and not person.AvatarLink:
                        person.AvatarLink = photo_url
                        personData['AvatarLink'] = photo_url
                    person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
                    role, roleU, roleData, role_is_new = get_model_and_update('Role', Position='Member of Parliament', Person_obj=person, District_obj=riding, Region_obj=country, Party_obj=party)
            
                roleData['Current'] = True
                role.Telephone = tel
                role.Fax = fax
                role.Address = postal
                role.Email = email
                role.LogoLink = photo_url
                role.Website = personal_url
                
                roleData['Telephone'] = tel
                roleData['Fax'] = fax
                roleData['Address'] = postal
                roleData['Email'] = email
                roleData['LogoLink'] = photo_url
                roleData['Website'] = personal_url
                if twitter:
                    role.XTwitter = twitter
                    roleData['XTwitter'] = twitter
                role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)
                


                # u.follow_person.add(r.Person)
            elif 'City Council' in type:
                if 'Ward' in district_name:
                    # print("WARD")
                    # try:
                    #     r = Role.objects.filter(Position=elected_office, District_obj=ward, Region_obj=municipality, Person_obj__LastName__icontains=last_name, Person_obj__FirstName__icontains=first_name, Current=True)[0]
                    #     # r.ward_name = ward.name
                    #     # r.save()
                    # except:
                    #     try:
                    #         p = Person.objects.filter(FirstName=first_name, LastName=last_name, Region_obj=municipality)[0]
                    #     except:
                    #         print('create person')
                    #         p = Person(FirstName=first_name, LastName=last_name, Gender=gender, Region_obj=municipality)
                    #         p.save()
                    #     if photo_url and not p.AvatarLink:
                    #         p.AvatarLink = photo_url
                    #         p.save()
                    #     r = Role(Position=elected_office, Person_obj=p, District_obj=ward, Region_obj=municipality, Current=True)        
                    # # u.follow_person.add(r.person)try:
                    try:
                        role = Role.objects.filter(Position=elected_office, District_obj=ward, Region_obj=municipality, Person_obj__LastName__icontains=last_name, Person_obj__FirstName__icontains=first_name)[0]
                        role, roleU, roleData, role_is_new = get_model_and_update('Role', obj=role)
                    except:
                        # party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=party_name, gov_level='Federal', Region_obj=country)
                        # party, partyU, partyData, party_is_new, shareData = save_and_return(party, partyU, partyData, party_is_new, shareData, func)
                        person, personU, personData, person_is_new = get_model_and_update('Person', Region_obj=municipality, FirstName=first_name, LastName=last_name)
                        if photo_url and not person.AvatarLink:
                            person.AvatarLink = photo_url
                            personData['AvatarLink'] = photo_url
                        person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
                        role, roleU, roleData, role_is_new = get_model_and_update('Role', Position=elected_office, Person_obj=person, District_obj=ward, Region_obj=municipality)
                
                else:
                    # print('NOT WARD')
                    # try:
                    #     r = Role.objects.filter(Position=elected_office, Region_obj=municipality, Person_obj__last_name__icontains=last_name, Person_obj__first_name__icontains=first_name, Current=True)[0]
                    #     # r.municipality_name = municipality.name
                    #     # r.save()
                    # except:
                        # try:
                        #     p = Person.objects.filter(FirstName=first_name, LastName=last_name, Region_obj=municipality)[0]
                        # except:
                        #     print('create person')
                        #     p = Person(FirstName=first_name, LastName=last_name, Gender=gender, Region_obj=municipality)
                        #     p.save()
                        # if photo_url and not p.AvatarLink:
                        #     p.AvatarLink = photo_url
                        #     p.save()
                        # r = Role(Position=elected_office, Person_obj=p, Region_obj=municipality, Current=True)
                    try:
                        role = Role.objects.filter(Position=elected_office, Region_obj=municipality, Person_obj__last_name__icontains=last_name, Person_obj__first_name__icontains=first_name)[0]
                        role, roleU, roleData, role_is_new = get_model_and_update('Role', obj=role)
                    except:
                        # party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=party_name, gov_level='Federal', Region_obj=country)
                        # party, partyU, partyData, party_is_new, shareData = save_and_return(party, partyU, partyData, party_is_new, shareData, func)
                        person, personU, personData, person_is_new = get_model_and_update('Person', Region_obj=municipality, FirstName=first_name, LastName=last_name)
                        if photo_url and not person.AvatarLink:
                            person.AvatarLink = photo_url
                            personData['AvatarLink'] = photo_url
                        person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
                        role, roleU, roleData, role_is_new = get_model_and_update('Role', Position=elected_office, Person_obj=person, Region_obj=municipality)
                
                # u.follow_person.add(r.person)
                roleData['Current'] = True
                role.Telephone = tel
                role.Fax = fax
                role.Address = postal
                role.Email = email
                role.LogoLink = photo_url
                role.Website = personal_url
                
                roleData['Telephone'] = tel
                roleData['Fax'] = fax
                roleData['Address'] = postal
                roleData['Email'] = email
                roleData['LogoLink'] = photo_url
                roleData['Website'] = personal_url
                if twitter:
                    role.XTwitter = twitter
                    roleData['XTwitter'] = twitter
                role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)
                
            elif 'School Board' in type:
                pass
                # print('PASS')
                # # if not region:
                # #     try:
                # #         region = Municipality.objects.filter(name=district_name, province=province)[0]
                # #     except:
                # #         region = Municipality(name=district_name, province=province)
                # #         region.save()
                # try:
                #     r = Role.objects.filter(position=elected_office, schoolBoardRegion=schoolRegion, person__last_name__icontains=last_name, person__first_name__icontains=first_name, current=True)[0]
                # except:
                #     try:
                #         p = Person.objects.filter(first_name=first_name, last_name=last_name)[0]
                #     except:
                #         print('create person')
                #         p = Person(first_name=first_name, last_name=last_name, gender=gender)
                #         p.save()
                #     if photo_url and not p.logo:
                #         p.logo = photo_url
                #         p.save()
                #     r = Role(position=elected_office, person=p, schoolBoardRegion=schoolRegion, current=True)
                # r.telephone = tel
                # r.fax = fax
                # r.address = postal
                # r.email = email
                # r.logo = photo_url
                # r.website = personal_url
                # if twitter:
                #     r.twitter = twitter
                # r.save()
            elif 'Regional Council' in type:
                # pass
                # print('Regiaonal')
                # print(name)
                # print(type)
                # print(district_name)
                region_name = type.replace(' Regional Council', '')
                try:
                    greater_municipality = Region.objects.filter(Name=region_name, ParentRegion_obj=provState, modelType='regionalMunicipality', nameType='Regional Municipality')[0]
                    # print('found')
                except:
                    greater_municipality = Region(Name=region_name, ParentRegion_obj=provState, modelType='regionalMunicipality', nameType='Regional Municipality')
                    greater_municipality.save()
                    shareData.append(greater_municipality)

                    municipality.ParentRegion_obj = greater_municipality
                    municipality.save()
                    shareData.append(municipality)


                # greater_municipality, greater_municipalityU, greater_municipalityData, greater_municipality_is_new = get_model_and_update('Region', Name=region_name, ParentRegion_obj=provState, modelType='regionalMunicipality', nameType='Regional Municipality')
                # greater_municipality, greater_municipalityU, greater_municipalityData, greater_municipality_is_new, shareData = save_and_return(greater_municipality, greater_municipalityU, greater_municipalityData, greater_municipality_is_new, shareData, func)
            
                # if greater_municipality_is_new:
                #     municipality
                #     municipalityU
                # municipality, municipalityU, municipalityData, municipality_is_new, shareData = save_and_return(municipality, municipalityU, municipalityData, municipality_is_new, shareData, func)
            

                result['greaterMunicipality_name'] = greater_municipality.Name
                result['greaterMunicipality_id'] = greater_municipality.id
                try:
                    greater_municipality_district = District.objects.filter(Name=district_name, Region_obj=upper_municipality, gov_level='regionalMunicipality', modelType='regionalDistrict', nameType='Regional District')[0]
                except:
                    greater_municipality_district = District(Name=district_name, Country_obj=country, Region_obj=upper_municipality, gov_level='regionalMunicipality', modelType='regionalDistrict', nameType='Regional District')
                    greater_municipality_district.save()
                    shareData.append(greater_municipality_district)

                # u.Greater_Municipality_obj = upper_municipality
                if municipality.Name.lower() == district_name.lower():
                    # u.Greater_Municipal_District_obj = upper_municipality_district
                    result['greaterMunicipalityDistrict_name'] = greater_municipality_district.Name
                    result['greaterMunicipalityDistrict_id'] = greater_municipality_district.id



                try:
                    role = Role.objects.filter(Position=elected_office, District_obj=upper_municipality_district, Region_obj=upper_municipality, Person_obj__LastName__icontains=last_name, Person_obj__FirstName__icontains=first_name)[0]
                    role, roleU, roleData, role_is_new = get_model_and_update('Role', obj=role)
                except:
                    # party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=party_name, gov_level='Federal', Region_obj=country)
                    # party, partyU, partyData, party_is_new, shareData = save_and_return(party, partyU, partyData, party_is_new, shareData, func)
                    
                    try:
                        person = Person.objects.filter(FirstName=first_name, LastName=last_name).filter(Q(Region_obj=upper_municipality)|Q(Region_obj=municipality))[0]
                        person, personU, personData, person_is_new = get_model_and_update('Person', obj=person)

                    except:
                        # print('create person')
                        # p = Person(FirstName=first_name, LastName=last_name, Gender=gender, Region_obj=upper_municipality)
                        # p.save()
                        person, personU, personData, person_is_new = get_model_and_update('Person', Region_obj=upper_municipality, FirstName=first_name, LastName=last_name)
                    if photo_url and not person.AvatarLink:
                        person.AvatarLink = photo_url
                        personData['AvatarLink'] = photo_url
                    person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
                    role, roleU, roleData, role_is_new = get_model_and_update('Role', Position=elected_office, Person_obj=person, Region_obj=municipality)
                
                # u.follow_person.add(r.person)
                roleData['Current'] = True
                role.Telephone = tel
                role.Fax = fax
                role.Address = postal
                role.Email = email
                role.LogoLink = photo_url
                role.Website = personal_url
                
                roleData['Telephone'] = tel
                roleData['Fax'] = fax
                roleData['Address'] = postal
                roleData['Email'] = email
                roleData['LogoLink'] = photo_url
                roleData['Website'] = personal_url
                if twitter:
                    role.XTwitter = twitter
                    roleData['XTwitter'] = twitter
                role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)
                

                # try:
                #     r = Role.objects.filter(Position=elected_office, District_obj=upper_municipality_district, Region_obj=upper_municipality, Person_obj__LastName__icontains=last_name, Person_obj__FirstName__icontains=first_name, Current=True)[0]
                # except:
                #     try:
                #         p = Person.objects.filter(FirstName=first_name, LastName=last_name).filter(Q(Region_obj=upper_municipality)|Q(Region_obj=municipality))[0]
                #     except:
                #         print('create person')
                #         p = Person(FirstName=first_name, LastName=last_name, Gender=gender, Region_obj=upper_municipality)
                #         p.save()
                #     if photo_url and not p.AvatarLink:
                #         p.AvatarLink = photo_url
                #         p.save()
                #     r = Role(Position=elected_office, Person_obj=p, District_obj=upper_municipality_district, Region_obj=upper_municipality, Current=True)
                # r.Telephone = tel
                # r.Fax = fax
                # r.Address = postal
                # r.Email = email
                # r.LogoLink = photo_url
                # r.Website = personal_url
                # if twitter:
                #     r.XTwitter = twitter
                # r.save()
                # print(upper_municipality)
            # else:
            #     print('ELSE')
    except Exception as e:
        print(str(e))
        pass
    # u.save()
    # print(result)
    
    send_for_validation(shareData, None, func)
    return result





def get_bill(b, func):
    print('----get bill')
    shareData = []
    dt_now = now_utc()
    today = dt_now - datetime.timedelta(hours=dt_now.hour, minutes=dt_now.minute, seconds=dt_now.second, microseconds=dt_now.microsecond)
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    ParliamentNumber = b.find('ParliamentNumber').text
    SessionNumber = b.find('SessionNumber').text
    # try:
    #     gov = Government.objects.filter(Country_obj=country, gov_level='Federal', GovernmentNumber=ParliamentNumber, SessionNumber=SessionNumber, Region_obj=country)[0]
    # except:
    #     gov = Government(Country_obj=country, gov_level='Federal', GovernmentNumber=ParliamentNumber, SessionNumber=SessionNumber, Region_obj=country)
    #     gov.save()
    #     gov.end_previous()
    
    gov, govU, govData, gov_is_new = get_model_and_update('Government', Country_obj=country, gov_level='Federal', GovernmentNumber=ParliamentNumber, SessionNumber=SessionNumber, Region_obj=country)
    if gov_is_new:
        shareData.append(gov.end_previous(func))
        gov, govU, govData, gov_is_new, shareData = save_and_return(gov, govU, govData, gov_is_new, shareData, func)
    print(gov)
    gov_iden = b.find('Id').text
    origin = b.find('OriginatingChamberName').text
    if origin == 'House of Commons':
        origin = 'House'
    numCode = b.find('NumberCode').text
    bill, billU, billData, bill_is_new = get_model_and_update('Bill', Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin, GovIden=gov_iden, NumberCode=numCode)
    print('got bill, bill_is_new:', bill_is_new)
    # time.sleep(10)
    # try:
    #     bill = Bill.objects.filter(Government_obj=gov, GovIden=gov_iden)[0]
    #     print('bill found')
    #     new_bill = False
    #     v = None
    # except:
    #     bill = Bill(Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin, GovIden=gov_iden)
    #     bill.LegisLink = 'http://www.parl.ca/LegisInfo/en/bill/%s-%s/%s' %(b.find('ParliamentNumber').text, b.find('SessionNumber').text, b.find('NumberCode').text)
    #     r = requests.get(bill.LegisLink, verify=False)
    #     soup = BeautifulSoup(r.content, 'html.parser')
    #     # span = soup.find('span', {'class':'session-date-range'}).text
    #     # print(span)
    #     # a = span.find(', to ')
    #     # d = span[:a]
    #     # # print(d)
    #     # dt = datetime.datetime.strptime(d, '%B %d, %Y')
    #     # print(dt)
    #     # bill.started = dt
    #     bill.NumberCode = b.find('NumberCode').text
    #     print(bill.NumberCode)
    #     bill.save()
    #     bill.create_post()
    if bill_is_new:
        bill.LegisLink = 'http://www.parl.ca/LegisInfo/en/bill/%s-%s/%s' %(b.find('ParliamentNumber').text, b.find('SessionNumber').text, b.find('NumberCode').text)
        new_bill = True
        # origin = b.find('OriginatingChamberName').text
        versions = ['House First Reading', 'House Second Reading','House Third Reading', 'Senate First Reading', 'Senate Second Reading', 'Senate Third Reading', 'Royal Assent']
        billData['billVersions'] = []
        for version in versions:
            billData['billVersions'].append({'version':version, 'current':False, 'started_dt':None, 'completed_dt':None})
            # try:
            #     v = BillVersion.objects.filter(Bill_obj=bill, version=version)[0]
            # except:
            #     v = BillVersion(Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin, Bill_obj=bill, version=version, NumberCode=bill.NumberCode)
            #     if origin == 'Senate':
            #         if version == 'Senate First Reading':
            #             v.empty = False
            #             v.Current = True
            #         else:
            #             v.empty = True
            #     else:
            #         if version == 'House First Reading':
            #             v.empty = False
            #             v.Current = True
            #         else:
            #             v.empty = True
            #     v.save()
            #     v.create_post()
        # if origin == 'Senate':
        #     try:
        #         v = BillVersion.objects.filter(bill=bill, version='Senate First Reading')[0]
        #     except:
        #         v = BillVersion(bill=bill, version='Senate First Reading', code=bill.NumberCode)
        #         v.save()
        #         v.create_post()
        # else:
        #     try:
        #         v = BillVersion.objects.filter(bill=bill, version='House First Reading')[0]
        #     except:
        #         v = BillVersion(bill=bill, version='House First Reading', code=bill.NumberCode)
        #         v.save()
        #         v.create_post()
        # v.current = True
        # v.empty = False
        # v.save()
        print('bill created')
        # bill.NumberPrefix = b.find('NumberPrefix').text
        bill.Number = b.find('Number').text
        bill.LongTitle = b.find('LongTitleEn').text
        print(bill.LongTitle)
        # bill.LongTitleFr = b.find('LongTitleFr').text
        if re.search('[a-zA-Z]', b.find('ShortTitle').text):
            bill.Title = b.find('ShortTitle').text
        else:
            bill.Title = bill.LongTitle
        # # bill.StatusId = b.find('StatusId').text
        # if billData['Status'] != b.find('StatusNameEn').text:
        #     updatedStatus = True
        # else:
        #     updatedStatus = False
        # billData['Status'] = b.find('StatusNameEn').text
        # # bill.StatusNameFr = b.find('StatusNameFr').text
        # # bill.LatestCompletedMajorStageId = b.find('LatestCompletedMajorStageId').text
        # # billData['LatestCompletedMajorStageName'] = b.find('LatestCompletedMajorStageName').text
        # billData['LatestCompletedBillStageNameWithChamberSuffix'] = b.find('LatestCompletedMajorStageNameWithChamberSuffix').text
        # # billData['LatestCompletedMajorStageChamberName'] = b.find('LatestCompletedMajorStageChamberName').text
        # # bill.OngoingStageId = b.find('OngoingStageId').text
        # billData['OngoingStageName'] = b.find('OngoingStageNameEn').text
        # # bill.LatestCompletedBillStageId = b.find('LatestCompletedBillStageId').text
        # billData['LatestCompletedBillStageName'] = b.find('LatestCompletedBillStageName').text
        # billData['LatestCompletedBillStageChamberName'] = b.find('LatestCompletedBillStageChamberName').text
        # billData['LatestCompletedBillStageDateTime'] = datetime.datetime.fromisoformat(b.find('LatestCompletedBillStageDateTime').text)
        # # try:
        #     date_time = datetime.datetime.strptime(b.find('LatestCompletedBillStageDateTime').text[:b.find('LatestCompletedBillStageDateTime').text.find('.')], '%Y-%m-%dT%H:%M:%S')
        #     if '-04:00' in b.find('LatestCompletedBillStageDateTime').text:
        #         date_time = date_time.replace(tzinfo=pytz.UTC)
        #     bill.LatestCompletedBillStageDateTime = date_time
        # except Exception as e:
        #     print(str(e))
        # try: 
        #     bill.parliament = Parliament.objects.filter(country='Canada', organization='Federal', ParliamentNumber= bill.ParliamentNumber, SessionNumber=bill.SessionNumber)[0]
        # except:
        #     parl = Parliament(country='Canada', organization='Federal', ParliamentNumber= bill.ParliamentNumber, SessionNumber=bill.SessionNumber, start_date=datetime.datetime.now())
        #     parl.save()
        #     parl.end_previous('Canada', 'Federal')
        #     bill.parliament = parl
        bill.BillDocumentTypeName = b.find('BillDocumentTypeName').text
        bill.IsGovernmentBill = b.find('IsGovernmentBill').text
        bill.chamber = b.find('OriginatingChamberName').text.replace(' of Commons', '')
        print(bill.chamber)
        bill.IsSenateBill = b.find('IsSenateBill').text
        bill.IsHouseBill = b.find('IsHouseBill').text
        # bill.SponsorSenateSystemAffiliationId = b.find('SponsorPersonId').text
        # bill.SponsorPersonId = b.find('SponsorPersonId').text
        # bill.SponsorPersonOfficialFirstName = b.find('SponsorPersonOfficialFirstName').text
        # bill.SponsorPersonOfficialLastName = b.find('SponsorPersonOfficialLastName').text
        # bill.SponsorPersonName = b.find('SponsorPersonName').text
        # bill.SponsorPersonShortHonorific = b.find('SponsorPersonShortHonorific').text
        # bill.SponsorAffiliationTitle = b.find('SponsorAffiliationTitle').text
        # bill.SponsorAffiliationRoleName = b.find('SponsorAffiliationRoleName').text
        # bill.SponsorConstituencyName = b.find('SponsorConstituencyName').text
        # print(bill.SponsorPersonId)
        # print(bill.SponsorSenateSystemAffiliationId)
        # print(bill.SponsorPersonOfficialFirstName)
        # print(bill.SponsorPersonOfficialLastName)
        # print(bill.SponsorAffiliationTitle)
        try:
            if b.find('OriginatingChamberOrganizationId').text == '2':  #senate
                print('senate')
                # bill, billU, billData, bill_is_new = get_model_and_update('Bill', Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin, GovIden=gov_iden, NumberCode=numCode)

                role = Role.objects.filter(Position=b.find('SponsorAffiliationTitle').text, Region_obj=country, Person_obj__FirstName__icontains=b.find('SponsorPersonOfficialFirstName').text, Person_obj__LastName=b.find('SponsorPersonOfficialLastName').text)[0]
                # print(r)
                bill.Person_obj = role.Person_obj
                # bill, billU, billData, bill_is_new = get_model_and_update('Bill', Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin, GovIden=gov_iden, NumberCode=numCode)

            else:
                print('house')
                person = Person.objects.filter(Region_obj=country, gov_iden=b.find('SponsorPersonId').text)[0]
                bill.Person_obj = person
        except:
            # try:
            #     p = Person.objects.filter(FirstName=b.find('SponsorPersonOfficialFirstName').text, LastName=b.find('SponsorPersonOfficialLastName').text)[0]
            # except:
            #     p = Person(FirstName=b.find('SponsorPersonOfficialFirstName').text, LastName=b.find('SponsorPersonOfficialLastName').text)
            #     # p.Region_obj = 
            #     p.save()
            #     # p.create_post()
            person, personU, personData, person_is_new = get_model_and_update('Person', Region_obj=country, Government_obj=gov, Country_obj=country, FirstName=b.find('SponsorPersonOfficialFirstName').text, LastName=b.find('SponsorPersonOfficialLastName').text)
            person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)
            # if person_is_new:
            #     shareData.append(save_obj_and_update(person, personU, personData, person_is_new))
            #     person, personU, personData, person_is_new = get_model_and_update('Person', Region_obj=country, Government_obj=gov, Country_obj=country, FirstName=b.find('SponsorPersonOfficialFirstName').text, LastName=b.find('SponsorPersonOfficialLastName').text)
            
            role, roleU, roleData, role_is_new = get_model_and_update('Role', Region_obj=country, Government_obj=gov, Country_obj=country, Position=b.find('SponsorAffiliationTitle').text, Person_obj=person)

            role, roleU, roleData, role_is_new, shareData = save_and_return(role, roleU, roleData, role_is_new, shareData, func)
            # shareData.append(save_obj_and_update(role, roleU, roleData, role_is_new))
            # try:
            #     r = Role.objects.filter(Position=b.find('SponsorAffiliationTitle').text, Person_obj=p)[0]
            # except:
            #     r = Role(Position=b.find('SponsorAffiliationTitle').text, Person_obj=p)
            #     # r.Region_obj =
            #     r.save()
            bill.Person_obj = person
        
        # if b.find('OriginatingChamberOrganizationId').text == '2':  #senate
        #     print('senate')
        #     person, personU, personData, person_is_new = get_model_and_update('Person', Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin, GovIden=gov_iden, NumberCode=numCode)
        
        # else:
        #     print('house')
    print('0000')
    if 'Status' not in billData or billData['Status'] != b.find('StatusNameEn').text:
        updatedStatus = True
    else:
        updatedStatus = False
    if b.find('LatestBillEventDateTime').text:
        print('002')
        # billData['LatestBillEventDateTime'] = b.find('LatestBillEventDateTime').text[:b.find('LatestBillEventDateTime').text.find('.')]
        # date_time = datetime.datetime.fromisoformat(billData['LatestBillEventDateTime'])
        # # bill.LatestBillEventTypeName = b.find('LatestBillEventTypeName').text
        

        date_time = datetime.datetime.strptime(b.find('LatestBillEventDateTime').text[:b.find('LatestBillEventDateTime').text.find('.')], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
        billData['LatestBillEventDateTime'] = date_time
        if bill_is_new:
            bill.DateTime = date_time
        # # print(date_time)
        # if '-04:00' in b.find('LatestBillEventDateTime').text:
        #     date_time = date_time.replace(tzinfo=pytz.UTC)
        #     if date_time > bill.LatestBillEventDateTime:
        #         bill.LatestBillEventDateTime = date_time
        # else:
        #     bill.LatestBillEventDateTime = date_time
        #         # bill.LatestBillEventDateTime = b.find('LatestBillEventDateTime').text
        print('Latest Time: %s' %(billData['LatestBillEventDateTime']))
    print('001')
    if updatedStatus:
        print('a')
        billData['Status'] = b.find('StatusNameEn').text
        print('b')
        # bill.StatusNameFr = b.find('StatusNameFr').text
        # bill.LatestCompletedMajorStageId = b.find('LatestCompletedMajorStageId').text
        # billData['LatestCompletedMajorStageName'] = b.find('LatestCompletedMajorStageName').text
        billData['LatestCompletedBillStageNameWithChamberSuffix'] = b.find('LatestCompletedMajorStageNameWithChamberSuffix').text
        # billData['LatestCompletedMajorStageChamberName'] = b.find('LatestCompletedMajorStageChamberName').text
        # bill.OngoingStageId = b.find('OngoingStageId').text
        billData['OngoingStageName'] = b.find('OngoingStageNameEn').text
        # bill.LatestCompletedBillStageId = b.find('LatestCompletedBillStageId').text
        billData['LatestCompletedBillStageName'] = b.find('LatestCompletedBillStageName').text
        billData['LatestCompletedBillStageChamberName'] = b.find('LatestCompletedBillStageChamberName').text
        billData['LatestCompletedBillStageDateTime'] = b.find('LatestCompletedBillStageDateTime').text

        billData['LatestBillEventChamberName'] = b.find('LatestBillEventChamberName').text
        billData['LatestBillEventNumberOfAmendments'] = b.find('LatestBillEventNumberOfAmendments').text
        # bill.LatestBillEventMeetingNumber = b.find('LatestBillEventMeetingNumber').text
        # bill.LatestBillEventAdditionalInformationEn = b.find('LatestBillEventAdditionalInformationEn').text
        # bill.LatestBillEventAdditionalInformationFr = b.find('LatestBillEventAdditionalInformationFr').text
    print('111')
    def convert_reading_time(item):
        print('convert')
        try:
            print(b.find(item).text)
            return datetime.datetime.fromisoformat(b.find(item).text).astimezone(pytz.utc) 
        except:
            return None
        # if '.' in b.find(item).text:
        #     date_time = datetime.datetime.strptime(b.find(item).text[:b.find(item).text.find('.')], '%Y-%m-%dT%H:%M:%S')
        #     if '-04:00' in b.find(item).text or '-05:00' in b.find(item).text:
        #         date_time = date_time.replace(tzinfo=pytz.UTC)
        # else:
        #     try:
        #         date_time = datetime.datetime.strptime(b.find(item).text, '%Y-%m-%dT%H:%M:%S%z')
        #     except:
        #         date_time = datetime.datetime.strptime(b.find(item).text, '%Y-%m-%dT%H:%M:%S')
        # return date_time
    # if not bill_is_new:
    # print('bill is new')
    print(b.find('PassedHouseFirstReadingDateTime').text)
    print(convert_reading_time('PassedHouseFirstReadingDateTime'))
    print('else11', date_time, today)
    if b.find('PassedHouseFirstReadingDateTime').text and convert_reading_time('PassedHouseFirstReadingDateTime') < today:
        print('if', convert_reading_time('PassedHouseFirstReadingDateTime'), date_time)
        if convert_reading_time('PassedHouseFirstReadingDateTime') < date_time:
            billData['LatestBillEventDateTime'] = b.find('PassedHouseFirstReadingDateTime').text
        else:
            billData['LatestBillEventDateTime'] = datetime.datetime.isoformat(date_time)
    else:
        # if date_time < today:
        billData['LatestBillEventDateTime'] = datetime.datetime.isoformat(date_time)
        # else:
        #     billData['LatestBillEventDateTime'] = datetime.datetime.isoformat(today)
        # v.save()
        # bill.PassedSenateFirstReadingDateTime = date_time
    
    print('------------SVE BILLL---------')
    bill, billU, billData, bill_is_new, shareData = save_and_return(bill, billU, billData, bill_is_new, shareData, func)
    # print(bill)
    print('done save bill')
    # print('112')
    def currentize_version(billData, version, dt, shareData):
        dt = datetime.datetime.fromisoformat(dt)
        print('currentize_version:', version)
        for v in billData['billVersions']:
            if v['version'] == version:
                v['status'] = 'Current'
                v['current'] = True
                v['started_dt'] = today.isoformat()
                billV, billVU, billVData, billV_is_new = get_model_and_update('BillVersion', Bill_obj=bill, Version=version, NumberCode=numCode, Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin)
                # print('bv1')
                # print('func', func)
                # print('shared', shareData)
                if not billV.DateTime:
                    billV.DateTime = dt
                billV, billVU, billVData, billV_is_new, shareData = save_and_return(billV, billVU, billVData, billV_is_new, shareData, func)
                # print('bv2')
            elif 'status' in v and v['status'] == 'current':
                v['status'] = 'Passed'
                v['current'] = False
                v['completed_dt'] = today.isoformat()
        return shareData
        
        # vs = BillVersion.objects.filter(bill=bill)
        # for v in vs:
        #     if v.version == version:
        #         # print(version)
        #         v.current = True
        #         v.empty = False
        #         v.dateTime = bill.LatestBillEventDateTime
        #     else:
        #         v.current = False
        #     v.save()
        # try:
        #     v = BillVersion.objects.filter(bill=bill, version=version)[0]  
        # except:
        #     v = BillVersion(bill=bill, version=version, code=bill.NumberCode)
        #     v.save()
        # v.create_post()
        # v.current = True
        # v.empty = False
        # billData['DateTime'] = bill.LatestBillEventDateTime
        # v.save()
    print('222')
    if b.find('PassedHouseFirstReadingDateTime').text and not 'PassedFirstChamberFirstReadingDateTime' in billData:
        # print('222a')
        billData['PassedFirstChamberFirstReadingDateTime'] = b.find('PassedHouseFirstReadingDateTime').text
        # print('222b')
        shareData = currentize_version(billData, 'House Second Reading', billData['PassedFirstChamberFirstReadingDateTime'], shareData)
    if b.find('PassedHouseSecondReadingDateTime').text and not 'PassedFirstChamberSecondReadingDateTime' in billData:
        billData['PassedFirstChamberSecondReadingDateTime'] = b.find('PassedHouseSecondReadingDateTime').text
        shareData = currentize_version(billData, 'House Third Reading', billData['PassedFirstChamberSecondReadingDateTime'], shareData)
    if b.find('PassedHouseThirdReadingDateTime').text and not 'PassedFirstChamberThirdReadingDateTime' in billData:
        billData['PassedFirstChamberThirdReadingDateTime'] = b.find('PassedHouseThirdReadingDateTime').text
        if not 'PassedSecondChamberFirstReadingDateTime' in billData:
            shareData = currentize_version(billData, 'Senate First Reading', billData['PassedFirstChamberThirdReadingDateTime'], shareData)
        else:
            for v in billData['billVersions']:
                if v['version'] == 'House Third Reading':
                    v['status'] = 'Passed'
                    v['completed_dt'] = today.isoformat()
                    break
            # try:
            #     v = BillVersion.objects.filter(bill=bill, version='House Third Reading')[0]
            # except:
            #     v = BillVersion(bill=bill, version='House Third Reading', code=bill.NumberCode)
            #     v.save()
            #     v.create_post()
            # v.dateTime = bill.LatestBillEventDateTime
            # v.current = False
            # v.save()
    if b.find('PassedSenateFirstReadingDateTime').text and not 'PassedSenateFirstReadingDateTime' in billData:
        billData['PassedSecondChamberFirstReadingDateTime'] = b.find('PassedSenateFirstReadingDateTime').text
        shareData = currentize_version(billData, 'Senate Second Reading', billData['PassedSecondChamberFirstReadingDateTime'], shareData)
    if b.find('PassedSenateSecondReadingDateTime').text and not 'PassedSenateSecondReadingDateTime' in billData:
        billData['PassedSecondChamberSecondReadingDateTime'] = b.find('PassedSenateSecondReadingDateTime').text
        shareData = currentize_version(billData, 'Senate Third Reading', billData['PassedSecondChamberSecondReadingDateTime'], shareData)
    if b.find('PassedSenateThirdReadingDateTime').text:
        print(b.find('PassedSenateThirdReadingDateTime').text)
        billData['PassedSecondChamberThirdReadingDateTime'] = b.find('PassedSenateThirdReadingDateTime').text
        if not 'PassedFirstChamberFirstReadingDateTime' in billData:
            shareData = currentize_version(billData, 'House First Reading', billData['PassedSecondChamberThirdReadingDateTime'], shareData)
        else:
            for v in billData['billVersions']:
                if v['version'] == 'Senate Third Reading':
                    v['status'] = 'Passed'
                    v['completed_dt'] = today.isoformat()
                    break
            # try:
            #     v = BillVersion.objects.filter(bill=bill, version='Senate Third Reading')[0]
            # except:
            #     v = BillVersion(bill=bill, version='Senate Third Reading', code=bill.NumberCode)
            #     v.save()
            #     v.create_post()
            # v.dateTime = bill.LatestBillEventDateTime
            # v.current = False
            # v.save()
    if b.find('ReceivedRoyalAssentDateTime').text:
        billData['ReceivedRoyalAssentDateTime'] = b.find('ReceivedRoyalAssentDateTime').text
        shareData = currentize_version(billData, 'Royal Assent', billData['ReceivedRoyalAssentDateTime'], shareData)
    print('3333')
    billData['PassedFirstChamberFirstReading'] = b.find('PassedFirstChamberFirstReading').text
    billData['PassedFirstChamberSecondReading'] = b.find('PassedFirstChamberSecondReading').text
    billData['PassedFirstChamberThirdReading'] = b.find('PassedFirstChamberThirdReading').text
    billData['PassedSecondChamberFirstReading'] = b.find('PassedSecondChamberFirstReading').text
    billData['PassedSecondChamberSecondReading'] = b.find('PassedSecondChamberSecondReading').text
    billData['PassedSecondChamberThirdReading'] = b.find('PassedSecondChamberThirdReading').text
    billData['ReceivedRoyalAssent'] = b.find('ReceivedRoyalAssent').text
    billData['BillFormName'] = b.find('BillFormName').text
    billData['Notes'] = b.find('Notes').text
    billData['IsSessionOngoing'] = b.find('IsSessionOngoing').text
    # bill.save()
    # get_text = False
    def get_text(billV, reading):
        print('getting text...', reading)
        # 'https://www.parl.ca/DocumentViewer/en/44-1/bill/C-294/first-reading'
        url = 'https://www.parl.ca/DocumentViewer/en/%s-%s/bill/%s/%s' %(gov.GovernmentNumber, gov.SessionNumber, bill.NumberCode, reading)
        print(url)
        r = requests.get(url, verify=False)
        print('link received')
        soup = BeautifulSoup(r.content, 'html.parser')
        print()
        # print(soup)
        # print()
        try:
            
            def case_insensitive_search(tag):
                # print('case_insensitive_search')
                # print(str(tag)[:500])
                # print()
                # if 'summary' in str(tag).lower():
                #     print('found')
                #     time.sleep(3)
                # else:
                #     print('not found')
                return tag.name == 'h2' and re.search('summary', tag.string, re.IGNORECASE)
            print('1')
            try:
                sum = soup.find(case_insensitive_search)
                print('2')
            except:
                sum = soup.find("h2", string="SUMMARY")
            print('2a')
            par = sum.parent
            text = str(par).replace(str(sum), '')
            print('3')
            def alter_rem(text, num, increase): #increase text size
                try:
                    match_list = []
                    for i in re.finditer('font-size:', str(text)):
                        match_list.insert(0,i)
                    for match in match_list:
                        q = str(text)[match.end():].find(';')
                        size = str(text)[match.end():match.end()+q]
                        if 'rem' in size:
                            x = size.replace('rem', '')
                            x = float(x)
                            if increase == 1:
                                newX = 1
                            else:
                                newX = x * increase
                            text = str(text)[:match.end()] + str(newX) + 'rem' + str(text)[match.end()+q:]
                        num += 1
                    return text
                except Exception as e:
                    # print(str(e))
                    return text
            text = alter_rem(text, 0, 1)
            text = text.replace('font-size:1rem;', '')
            text = text.replace('RECOMMENDATION', ' ')
            print('4')
            billV.Summary = text
            print('summ:', billV.Summary[:100])
            publication = soup.find('div', {'class':'publication-container-content'})
            sidebar = soup.find('div', {'class':'publication-container-explorer'})
            toc = soup.find('div', {'id':'TableofContent'})
            script = publication.find('script')
            final = str(publication).replace(str(sidebar), '').replace(str(toc), '').replace(str(script), '')
            # print('get text')
            # if bill.NumberCode != 'C-86' or bill.ParliamentNumber != '42' or bill.SessionNumber != '1':
            final = alter_rem(final, 0, 1.30)
            # else:
            #     print('skip processing')
            print('next')
            toc_d = {}
            for match in re.finditer('<h2', str(final)):
                q = str(final)[match.end():].find('>')
                # print(text[match.end():match.end()+q])
                w = str(final)[match.end():match.end()+q]
                e = str(final)[match.end()+q:].find('</h2>')
                r = str(final)[match.end()+q+1:match.end()+q+e]
                html = str(final)[match.start():match.end()+q]
                string =  re.sub('<[^<]+?>', '', r)
                toc_d[string] = html
            billV.TextHtml = str(final)
            print('str', str(final)[:100])
            billV.TextNav = json.dumps(dict(toc_d))
            print('done')
            time.sleep(5)
            return billV
        except Exception as e:
            print(str(e))
            time.sleep(10)
            print('old document type')
            a = soup.find("a", string="Complete Document")['href']
            section_list = []
            sections = soup.find_all('a', {'class':'DefaultTableOfContentsSectionLink'})
            sum_link = None
            for s in sections:
                if 'Summary' in s.text:
                    sum_link = s['href']
                section_list.append(s.text)
            sections = soup.find_all('a', {'class':'DefaultTableOfContentsFile Link'})
            for s in sections:
                section_list.append(s.text)
            print(section_list)
            # print('')
            def alter_pt(text, num):
                try:
                    match_list = []
                    for i in re.finditer('font-size:', str(text)):
                        match_list.insert(0,i)
                    for match in match_list:
                        # if n == num:
                        q = str(text)[match.end():].find(';')
                        size = str(text)[match.end():match.end()+q]
                        if 'pt' in size:
                            n = size.replace('pt', '')
                            n = float(n)
                            text = str(text)[:match.end()] + ';' + str(text)[match.end()+q:]
                        num += 1
                    return text
                except Exception as e:
                    # print(str(e))
                    return text
            def alter_line_height(text, num):
                try:
                    match_list = []
                    for i in re.finditer('font-size:', str(text)):
                        match_list.insert(0,i)
                    for match in match_list:
                        q = str(text)[match.end():].find(';')
                        size = str(text)[match.end():match.end()+q]
                        if 'pt' in size:
                            n = size.replace('pt', '')
                            n = float(n)
                            text = str(text)[:match.end()] + ';' + str(text)[match.end()+q:]
                        num += 1
                    return text
                except Exception as e:
                    # print(str(e))
                    return text
            if sum_link:
                try:
                    r = requests.get('https://www.parl.ca' + sum_link, verify=False)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    sum = soup.find("div", string="SUMMARY")
                    par = sum.parent
                    html = str(par).replace(str(sum), '')
                    html = alter_pt(html, 0)
                    html = alter_line_height(html, 0)
                    bill.summary = html
                except:
                    pass
            r = requests.get('https://www.parl.ca' + a, verify=False)
            print('link received')
            soup = BeautifulSoup(r.content, 'html.parser')
            final = soup.find('div', {'class':'publication-container-content'})
            # centers = soup.find_all('div', attrs={'text-align':'Center'})
            centers = soup.find_all('div',style=lambda value: value and 'text-align:Center' in value)
            # print(centers)
            toc_d = {}
            for c in centers:
                if c.text in section_list:
                    html = str(c).replace('\\"', "'")
                    # html = html.replace('="', "='").replace('">', "'>")
                    
                    toc_d[c.text] = str(c)
            time.sleep(5)
            return str(final), toc_d
    
    # try:
    #     billVersion = BillVersion.objects.filter(Bill_obj=bill, version=version)
    # except:
    #     pass
    if bill_is_new:
        pass

    print('get lastest version')
    for v in billData['billVersions']:
        print(v)
        if 'status' in v and v['status'] == 'Current':
            version = v['version']
            break
    # time.sleep(10)

    print('------------SVE BILLL---------')
    bill, billU, billData, bill_is_new, shareData = save_and_return(bill, billU, billData, bill_is_new, shareData, func)
    # print(bill)
    print('done save bill')
    print('get bill version', version)
    billV, billVU, billVData, billV_is_new = get_model_and_update('BillVersion', Bill_obj=bill, Version=version, NumberCode=numCode, Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin)

    # C-86 / 42-1 is a giant bill that crashes the system when processing
    # if bill.NumberCode != 'C-86' or bill.ParliamentNumber != '42' or bill.SessionNumber != '1':
        # if not bill.first_reading_html:
    
    if not billV.TextHtml:
        print('billv is new')
        billV.DateTime = date_time
        if 'LatestCompletedBillStageName' in billData and 'Second' in billData['LatestCompletedBillStageName']:
        # if bill.bill_text_version != 'Second':
            try:
                billV = get_text(billV, 'second-reading')
                # final, toc_d = get_text('second-reading')
                # bill.bill_text_html = str(final)
                # bill.bill_text_nav = json.dumps(dict(toc_d))
                # bill.bill_text_version = 'Second'
            except Exception as e:
                print(str(e))
    # if b.find('PassedFirstChamberThirdReading').text == 'true':
        elif 'LatestCompletedBillStageName' in billData and 'Third' in billData['LatestCompletedBillStageName']:
        # if bill.bill_text_version != 'Third':
            try:
                billV = get_text(billV, 'third-reading')
                # final, toc_d = get_text('third-reading')
                # bill.bill_text_html = str(final)
                # bill.bill_text_nav = json.dumps(dict(toc_d))
                # bill.bill_text_version = 'Third'
            except Exception as e:
                print(str(e))
        elif 'LatestCompletedBillStageName' in billData and 'Royal Assent' in billData['LatestCompletedBillStageName']:
        # if bill.bill_text_version != 'Royal':
            try:
                billV = get_text(billV, 'royal-assent')
                # final, toc_d = get_text('royal-assent')
                # bill.bill_text_html = str(final)
                # bill.bill_text_nav = json.dumps(dict(toc_d))
                # bill.bill_text_version = 'Royal'
            except Exception as e:
                print(str(e))
        else:
            try:
                billV = get_text(billV, 'first-reading')
                # billV.TextHtml = str(final)
                # billV.TextNav = json.dumps(dict(toc_d))
                # bill.bill_text_version = 'First'
            except Exception as e:
                print(str(e))
        billData['Summary'] = billV.Summary
    print('444')
    body = str(bill.Title)
    if bill_is_new and bill.Person_obj:
        # print('send alerts')
        n = Notification(title='%s has sponsored bill %s' %(bill.Person_obj.FullName, bill.NumberCode), link=str(bill.get_absolute_url()))
        n.save()
        for u in User.objects.filter(follow_Person_objs=bill.Person_obj):
            u.alert('%s has sponsored bill %s' %(bill.Person_obj.FullName, bill.NumberCode), str(bill.get_absolute_url()), body)
    # if new_bill:
    #     bill.getSpren(False)
    # if bill.ReceivedRoyalAssentDateTime:
    #     if not bill.royal_assent_html:
    #         try:
    #             final, toc_d = get_text('royal-assent')
    #             bill.royal_assent_html = str(final)
    #             bill.royal_assent_nav = json.dumps(dict(toc_d))
    #         except Exception as e:
    #             print(str(e))
    #             # u = User.objects.filter(username='Sozed')[0]
    #             # title = 'royal alert fail %s' %(bill.NumberCode)
    #             # u.alert(title, str(bill.get_absolute_url()), str(e))
        



    # print('saving bill')
    # shareData.append(save_obj_and_update(bill, billU, billData, bill_is_new))
    # print('bill saved')
    # if bill_is_new:
    #     bill, billU, billData, bill_is_new = get_model_and_update('Bill', Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin, GovIden=gov_iden, NumberCode=numCode)
    #     billV.Bill_obj = bill
    print('save billv')
    # shareData.append(save_obj_and_update(billV, billVU, billVData, billV_is_new))
    billV, billVU, billVData, billV_is_new, shareData = save_and_return(billV, billVU, billVData, billV_is_new, shareData, func)

    # print('version', version)
    billVersions = get_dynamic_model('BillVersion', list=True, Bill_obj=bill)
    for bV in billVersions:
        # print()
        # print(bV)
        billV, billVU, billVData, billV_is_new = get_model_and_update('BillVersion', obj=bV)
        # print(billVData)
        if version == billV.Version:
            billVData['status'] = 'Current'
        elif 'status' in billVData and billVData['status'] == 'Current':
            billVData['status'] = 'Passed'
        billV, billVU, billVData, billV_is_new, shareData = save_and_return(billV, billVU, billVData, billV_is_new, shareData, func)
    # print('done versions')
    # bill, billU, billData, bill_is_new, shareData = save_and_return(bill, billU, billData, bill_is_new, shareData, func)
    # # print(bill)
    # print('get bill version', version)
    # billV, billVU, billVData, billV_is_new = get_model_and_update('BillVersion', Bill_obj=bill, Version=version, NumberCode=numCode, Government_obj=gov, Country_obj=country, Region_obj=country, chamber=origin)

    
    if updatedStatus:
        if billData['Status'] != 'Royal assent received':
            for u in User.objects.filter(follow_Bill_objs=bill):
                title = 'Bill %s updated' %(bill.NumberCode)
                u.alert(title, str(bill.get_absolute_url()), body + '\n' + billData['Status'], obj=bill, share=False)
        elif 'Royal assent received' in billData['Status']:
            n = Notification(title='Bill %s has reached Royal Assent - %s' %(bill.NumberCode, body), link=str(bill.get_absolute_url()), pointerType=bill.object_type, pointerId=bill.id)
            n.save(share=False)
            for u in User.objects.all():
                title = 'Bill %s has reached Royal Assent' %(bill.NumberCode)
                u.alert(title, str(bill.get_absolute_url()), body, obj=bill, share=False)
    # share_all_with_network(shareData)
    # bill.save()
    # bill.update_post_time()
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()
    # print('bill saved')
    return shareData, gov
    
def get_house_votes(m):
    print('-----get house votes')
    url = 'https://www.ourcommons.ca/members/en/votes/%s/%s/%s' %(m.ParliamentNumber, m.SessionNumber, m.vote_number)
    m.gov_url = url
    print(url)
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    title = soup.find('div', {'class':'mip-vote-title-section'})
    # print(title)
    p = title.find('p')
    sita = p.text.find('No. ')+len('No. ')
    sitb = p.text[sita:].find(' - ')
    sitting = p.text[sita:sita+sitb]
    m.sitting = int(sitting)
    date = p.text[sita+sitb+len(' - '):]
    date_time = datetime.datetime.strptime(date, '%A, %B %d, %Y')
    m.date_time = date_time
    block = soup.find('div', {'class':'ce-mip-vote-block'})
    h = block.find('h2').text
    bill_code = h.replace('Bill ', '')
    try:
        bill = Bill.objects.get(ParliamentNumber=m.ParliamentNumber, SessionNumber=m.SessionNumber, NumberCode=bill_code)
    except:
        bill_url = 'https://www.parl.ca/LegisInfo/en/bill/%s-%s/%s/xml' %(m.ParliamentNumber, m.SessionNumber, bill_code)
        r = requests.get(bill_url, verify=False)
        root = ET.fromstring(r.content)
        bill_data = root.find('Bill')
        get_bill(bill_data)
        gov_iden = bill_data.find('Id').text
        bill = Bill.objects.get(gov_iden=gov_iden)
    m.bill_id = bill.id
    a = soup.find('a', {'class':'ce-mip-mp-tile'})
    b = a['href'].find('(')+1
    c = a['href'][b:].find(')')
    sponsor_link = a['href'][b:b+c]
    try:
        s = Person.objects.filter(gov_profile_page__icontains=sponsor_link)[0]
        m.sponsor = s
    except Exception as e:
        print(str(e))
    desc = soup.find('div', {'id':'mip-vote-desc'})
    m.subject = desc.text
    text = soup.find('div', {'id':'mip-vote-text-collapsible-text'})
    m.motion_text = text.text
    # m.save()
    sum = soup.find('div', {'class':'mip-vote-summary-section'})
    row = sum.find('div', {'class':'row'})
    divs = row.find_all('div')
    for d in divs:
        # print(d)
        if 'Results' in d.text:
            m.result = d.text.replace('Results: ', '')
        elif 'Yea:' in d.text:
            m.yeas = int(d.text.replace('Yea: ', ''))
        elif 'Nay:' in d.text:
            m.nays = int(d.text.replace('Nay: ', ''))
        elif 'Paired:' in d.text:
            m.pairs = int(d.text.replace('Paired: ', ''))
        elif 'Total:' in d.text:
            m.total_votes = int(d.text.replace('Total: ', ''))
    m.save()
    xml = url + '/xml'
    print(xml)
    tries = 0
    root = None
    while tries < 3 and root == None:
        try:
            tries += 1
            r = requests.get(xml, verify=False)
            root = ET.fromstring(r.content)
        except Exception as e:
            print(str(e))
            time.sleep(4)
    voters = root.findall('VoteParticipant')
    for v in voters:
        ParliamentNumber = v.find('ParliamentNumber').text
        SessionNumber = v.find('SessionNumber').text
        DecisionEventDateTime = v.find('DecisionEventDateTime').text
        '2022-10-26T17:50:00'
        date_time = datetime.datetime.strptime(DecisionEventDateTime, '%Y-%m-%dT%H:%M:%S')
        DecisionDivisionNumber = v.find('DecisionDivisionNumber').text
        PersonShortSalutation = v.find('PersonShortSalutation').text
        ConstituencyName = v.find('ConstituencyName').text
        VoteValueName = v.find('VoteValueName').text
        PersonOfficialFirstName = v.find('PersonOfficialFirstName').text
        PersonOfficialLastName = v.find('PersonOfficialLastName').text
        ConstituencyProvinceTerritoryName = v.find('ConstituencyProvinceTerritoryName').text
        CaucusShortName = v.find('CaucusShortName').text
        IsVoteYea = v.find('IsVoteYea').text
        IsVoteNay = v.find('IsVoteNay').text
        IsVotePaired = v.find('IsVotePaired').text
        DecisionResultName = v.find('DecisionResultName').text
        PersonId = v.find('PersonId').text
        print(PersonOfficialLastName, ',', PersonOfficialFirstName)
        try:
            v = Vote.objects.filter(ParliamentNumber=ParliamentNumber, SessionNumber=SessionNumber, motion_id=m.id, PersonId=PersonId)[0]
        except:
            v = Vote()
            v.ParliamentNumber = ParliamentNumber
            v.SessionNumber = SessionNumber
            v.motion_id = m.id
            v.bill_id = bill.id
            v.PersonId = PersonId
            try:
                p = Person.objects.filter(gov_iden=PersonId)[0]
                v.person_id = p.id
            except Exception as e:
                print(str(e))
        v.DecisionEventDateTime = date_time
        v.DecisionDivisionNumber = DecisionDivisionNumber
        v.PersonShortSalutation = PersonShortSalutation
        v.ConstituencyName = ConstituencyName
        v.VoteValueName = VoteValueName
        v.PersonOfficialFirstName = PersonOfficialFirstName
        v.PersonOfficialLastName = PersonOfficialLastName
        v.ConstituencyProvinceTerritoryName = ConstituencyProvinceTerritoryName
        v.CaucusShortName = CaucusShortName
        v.IsVoteYea = IsVoteYea
        v.IsVoteNay = IsVoteNay
        v.IsVotePaired = IsVotePaired
        v.DecisionResultName = DecisionResultName
        v.save()
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()

def get_live_house_votes(m):
    pass

def get_bills(func):
    print('---------------------bills')
    shareData = []
    url = 'https://www.parl.ca/LegisInfo/en/overview/xml/recentlyintroduced'
    r = requests.get(url, verify=False)
    root = ET.fromstring(r.content)
    bills = root.findall('Bill')
    for b in bills:
        ShortTitle = b.find('ShortTitle').text
        print(ShortTitle)
        try:
            data, gov = get_bill(b, func)
            for d in data:
                shareData.append(d)
            # break
        except Exception as e:
            print(str(e))
        # break
    # share_all_with_network(shareData)
    return shareData, gov
    
        # break
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()

#dont use
def get_house_votes():
    url = 'https://www.ourcommons.ca/members/en/votes'
    r = requests.get(url, verify=False)
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.find('table', {'id':'global-votes'})
    tbody = table.find('tbody')
    trs = tbody.find_all('tr')
    count = 0
    for tr in trs:
        count += 1
        a = tr.find('a')
        link = 'https://www.ourcommons.ca' + a['href']
        'https://www.ourcommons.ca/members/en/votes/44/1/2'
        b =  link.find('votes/')+len('votes/')
        c = link[b:].find('/')
        parliament = link[b:b+c]
        d = link[b+c+1:].find('/')
        session = link[b+c+1:b+c+1+d]
        vote_number = a.text.replace('No. ', '')
        try:
            m = Motion.objects.filter(gov_url=link, vote_number=vote_number)[0]
        except:
            m = Motion()
            m.gov_url = link
            m.ParliamentNumber = parliament
            m.SessionNumber = session
            m.vote_number = vote_number
            m.is_offical = True
            m.save()
            m.create_post()
            get_house_votes(m)
        if count > 3:
            break
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()


# dont use
def get_all_bills(period=None):
    print('get bills', period)
    func = 'get_all_bills'
    shareData = []
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    if period == 'alltime':
        url = 'https://www.parl.ca/LegisInfo/en/bills/xml?parlsession=all'
    else:
        print('get session bills')
        # this parliment or this session, not sure yet
        url = 'https://www.parl.ca/LegisInfo/en/bills/xml'
    r = requests.get(url, verify=False)
    root = ET.fromstring(r.content)
    bills = root.findall('Bill')
    for b in bills[:20]:
        # print(b.find('StatusNameEn').text)
        ShortTitle = b.find('LongTitleEn').text
        # print(ShortTitle)
        code = b.find('NumberCode').text
        parl = b.find('ParliamentNumber').text
        sess = b.find('SessionNumber').text
        
        gov, govU, govData, gov_is_new = get_model_and_update('Government', Country_obj=country, gov_level='Federal', GovernmentNumber=parl, SessionNumber=sess, Region_obj=country)
        if gov_is_new:
            shareData.append(gov.end_previous(func))
            gov, govU, govData, gov_is_new, shareData = save_and_return(gov, govU, govData, gov_is_new, shareData, func)
        print(gov)
        try:
            date_time = datetime.datetime.fromisoformat(b.find('LatestCompletedBillStageDateTime').text).replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
            # date_time = datetime.datetime.strptime(b.find('LatestCompletedBillStageDateTime').text[:b.find('LatestCompletedBillStageDateTime').text.find('.')], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
            # if '-04:00' in b.find('LatestCompletedBillStageDateTime').text:
            #     bill_date_time = date_time.replace(tzinfo=pytz.UTC)
            # bill.LatestCompletedBillStageDateTime = date_time
        except Exception as e:
            print(str(e))
            bill_date_time = None
        print(code, parl, sess)
        try:
            billU = Update.objects.filter(Bill_obj__NumberCode=code, Government_obj=gov, Country_obj=country, Region_obj=country)[0]
            billData = json.loads(billU.data)
        except:
            billU = None
            billData = None
        xml = 'https://www.parl.ca/LegisInfo/en/bill/%s-%s/%s/xml' %(parl, sess, code)
        print(xml)
        if billU == None or billData['Status'] != b.find('StatusNameEn').text or 'LatestBillEventDateTime' not in billData or billData['LatestBillEventDateTime'] == None:
        # if period == 'alltime' and bill == None or period != 'alltime':
            time.sleep(2)
            # print(xml)
            r2 = requests.get(xml, verify=False)
            root2 = ET.fromstring(r2.content)
            bills2 = root2.findall('Bill')
            for bill in bills2:
                try:
                    data, gov = get_bill(bill, func)
                    for d in data:
                        shareData.append(d)
                except Exception as e:
                    print(str(e))
    print('done')
    send_for_validation(shareData, gov, func)

def get_MP(mp, mpU, mpData, mp_is_new, country, func, chamber='House'):
    # print('start get_MP')
    # print(mp.FirstName, mp.FirstName)
    shareData = []
    if 'http' not in mpData['GovProfilePage']:
        url = 'https:%s/roles' %(mpData['GovProfilePage'])
    else:
        url = '%s/roles' %(mpData['GovProfilePage'])
    if not mp.GovIden:
        a = mpData['GovProfilePage'].find('members/')+len('members/')
        mp.GovIden = mpData['GovProfilePage'][a:]
        # mp.save()
    r = requests.get(url, verify=False)
    # print(r.content)
    soup = BeautifulSoup(r.content, 'html.parser')
    h1 = soup.find('h1', {'class':'mt-0'}).text

    if 'Hon' in h1:
        # print('is honourable')
        mpData['Honorific'] = 'Hon.'
        # mp.Honorific = 'Hon.'
        # mp.save()
    if not mp.AvatarLink:
        try:
            div = soup.find('div', {'class':'ce-mip-mp-picture-container'})
            img = div.find('img')['src']
            # 'https://www.ourcommons.ca/Content/Parliamentarians/Images/OfficialMPPhotos/38/Schmiw.JPG'
            mp.AvatarLink = 'https://www.ourcommons.ca' + img
            # mp.save()
        except:
            pass
    try:
        mpData['GovernmentPosition'] = 'Member of Parliament'
            #     if end_date == None:
            #         rolData['Current'] = True
            #         if mpData['GovernmentPosition'] == '':
            #             mpData['GovernmentPosition'] = rol.title
            #         else:
            #             mpData['GovernmentPosition'] = mpU['GovernmentPosition'] + '\n' + rol.Title
            #     else:
            #         rolData['Current'] = False
            #         rolData['EndDate'] = end_date.isoformat()
            #     shareData.append(save_obj_and_update(rol, rolU, rolData, rol_is_new))
            #     # rol.save()
            # except Exception as e:
            #     print(str(e))
        # print('mpData111111', mpData)
        party_name = soup.find('div', {'class':'ce-mip-mp-party'})
        party_name = party_name.text
        try:
            party = Party.objects.filter(Q(Name=party_name)|Q(AltName=party_name)).filter(Country_obj=country, Region_obj=country, gov_level='Federal')[0]
            party, partyU, partyData, party_is_new = get_model_and_update('Party', obj=party)
            partyU.Party_obj = party
        except:
            party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=party_name, AltName=party_name, Country_obj=country, Region_obj=country, gov_level='Federal')
            partyU.Party_obj = party
        # shareData.append(save_obj_and_update(party, partyU, partyData, party_is_new))
        party, partyU, partyData, party_is_new, shareData = save_and_return(party, partyU, partyData, party_is_new, shareData, func)
        mpU.Party_obj = party
        try:
            constituency_name = soup.find('div', {'class':'ce-mip-mp-constituency'}).text
            con = District.objects.filter(Q(Name=constituency_name)|Q(AltName=constituency_name.replace('—', ''))).filter(Country_obj=country, Region_obj=country, gov_level='Federal')[0] #that character being removed is important, it is not a regular dash
            # con, conU, conData, con_is_new = get_model_and_update('District', obj=con)
            # conU.District_obj = con
            # mpU.District_obj = con
        except:
            con = District.objects.filter(func=func, Name=constituency_name, AltName=constituency_name.replace('—', ''), Country_obj=country, Region_obj=country, gov_level='Federal', modelType='riding', nameType='Riding')
            con.save(share=False)
            shareData.append(con)
            # con, conU, conData, con_is_new = get_model_and_update('District', Name=constituency_name, AltName=constituency_name.replace('—', ''), Country_obj=country, Region_obj=country, gov_level='Federal', modelType='riding', nameType='Riding')
            # conU.District_obj = con
            mpU.District_obj = con
        # shareData.append(save_obj_and_update(con, conU, conData, con_is_new))
        # con, conU, conData, con_is_new, shareData = save_and_return(con, conU, conData, con_is_new, shareData, func)

        # try:
        #     constituency = soup.find('div', {'class':'ce-mip-mp-constituency'}).text
        #     mp.constituency_name = constituency
        #     try:
        #         # print(constituency.replace('—', ''))
        #         con = Riding.objects.filter(Q(name=constituency)|Q(alt_name=constituency.replace('—', '')))[0] #that character being removed is important, it is not a regular dash
        #         mp.riding = con
        #     except Exception as e:
        #         print(str(e))
        #     prov = soup.find('div', {'class':'cce-mip-mp-province'}).text
        #     mp.province_name = prov
        # except Exception as e:
        #     print(str(e))
        # mp.save()
    except Exception as e:
        print(str(e))


    ordered = 0
    try:
        # print('roles-mp')
        table = soup.find('table', {'id':'roles-mp'})
        tbody = table.find('tbody')
        roles = tbody.find_all('tr', {'role':'row'})
        ordered += 1
        for r in roles:
            try:
                td = r.find_all('td')
                constituency_name = td[0].text
                province_name = td[1].text
                start = td[2].text
                end = td[3].text
                start_date = datetime.datetime.strptime(start, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                if end:
                    end_date = datetime.datetime.strptime(end, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                else:
                    end_date = None
                # prov, provU, provData, prov_is_new = get_model_and_update('Region', Name=province_name, nameType='Province', modelType='provState', ParentRegion_obj=country)
                # # shareData.append(save_obj_and_update(prov, provU, provData, prov_is_new))
                # prov, provU, provData, prov_is_new, shareData = save_and_return(prov, provU, provData, prov_is_new, shareData, func)
                # mpU.ProvState_obj = prov
                try:
                    prov = Region.objects.filter(Name=province_name, nameType='Province', modelType='provState', ParentRegion_obj=country)[0] #that character being removed is important, it is not a regular dash
                except:
                    prov = Region.objects.filter(func=func, Name=province_name, nameType='Province', modelType='provState', ParentRegion_obj=country)
                    # con.ProvState_obj=prov
                    prov.save(share=False)
                    shareData.append(prov)
                    mpU.ProvState_obj = prov
                    # mpU.District_obj = con

                # try:
                #     # constituency_name = soup.find('div', {'class':'ce-mip-mp-constituency'}).text
                #     con = District.objects.filter(Q(Name=constituency_name)|Q(AltName=constituency_name.replace('—', ''))).filter(Country_obj=country, gov_level='Federal')[0] #that character being removed is important, it is not a regular dash
                #     con, conU, conData, con_is_new = get_model_and_update('District', obj=con)
                #     conU.District_obj = con
                #     con.ProvState_obj=prov
                #     mpU.District_obj = con
                # except:
                #     con, conU, conData, con_is_new = get_model_and_update('District', Name=constituency_name, AltName=constituency_name.replace('—', ''), Country_obj=country, Region_obj=country, ProvState_obj=prov, gov_level='Federal', modelType='riding', nameType='Riding')
                #     conU.District_obj = con
                #     mpU.District_obj = con
                # # shareData.append(save_obj_and_update(con, conU, conData, con_is_new))
                # con, conU, conData, con_is_new, shareData = save_and_return(con, conU, conData, con_is_new, shareData, func)
                
                try:
                    constituency_name = soup.find('div', {'class':'ce-mip-mp-constituency'}).text
                    con = District.objects.filter(Name=constituency_name, AltName=constituency_name.replace('—', ''), Country_obj=country, Region_obj=country, ProvState_obj=prov, gov_level='Federal', modelType='riding', nameType='Riding')[0]
                except:
                    con = District.objects.filter(func=func, Name=constituency_name, AltName=constituency_name.replace('—', ''), Country_obj=country, Region_obj=country, ProvState_obj=prov, gov_level='Federal', modelType='riding', nameType='Riding')
                    con.ProvState_obj=prov
                    con.save(share=False)
                    shareData.append(con)
                    mpU.District_obj = con

                # con.
                # try:
                #     # print(constituency.replace('—', ''))
                #     con = Riding.objects.filter(Q(name=constituency)|Q(alt_name=constituency.replace('—', '')))[0] #that character being removed is important, it is not a regular dash
                # except Exception as e:
                #     print(str(e))
                    # try:
                    #     prov = Province.objects.filter(name=province)[0]
                    # except:
                    #     prov = Province()
                    #     prov.name = province
                    #     prov.save()
                    # con = Riding()
                    # con.name = constituency
                    # # con.alt_name = constituency.replace('--', '-')
                    # con.province = prov
                    # con.province_name = prov.name
                    # con.save()
                    # con.create_post()
                    # con.fillout()
                # person, personU, personData, person_is_new = get_model_and_update('Role', person=mp, position='Member of Parliament', riding=con, start_date=start_date, Government_obj=gov, Country_obj=country, Region_obj=country)
                rol, rolU, rolData, rol_is_new = get_model_and_update('Role', ordered=ordered, gov_level='Federal', Person_obj=mp, Position='Member of Parliament', chamber=chamber, District_obj=con, Country_obj=country, Region_obj=country, ProvState_obj=prov, StartDate=start_date)
                
                # try:
                #     rol = Role.objects.filter(Person_obj=mp, Position='Member of Parliament', District_obj=con, StartDate=start_date)[0]
                #     # print('found parliament role')
                # except:
                #     rol = Role()
                #     # r.Region_obj =
                #     rol.person = mp
                #     rol.person_name = '%s %s' %(mp.first_name, mp.last_name)
                # if rol_is_new:
                #     rol.ordered = ordered
                #     rol.StartDate = start_date
                    # rol.Position = 'Member of Parliament'
                    # rol.constituency_name = constituency
                    # rol.riding = con
                    # rol.province_name = province
                    # rol.party = caucus
                if end_date == None:
                    rolData['Current'] = True
                else:
                    rolData['Current'] = False
                    rolData['EndDate'] = end_date.isoformat()
                # rol.save()
                if end_date == None:
                    mpU.District_obj = con
                    # mp.province_name = province
                    # mp.constituency_name = constituency
                    # mp.save()
                # shareData.append(save_obj_and_update(rol, rolU, rolData, rol_is_new))
                rol, rolU, rolData, rol_is_new, shareData = save_and_return(rol, rolU, rolData, rol_is_new, shareData, func)

            except Exception as e:
                print(str(e))
    except Exception as e:
        print('mp')
        print(str(e))
    try: 
        # print('roles-affiliation')
        table = soup.find('table', {'id':'roles-affiliation'})
        tbody = table.find('tbody')
        roles = tbody.find_all('tr', {'role':'row'})
        ordered += 1
        for r in roles:
            try:
                td = r.find_all('td')
                one = td[0].text
                party_name = td[1].text
                start = td[2].text
                end = td[3].text
                start_date = datetime.datetime.strptime(start, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                if end:
                    end_date = datetime.datetime.strptime(end, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                else:
                    end_date = None


                # prov, provU, provData, prov_is_new = get_model_and_update('Region', Name=province_name, nameType='Province', modelType='provState', ParentRegion_obj=country)
                try:
                    party = Party.objects.filter(Q(Name=party_name)|Q(AltName=party_name)).filter(Country_obj=country, gov_level='Federal')[0]
                    party, partyU, partyData, party_is_new = get_model_and_update('Party', obj=party)
                except:
                    party, partyU, partyData, party_is_new = get_model_and_update('Party', Name=party_name, AltName=party_name, Country_obj=country, Region_obj=country, gov_level='Federal')

                # shareData.append(save_obj_and_update(party, partyU, partyData, party_is_new))
                party, partyU, partyData, party_is_new, shareData = save_and_return(party, partyU, partyData, party_is_new, shareData, func)

                # try:
                #     party = Party.objects.filter(Q(name=party_name)|Q(alt_name=party_name)).filter(level='Federal')[0]
                # except:
                #     party = Party()
                #     party.name = party_name
                #     party.level = 'Federal'
                #     # party.parlinfo_link = party_link
                #     party.save()
                #     party.create_post()
                #     # party.fillout()
                # try:
                #     party = Party.objects.filter(Q(Name=party_name)|Q(AltName=party_name)).filter(Country_obj=country, gov_level='Federal')[0]
                #     party, partyU, partyData, party_is_new = get_model_and_update('Party', obj=party)
                # except:
                
                rol, rolU, rolData, rol_is_new = get_model_and_update('Role', ordered=ordered, Person_obj=mp, Position='Caucus Member', Party_obj=party, StartDate=start_date, Country_obj=country, Region_obj=country, gov_level='Federal')

                # try:
                #     rol = Role.objects.filter(Person_obj=mp, Position='Caucus Member', Party_obj=two, StartDate=start_date)[0]
                # except:
                #     rol = Role()
                #     # r.Region_obj =
                #     rol.person = mp
                #     rol.person_name = '%s %s' %(mp.first_name, mp.last_name)
                # if rol_is_new:
                    # rol.StartDate = start_date
                # rolData['EndDate'] = end_date.isoformat()
                    # rol.position = 'Caucus Member'
                if end_date == None:
                    rolData['Current'] = True
                else:
                    rolData['Current'] = False
                    rolData['EndDate'] = end_date.isoformat()
                if end_date == None:
                    mpU.District_obj = con
                # shareData.append(save_obj_and_update(rol, rolU, rolData, rol_is_new))
                rol, rolU, rolData, rol_is_new, shareData = save_and_return(rol, rolU, rolData, rol_is_new, shareData, func)
            except Exception as e:
                print(str(e))
    except Exception as e:
        print('roles-affiliation')
        print(str(e))
    try:
        print('roles-offices')
        
        table = soup.find('table', {'id':'roles-offices'})
        tbody = table.find('tbody')
        roles = tbody.find_all('tr', {'role':'row'})
        ordered += 1
        mpU['GovernmentPosition'] = ''
        for r in roles:
            print(r)
            try:
                td = r.find_all('td')
                one = td[0].text
                two = td[1].text
                start = td[2].text
                end = td[3].text
                start_date = datetime.datetime.strptime(start, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                if end:
                    end_date = datetime.datetime.strptime(end, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                else:
                    end_date = None
                rol, rolU, rolData, rol_is_new = get_model_and_update('Role', ordered=ordered, Person_obj=mp, Position='Parliamentary Position', Title=two, StartDate=start_date, Country_obj=country, Region_obj=country, gov_level='Federal')
                
                # try:
                #     rol = Role.objects.filter(person=mp, position='Parliamentary Position', Title=two, StartDate=start_date)[0]
                # except:
                #     rol = Role()
                #     # r.Region_obj =
                #     rol.person = mp
                #     rol.person_name = '%s %s' %(mp.first_name, mp.last_name)
                # if rol_is_new:
                #     rol.StartDate = start_date
                # rolData['EndDate'] = end_date.isoformat()
                    # rol.position = 'Parliamentary Position'
                # if end_date == None:
                #     rolData['Current'] = True
                # else:
                #     rolData['Current'] = False
                # if end_date == None:
                #     mpU.District_obj = con

                # rol.ordered = ordered
                # rol.start_date = start_date
                # rol.end_date = end_date
                # rol.position = 'Parliamentary Position'
                # rol.title = two
                # rol.parliamentNumber = one
                if end_date == None:
                    rolData['Current'] = True
                    # if mpData['GovernmentPosition'] == '':
                    #     mpData['GovernmentPosition'] = rol.title
                    # else:
                    #     mpData['GovernmentPosition'] = mpU['GovernmentPosition'] + '\n' + rol.Title
                else:
                    rolData['Current'] = False
                    rolData['EndDate'] = end_date.isoformat()
                # shareData.append(save_obj_and_update(rol, rolU, rolData, rol_is_new))
                rol, rolU, rolData, rol_is_new, shareData = save_and_return(rol, rolU, rolData, rol_is_new, shareData, func)
                # rol.save()
            except Exception as e:
                print(str(e))
            # print('mpData111111', mpData)
            
    except Exception as e:
        print('roles-offices')
        print(str(e))
    try:
        # print('roles-committees')
        table = soup.find('table', {'id':'roles-committees'})
        tbody = table.find('tbody')
        roles = tbody.find_all('tr', {'role':'row'})
        ordered += 1
        for r in roles:
            try:
                td = r.find_all('td')
                one = td[0].text
                two = td[1].text
                three = td[2].text
                start = td[3].text
                end = td[4].text
                start_date = datetime.datetime.strptime(start, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                if end:
                    end_date = datetime.datetime.strptime(end, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                else:
                    end_date = None
                rol, rolU, rolData, rol_is_new = get_model_and_update('Role', ordered=ordered, Person_obj=mp, Position='Committee Member', Group=three, StartDate=start_date, Country_obj=country, Region_obj=country, gov_level='Federal')
                # try:
                #     rol = Role.objects.filter(person=mp, position='Committee Member', Group=three, start_date=start_date)[0]
                # except:
                #     rol = Role()
                #     # r.Region_obj =
                #     rol.person = mp
                #     rol.person_name = '%s %s' %(mp.first_name, mp.last_name)
                # rol.ordered = ordered
                # rol.start_date = start_date
                # rolData['EndDate'] = end_date.isoformat()
                # rol.position = 'Committee Member'
                # rol.group = three
                # rol.parliamentNumber = one
                # rol.affiliation = two
                if end_date == None:
                    rolData['Current'] = True
                else:
                    rolData['Current'] = False
                    rolData['EndDate'] = end_date.isoformat()
                # shareData.append(save_obj_and_update(rol, rolU, rolData, rol_is_new))
                rol, rolU, rolData, rol_is_new, shareData = save_and_return(rol, rolU, rolData, rol_is_new, shareData, func)
                # rol.save()
            except Exception as e:
                print(str(e))
    except Exception as e:
        print('roles-committees')
        print(str(e))
    try:
        # print('roles-iia')
        table = soup.find('table', {'id':'roles-iia'})
        tbody = table.find('tbody')
        roles = tbody.find_all('tr', {'role':'row'})
        ordered += 1
        for r in roles:
            try:
                td = r.find_all('td')
                one = td[0].text
                two = td[1].text
                three = td[2].text
                start = td[3].text
                end = td[4].text
                start_date = datetime.datetime.strptime(start, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                if end:
                    end_date = datetime.datetime.strptime(end, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                else:
                    end_date = None
                rol, rolU, rolData, rol_is_new = get_model_and_update('Role', ordered=ordered, Person_obj=mp, Position='Parliamentary Association', Group=three, StartDate=start_date, Country_obj=country, Region_obj=country, gov_level='Federal')
                # try:
                #     rol = Role.objects.filter(person=mp, position='Parliamentary Association', group=three, start_date=start_date)[0]
                # except:
                #     rol = Role()
                #     # r.Region_obj =
                #     rol.person = mp
                #     rol.person_name = '%s %s' %(mp.first_name, mp.last_name)
                # rol.ordered = ordered
                # rol.start_date = start_date
                # rolData['EndDate'] = end_date.isoformat()
                # rol.position = 'Parliamentary Association'
                # rol.parliamentNumber = one
                # rol.group = three
                if end_date == None:
                    rolData['Current'] = True
                else:
                    rolData['Current'] = False
                    rolData['EndDate'] = end_date.isoformat()
                # shareData.append(save_obj_and_update(rol, rolU, rolData, rol_is_new))
                rol, rolU, rolData, rol_is_new, shareData = save_and_return(rol, rolU, rolData, rol_is_new, shareData, func)
                # rol.save()
            except Exception as e:
                print(str(e))
    except Exception as e:
        print('roles-iia')
        print(str(e))
    try:
        # print('roles-elections')
        table = soup.find('table', {'id':'roles-elections'})
        tbody = table.find('tbody')
        roles = tbody.find_all('tr', {'role':'row'})
        ordered += 1
        for r in roles:
            try:
                td = r.find_all('td')
                end = td[0].text
                if end:
                    start_date = datetime.datetime.strptime(end, '%B %d, %Y').replace(tzinfo=pytz.UTC)
                else:
                    start_date = None
                two = td[1].text
                constituency_name = td[2].text
                province_name = td[3].text
                result = td[4].text

                
                try:
                    prov = Region.objects.filter(Name=province_name, nameType='Province', modelType='provState', ParentRegion_obj=country)[0]
                except:
                    prov = Region.objects.filter(func=func, Name=province_name, nameType='Province', modelType='provState', ParentRegion_obj=country)
                    prov.save(share=False)
                    shareData.append(prov)

                # prov, provU, provData, prov_is_new = get_model_and_update('Region', Name=province_name, nameType='Province', modelType='provState', ParentRegion_obj=country)
                # # shareData.append(save_obj_and_update(prov, provU, provData, prov_is_new))
                # prov, provU, provData, prov_is_new, shareData = save_and_return(prov, provU, provData, prov_is_new, shareData, func)
                
                # try:
                #     # constituency_name = soup.find('div', {'class':'ce-mip-mp-constituency'}).text
                #     con = District.objects.filter(Q(Name=constituency_name)|Q(AltName=constituency_name.replace('—', ''))).filter(Country_obj=country, gov_level='Federal')[0] #that character being removed is important, it is not a regular dash
                #     con, conU, conData, con_is_new = get_model_and_update('District', obj=con)
                #     conU.District_obj = con
                #     con.ProvState_obj=prov
                #     # mpU.District_obj = con
                # except:
                #     con, conU, conData, con_is_new = get_model_and_update('District', Name=constituency_name, AltName=constituency_name.replace('—', ''), Country_obj=country, Region_obj=country, ProvState_obj=prov, gov_level='Federal', modelType='riding', nameType='Riding')
                #     conU.District_obj = con
                #     # mpU.District_obj = con
                # # shareData.append(save_obj_and_update(con, conU, conData, con_is_new))
                # con, conU, conData, con_is_new, shareData = save_and_return(con, conU, conData, con_is_new, shareData, func)
                
                try:
                    # constituency_name = soup.find('div', {'class':'ce-mip-mp-constituency'}).text
                    con = District.objects.filter(Q(Name=constituency_name)|Q(AltName=constituency_name.replace('—', ''))).filter(Country_obj=country, gov_level='Federal')[0]
                except:
                    con = District.objects.filter(func=func, Name=constituency_name, AltName=constituency_name.replace('—', ''), Country_obj=country, Region_obj=country, ProvState_obj=prov, gov_level='Federal', modelType='riding', nameType='Riding')
                    # con.ProvState_obj=prov
                    con.save(share=False)
                    shareData.append(con)
                    # mpU.District_obj = con

                # try:
                #     con = Riding.objects.filter(Q(name=constituency)|Q(alt_name=constituency.replace('—', '')))[0] #that character being removed is important, it is not a regular dash
                # except:
                #     try:
                #         prov = Province.objects.filter(name=province)[0]
                #     except:
                #         prov = Province()
                #         prov.name = province
                #         prov.save()
                    # con = Riding()
                    # con.name = constituency
                    # con.province = prov
                    # con.province_name = prov.name
                    # con.save()
                    # con.create_post()
                    # con.fillout()
                # try:
                #     party = Party.objects.get(name=caucus, level='Federal')
                # except:
                #     party = Party()
                #     party.name = caucus
                #     party.level = 'Federal'
                #     party.parlinfo_link = party_link
                #     party.save()
                #     party.fillout()
                rol, rolU, rolData, rol_is_new = get_model_and_update('Role', ordered=ordered, gov_level='Federal', Person_obj=mp, Position='Election Candidate', Group=two, District_obj=con, Country_obj=country, Region_obj=country, ProvState_obj=prov, StartDate=start_date)
                # rol, rolU, rolData, rol_is_new = get_model_and_update('Role', ordered=ordered, Person_obj=mp, Position='Parliamentary Association', Group=three, StartDate=start_date, Country_obj=country, Region_obj=country, gov_level='Federal')
                # try:
                #     rol = Role.objects.filter(person=mp, position='Election Candidate', group=two, end_date=end_date)[0]
                # except:
                #     rol = Role()
                #     # r.Region_obj =
                #     rol.person = mp
                #     rol.person_name = '%s %s' %(mp.first_name, mp.last_name)
                # rol.ordered = ordered
                # rol.start_date = start_date
                # rolData['EndDate'] = end_date.isoformat()
                # rol.position = 'Election Candidate'
                # # rol.title = title
                # rol.province_name = province
                # rol.riding = con
                # rol.constituency_name = constituency
                rolData['Result'] = result
                # rol.group = two
                # if end_date == None:
                #     rolData['Current'] = True
                # else:
                #     rolData['Current'] = False
                #     rolData['EndDate'] = end_date.isoformat()
                # rol.save()
                # shareData.append(save_obj_and_update(rol, rolU, rolData, rol_is_new))
                rol, rolU, rolData, rol_is_new, shareData = save_and_return(rol, rolU, rolData, rol_is_new, shareData, func)

            except Exception as e:
                print(str(e))
    except Exception as e:
        print('roles-elections')
        print(str(e))
    print('mpData', mpData)
    # shareData.append(save_obj_and_update(mp, mpU, mpData, mp_is_new))
    mp, mpU, mpData, mp_is_new, shareData = save_and_return(mp, mpU, mpData, mp_is_new, shareData, func)

    # print('-----------')
    # mp.save()
    # print('')
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()
    print('done get _MP')
    return shareData

def get_federal_candidates(num):
    print('get federal candidates', num)
    url = 'https://lop.parl.ca/sites/ParlInfo/default/en_CA/ElectionsRidings/Elections'
    try:
        print("opening browser")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_experimental_option( "prefs",{'profile.managed_default_content_settings.javascript': 2})
        # chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        caps = DesiredCapabilities().CHROME
        # caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
        caps["pageLoadStrategy"] = "eager"   # Do not wait for full page load
        driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
    except Exception as e:
        print(str(e))
    print('getting link')
    driver.get(url)
    # print('link retreived')
    toFillList = []
    timeout = 30
    element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="gridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr[1]/td[2]'))
    WebDriverWait(driver, timeout).until(element_present)
    # num = 1
    xpath = '//*[@id="gridContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr'
    one = xpath + '[%s]' %(num)
    tr = driver.find_element(By.XPATH, one)
    parliamentNum = tr.text.replace('Parliament: ', '')
    print('parliament', parliamentNum)
    td = tr.find_element(By.CLASS_NAME, "dx-datagrid-group-closed")
    td.click()
    print('clicked')
    time.sleep(1)
    num += 1
    two = xpath + '[%s]' %(num)
    tr = driver.find_element(By.XPATH, two)
    title = tr.text.replace('Type of Election: ', '')
    td = tr.find_element(By.CLASS_NAME, "dx-datagrid-group-closed")
    td.click()
    print('clicked')
    time.sleep(1)
    num += 1
    three = xpath + '[%s]' %(num)
    tr = driver.find_element(By.XPATH, three)
    try:
        date = tr.text.replace('Date of Election: ', '').replace(' Profile', '')
        date_time = datetime.datetime.strptime(date, '%Y-%m-%d')
    except:
        date_time = None
    try:
        e = Election.objects.filter(level='Federal', type=title, end_date=date_time)[0]
    except:
        e = Election(level='Federal', type=title, end_date=date_time)
        e.save()
    e.Parliament = int(parliamentNum)
    td = tr.find_element(By.CLASS_NAME, "dx-datagrid-group-closed")
    td.click()
    print('clicked')
    time.sleep(2)
    def get_list(driver):
        data = driver.find_elements(By.CLASS_NAME, "dx-data-row")
        for d in data:
            # time.sleep(1)
            tds = d.find_elements(By.CSS_SELECTOR, "td")
            for t in tds:
                if t.get_attribute('aria-colindex') == '4':
                    try:
                        img = t.find_element(By.CSS_SELECTOR, "img").get_attribute('src')
                    except:
                        img = None
                elif t.get_attribute('aria-colindex') == '5':
                    province = t.text
                elif t.get_attribute('aria-colindex') == '6':
                    a = t.find_element(By.CSS_SELECTOR, "a")
                    con_link = a.get_attribute('href')
                    constituency = a.text
                elif t.get_attribute('aria-colindex') == '7':
                    try:
                        a = t.find_element(By.CSS_SELECTOR, "a")
                        person_link = a.get_attribute('href')
                        name = a.text
                    except:
                        person_link = None
                        name = t.text
                elif t.get_attribute('aria-colindex') == '9':
                    occupation = t.text
                elif t.get_attribute('aria-colindex') == '10':
                    try:
                        a = t.find_element(By.CSS_SELECTOR, "a")
                        party_link = a.get_attribute('href')
                        alt_caucus = a.text
                    except:
                        party_link = None
                        alt_caucus = t.text
                    caucus = alt_caucus.replace(' Party of Canada', '').replace(' of Canada', '')
                elif t.get_attribute('aria-colindex') == '11':
                    result = t.text
                    # cant print text on headless for unknown reason
                    z = str(t.get_attribute('outerHTML'))
                    x = z.find('>')
                    c = z[x+1:].find('<')
                    result = z[x+1:x+1+c]
                elif t.get_attribute('aria-colindex') == '12':
                    vote_count = t.text
                    # cant print text on headless for unknown reason
                    z = str(t.get_attribute('outerHTML'))
                    x = z.find('>')
                    c = z[x+1:].find('<')
                    vote_count = z[x+1:x+1+c]
            a = name.find(', ')
            last_name = name[:a]
            first_name = name[a+2:]
            print(first_name, last_name)
            try:
                p = Person.objects.filter(first_name=first_name, last_name=last_name)[0]
                # break
            except:
                p = Person()
                # p.Region_obj = 
                p.first_name = first_name
                p.last_name = last_name
                p.save()
                p.create_post()
            if p.parl_ca_small_img != img:
                p.parl_ca_small_img = img
                p.save()
            try:
                con = Riding.objects.filter(Q(name=constituency)|Q(alt_name=constituency.replace('-', '')))[0]
            except:
                try:
                    prov = Province.objects.filter(name=province)[0]
                except:
                    prov = Province()
                    prov.name = province
                    prov.save()
                con = Riding()
                con.name = constituency
                con.alt_name = constituency.replace('-', '')
                con.province = prov
                con.province_name = prov.name
                con.parlinfo_link = con_link
                con.save()
                con.create_post()
                # con.fillout()
                toFillList.append(con)
            if con.parlinfo_link != con_link:
                con.parlinfo_link = con_link
                con.save()
            try:
                party = Party.objects.filter(Q(name=caucus)|Q(alt_name=alt_caucus), level='Federal')[0]
            except:
                party = Party()
                party.name = caucus
                party.alt_name = alt_caucus
                party.level = 'Federal'
                party.parlinfo_link = party_link
                party.save()
                party.create_post()
                # party.fillout()
                toFillList.append(party)
            if party.parlinfo_link != party_link:
                party.parlinfo_link = party_link
                party.save()
            try:
                r = Role.objects.filter(person=p, position='Election Candidate', group='General Election', end_date=date_time)[0]
            except:
                r = Role()
                # r.Region_obj = 
                r.person = p
                r.person_name = '%s %s' %(p.first_name, p.last_name)
                r.position = 'Election Candidate'
                r.group = 'General Election'
            r.end_date = date_time
            r.party_name = caucus
            r.province_name = province
            r.constituency_name = constituency
            r.riding = con
            r.party = party
            r.election = e
            r.occupation = occupation
            r.result = result
            # print(vote_count)
            # print(int(vote_count.replace(',','')))
            r.vote_count = int(vote_count.replace(',',''))
            r.parlinfo_link = person_link
            r.save()
    # print('get_list')        
    get_list(driver)
    n = 2
    # completed = 'notCompleted'
    while driver.find_element(By.CLASS_NAME, "dx-next-button") and 'disable' not in driver.find_element(By.CLASS_NAME, "dx-next-button").get_attribute('class'):
        print('')
        print('page ', n)
        next = driver.find_element(By.CLASS_NAME, "dx-next-button")
        next.click()
        time.sleep(2)
        get_list(driver)
        n += 1
    # if 'disable' in driver.find_element(By.CLASS_NAME, "dx-next-button").get_attribute('class'):
    #     completed = 'isCompleted'
    print('done1')
    driver.quit()
    print('-------toFillList----------')
    for i in toFillList:
        if i.parlinfo_link or not i.wikipedia:
            i.fillout()
    driver.quit()
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()
    
def get_all_federal_candidates():
    num = 44
    for n in range(num):
        n+=1
        get_federal_candidates(n)
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()

def get_house_committees(object_type='committee', value='latest'):
    get_house_hansard_or_committee(object_type, value)
    get_house_committee_list('latest')
    get_house_committee_work('latest')

def get_house_hansard_or_committee(object_type, value, func):
    shareData = []
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    # gov = Government.objects.filter(Country_obj=country, gov_level='Federal', Region_obj=country)[0]
    xml = 'https://www.ourcommons.ca/PublicationSearch/en/?PubType=37&xml=1'
    is_hansard = False
    is_committee = False
    if object_type == 'hansard' and value == 'latest':
        print('---------------------housee hansard')
        # print('is hansard')
        is_hansard = True
        # xml = 'https://www.ourcommons.ca/PublicationSearch/en/?View=D&Item=&ParlSes=from2022-10-31to2022-10-31&oob=&Topic=&Proc=&Per=&Prov=&Cauc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=150000&PubType=37&xml=1'
        xml = 'https://www.ourcommons.ca/PublicationSearch/en/?View=D&Item=&ParlSes=&oob=&Topic=&Proc=&Per=&Prov=&Cauc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=150000&PubType=37&xml=1'
    elif object_type == 'committee' and value == 'latest':
        # print('is committee')
        is_committee = True
        # xml = 'https://www.ourcommons.ca/PublicationSearch/en/?View=D&Item=&ParlSes=from2022-10-31to2022-10-31&oob=&Topic=&Proc=&Per=&Prov=&Cauc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=150000&PubType=40017&xml=1'
        xml = 'https://www.ourcommons.ca/PublicationSearch/en/?View=D&Item=&ParlSes=&oob=&Topic=&Proc=&Per=&Prov=&Cauc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=150000&PubType=40017&xml=1'
    elif object_type == 'committee':
        # print('build database')
        xml = value
        # xml = 'https://www.ourcommons.ca/PublicationSearch/en/?PubType=40017&xml=1&parlses=from2023-03-01to2023-04-01'
        is_committee = True
    elif object_type == 'hansard':
        # print('build database')
        xml = value
        # xml = 'https://www.ourcommons.ca/PublicationSearch/en/?View=D&Item=&ParlSes=from2002-05-02to2002-05-02&oob=&Topic=&Proc=&Per=&Prov=&Cauc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=2000000&PubType=37&xml=1'
        is_hansard = True
    print(xml)
    # fail
    # start_time = datetime.datetime.now()
    # print('start', start_time)
    r = requests.get(xml, verify=False)
    print('received')
    # end_time = datetime.datetime.now() - start_time
    # print('end11', end_time)
    # mb = to_megabytes(r)
    # print('mb', mb)
    root = ET.fromstring(r.content)
    # mb = to_megabytes(root)
    # print('mb', mb)
    # time.sleep(3)
    # print('----root')
    publications = root.find('Publications')
    # print(publications)
    pubs = publications.findall('Publication')
    for p in reversed(pubs):
        # print(p.tag)
        Title = p.attrib['Title']
        print(Title)
        # print(len(Title))
        pub_iden = p.attrib['Id']
        date = p.attrib['Date']
        # '2022-10-28'
        xTime = p.attrib['Time']
        # Publication_date_time = None
        Parliament = p.attrib['Parliament']
        Session = p.attrib['Session']
        # try:
        #     gov = Government.objects.filter(Country_obj=country, gov_level='Federal', GovernmentNumber=Parliament, SessionNumber=Session, Region_obj=country)[0]
        # except:
        #     gov = Government(Country_obj=country, gov_level='Federal', GovernmentNumber=Parliament, SessionNumber=Session, Region_obj=country)
        #     gov.save()
        #     gov.end_previous()
        gov, govU, govData, gov_is_new = get_model_and_update('Government', Country_obj=country, gov_level='Federal', GovernmentNumber=Parliament, SessionNumber=Session, Region_obj=country)
        if gov_is_new:
            shareData.append(gov.end_previous(func))
            gov, govU, govData, gov_is_new, shareData = save_and_return(gov, govU, govData, gov_is_new, shareData, func)
        # Organization = p.attrib['Organization']
        # PdfURL = p.attrib['PdfURL']
        # IsAudioOnly = p.attrib['IsAudioOnly']
        # IsTelevised = p.attrib['IsTelevised']
        # TypeId = p.attrib['TypeId']
        # HtmlURL = p.attrib['HtmlURL']
        # MeetingIsForSenateOrganization = p.attrib['MeetingIsForSenateOrganization']
        if value == 'latest':
            new = False
        else:
            new = True
        if is_hansard:
            date_A = datetime.datetime.strptime('%s' %(date), '%Y-%m-%d').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
            date_time = datetime.datetime.strptime('%s/%s' %(date, xTime), '%Y-%m-%d/%H:%M').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
            try:
                meeting = Meeting.objects.filter(meeting_type='Debate', DateTime__gte=date_A, DateTime__lt=date_A + datetime.timedelta(days=1), Title=Title, chamber='House', Government_obj=gov, Country_obj=country, Region_obj=country)[0]
                meeting, meetingU, meetingData, meeting_is_new = get_model_and_update('Meeting', obj=meeting)
            except:
                meeting, meetingU, meetingData, meeting_is_new = get_model_and_update('Meeting', meeting_type='Debate', DateTime=date_time, Title=Title, chamber='House', Government_obj=gov, Country_obj=country, Region_obj=country)
            
            # debate, debateU, debateData, debate_is_new = get_model_and_update('Meeting', meeting_type='debate', DateTime__gte=date_A, DateTime__lt=date_A + datetime.timedelta(days=1), chamber='House', Government_obj=gov, Country_obj=country, Region_obj=country)
            # debate.Title=Title
            # debate.DateTime=date_time
            if 'has_transcript' not in meetingData or meetingData['has_transcript'] == False:
                new = True
                meetingData['has_transcript'] = False
            if meeting_is_new:
                
                try:
                    A = Agenda.objects.filter(DateTime__gte=date_time, DateTime__lt=date_time + datetime.timedelta(hours=12), chamber='House', Government_obj=gov, Country_obj=country, Region_obj=country)[0]
                    A, Au, AData, A_is_new = get_model_and_update('Agenda', obj=A)
                except:
                    A, Au, AData, A_is_new = get_model_and_update('Agenda', DateTime=date_time, chamber='House', Government_obj=gov, Country_obj=country, Region_obj=country)
                    A, Au, AData, A_is_new, shareData = save_and_return(A, Au, AData, A_is_new, shareData, func)
                meeting.Agenda_obj = A    
            
            # try:
            #     H = Hansard.objects.filter(DateTime__gte=date_A, DateTime__lt=date_A + datetime.timedelta(days=1), ParliamentNumber=Parliament, SessionNumber=Session, Organization='House')[0]
            #     print('hansard found')
            #     H.Title=Title
            #     H.DateTime=date_time
            #     if not H.has_transcript:
            #         new = True
            # except:
            #     try:
            #         A = Agenda.objects.filter(date_time__gte=date_time, date_time__lt=date_time + datetime.timedelta(days=1), organization='House', gov_level='Federal')[0]
            #         print('agenda found')
            #     except:
            #         print('create agenda')
            #         A = Agenda(date_time=date_time, organization='House', gov_level='Federal')
            #         A.save()
            #         A.create_post()
            #     try:
            #         H = Hansard.objects.filter(agenda=A)[0]
            #         if not H.has_transcript:
            #             new = True
            #     except:
            #         H = Hansard(agenda=A, Title=Title, ParliamentNumber=Parliament, SessionNumber=Session, Publication_date_time=date_time, Organization='House')
            #         new = True
            #         H.save()
            #         H.create_post() 
                # H = Hansard(Title=Title, ParliamentNumber=Parliament, SessionNumber=Session, Publication_date_time=date_time, Organization='House')
                # new = True
                print('hansard created')
            meeting.GovPage = 'https://www.ourcommons.ca/DocumentViewer/en/%s-%s/house/sitting-%s/hansard' %(Parliament, Session, meeting.Title.replace('Hansard - ',''))
        elif is_committee:
            a = Title.find(' - ')+len(' - ')
            b = Title[a:].find('-')
            code = Title[a:a+b]
            try:
                committee = Committee.objects.filter(code=code.upper(), ParliamentNumber=44, SessionNumber=1)[0]
            except:
                committee = Committee(code=code.upper(), Organization='House', Title=p.attrib['Organization'], ParliamentNumber=44, SessionNumber=1)
                committee.save()
                committee.create_post()
            try:
                date_time_start = datetime.datetime.strptime('%s' %(date), '%Y-%m-%d')
                dt_plus_one = date_time_start + datetime.timedelta(days=1)
                H = CommitteeMeeting.objects.filter(committee=committee, date_time_start__range=[datetime.datetime.strftime(date_time_start, '%Y-%m-%d'), datetime.datetime.strftime(dt_plus_one, '%Y-%m-%d')], ParliamentNumber=Parliament, SessionNumber=Session)[0]
                print('committeeM found')
                # H.code = code
                if not H.Title:
                    H.Title = Title
            except:
                H = CommitteeMeeting(committee=committee, Title=Title, code=code, Organization='House', ParliamentNumber=Parliament, SessionNumber=Session)
                H.has_transcript = True
                print('committeeM created')
                new = True
        meeting.DateTime = datetime.datetime.strptime('%s-%s' %(date, xTime), '%Y-%m-%d-%H:%M').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
        # meeting.ParliamentNumber = int(p.attrib['Parliament'])
        # meeting.SessionNumber = int(p.attrib['Session'])
        # H.Title = p.attrib['Title']
        meeting.PubIden = pub_iden
        # H.Organization = p.attrib['Organization']
        meetingData['PdfURL'] = p.attrib['PdfURL']
        meeting.IsAudioOnly = int(p.attrib['IsAudioOnly'])
        meeting.IsTelevised = int(p.attrib['IsTelevised'])
        meeting.TypeId = int(p.attrib['TypeId'])
        # H.ItemId = p.attrib['Id']
        meeting.HtmlURL = p.attrib['HtmlURL']
        meeting.MeetingIsForSenateOrganization = p.attrib['MeetingIsForSenateOrganization']
        # print('saving')
        # H.Terms = []
        if 'Terms' in meetingData:
            meeting_terms = json.loads(meetingData['Terms'])
        else:
            meeting_terms = {}
        # H.save()
        # H.create_post()
        # print('saved')
        meeting, meetingU, meetingData, meeting_is_new, shareData = save_and_return(meeting, meetingU, meetingData, meeting_is_new, shareData, func)
        items = p.findall('PublicationItems')
        if new or meetingData['has_transcript'] == False:
        # if new or H.object_type == 'hansard' and H.completed_model == False:
            for item in items:
                it = item.findall('PublicationItem')
                for i in it:
                    ItemId = i.attrib['Id']
                    # print('itemdid', ItemId)
                    EventId = i.attrib['EventId']
                    Date = i.attrib['Date']
                    Hour = i.attrib['Hour']
                    Minute = i.attrib['Minute']
                    Second = i.attrib['Second']
                    # '2022-10-31-11:03:49'
                    # print('---1')
                    # dt = '%s:%s:%s' %(Hour, Minute, Second)
                    # print(dt)
                    # Item_date_time = datetime.datetime.strptime(dt, '%H:%M:%S')
                    # print(Item_date_time)
                    # print('---2')
                    dt = '%s-%s:%s:%s' %(Date, Hour, Minute, Second)
                    print(dt)
                    Item_date_time = datetime.datetime.strptime(dt, '%Y-%m-%d-%H:%M:%S').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
                    if is_hansard:
                        statement, statementU, statementData, statement_is_new = get_model_and_update('Statement', ItemId=ItemId, EventId=EventId, DateTime=Item_date_time, Meeting_obj=meeting, chamber='House', Government_obj=gov, Country_obj=country, Region_obj=country)
                        # try:
                        #     h = HansardItem.objects.filter(ItemId=ItemId, EventId=EventId, Item_date_time=Item_date_time)[0]
                        #     # print('----handsard--found')
                        # except:
                        #     h = HansardItem(ItemId=ItemId, EventId=EventId, Item_date_time=Item_date_time)
                        #     # print('----hansard--created')
                        # h.hansard = H
                    elif is_committee:
                        try:
                            h = CommitteeItem.objects.filter(committeeMeeting=H, EventId=EventId, Item_date_time=Item_date_time)[0]
                            # print('----handsard--found')
                        except:
                            h = CommitteeItem(committeeMeeting=H, ItemId=ItemId, EventId=EventId, Item_date_time=Item_date_time, meeting_title=H.Title)
                            # print('----hansard--created')
                        # h.committeeMeeting = H
                    # h.hansardId = H.id
                    statement.VideoURL = i.attrib['VideoURL'] + '&vt=watch&autoplay=true'
                    # h.Sequence = i.attrib['Sequence']
                    try:
                        statement.Page = i.attrib['Page']
                    except:
                        pass
                    try:
                        statement.PdfPage = i.attrib['PdfPage']
                    except:
                        pass
                    statement.TypeId = i.attrib['TypeId']
                    # h.FacebookLink = i.attrib['FacebookLink']
                    # h.TwitterLink = i.attrib['TwitterLink']
                    # h.Title = p.attrib['Title']
                    # print(h.Title)
                    statement.PublicationId = int(p.attrib['Id'])
                    # print(int(p.attrib['Id']))
                    date = p.attrib['Date']
                    # '2022-10-28-11:00'# print('----')
                    person = i.find('Person')
                    try:
                        Id = person.attrib['Id']
                    except: 
                        Id = None
                    # print('before name')
                    # IsMember = person.attrib['IsMember']
                    try:
                        ProfileUrl = person.find('ProfileUrl').text
                    except:
                        ProfileUrl = None
                    # print(ProfileUrl)
                    FirstName = person.find('FirstName').text
                    # print(FirstName)
                    LastName = person.find('LastName').text
                    # print(LastName)
                    # Honorific = person.find('Honorific').text
                    # URLFullName = person.find('URLFullName').text
                    # Constituency = person.find('Constituency').text
                    # Caucus = person.find('Caucus').text
                    # Province = person.find('Province').text
                    
                    try:
                        Image = person.find('Image').text
                    except:
                        Image = None

                    try:
                        if Id:
                        # if IsMember == '1':
                            # print('has id', Id)
                            profile, profileU, profileData, profile_is_new = get_model_and_update('Person', GovIden=Id, Country_obj=country, Region_obj=country)
                        # try:
                        #     profile = Person.objects.filter(GovIden=Id, Country_obj=country)[0]
                        #     print(profile)
                        # except:
                        #     print('except')
                        else:
                            profile, profileU, profileData, profile_is_new = get_model_and_update('Person', FirstName=FirstName, LastName=LastName, Country_obj=country, Region_obj=country)
                            
                            # try:
                            #     profile = Person.objects.filter(FirstName=FirstName, LastName=LastName, Country_obj=country)[0]
                            #     # profile = profiles[0] #to cause fail if return none
                            # except:
                            #     profile = Person.objects.filter(FirstName__icontains=FirstName, LastName=LastName, Country_obj=country)[0]
                                # profile = profiles[0] #to cause fail if return none
                            # print(profiles)
                            # print('next')
                            # for profile in profiles:
                            try:
                                # print(profile)
                                # r = None
                                r = Role.objects.filter(Person_obj=profile, Position='Member of Parliament')[0]
                                print(r)
                                if ProfileUrl:
                                    profileData['GovProfilePage'] = ProfileUrl
                                    # profile.save()
                                    try:
                                        mpData = get_MP(profile, profileU, profileData, profile_is_new, func)
                                        for d in mpData:
                                            shareData.append(d)
                                    except Exception as e:
                                        print(str(e))
                                # print('break')
                                # break
                            except Exception as e:
                                print(str(e))
                            # if not r:
                            #     print('looking for candidates')
                            #     # for profile in profiles:
                            #     try:
                            #         print(profile)
                            #         # r = Role.objects.filter(person=profile, position='Election Candidate', group='General Election', result__icontains='Elected')[0]
                            #         print(r)
                            #         if ProfileUrl:
                            #             profile.gov_profile_page = ProfileUrl
                            #             profile.save()
                            #             try:
                            #                 get_MP(profile)
                            #             except Exception as e:
                            #                 print(str(e))
                            #         # print('break')
                            #         # break
                            #     except Exception as e:
                            #         print(str(e))
                            # if not r:
                            #     fail
                        # if not profile.party_name:
                        #     try:
                        #         get_MP(profile)
                        #     except Exception as e:
                        #         print(str(e))
                        # else:
                        #     print('no id')
                        #     profile, profileU, profileData, profile_is_new = get_model_and_update('Person', FirstName=FirstName, LastName=LastName, Country_obj=country, Region_obj=country)
                            # profile = Person.objects.filter(first_name=FirstName, last_name=LastName, gov_iden=0)[0]
                        # print('----person--found')
                    except Exception as e:
                        print(str(e))
                        print('create person')
                        profile, profileU, profileData, profile_is_new = get_model_and_update('Person', FirstName=FirstName, LastName=LastName, Country_obj=country, Region_obj=country)
                            # profile = Person(gov_iden=Id)
                            # # p.Region_obj = 
                            # profile.first_name = FirstName
                            # profile.last_name = LastName
                        if Id:
                            profile.GovProfilePage = ProfileUrl
                            profile.GovIden = Id
                            # profile.save()
                            # profile.create_post()
                            try:
                                mpData = get_MP(profile, profileU, profileData, profile_is_new, func)
                                for d in mpData:
                                    shareData.append(d)
                            except Exception as e:
                                print(str(e))
                        # else:
                        #     print('no id')
                        #     profile, profileU, profileData, profile_is_new = get_model_and_update('Person', FirstName=FirstName, LastName=LastName, Country_obj=country, Region_obj=country)
                        #     # profile = Person(first_name=FirstName, last_name=LastName)
                        #     # # p.Region_obj = 
                        #     # profile.save()
                        #     # profile.create_post()
                        if Image:
                            profile.AvatarLink = Image
                        # profile.save()
                        # print('----person--created')
                    profile, profileU, profileData, profile_is_new, shareData = save_and_return(profile, profileU, profileData, profile_is_new, shareData, func)
                    statement.Person_obj = profile
                    statement.PersonName = profile.FullName
                    # if profile not in H.people.all():
                    # H.people.add(profile)
                    # print('2')
                    # try:
                    #     if profile not in H.people:
                    #         H.people.append(profile)
                    # except Exception as e:
                    #     # print(' e', str(e))
                    #     H.people = []
                    #     if profile not in H.people:
                    #         H.people.append(profile)
                    # print('aaa')
                    statement.OrderOfBusiness = i.find('OrderOfBusiness').text
                    statement.SubjectOfBusiness = i.find('SubjectOfBusiness').text
                    # try:
                    if statement.SubjectOfBusiness:
                        if 'subjects' in meetingData:
                        # try:
                            meetingData['subjects'].append(statement.SubjectOfBusiness)
                        else:
                            meetingData['subjects'] = [statement.SubjectOfBusiness]
                            # statement.subjects.append(h.SubjectOfBusiness)
                    # except Exception as e:
                    #     # print(' e', str(e))
                    #     H.subjects = []
                    #     if h.SubjectOfBusiness not in H.subjects:
                    #         H.subjects.append(h.SubjectOfBusiness)
                    statement.EventType = i.find('EventType').text
                    # print('-_-_-_-')
                    XmlContent = i.find('XmlContent')
                    try:
                        # print('try')
                        Intervention = XmlContent.find('Intervention')
                        # print('intervention')
                        try:
                            statement.Type = Intervention.attrib['Type']
                        except:
                            pass
                        # print(Intervention.attrib['ToC'])
                        try:
                            ToCText = Intervention.attrib['ToCText']
                        except:
                            pass
                        # print(Intervention.attrib['id'])
                        try:
                            PersonSpeaking = Intervention.find('PersonSpeaking')
                            # h.person_name  = PersonSpeaking.find('Affiliation').text
                        except:
                            pass
                        # print('b')
                        # print(Affiliation.text)
                        Content = Intervention.find('Content')
                        FloorLanguage = Content.find('FloorLanguage')
                        # print('c')
                        try:
                            statement.Language = FloorLanguage.attrib['language']
                        except:
                            pass
                        ParaText = Content.findall('ParaText')
                        # h.wordCount = len(''.join(Content.itertext())) 
                        statement.Content = ''
                        for pt in ParaText:
                            Content = ET.tostring(pt).decode()
                            # print(str(Content))
                            statement.Content = statement.Content + '\n' + str(Content)
                        # h.Content = h.Content.decode("utf-8")
                        # print(statement.Content)
                        string =  re.sub('<[^<]+?>', '', statement.Content)
                        words = re.findall(r'\w+', string)
                        # print(words)
                        statement.word_count = len(words)
                        # print(statement.word_count)
                    except Exception as e:
                        print('except', str(e))
                        # h.save()
                        SubjectOfBusiness = XmlContent.find('SubjectOfBusiness')
                        SubjectOfBusinessContent = SubjectOfBusiness.find('SubjectOfBusinessContent')
                        FloorLanguage = SubjectOfBusinessContent.find('FloorLanguage')
                        # print(FloorLanguage.attrib['language'])
                        try:
                            statement.Language = FloorLanguage.attrib['language']
                        except:
                            pass
                        # print('1')
                        WrittenQuestionResponse = SubjectOfBusinessContent.findall('WrittenQuestionResponse')
                        # print('writtenquestionnresponse found')
                        statement.word_count = 0
                        statementData['questions'] = []
                        for Quest in WrittenQuestionResponse:
                            question = {}
                            QuestionId = Quest.find('QuestionID')
                            QuestionNumber = ''.join(QuestionId.itertext())
                            question['QuestionId'] = QuestionId
                            question['QuestionNumber'] = QuestionNumber
                            # try:
                            #     q = Question.objects.filter(HansardTitle=H.Title, Parliament=H.ParliamentNumber, Session=H.SessionNumber, QuestionNumber=QuestionNumber)[0]
                            # except:
                            #     q = Question(HansardTitle=H.Title, Parliament=H.ParliamentNumber, Session=H.SessionNumber, QuestionNumber=QuestionNumber)
                            #     q.save()
                            # if q not in h.questions.all():
                            #     h.questions.add(q)
                            # try:
                            #     if q not in h.questions:
                            #         h.questions.append(q)
                            # except Exception as e:
                            #     # print(' e', str(e))
                            #     h.questions = []
                            #     if q not in h.questions:
                            #         h.questions.append(q)
                            # h.question = q
                            # print(ET.tostring(q))
                            try:
                                Questioner = Quest.find('Questioner')
                                # print('aa')
                                QuestionerName = Questioner.find('Affiliation').text
                            except:
                                QuestionerName = None
                            # print('bb')
                            if '. ' in QuestionerName:
                                a = QuestionerName.find('. ')
                            else:
                                a = 0
                            if '(' in QuestionerName:
                                b = QuestionerName[a:].find('(')
                            else:
                                b = len(QuestionerName[a:])
                            name = QuestionerName[a:a+b].split()
                            # # print('quesiton', name)
                            # try:
                            #     qp = Person.objects.filter(Q(first_name__in=name)&Q(last_name__in=name)).exclude(gov_iden=0).first()
                            #     q.questioner = qp
                            # except Exception as e:
                            #     print(str(e))
                                # fail
                            # print('---33')
                            # q.questioner_name = 
                            question['QuestionerName'] = '%s %s' %(name[1], name[2])
                            QuestionContent = Quest.find('QuestionContent')
                            ParaText = QuestionContent.findall('ParaText')
                            question['QuestionContent'] = ''
                            for pt in ParaText:
                                # print(pt)
                                # print(ET.tostring(pt))
                                Content = ET.tostring(pt).decode()
                                question['QuestionContent'] = question['QuestionContent'] + '\n' + str(Content)
                            string =  re.sub('<[^<]+?>', '', question['QuestionContent'])
                            words = re.findall(r'\w+', string)
                            try:
                                statement.word_count = statement.word_count + len(words)
                            except:
                                statement.word_count = len(words)
                            response = {}
                            try:
                                # print('cc')
                                Responder = Quest.find('Responder')
                                ResponderName = Responder.find('Affiliation').text
                                if '. ' in ResponderName:
                                    a = ResponderName.find('. ')
                                else:
                                    a = 0
                                if '(' in ResponderName:
                                    b = QuestionerName[a:].find('(')
                                else:
                                    b = len(ResponderName[a:])
                                name = ResponderName[a:a+b].split()
                                # print('responder', name)
                                # try:
                                #     qr = Person.objects.filter(Q(first_name__in=name)&Q(last_name__in=name)).exclude(gov_iden=0).first()
                                #     q.responer = qr
                                # except:
                                #     pass
                                response['ResponderName'] = '%s %s' %(name[1], name[2])
                            except:
                                pass
                            # print('---4')
                            try:
                                ResponseContent = Quest.find('ResponseContent')
                                # print('responsecontent found')
                                ParaText = ResponseContent.findall('ParaText')
                                response['ResponseContent'] = ''
                                for pt in ParaText:
                                    # print(pt)
                                    # print(ET.tostring(pt))
                                    Content = ET.tostring(pt).decode()
                                    response['ResponseContent'] = response['ResponseContent'] + '\n' + str(Content)
                                string =  re.sub('<[^<]+?>', '', response['ResponseContent'])
                                words = re.findall(r'\w+', string)
                                try:
                                    statement.word_count = statement.word_count + len(words)
                                except:
                                    statement.word_count = len(words)
                            except:
                                try:
                                    ProceduralText = SubjectOfBusinessContent.find('ProceduralText').text
                                    # Content = ET.tostring(ProceduralText).decode()
                                    question['QuestionContent'] = question['QuestionContent'] + '\n' + str(ProceduralText)
                                except:
                                    pass
                            question['response'] = response
                            statementData['questions'].append(question)
                            # q.save()
                                    #     print(pt.text)
                                    #     try:
                                    #         document = pt.find('Document')
                                    #         print(document.text)
                                    #         print('DOCUMENT')
                                    #     except:
                                    #         pass
                                    #     quote = pt.find('Quote')
                                    #     try:
                                    #         QuotePara = quote.find('QuotePara')
                                    #         print('QUOTE')
                                    #         print(QuotePara.text)
                                    #     except:
                                    #         pass
                                    #     print(pt.text)
                                    #     ParaText2 = pt.findall('ParaText')
                                    #     print(ParaText2)
                                    #     for pt2 in ParaText2:
                                    #         print(pt2.text)
                                    # print(XmlContent.text)
                    statement, statementU, statementData, statement_is_new, shareData = save_and_return(statement, statementU, statementData, statement_is_new, shareData, func)
                    try:
                        # print('----555')
                        IndexEntries = i.find('IndexEntries')
                        Terms = IndexEntries.findall('Term')
                        # print(Terms)
                        statement.Terms_array = []
                        s_terms = []
                        for t in Terms:
                            # print(t.attrib['Id'])
                            # print(t.attrib['IsProceduralTerm'])
                            text = t.text
                            s_terms.append(text)
                            # if not text in meeting_terms:
                            #     meeting_terms[text] = 1
                            # else:
                            #     meeting_terms[text] += 1
                            try:
                                a = text.find(', ')
                                b = text[:a]
                                bill = Bill.objects.filter(NumberCode=b, Country_obj=country, Government_obj=gov).filter(Q(chamber='Senate')|Q(chamber='House'))[0]
                                bill, billU, billData, bill_is_new = get_model_and_update('Bill', obj=bill)
                                print(bill)
                                LatestBillEventDateTime = datetime.datetime.fromisoformat(billData['LatestBillEventDateTime'])
                                if meeting.DateTime > LatestBillEventDateTime:
                                    billData['LatestBillEventDateTime'] = datetime.datetime.isoformat(meeting.DateTime)
                                    bill, billU, billData, bill_is_new, shareData = save_and_return(bill, billU, billData, bill_is_new, shareData, func)
                                # h.bills.add(bill)
                                # h.save()
                                statement = statement.add_term(text, bill)
                            except Exception as e:
                                # h.save()
                                statement = statement.add_term(text, None)
                        for text in s_terms:
                            if not text in meeting_terms:
                                meeting_terms[text] = 1
                            else:
                                meeting_terms[text] += 1

                    except Exception as e:
                        print('e3', str(e))
                        if 'findall' not in str(e):
                            fail
                        # break
                    # print('next')
                    # h.save()
                    # h.create_post()
                    # shareData.append(save_obj_and_update(statement, statementU, statementData, statement_is_new))
                    # if not s_terms:
                        # x = Statement.objects.filter(id=statement.id)[0]
                        # if x.keyword_array:
                    for k in statement.keyword_array:
                        # text = k[0].upper() + k[1:]
                        if not k in meeting_terms:
                            meeting_terms[k] = 1
                        else:
                            meeting_terms[k] += 1
            meetingData['has_transcript'] = True
            meetingData = meeting.apply_terms(meeting_terms, meetingData)
            # try:
            #     d = json.loads(H.TermsText)
            #     for t in list(d.items()):
            #         topic_link = '%s?topic=%s' %(H.get_absolute_url(), t)
            #         followers = User.objects.filter(follow_topic__contains=t)
            #         for f in followers:
            #             try:
            #                 n = Notification.objects.filter(user=f, link=topic_link)[0]
            #             except:
            #                 f.alert('%s was discussed in the %s' %(t, H.Organization), topic_link, '%s the %s' %(H.Publication_date_time.strftime('%A'), get_ordinal(int(H.Publication_date_time.strftime('%d')))))
            # except Exception as e:
            #     print(str(e))
            if is_hansard:
                people = Statement.objects.filter(Meeting_obj=meeting)
            elif is_committee:
                people = CommitteeItem.objects.filter(committeeMeeting=H)
            H_people = {}
            for p in people:
                # print(p)
                # print(p.person)
                # print(p.person.id)
                if not p.Person_obj.id in H_people:
                    H_people[p.Person_obj.id] = 1
                else:
                    H_people[p.Person_obj.id] += 1
            H_people = sorted(H_people.items(), key=operator.itemgetter(1),reverse=True)
            # if is_hansard:
            #     # print('--------------------assign notifications')
            #     for p in H.people.all():
            #         # print(p)
            #         # r = Role.objects.filter(position='Member of Parliament', person=p)[0]
            #         # users = User.objects.filter(riding=r.riding)
            #         # for u in users:
            #         #     u.alert('%s %s spoke in Parliament %s' %(p.first_name, p.last_name, H.Publication_date_time.weekday()), '%s?speaker=%s' %(H.get_absolute_url(), p.id))
            #         users = User.objects.filter(follow_person=p)
            #         for u in users:
            #             u.alert('%s %s spoke in Parliament' %(p.first_name, p.last_name), '%s?speaker=%s' %(H.get_absolute_url(), p.id), '%s the %s' %(H.Publication_date_time.strftime('%A'), get_ordinal(int(H.Publication_date_time.strftime('%d')))))
            H_people = dict(H_people)
            meetingData['People_json'] = json.dumps(H_people)
            if is_hansard:
                meetingData['VideoURL'] = Statement.objects.filter(Meeting_obj=meeting).last().VideoURL
                # sprenderize(H)
            meetingData['completed_model'] = True
            meeting, meetingU, meetingData, meeting_is_new, shareData = save_and_return(meeting, meetingU, meetingData, meeting_is_new, shareData, func)

            # H.save()
            # H.create_post()
            print('saved')
            # break
    return shareData, gov

# def get_house_committees():
#     get_house_hansard_or_committee('committee', 'latest')
#     get_house_committee_list('latest')
#     get_house_committee_work('latest')

def get_house_committee_list(day):
    # url = 'https://www.ourcommons.ca/Committees/en/Meetings?meetingDate=2022-10-31'
    # r = requests.get(url)
    # soup = BeautifulSoup(r.content, 'html.parser')
    # container = soup.find('div', {'id':'meeting-accordion'})
    # date = container.find('div', {'class':'grouping-header'})
    # print(date.text)
    # items = container.find_all('div', {'class':'accordion-item'})
    # for item in items:
    #     acron = item.find('span', {'class':'meeting-acronym'})
    #     timerange = item.find('div', {'class':'the-time'})
    #     title = item.find('div', {'class':'studies-activities-item'})
    #     h4 = item.find('h4', {'class':'meeting-card-committee-details-name'})
    #     title_link = h4.find('a')
    #     studies = item.find('div', {'class':'meeting-card-studiesactivities-title'})
    #     study = item.find('a', {'class':'current-study'})
    #     evidence = item.find('a', {'class':'btn-meeting-evidence'})
    #     minutes = item.find('a', {'class':'btn-meeting-minutes'})
    #     preview = item.find('div', {'class':'meeting-card-media-preview'})
    #     preview_src = preview.find('img')['src']
    #     try:
    #         embed = preview.find('button', {'class':'video-play-button'})['data-player-url']
    #     except:
    #         embed = None
    #     print(acron.text)
    #     print(timerange.text)
    #     print(title.text)
    #     print(h4.text.strip())
    #     print(title_link['href'])
    #     print(studies.text)
    #     print(study['href'])
    #     try:
    #         print(evidence['href'])
    #     except:
    #         print('no evidence')
    #     try:
    #         print(minutes['href'])
    #     except:
    #         print('no mins')
    #     print(preview_src)
    #     print(embed)
    #     com_title = h4.text.strip()
    #     a = com_title.find(' (')
    #     com_title = com_title[:a]

    print('--------------------house committees')
    parl = Parliament.objects.filter(country='Canada', organization='Federal')[0]
    try:
        if day == 'latest':
            url = 'https://www.ourcommons.ca/Committees/en/Meetings'
        else:
            url = day
        # print(url)
        r = requests.get(url, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        container = soup.find('div', {'id':'meeting-accordion'})
        date = container.find('div', {'class':'grouping-header'})
        print(date.text)
        items = container.find_all('div', {'class':'accordion-item'})
        for item in items:
            # print('-----------------------------')
            iden = item['id'].replace('meeting-item-', '')
            date = item['class'][1].replace('meeting-item-', '')
            acron = item.find('span', {'class':'meeting-acronym'})
            timerange = item.find('div', {'class':'the-time'})
            dt = timerange.text
            a = dt.find(' - ')
            start = dt[:a].replace('.','')
            print('start', start)
            b = dt[a:].find(' (')
            end = dt[a+3:a+b].replace('.', '')
            date_time_start = datetime.datetime.strptime(date + ' - ' + start, '%Y-%m-%d - %I:%M %p')
            date_time_end = datetime.datetime.strptime(date + ' - ' + end, '%Y-%m-%d - %I:%M %p')
            dt_plus_one = date_time_start + datetime.timedelta(days=1)

            titles = item.find_all('div', {'class':'studies-activities-item'})
            title = ''
            for t in titles:
                if not title:
                    title = t.text
                elif t.text not in title:
                    title = title + '\n' + t.text

            h4 = item.find('h4', {'class':'meeting-card-committee-details-name'})
            title_link = h4.find('a')
            location = item.find('div', {'class':'meeting-location'})
            webcast = item.find('i', {'class':'icon-web-video-cast'})
            television = item.find('i', {'class':'icon-television'})
            speaker = item.find('i', {'class':'icon-speaker'})
            studies = item.find('div', {'class':'meeting-card-studiesactivities-title'})
            study = item.find('a', {'class':'current-study'})
            evidence = item.find('a', {'class':'btn-meeting-evidence'})
            minutes = item.find('a', {'class':'btn-meeting-minutes'})
            preview = item.find('div', {'class':'meeting-card-media-preview'})
            preview_src = preview.find('img')['src']
            try:
                embed = preview.find('button', {'class':'video-play-button'})['data-player-url']
            except:
                embed = None
            # print(date)
            # print(date)
            # print(iden)
            # print(acron.text)
            # print(timerange.text)
            print(title)
            # print(h4.text.strip())
            # print(title_link['href'])
            # print(location.text.strip())
            # if webcast:
            #     print(webcast)
            # else:
            #     print('no webcast')
            # if television:
            #     print(television)
            # else:
            #     print('no television')
            # if speaker:
            #     print(speaker)
            # else:
            #     print('no speaker')
            # print(studies.text)
            # print(study['href'])
            # try:
            #     print(evidence['href'])
            # except:
            #     print('no evidence')
            # try:
            #     print(minutes['href'])
            # except:
            #     print('no mins')
            # print(preview_src)
            # print(embed)
            com_title = h4.text.strip()
            a = com_title.find(' (')
            com_title = com_title[:a]
            # print(com_title) 

            try:
                committee = Committee.objects.filter(code=acron.text, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber)[0]
            except:
                committee = Committee(code=acron.text, Title=com_title, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber)
                committee.save()
                committee.create_post()
            try:
                com = CommitteeMeeting.objects.filter(committee=committee, code=acron.text, date_time_start__range=[datetime.datetime.strftime(date_time_start, '%Y-%m-%d'), datetime.datetime.strftime(dt_plus_one, '%Y-%m-%d')])[0]
                print('com found')
                # print(com)
            except Exception as e:
                com = CommitteeMeeting(code=acron.text, committee=committee, date_time_start=date_time_start, Organization='House', ParliamentNumber=committee.ParliamentNumber, SessionNumber=committee.SessionNumber)
                # com.Publication_date_time = datetime.datetime.strptime('2022-10-31', '%Y-%m-%d')
                com.save()
                com.create_post()
                print('com created')
                # print(str(e))
            # dt = timerange.text
            # a = dt.find(' - ')
            # start = dt[:a].replace('.','')
            # print('start', start)
            # b = dt[a:].find(' (')
            # end = dt[a+3:a+b].replace('.', '')
            if 'Bill' in title:
                a = title.find('Bill')+len('Bill ')
                if ', ' in title:
                    b = title[a:].find(',')
                    code = title[a:a+b]
                else:
                    code = title[a:]
                try:
                    bill = Bill.objects.filter(NumberCode=code)[0]
                    com.bill = bill
                    print('BIll', bill)
                except Exception as e:
                    print(str(e))
            com.date_time_start = date_time_start
            com.date_time_end = date_time_end
            print(com.date_time_start)
            print(com.date_time_end)
            com.ItemId = iden
            com.Title = title
            # com.Organization = h4.text.strip()
            com.timeRange = timerange.text
            com.location = location.text.strip()
            # print('https://www.ourcommons.ca' + title_link['href'])
            com.govURL = 'https://www.ourcommons.ca' + title_link['href']
            com.studies = 'https://www.ourcommons.ca' + study['href']
            if evidence:
                com.evidence = evidence['href']
            if minutes:
                com.minutes = minutes['href']
            com.previewURL = 'https://www.ourcommons.ca' + preview_src
            if webcast or television or speaker:
                x = 'http://www.ourcommons.ca/embed/en/m/%s?ml=en&vt=watch&autoplay=true' %(com.ItemId)
                time.sleep(1)
                r = requests.get(x, verify=False)
                com.embedURL = r.url
            com.save()
            print('saved')
            # r = requests.get('https://www.ourcommons.ca' + title_link['href'])
            # soup = BeautifulSoup(r.content, 'html.parser')
            # chair = soup.find('span', {'class':'committee-member-card'})
            # a = chair.find('a')['href']
            # # print('chaired by')
            # print(a)
            # if a.startswith('//'):
            #     a = a[2:]
            # print(a)
            # print('should be:')
            # print('https://www.ourcommons.ca/Members/en/marc-garneau(10524)')
            # span = chair.find('span', {'class':'member-info'})
            # first_name = span.find('span', {'class':'first-name'}).text
            # last_name = span.find('span', {'class':'last-name'}).text
            # print(first_name, last_name)
            # try:
            #     p = Person.objects.filter(gov_profile_page=a)
                
            #     # p = r.person
            # except Exception as e:
            #     print(str(e))
            #     try:
            #         p = Person.objects.filter(first_name=first_name, last_name=last_name)[0]
            #     except Exception as e:
            #         print(str(e))
            #         p = None
            # print(p)
            # print(p.gov_profile_page)
            # print(p.gov_iden)
            # com_title = com.Organization
            # a = com_title.find(' (')
            # com_title = com_title[:a]
            # print('--%s--' %(com_title))
            try:
                if not committee.chair:
                    r = Role.objects.filter(group=com_title, current=True, affiliation='Chair')[0]
                    if r.person:
                        committee.chair = r
                    committee.save()
            except Exception as e:
                print(str(e))
                # try:
                #     r = Role.objects.filter(group=com_title)
                #     for i in r:
                #         print(i.affiliation)
                # except Exception as e:
                #     print(str(e))
            print('-------------------')
            # break
    except Exception as e:
        print(str(e))
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()

def get_house_committee_work(value):   
    print('--------------------house committee work')
    def go(url):
        r = requests.get(url, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        table = soup.find('table', {'class':'allcommittees-studiestable'})
        tbody = table.find('tbody')
        trs = tbody.find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            code = tds[0].find('a').text.strip()
            print('---',code,'----')
            activity = tds[1].text.strip()
            print(activity)
            event = tds[2]
            try:
                a = 'https:' + event.find('a')['href']
            except:
                a = None
            event = re.sub(' +', ' ', event.text.strip())
            # print(event)
            # print(a)
            date = tds[3].text.strip()
            print(date)
            dt = datetime.datetime.strptime(date, '%A, %B %d, %Y')
            try:
                agendaItem = AgendaItem.objects.filter(date_time=dt, text='Government Orders')[0]
                # now = datetime.datetime.now()
                dt = dt.replace(hour=agendaItem.hour, minute=agendaItem.minute)
            except:
                pass
            # com = Committee.objects.filter(code=com)[0]
            print(dt)
            parl = Parliament.objects.filter(start_date__lte=dt, country='Canada', organization='Federal')[0]
            # print(parl)
            try:
                comMeeting = CommitteeMeeting.objects.filter(code=code, Title=activity, event=event)[0]
                # comItem = CommitteeItem.objects.filter(committeeCode=com, eventTitle=event, Item_date_time__year=dt.year, Item_date_time__month=dt.month, Item_date_time__day=dt.day)[0]
                print('meeting found')
            except:
                print('creating meeting')
                if code != 'SSRS':
                    print(code)
                    com = Committee.objects.filter(code=code, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber)[0]
                    comMeeting = CommitteeMeeting(Organization='House', committee=com, code=code, Title=activity, event=event, date_time_start=dt, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber)
                    if 'Bill' in activity:
                        print('bill:')
                        x = activity.find('Bill')+len('Bill ')
                        # print(x)
                        if ',' in activity[x:]:
                            y = activity[x:].find(',')
                            z = activity[x:x+y]   
                        elif '-' in activity[x:]:
                            y = activity[x:].find('-')
                            if ' ' in activity[x+y:]:
                                w = activity[x+y:].find(' ')
                                z = activity[x+y-1:x+y+w]   
                            else:
                                z = activity[x+y-1:]   
                        print(z)
                        bill = Bill.objects.filter(NumberCode=z, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber)[0]
                        comMeeting.bill = bill
                        print(bill)
                    if a:
                        # url = 'https://www.ourcommons.ca/DocumentViewer/en/44-1/HUMA/report-7/'
                        print(a)
                        time.sleep(1)
                        r = requests.get(a, verify=False)
                        soup = BeautifulSoup(r.content, 'html.parser')
                        try:
                            btn_toc = soup.find('a', {'class':'btn-toc'})['href']
                            print('TOC found')
                            r = requests.get('https://www.ourcommons.ca' + btn_toc, verify=False)
                            soup = BeautifulSoup(r.content, 'html.parser')
                            try:
                                sum_link = soup.find("a", string="LIST OF RECOMMENDATIONS")['href']
                            except:
                                sum_link = soup.find("a", string="SUMMARY")['href']
                            # print(sum_link)
                            comMeeting.reportLink = 'https://www.ourcommons.ca' + sum_link
                            r = requests.get(comMeeting.reportLink, verify=False)
                            soup = BeautifulSoup(r.content, 'html.parser')
                            div = soup.find('div', {'class':'WordSection1'})
                            paras = div.find_all('p')
                            content = ''
                            for p in paras:
                                if str(p) != '<p> </p>':
                                    # content = content + re.sub(' +', ' ', p.text.strip()) + '\n\n'
                                    content = content + str(p)
                            # # print('-----')
                            # # print(content.strip())
                            # # print('------')
                            comMeeting.report = content.strip()
                        except Exception as e:
                            print(str(e))
                            comMeeting.reportLink = a
                            # body = soup.find('div', {'class':'report-body'})
                            tables = soup.find_all('table')
                            content = ''
                            paragraph = ''
                            paragraph2 = ''
                            # td = tables[0].find('td')
                            for table in tables:
                                content = content + str(table)
                            #     if re.sub(' +', ' ', table.text.strip()) not in content:
                            #         content = content + re.sub(' +', ' ', table.text.strip()) + '\n\n'
                            #         paras = table.find_all('p')
                            #         for p in paras:
                            #             paragraph = paragraph + p.text
                            #             paragraph2 = paragraph2 + re.sub(' +', ' ', p.text.strip()) + '\n\n'
                            # content = content.replace(paragraph, '')
                            # report = content + '\n\n' + paragraph2
                            # # print('------')
                            # # print(report)
                            # # print('------')
                            if '<' in content and '>' in content:
                                x = content.find('>')
                                content = content[:x] + 'style="font-size:100%;"' + content[x:]
                            comMeeting.report = content
                    comMeeting.save()
                    comMeeting.create_post()
                    print('saved')
                time.sleep(3)
            print('-----------')
    if value == 'latest':
        # url = 'https://www.ourcommons.ca/Committees/en/Work?refineByEvents=&pageNumber=1&refineByCommittees='
        url = 'https://www.ourcommons.ca/Committees/en/Work?show=allwork&parl=44&ses=1&refineByEvents=Creation,ReportPresented,ReportGovernmentResponse,ReportConcurred,ReportNegatived,ReportWithdrawn&pageNumber=1&pageSize=20'
        go(url)
    elif value == 'session':
        url = 'https://www.ourcommons.ca/Committees/en/Work?parl=44&ses=1&refineByCommittees=&refineByCategories=&refineByEvents=Creation,ReportPresented,ReportGovernmentResponse,ReportConcurred,ReportNegatived&sortBySelected=LatestEvents&show=allwork&pageNumber=1&pageSize=0'
        # url = 'https://www.ourcommons.ca/Committees/en/Work?show=allwork&parl=44&ses=1&refineByEvents=ReportGovernmentResponse&pageNumber=1'
        go(url)
    elif value == 'all':
        parls = ['44', '43', '42', '41', '40', '39', '38', '37']
        for parl in parls:
            print('---------------------------------')
            print(parl)
            print('--------------------------------')
            time.slee(3)
            url = 'https://www.ourcommons.ca/Committees/en/Work?parl=%s&ses=0&refineByCommittees=&refineByCategories=&refineByEvents=Creation,ReportPresented,ReportGovernmentResponse,ReportConcurred,ReportNegatived&sortBySelected=LatestEvents&show=allwork&pageNumber=1&pageSize=0' %(parl)
            go(url)
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()


def get_all_house_motions():
    print('-----get all house motions')
    sessions = ['44-1', '43-2', '43-1', '42-1', '41-2', '41-1', '40-3', '40-2', '40-1', '39-2','39-1','38-1']
    sessions = ['39-1','38-1']
    # sessions = ['44-1']
    for s in sessions:
        print(s)
        url = 'https://www.ourcommons.ca/members/en/votes/xml?parlSession=%s' %(s)
        r = requests.get(url, verify=False)
        root = ET.fromstring(r.content)
        motions = root.findall('Vote')
        # count = 0
        for motion in motions:
            m = add_motion(motion)
            print('-----------')
        time.sleep(2)

def add_motion(motion, shareData, func):
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    # count += 1
    ParliamentNumber = motion.find('ParliamentNumber').text
    SessionNumber = motion.find('SessionNumber').text
    
    gov, govU, govData, gov_is_new = get_model_and_update('Government', Country_obj=country, gov_level='Federal', GovernmentNumber=ParliamentNumber, SessionNumber=SessionNumber, Region_obj=country)
    if gov_is_new:
        shareData.append(gov.end_previous(func))
        gov, govU, govData, gov_is_new, shareData = save_and_return(gov, govU, govData, gov_is_new, shareData, func)

    DecisionEventDateTime = motion.find('DecisionEventDateTime').text
    # date_time = datetime.datetime.strptime(motion.find('DecisionEventDateTime').text, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
    date_time = datetime.datetime.fromisoformat(DecisionEventDateTime).replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
    DecisionDivisionNumber = motion.find('DecisionDivisionNumber').text
    DecisionDivisionSubject = motion.find('DecisionDivisionSubject').text
    DecisionResultName = motion.find('DecisionResultName').text
    DecisionDivisionNumberOfYeas = motion.find('DecisionDivisionNumberOfYeas').text
    DecisionDivisionNumberOfNays = motion.find('DecisionDivisionNumberOfNays').text
    DecisionDivisionNumberOfPaired = motion.find('DecisionDivisionNumberOfPaired').text
    DecisionDivisionDocumentTypeName = motion.find('DecisionDivisionDocumentTypeName').text
    DecisionDivisionDocumentTypeId = motion.find('DecisionDivisionDocumentTypeId').text
    BillNumberCode = motion.find('BillNumberCode').text
    # print(DecisionDivisionNumber)
    print('BillNumberCode', BillNumberCode)
    print('date_time', date_time)
    # print(DecisionDivisionSubject)
    print(DecisionDivisionNumber)
    try:
        motion, motionU, motionData, motion_is_new = get_model_and_update('Motion', VoteNumber=DecisionDivisionNumber, Country_obj=country, Government_obj=gov, Region_obj=country)
        # m = Motion.objects.filter(ParliamentNumber=ParliamentNumber, SessionNumber=SessionNumber, vote_number=DecisionDivisionNumber)[0]
        print('motion found')
        if motion_is_new or motionData['TotalVotes'] == 0:
            print('rerunning')
            fail
        return None, shareData
    except:
        time.sleep(2)
        # try:
        #     m = Motion.objects.filter(ParliamentNumber=ParliamentNumber, SessionNumber=SessionNumber, vote_number=DecisionDivisionNumber)[0]
        # except:
        #     m = Motion(ParliamentNumber=ParliamentNumber, SessionNumber=SessionNumber, vote_number=DecisionDivisionNumber)
        motion.DateTime = date_time
        motion.Yeas = DecisionDivisionNumberOfYeas
        motion.Nays = DecisionDivisionNumberOfNays
        motion.Pairs = DecisionDivisionNumberOfPaired
        motion.DecisionDivisionDocumentTypeName = DecisionDivisionDocumentTypeName
        motion.DecisionDivisionDocumentTypeId = DecisionDivisionDocumentTypeId
        motion.Result = DecisionResultName
        motion.Subject = DecisionDivisionSubject
        motion.billCode = BillNumberCode
        motion.chamber = 'House'
        motion.is_offical = True
        try:
            # b = Bill.objects.filter(ParliamentNumber=ParliamentNumber, SessionNumber=SessionNumber, NumberCode=BillNumberCode)[0]
            # m.bill = b
            bill = Bill.objects.filter(NumberCode=BillNumberCode, Government_obj=gov, Country_obj=country, Region_obj=country)[0]
            motion.Bill_obj = bill
            print(bill)
        except Exception as e:
            print(str(e))
            bill = None
            # time.sleep(10)
        vote_url = 'https://www.ourcommons.ca/members/en/votes/%s/%s/%s' %(ParliamentNumber, SessionNumber, DecisionDivisionNumber)
        print(vote_url)
        # vote_url = 'https://www.ourcommons.ca/members/en/votes/44/1/210'
        r = requests.get(vote_url, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        # print(soup)
        # print(sponsor_link)
        try:
            sponsor_link = soup.find('a', {'class':'ce-mip-mp-tile'})['href']
            s = Person.objects.filter(GovProfilePage__icontains=sponsor_link)[0]
            motion.Sponsor_obj = s
        except:
            pass
        # sub = soup.find('div', {'id':'mip-vote-desc'}).text
        # print(sub)
        text = str(soup.find('div', {'id':'mip-vote-text-collapsible-text'}))
        # print(text)
        motion.MotionText = text
        motion, motionU, motionData, motion_is_new, shareData = save_and_return(motion, motionU, motionData, motion_is_new, shareData, func)
        # print('1')
        # block = soup.find('div', {'class':'ce-mip-vote-block'})
        # ass = block.find_all('a')
        # for a in ass:
        #     if 'View this Bill' in a.text: 
        #         print(a['href'])
        # m.save()
        # print('motion saved')
        # m.create_post()

        vote_xml = 'https://www.ourcommons.ca/members/en/votes/%s/%s/%s/xml' %(ParliamentNumber, SessionNumber, DecisionDivisionNumber)
        print(vote_xml)
        r = requests.get(vote_xml, verify=False)
        root = ET.fromstring(r.content)
        votes = root.findall('VoteParticipant')
        vote_count = 0
        print('run votes')
        for vote in votes:
            vote_count += 1
            ParliamentNumber = vote.find('ParliamentNumber').text
            SessionNumber = vote.find('SessionNumber').text
            DecisionEventDateTime = vote.find('DecisionEventDateTime').text
            '2022-11-03T15:30:00'
            DecisionDivisionNumber = vote.find('DecisionDivisionNumber').text
            PersonShortSalutation = vote.find('PersonShortSalutation').text
            ConstituencyName = vote.find('ConstituencyName').text
            VoteValueName = vote.find('VoteValueName').text
            PersonOfficialFirstName = vote.find('PersonOfficialFirstName').text
            PersonOfficialLastName = vote.find('PersonOfficialLastName').text
            ConstituencyProvinceTerritoryName = vote.find('ConstituencyProvinceTerritoryName').text
            CaucusShortName = vote.find('CaucusShortName').text
            IsVoteYea = vote.find('IsVoteYea').text
            IsVoteNay = vote.find('IsVoteNay').text
            IsVotePaired = vote.find('IsVotePaired').text
            DecisionResultName = vote.find('DecisionResultName').text
            PersonId = vote.find('PersonId').text
            # print(PersonOfficialLastName)
            # print(VoteValueName)
            vote, voteU, voteData, vote_is_new = get_model_and_update('Vote', Motion_obj=motion, vote_number=DecisionDivisionNumber, PersonId=PersonId, Country_obj=country, Government_obj=gov, Region_obj=country)
            # try:
            #     v = Vote.objects.filter(ParliamentNumber=ParliamentNumber, SessionNumber=SessionNumber, VoteNumber=DecisionDivisionNumber, PersonId=PersonId)[0]
            # except:
            #     v = Vote(ParliamentNumber=ParliamentNumber, SessionNumber=SessionNumber, vote_number=DecisionDivisionNumber, PersonId=PersonId)
            try:
                p = Person.objects.filter(GovIden=PersonId, Country_obj=country)[0]
                vote.Person_obj = p
            except:
                p = None
            print('p,bill', p, bill)
            if p and bill:
                try:
                    post = Post.objects.filter(Bill_obj=bill)[0]
                    print()
                    print('create Interation')
                    interaction, interactionU, interactionData, interaction_is_new = get_model_and_update('Interaction', Person_obj=p, Post_obj=post)
                    interaction, interactionU, interactionData, interaction_is_new, shareData = save_and_return(interaction, interactionU, interactionData, interaction_is_new, shareData, func)
                    print('done interaction')
                    # if interaction_is_new:
                    #     interaction.calculate_vote(VoteValueName, True)
                    # else:
                    #     interaction.calculate_vote(VoteValueName, False)

                    # try:
                    #     interaction = Interaction.objects.filter(post=post, person=p)[0]
                    #     reaction.calculate_vote(VoteValueName, True)
                    # except:
                    #     reaction = Interaction(post=post, person=p)
                    #     reaction.save()
                    #     reaction.calculate_vote(VoteValueName, False)
                except Exception as e:
                    print(str(e))
                    pass
            # try:
            #     r = Role.objects.filter(person=p, position='Member of Parliament', current=True)[0]
            #     r.attendanceCount += 1
            #     r.attendancePercent = int((r.attendanceCount/total_motions)*100)
            #     r.save()
            # except:
            #     pass
            # vote.person = p
            # vote.
            vote.PersonShortSalutation = PersonShortSalutation
            vote.ConstituencyName = ConstituencyName
            vote.VoteValueName = VoteValueName
            # vote.PersonOfficialFirstName = PersonOfficialFirstName
            # vote.PersonOfficialLastName = PersonOfficialLastName
            vote.PersonOfficialFullName = PersonOfficialFirstName + ' ' + PersonOfficialLastName
            vote.ConstituencyProvinceTerritoryName = ConstituencyProvinceTerritoryName
            vote.CaucusShortName = CaucusShortName
            vote.IsVoteYea = IsVoteYea
            vote.IsVoteNay = IsVoteNay
            vote.IsVotePaired = IsVotePaired
            vote.DecisionResultName = DecisionResultName
            # print('DecisionEventDateTime', DecisionEventDateTime)
            vote.DateTime = date_time
            # v.save()
            # v.create_post()
            # print('')
            vote, voteU, voteData, vote_is_new, shareData = save_and_return(vote, voteU, voteData, vote_is_new, shareData, func)
            # break
        motion.TotalVotes = vote_count
        motionData['TotalVotes'] = vote_count
        motion, motionU, motionData, motion_is_new, shareData = save_and_return(motion, motionU, motionData, motion_is_new, shareData, func)
        # m.save()
        print('done', vote_count)
        # print(m.total_votes)
        # print(count)
        print('')
        return motion, gov, shareData


    # if count >= 5:
    #     break

def get_house_expenses():
    def run(url):
        r = requests.get(url, verify=False)
        soup = BeautifulSoup(r.content, 'html.parser')
        container = soup.find('div', {'class':'data-table-container'})
        trs = container.find_all('tr')
        for tr in trs:
            if tr != trs[0]:
                tds = tr.find_all('td')
                # print(tds[0].text.strip())
                # print(tds[1].text.strip())
                # print(tds[3].text.strip())
                # print(tds[4].text.strip())
                # print(tds[5].text.strip())
                # print(tds[6].text.strip())
                name = tds[0].text.strip()
                a = name.find(', ')
                last_name = name[:a]
                first_name = name[a+2:].replace('Hon. ', '').replace('Right ', '')
                print(first_name, last_name)
                con = tds[1].text.strip()
                # print(con)
                try:
                    riding = Riding.objects.filter(Q(name=con)|Q(alt_name=con.replace('—','')))[0]
                    r = Role.objects.filter(person__last_name=last_name, person__first_name=first_name, position='Member of Parliament', current=True, riding=riding)[0]
                    total = float(tds[3].text.strip().replace('$', '').replace(',','').replace('(','').replace(')','')) + float(tds[4].text.strip().replace('$', '').replace(',','').replace('(','').replace(')','')) + float(tds[5].text.strip().replace('$', '').replace(',','').replace('(','').replace(')','')) + float(tds[6].text.strip().replace('$', '').replace(',','').replace('(','').replace(')','')) 
                    print(total)
                    r.quarterlyExpenseReport = total
                    r.save()
                except Exception as e:
                    print(str(e))
                print('')
    try:
        url = 'https://www.ourcommons.ca/ProactiveDisclosure/en/members/%s/4' %(datetime.datetime.now().year)
        run(url)
    except Exception as e:
        print(str(e))
        try:
            url = 'https://www.ourcommons.ca/ProactiveDisclosure/en/members/%s/3' %(datetime.datetime.now().year)
            run(url)
        except Exception as e:
            print(str(e))
            try:
                url = 'https://www.ourcommons.ca/ProactiveDisclosure/en/members/%s/2' %(datetime.datetime.now().year)
                run(url)
            except Exception as e:
                print(str(e))
                try:
                    url = 'https://www.ourcommons.ca/ProactiveDisclosure/en/members/%s/1' %(datetime.datetime.now().year)
                    run(url)
                except Exception as e:
                    print(str(e))
                    print('fail fail')
    
def add_senate_hansard(link, reprocess, func):
    print('add senate hansard')
    print(link)
    shareData = []
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    gov = Government.objects.filter(Country_obj=country, gov_level='Federal', Region_obj=country)[0]
    try:
        meetingU = Update.objects.filter(Meeting_obj__GovPage=link)[0]
        print(meetingU.Meeting_obj)
        meetingData = json.loads(meetingU.data)
        if reprocess or 'has_transcript' not in meetingData or meetingData['has_transcript'] == False:
            fail
    except:
        print('adding')
        # a = 'https://sencanada.ca/en\content\sen\chamber\441\debates\076db_2022-11-01-e'
        # a = 'https://sencanada.ca/en/content/sen/chamber/441/debates/076db_2022-11-01-e'
        r = requests.get(link)
        soup = BeautifulSoup(r.content, 'html.parser')
        portal = soup.find('div', {'id':'portal-middle'})
        hs = portal.find_all('h2')
        for h in hs:
            # print(h.text)
            nums = re.findall(r'\d+', h.text)
            Title = 'Volume %s, Issue %s' %(nums[2], nums[3])
            print(Title)
            break
        print('')
        content = soup.find('div', {'id':'content-viewer-document'})
        center = content.find('center')
        # print(center.text)
        h3 = center.find('h3')
        # print(h3)
        dtime = center.find_next_sibling().find_next_sibling().text
        # print(dtime)
        # 'The Senate met at 2 p.m., the Speaker in the chair.'
        dt = h3.text + dtime.replace('.','')
        print(dt)
        try:
            date_time = datetime.datetime.strptime(dt, '%A, %B %d, %YThe Senate met at %I %p, the Speaker in the chair').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
            date = date_time.replace(hour=0)
        except Exception as e:
            # print(dt)
            print(str(e))
            # fail
            div = soup.find('div', {'id':'portal-middle'})
            h2 = div.find_all('h2')[1]
            span = h2.find('span')
            print(h2.text.replace(span.text,''))
            date = datetime.datetime.strptime(h2.text.replace(span.text,''), '%A, %B %d, %Y').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
            date_time = date.replace(hour=14)
            # date_time = datetime.datetime.now()
        print('date_time', date_time)
        # try:
        #     A = Agenda.objects.filter(organization='Senate', date_time__gte=date, date_time__lt=date+datetime.timedelta(days=1))[0]
        # except:
        #     A = Agenda(organization='Senate', gov_level='Federal', date_time=date_time)
        #     A.save()
        # try:
        #     H = Hansard.objects.filter(Publication_date_time__gte=date, Publication_date_time__lt=date+datetime.timedelta(days=1), Organization='Senate')[0]
        #     print('hansard found')
        #     H.ParliamentNumber=nums[1]
        #     H.SessionNumber=nums[0]
        #     H.Title=Title
        #     H.gov_page = link
        #     H.agenda = A
        #     H.save()
        # except:
        #     H = Hansard(ParliamentNumber=nums[1], SessionNumber=nums[0], Title=Title, Publication_date_time=date_time, Organization='Senate', agenda=A)
        #     H.gov_page = link
        #     H.save() 
        #     H.create_post() 
        #     print('hansard created')
        try:
            meeting = Meeting.objects.filter(meeting_type='Debate', GovPage=link, DateTime__gte=date, DateTime__lt=date+datetime.timedelta(days=1), chamber='Senate', Government_obj=gov, Country_obj=country, Region_obj=country)[0]
            meeting, meetingU, meetingData, meeting_is_new = get_model_and_update('Meeting', obj=meeting)
        except:
            meeting, meetingU, meetingData, meeting_is_new = get_model_and_update('Meeting', meeting_type='Debate', GovPage=link, DateTime=date_time, Title=Title, chamber='Senate', Government_obj=gov, Country_obj=country, Region_obj=country)
            meeting, meetingU, meetingData, meeting_is_new, shareData = save_and_return(meeting, meetingU, meetingData, meeting_is_new, shareData, func)
        if 'Terms' in meetingData:
            meeting_terms = json.loads(meetingData['Terms'])
        else:
            meeting_terms = {}
        
        def get_text(nexth1, title_text, date_time, meeting_terms, num, shareData):
            print('get text')
            try:
                while nexth1.name == "h2" or nexth1.name == "p" or nexth1.name == 'blockquote' or nexth1.name == 'center' or nexth1.name == 'div':  
                    if nexth1.name == 'h2':
                        print()
                        print()
                        print(nexth1.text)
                        subtext = '%s' %(nexth1.text.strip())
                        next_div = nexth1.find_next_sibling()
                        # print(next_div.name)
                        statement = None
                        s_terms = []
                        senators = {}
                        blockquote = None
                        while next_div.name == "p" or next_div.name == 'blockquote':
                            # print(next_div.text)
                            # print('p')
                            try:
                                date_time = datetime.datetime.strptime(date_time.strftime('%Y-%m-%d') + '-' + next_div.text, '%Y-%m-%d-(%H%M)').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
                                print(date_time)
                            except Exception as e:
                                # print(str(e))
                                person = None
                                # statement = None
                                if next_div.name == 'p':
                                    try:
                                        bold = next_div.find('b')
                                        # print(bold.text)
                                        if 'Hon' in bold.text:
                                            print('---a')
                                            # print(bold.text)
                                            if statement:
                                                statement, statementU, statementData, statement_is_new, shareData = save_and_return(statement, statementU, statementData, statement_is_new, shareData, func)
                                                for term in s_terms:
                                                    statement = statement.add_term(term[0], term[1])
                                                    if not term[0] in meeting_terms:
                                                        meeting_terms[term[0]] = 1
                                                    else:
                                                        meeting_terms[term[0]] += 1
                                                s_terms = []
                                                for k in statement.keyword_array:
                                                    if not k in meeting_terms:
                                                        meeting_terms[k] = 1
                                                    else:
                                                        meeting_terms[k] += 1
                                            # print(str(next_div.text)[:50])
                                            a = None
                                            a = bold.text.find('(')
                                            name = bold.text[:a].replace('Hon. ', '').replace(':', '').replace('The', '').replace('the','')
                                            # print(name)
                                            if 'Speaker pro tempore' in name:
                                                name = 'Speaker pro tempore'
                                                last_name = name
                                                get_name_by = 'title'
                                            elif 'Speaker' in name:
                                                name = 'Speaker'
                                                last_name = name
                                                get_name_by = 'title'
                                            elif 'Senators' in name:
                                                name = name
                                                last_name = name
                                                get_name_by = 'None'
                                            else:
                                                name_split = name.split()
                                                first_name = name_split[0]
                                                last_name = name_split[-1]
                                                get_name_by = 'name'
                                            # print(name)
                                            if get_name_by == 'name':
                                                # person, personU, personData, person_is_new = get_model_and_update('Person', FirstName=first_name, LastName=last_name, Country_obj=country, Region_obj=country, chamber=chamber)
                                                try:
                                                    person = Person.objects.filter(Q(FirstName__icontains=first_name)&Q(LastName__icontains=last_name, Country_obj=country, Region_obj=country, chamber='Senate'))[0]
                                                except Exception as e:
                                                    # print(str(e))
                                                    person = None
                                            elif get_name_by == 'title':
                                                try:
                                                    # role, roleU, roleData, role_is_new = get_model_and_update('Role', Person_obj=person, Position='Senator', gov_level='Federal', Country_obj=country, Region_obj=country, chamber=chamber)
                                                    roleU = Update.objects.filter(Role_obj__Position='Senator', Role_obj__Title=name, data__icontains='"Current": true', Role_obj__gov_level='Federal', Country_obj=country)[0]
                                                    # role = Role.objects.filter(position='Senator', current=True, title=name)
                                                    person = roleU.Role_obj.Person_obj
                                                except Exception as e:
                                                    # print(str(e))
                                                    person = None
                                            else:
                                                person = None
                                            # print(name)
                                            # print(person)
                                            # try:
                                            #     if person:
                                            #         s = Statement.objects.filter(Person_obj=person, Meeting_obj=meeting, Content__icontains=str(next_div))[0]
                                            #         # print('found1')
                                            #     else:    
                                            #         s = Statement.objects.filter(Meeting_obj=meeting, Content__icontains=str(next_div))[0]
                                            #     # h.Content = ''
                                            #     statement, statementU, statementData, statement_is_new = get_model_and_update('Statement', obj=s)
                                            # except Exception as e:
                                                # print(str(e))
                                            # s = Statement(Meeting_obj=meeting, DateTime=date_time, chamber='Senate', Government_obj=gov, Country_obj=country, Region_obj=country)
                                            
                                            # s.save(share=False)
                                            statement, statementU, statementData, statement_is_new = get_model_and_update('Statement', new_model=True, Meeting_obj=meeting, DateTime=date_time, chamber='Senate', Government_obj=gov, Country_obj=country, Region_obj=country)
                                            # print('statement created')
                                            # print('statement_is_new', statement_is_new)
                                            # time.sleep(1)
                                            if person:
                                                statement.Person_obj = person
                                                # H.people.add(person)
                                                statement.PersonName = 'Hon. %s' %(person.FullName)
                                            else:
                                                statement.PersonName = name
                                            # print(h.id)
                                            # time.sleep(1)
                                            # h.hansardId = H.id
                                            senators[last_name] = person
                                            statement.Content = statement.Content + '\n' + str(next_div)
                                            string =  re.sub('<[^<]+?>', '', statement.Content)
                                            words = re.findall(r'\w+', string)
                                            statement.word_count = len(words)
                                            # if title_text and title_text != '':
                                            #     if not title_text in meeting_terms:
                                            #         meeting_terms[title_text] = 1
                                            #     else:
                                            #         meeting_terms[title_text] += 1
                                            #     # print(title_text)
                                            if subtext and subtext != '':
                                            #     if not subtext in meeting_terms:
                                            #         meeting_terms[subtext] = 1
                                            #     else:
                                            #         meeting_terms[subtext] += 1
                                                # print(subtext)
                                                if subtext[-4:] == 'Bill' or subtext[:7] == 'Bill to':
                                                    try:
                                                        b = subtext.replace(' Bill','').replace('Bill to ','').replace("’", "'")
                                                        # print(b)
                                                        bill = Bill.objects.filter(Government_obj=gov, Country_obj=country).filter(Q(LongTitle__icontains=b)|Q(Title__icontains=b)).filter(Q(chamber='Senate')|Q(chamber='House'))[0]
                                                        print(bill)
                                                        bill, billU, billData, bill_is_new = get_model_and_update('Bill', obj=bill)
                                                        LatestBillEventDateTime = datetime.datetime.fromisoformat(billData['LatestBillEventDateTime'])
                                                        if meeting.DateTime > LatestBillEventDateTime:
                                                            billData['LatestBillEventDateTime'] = datetime.datetime.isoformat(meeting.DateTime)
                                                            bill, billU, billData, bill_is_new, shareData = save_and_return(bill, billU, billData, bill_is_new, shareData, func)
                                
                                                        # if date_time:
                                                        #     try:
                                                        #         agendaTime = AgendaTime.objects.filter(agenda=A, date_time=date_time, gov_level=A.gov_level, organization=A.organization)[0]
                                                        #         input_time = False
                                                        #     except:
                                                        #         agendaTime = AgendaTime(agenda=A, date_time=date_time, gov_level=A.gov_level, organization=A.organization)
                                                        #         input_time = True
                                                        #         agendaTime.save()
                                                        #     # print(agendaTime)
                                                        # else:
                                                        #     agendaTime = None
                                                        # try:
                                                        #     agendaItem = AgendaItem.objects.filter(agenda=A, text=b)[0]
                                                        # except Exception as e:
                                                        #     # print(str(e))
                                                        #     agendaItem = AgendaItem(agenda=A, position=num, agendaTime=agendaTime, gov_level=A.gov_level, organization=A.organization)
                                                        #     agendaItem.text = b
                                                        #     if input_time:
                                                        #         agendaItem.date_time = date_time
                                                        # agendaItem.bill = bill
                                                        # agendaItem.save()
                                                        # print(agendaItem)
                                                        # agendaItem.agenda.bills.add(bill)
                                                        # agendaItem.agenda.save()
                                                        # h.save()
                                                        # h.add_term(subtext, bill)
                                                        # statement = statement.add_term(subtext, bill)
                                                        s_terms.append([subtext, bill])
                                                        # sozed.alert('%s-STEP TWO' %(bill.NumberCode), None)
                                                        # try:
                                                        #     bill.LatestBillEventDateTime = date_time
                                                        #     # print(bill.LatestBillEventDateTime)
                                                        #     bill.save()
                                                        #     bill.update_post_time()
                                                        # except Exception as e:
                                                        #     print('FailGetBIll-%s' %(str(e)))
                                                    except Exception as e:
                                                        print(str(e))
                                                        print('Bill not found')
                                                        # statement = statement.add_term(subtext, None)
                                                        s_terms.append([subtext, None])

                                                else:
                                                    # statement = statement.add_term(subtext, None)
                                                    s_terms.append([subtext, None])

                                            statement.OrderOfBusiness = title_text
                                            if blockquote:
                                                statement.SubjectOfBusiness = blockquote
                                            else:
                                                statement.SubjectOfBusiness = subtext
                                            # try:
                                            if title_text and title_text != '' and title_text not in statement.Terms_array:
                                                # h.Terms.append(title_text)
                                                # statement = statement.add_term(title_text, None)
                                                s_terms.append([title_text, None])
                                            if subtext and subtext != '' and subtext not in statement.Terms_array:
                                                # h.Terms.append(subtext)
                                                # done higher up
                                                pass
                                            if blockquote and blockquote not in statement.Terms_array:
                                                # h.Terms.append(blockquote)
                                                # statement = statement.add_term(blockquote, None)
                                                s_terms.append([blockquote, None])
                                            # except Exception as e:
                                            #     # print(str(e))
                                            #     h.Terms = []
                                            #     if title_text and title_text != '' and title_text not in h.Terms:
                                            #         h.Terms.append(title_text)
                                            #     if subtext and subtext != '' and subtext not in h.Terms:
                                            #         h.Terms.append(subtext)
                                            #     if blockquote and blockquote not in h.Terms:
                                            #         h.Terms.append(blockquote)
                                            # h.save()
                                            # h.create_post()
                                            # statement, statementU, statementData, statement_is_new, shareData = save_and_return(statement, statementU, statementData, statement_is_new, shareData)
                                            # for k in statement.keyword_array:
                                            #     if not k in meeting_terms:
                                            #         meeting_terms[k] = 1
                                            #     else:
                                            #         meeting_terms[k] += 1
                                        elif 'Senator' in bold.text:
                                            print('senator')
                                            if statement:
                                                statement, statementU, statementData, statement_is_new, shareData = save_and_return(statement, statementU, statementData, statement_is_new, shareData, func)
                                                for term in s_terms:
                                                    statement = statement.add_term(term[0], term[1])
                                                    if not term[0] in meeting_terms:
                                                        meeting_terms[term[0]] = 1
                                                    else:
                                                        meeting_terms[term[0]] += 1
                                                s_terms = []
                                                for k in statement.keyword_array:
                                                    if not k in meeting_terms:
                                                        meeting_terms[k] = 1
                                                    else:
                                                        meeting_terms[k] += 1
                                            last_name = bold.text.replace('Senator ', '').replace(':','').replace(' ','')
                                            person = senators[last_name]
                                            # print(person)
                                            # print(str(next_div.text)[:50])
                                            # if get_name_by == 'name':
                                            #     # person, personU, personData, person_is_new = get_model_and_update('Person', FirstName=first_name, LastName=last_name, Country_obj=country, Region_obj=country, chamber=chamber)
                                            #     try:
                                            #         person = Person.objects.filter(Q(FirstName__icontains=first_name)&Q(LastName__icontains=last_name, Country_obj=country, Region_obj=country, chamber='Senate'))[0]
                                            #     except Exception as e:
                                            #         # print(str(e))
                                            #         person = None
                                            # elif get_name_by == 'title':
                                            #     try:
                                            #         # role, roleU, roleData, role_is_new = get_model_and_update('Role', Person_obj=person, Position='Senator', gov_level='Federal', Country_obj=country, Region_obj=country, chamber=chamber)
                                            #         roleU = Update.objects.filter(Role_obj__Position='Senator', Role_obj__Title=name, data__icontains='"Current": true', Role_obj__gov_level='Federal', Country_obj=country)[0]
                                            #         # role = Role.objects.filter(position='Senator', current=True, title=name)
                                            #         person = roleU.Role_obj.Person_obj
                                            #     except Exception as e:
                                            #         # print(str(e))
                                            #         person = None
                                            # else:
                                            #     person = None


                                            # try:
                                            #     if person:
                                            #         s = Statement.objects.filter(Person_obj=person, Meeting_obj=meeting, Content__icontains=str(next_div))[0]
                                            #         # print('found1')
                                            #     else:    
                                            #         s = Statement.objects.filter(Meeting_obj=meeting, Content__icontains=str(next_div))[0]
                                            #     # h.Content = ''
                                            #     statement, statementU, statementData, statement_is_new = get_model_and_update('Statement', obj=s)
                                            # except Exception as e:
                                            #     # print(str(e))
                                            # s = Statement(Meeting_obj=meeting, DateTime=date_time, chamber='Senate', Government_obj=gov, Country_obj=country, Region_obj=country)
                                            
                                            # s.save(share=False)
                                            statement, statementU, statementData, statement_is_new = get_model_and_update('Statement', new_model=True, Meeting_obj=meeting, DateTime=date_time, chamber='Senate', Government_obj=gov, Country_obj=country, Region_obj=country)
                                            # print('h created')
                                            # print('statement created22')
                                            # print('statement_is_new', statement_is_new)
                                            # time.sleep(1)
                                            # s_terms = []
                                            if person:
                                                statement.Person_obj = person
                                                # H.people.add(person)
                                                statement.PersonName = 'Hon. %s' %(person.FullName)
                                            else:
                                                statement.PersonName = 'Senator %s' %(last_name)


                                            # try:
                                            #     if person:
                                            #         # print(person)
                                            #         h = HansardItem.objects.filter(person=person, hansard=H, Content__icontains=str(next_div))[0]
                                            #     else:
                                            #         h = HansardItem.objects.filter(hansard=H, Content__icontains=str(next_div))[0]
                                            #     # print('senator h found')
                                            #     h.Content = ''
                                            # except Exception as e:
                                            #     # print('senexcept11', str(e))
                                            #     h = HansardItem(person=person, hansard=H)
                                            #     if person:
                                            #         h.person = person
                                            #         h.person_name = 'Hon. %s' %(person.get_name())
                                            #         H.people.add(person)
                                            #     else:
                                            #         h.person_name = 'Hon. %s' %(person)
                                            statement.Content = statement.Content + '\n' + str(next_div)
                                            string =  re.sub('<[^<]+?>', '', statement.Content)
                                            words = re.findall(r'\w+', string)
                                            statement.word_count = len(words)
                                            # if title_text and title_text != '':
                                            #     if not title_text in meeting_terms:
                                            #         meeting_terms[title_text] = 1
                                            #     else:
                                            #         meeting_terms[title_text] += 1
                                            # if subtext and subtext != '':
                                            #     if not subtext in meeting_terms:
                                            #         meeting_terms[subtext] = 1
                                            #     else:
                                            #         meeting_terms[subtext] += 1
                                            statement.OrderOfBusiness = title_text
                                            if blockquote:
                                                statement.SubjectOfBusiness = blockquote
                                            else:
                                                statement.SubjectOfBusiness = subtext
                                            if not statement.Terms_array: 
                                                statement.Terms_array = []
                                            # try:
                                            if title_text and title_text != '' and title_text not in statement.Terms_array:
                                                # h.Terms.append(title_text)
                                                # statement = statement.add_term(title_text, None)
                                                s_terms.append([title_text, None])
                                            if subtext and subtext != '' and subtext not in statement.Terms_array:
                                                # h.Terms.append(subtext)
                                                # statement = statement.add_term(subtext, None)
                                                s_terms.append([subtext, None])
                                            if blockquote and blockquote not in statement.Terms_array:
                                                # h.Terms.append(blockquote)
                                                # statement = statement.add_term(blockquote, None)
                                                s_terms.append([blockquote, None])
                                            # except Exception as e:
                                            #     # print(str(e))
                                            #     h.Terms = []
                                            #     if title_text and title_text != '' and title_text not in h.Terms:
                                            #         h.Terms.append(title_text)
                                            #     if subtext and subtext != '' and subtext not in h.Terms:
                                            #         h.Terms.append(subtext)
                                            #     if blockquote and blockquote not in h.Terms:
                                            #         h.Terms.append(blockquote)
                                            # h.save()
                                            # h.create_post()
                                            # print('sen saved', h.id)
                                            # statement, statementU, statementData, statement_is_new, shareData = save_and_return(statement, statementU, statementData, statement_is_new, shareData)
                                            # for k in statement.keyword_array:
                                            #     if not k in meeting_terms:
                                            #         meeting_terms[k] = 1
                                            #     else:
                                            #         meeting_terms[k] += 1
                                    except Exception as e:
                                        # print('exception 1111', str(e))
                                        # print(str(next_div.text)[:50])
                                        try:
                                            statement.Content = statement.Content + '\n' + str(next_div)
                                            string =  re.sub('<[^<]+?>', '', statement.Content)
                                            words = re.findall(r'\w+', string)
                                            statement.word_count = len(words)
                                            # h.save()
                                            # print('saved')
                                            # statement, statementU, statementData, statement_is_new, shareData = save_and_return(statement, statementU, statementData, statement_is_new, shareData)
                                            # for k in statement.keyword_array:
                                            #     if not k in meeting_terms:
                                            #         meeting_terms[k] = 1
                                            #     else:
                                            #         meeting_terms[k] += 1
                                        except Exception as e:
                                            print('22222',str(e))
                                            # print(str(next_div.text)[:50])
                                            # time.sleep(5)
                                            # if person not senator
                                            if not statement:
                                            # try:
                                            #     s = Statement.objects.filter(Meeting_obj=meeting, Content__icontains=next_div)[0]
                                            # except Exception as e:
                                                # print(str(e))
                                                # s = Statement(Meeting_obj=meeting, DateTime=date_time, chamber='Senate', Government_obj=gov, Country_obj=country, Region_obj=country)
                                                statement, statementU, statementData, statement_is_new = get_model_and_update('Statement', new_model=True, Meeting_obj=meeting, DateTime=date_time, chamber='Senate', Government_obj=gov, Country_obj=country, Region_obj=country)
                                                # h = HansardItem(hansard=H)
                                                print('item created')
                                            statement.PersonName = None
                                            statement.Content = statement.Content + '\n' + str(next_div)
                                            string =  re.sub('<[^<]+?>', '', statement.Content)
                                            words = re.findall(r'\w+', string)
                                            statement.word_count = len(words)
                                                # s.save(share=False)
                                                # h.create_post()
                                    
                                else:
                                    blockquote = next_div.text.strip()
                                    # print(blockquote)
                            next_div = next_div.find_next_sibling()
                        # print(senators)
                        # print('----')
                        
                        # print('passed while P')
                        if statement:
                            statement, statementU, statementData, statement_is_new, shareData = save_and_return(statement, statementU, statementData, statement_is_new, shareData, func)
                            for term in s_terms:
                                statement = statement.add_term(term[0], term[1])
                                if not term[0] in meeting_terms:
                                    meeting_terms[term[0]] = 1
                                else:
                                    meeting_terms[term[0]] += 1
                            s_terms = []
                            for k in statement.keyword_array:
                                if not k in meeting_terms:
                                    meeting_terms[k] = 1
                                else:
                                    meeting_terms[k] += 1
                            statement = None
                        time.sleep(5)
                    nexth1 = nexth1.find_next_sibling()
                    # print('next', nexth1)
            except Exception as e:
                print(str(e))
            # print('---done get text')
            return date_time, meeting_terms, shareData
        # H_terms = {}
        precursors = h3.find_all_next('h2')
        num = 0
        for precursor in precursors:
            num += 1
            if not precursor.find_previous_sibling() or precursor.find_previous_sibling().name == 'h1':
                print('-----------break----------')
                break
            else:
                nexth1 = precursor.find_next_sibling()
                # print(nexth1)
                title_text = precursor.text.strip()
                # print(title_text)
                date_time, meeting_terms, shareData = get_text(nexth1, title_text, date_time, meeting_terms, num, shareData)
        h1s = content.find_all('h1')
        if h1s:
            num = 0
            for h1 in h1s:
                # print('-----------------')
                num += 1
                print(h1.text, '-----------', num)
                print('date', date_time)
                nexth1 = h1.find_next_sibling()
                title_text = h1.text.strip()
                # if date_time:
                #     try:
                #         agendaTime = AgendaTime.objects.filter(agenda=A, date_time=date_time, gov_level=A.gov_level, organization=A.organization)[0]
                #         input_time = False
                #     except:
                #         agendaTime = AgendaTime(agenda=A, date_time=date_time, gov_level=A.gov_level, organization=A.organization)
                #         input_time = True
                #         agendaTime.save()
                #     print(agendaTime)
                # else:
                #     agendaTime = None
                # try:
                #     agendaItem = AgendaItem.objects.filter(agenda=A, agendaTime=agendaTime, text=title_text)[0]
                # except Exception as e:
                #     # print(str(e))
                #     agendaItem = AgendaItem(agenda=A, position=num, agendaTime=agendaTime, gov_level=A.gov_level, organization=A.organization)
                #     agendaItem.text = title_text
                #     if input_time:
                #         agendaItem.date_time = date_time
                # agendaItem.position = num
                # agendaItem.save()
                # print(agendaItem, '----------', agendaItem.position)
                # H_terms[title_text] = 1
                date_time, meeting_terms, shareData = get_text(nexth1, title_text, date_time, meeting_terms, num, shareData)
        else:
            num = 0
            h2s = content.find_all('h2')
            for h2 in h2s:
                num += 1
                try:
                    # print(h2)
                    print('----------',h2.text)
                    title_text = h2.text.strip()
                    # try:
                    #     agendaItem = AgendaItem.objects.filter(agenda=A, agendaTime=agendaTime, text=title_text)[0]
                    # except Exception as e:
                    #     # print(str(e))
                    #     agendaItem = AgendaItem(agenda=A, position=num, agendaTime=agendaTime, gov_level=A.gov_level, organization=A.organization)
                    #     agendaItem.text = title_text
                    #     # if input_time:
                    #     #     agendaItem.date_time = date_time
                    #     agendaItem.save()
                    # print(agendaItem)
                    date_time, meeting_terms, shareData = get_text(h2, title_text, date_time, meeting_terms, num, shareData)
                    print('break')
                    break
                except Exception as e:
                    print('!!!!!!!!!!!!!!!!!!', str(e))
        # print('done all get text')
        # H.has_transcript = True
        # H.apply_terms(H_terms)
        meetingData['has_transcript'] = True
        meetingData = meeting.apply_terms(meeting_terms, meetingData)

        people = Statement.objects.filter(Meeting_obj=meeting)
        # print('people', people)
        # people = HansardItem.objects.filter(hansard=H)
        H_people = {}
        for p in people:
            try:
                if not p.Person_obj.id in H_people:
                    H_people[p.Person_obj.id] = 1
                else:
                    H_people[p.Person_obj.id] += 1
            except:
                pass
        H_people = sorted(H_people.items(), key=operator.itemgetter(1),reverse=True)
        H_people = dict(H_people)
        meetingData['People_json'] = json.dumps(H_people)
        # H.peopleText = json.dumps(H_people)
        # H.save()
        meetingData['completed_model'] = True
        meeting, meetingU, meetingData, meeting_is_new, shareData = save_and_return(meeting, meetingU, meetingData, meeting_is_new, shareData, func)
    return shareData, gov
        # sprenderize(H)

def add_senate_motion(tr, shareData, func):
    # num = 1
    country = Region.objects.filter(modelType='country', Name='Canada')[0]
    # gov, govU, govData, gov_is_new = get_model_and_update('Government', Country_obj=country, gov_level='Federal', GovernmentNumber=ParliamentNumber, SessionNumber=SessionNumber, Region_obj=country)
    gov = Government.objects.filter(Country_obj=country, gov_level='Federal', Region_obj=country)[0]
    td = tr.find_all('td')
    dt = td[0]['data-order']
    # print(dt)
    date_time = datetime.datetime.strptime(dt[:19], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
    # print(date_time)
    link = 'https://sencanada.ca' + td[1].find('a')['href']
    # print(link)
    # 'https://sencanada.ca/en/in-the-chamber/votes/details/593588/44-1'
    a = link.find('/details/')+len('/details/')
    b = link[a:].find('/')
    motion_iden = link[a:a+b]
    text = td[1]['data-order']
    print(text)
    # print('')
    try:
        bill_link = td[2].find('a')['href']
        print(bill_link)
    except Exception as e:
        print(str(e))
        # print('no bill')
    # print('')
    try: 
        motion, motionU, motionData, motion_is_new = get_model_and_update('Motion', GovUrl=link, Country_obj=country, Government_obj=gov, Region_obj=country)
        # m = Motion.objects.filter(gov_url=link)[0]
        print('motion found')
        if motion_is_new or motionData['TotalVotes'] == 0:
            print('rerunning')
            fail
        return None, shareData
    except:
        try:
            billId = bill_link[bill_link.find('billId=')+len('billId='):]
            bill = Bill.objects.filter(GovIden=billId, Government_obj=gov, Country_obj=country, Region_obj=country)[0]
        except Exception as e:
            print(str(e))
            bill = None
        # m = Motion(gov_url=link, date_time=date_time, bill=bill)
        motion.DateTime = date_time
        if bill:
            motion.Bill_obj = bill
            motion.billCode = bill.NumberCode
        # m.ParliamentNumber = 44
        # m.SessionNumber = 1
        motion.chamber = 'Senate'
        motion.VoteNumber = motion_iden
        # if bill:
        motion.Subject = text
        # print(text)
        # m.save()
        # m.create_post()
        r = requests.get(motion.GovUrl)
        soup = BeautifulSoup(r.content, 'html.parser')
        # print(soup)
        div = soup.find('div', {'class':'sc-vote-details-summary-table'})
        col = div.find_all('div', {'class':'sc-vote-details-summary-table-col'})
        yeas = col[0].find_all('div', {'class':'sc-vote-details-summary-table-col-cell'})[1].text
        # print(yeas)
        motion.Yeas = int(yeas)
        nays = col[1].find_all('div', {'class':'sc-vote-details-summary-table-col-cell'})[1].text
        # print(nays)
        motion.Nays = int(nays)
        abs = col[2].find_all('div', {'class':'sc-vote-details-summary-table-col-cell'})[1].text
        # print(abs)
        motion.Absentations = int(abs)
        totals = col[3].find_all('div', {'class':'sc-vote-details-summary-table-col-cell'})[1].text
        # print(totals)
        motion.TotalVotes = int(totals)
        result = col[4].find_all('div', {'class':'sc-vote-details-summary-table-col-cell-tall'})[0].text
        # print(result)
        motion.Result = result
        # print('')
        # m.save()
        motion, motionU, motionData, motion_is_new, shareData = save_and_return(motion, motionU, motionData, motion_is_new, shareData, func)

        table = soup.find('div',{'class':'table-responsive'})
        tbody = table.find('tbody')
        trs = tbody.find_all('tr')
        vote_count = 0
        for tr in trs:
            vote_count += 1
            td = tr.find_all('td')
            a = td[0].find('a')
            person_link = a['href']
            # person_name_unstripped = a.text
            person_name = a.text.strip()
            print(person_name)
            a = person_name.find(', ')
            last_name = person_name[:a]
            first_name = person_name[a+2:]
            a = person_link.find('/senator/')+len('/senator/')
            b = person_link[a:].find('/')
            iden = person_link[a:a+b]
            # print(iden)

            
            try:
                # person, personU, personData, person_is_new = get_model_and_update('Person', )
                person = Person.objects.filter(GovIden=iden)[0]
                # v.person = p
            except Exception as e:
                # print(str(e))
                try:
                    roleUpdate = Update.objects.filter(Role_obj__Position='Senator', Role_obj__Person_obj__FirstName__icontains=first_name, Role_obj__Person_obj__LastName__icontains=last_name, data__icontains='"Current": true')[0]
                    # r = Role.objects.filter(Position='Senator', Person_obj__FirstName__icontains=first_name, Person_obj__LastName__icontains=last_name)[0]
                    person, personU, personData, person_is_new = get_model_and_update('Person', obj=roleUpdate.Role_obj.Person_obj)
                    if not person.GovIden:
                        person.GovIden = iden
                        personData['GovIden'] = iden
                        person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)

                except Exception as e:
                    print(str(e))
                    person, personU, personData, person_is_new = get_model_and_update('Person', FirstName=first_name, LastName=last_name, Country_obj=country, Region_obj=country)
                    person, personU, personData, person_is_new, shareData = save_and_return(person, personU, personData, person_is_new, shareData, func)



            vote, voteU, voteData, vote_is_new = get_model_and_update('Vote', Motion_obj=motion, Person_obj=person, Country_obj=country, Government_obj=gov, Region_obj=country)
            
            
            # try:
            #     v = Vote.objects.filter(motion=m, PersonOfficialFullName=person_name)[0]
            #     # v.PersonOfficialFullName = person_name
            # except:
            #     v = Vote(motion=m, PersonOfficialFullName=person_name)
            #     try:
            #         p = Person.objects.filter(gov_iden=iden)[0]
            #         v.person = p
            #     except Exception as e:
            #         print(str(e))
            #         try:
            #             r = Role.objects.filter(position='Senator', person__first_name__icontains=first_name, person__last_name__icontains=last_name)[0]
            #             if not r.person.gov_iden:
            #                 r.person.gov_iden = iden
            #                 r.person.save()
            #             v.person = r.person
            #         except Exception as e:
            #             print(str(e))
            if td[3]['data-order'] == 'aaa':
                # print('yea')
                vote.IsVoteYea = 'True'
                vote.VoteValueName = 'Yea'
            if td[4]['data-order'] == 'aaa':
                # print('nay')
                vote.IsVoteNay = 'True'
                vote.VoteValueName = 'Nay'
            if td[5]['data-order'] == 'aaa':
                # print('absentation')
                vote.IsVoteAbsentation = 'True'
                vote.VoteValueName = 'Absentation'
            # v.save() 
            vote.DateTime = date_time
            if person and bill:
                try:
                    post = Post.objects.filter(Bill_obj=bill)[0]
                    interaction, interactionU, interactionData, interaction_is_new = get_model_and_update('Interaction', Person_obj=person, Post_obj=post)
                    interaction, interactionU, interactionData, interaction_is_new, shareData = save_and_return(interaction, interactionU, interactionData, interaction_is_new, shareData, func)
                    print('done interaction')
                    # if interaction_is_new:
                    #     interaction.calculate_vote(VoteValueName, True)
                    # else:
                    #     interaction.calculate_vote(VoteValueName, False)
                    # try:
                    #     reaction = Reaction.objects.filter(Post_obj=post, Person_obj=person)[0]
                    #     reaction.calculate_vote(v.VoteValueName, True)
                    # except:
                    #     reaction = Reaction(post=post, person=v.person)
                    #     reaction.save()
                    #     reaction.calculate_vote(v.VoteValueName, False)
                except Exception as e:
                    print(str(e))
                    pass   
            vote, voteU, voteData, vote_is_new, shareData = save_and_return(vote, voteU, voteData, vote_is_new, shareData, func)
            
        time.sleep(2)
    motion.TotalVotes = vote_count
    motionData['TotalVotes'] = vote_count
    motion, motionU, motionData, motion_is_new, shareData = save_and_return(motion, motionU, motionData, motion_is_new, shareData, func)
    print('done')
    return gov, shareData

def get_senate_committee_transcript(committeeMeeting):
    print('--------getting transcript------------')
    print(committeeMeeting.transcriptURL)
    time.sleep(3)
    r = requests.get(committeeMeeting.transcriptURL)
    soup = BeautifulSoup(r.content, 'html.parser')
    ps = soup.find_all('p')
    speakers = {}
    # currentChair = None
    for p in ps:
        # print('-----------------')
        # print(p.text)
        # print(p['class'])
        samePerson = False
        try:
            if 'center' in p['class']:
                print('has center class')
        except:
            # print('go')
            bold = p.find('b')
            if bold:
                div = bold
                # print('----New speaker----')
                # print(bold)
                title = bold.text
                # if ', ' in bold.text and 'Hon.' in bold.text or ', ' in bold.text and 'Mr.' in bold.text or ', ' in bold.text and 'Mrs.' in bold.text or ', ' in bold.text and 'Ms.' in bold.text:
                # if ', ' in bold.text and len(bold.text) > 20:
                if ', ' in bold.text and bold.text[-1] == ':' and not '(' in bold.text and not '"' in bold.text or ', ' in bold.text and bold.text[-2] == ':'  and not '(' in bold.text and not '"' in bold.text:
                    # print('else')
                    text = bold.text.replace('Hon. ', '').replace('The Hon. ', '').replace('Mr. ', '').replace('Mrs. ', '').replace('Ms. ', '').replace('Hon.\xa0', '').replace('The Hon.\xa0', '').replace('Mr.\xa0', '').replace('Mrs.\xa0', '').replace('Ms.\xa0', '').replace(': ', '').strip()
                    a = text.find(',')
                    name = text[:a]
                    name = name.split()
                    print(name)
                    last_name = name[-1]
                    # print(last_name)
                    first_name = text[:a].replace(last_name, '').strip()
                    try:
                        person = Person.objects.filter(first_name__icontains=first_name, last_name=last_name)[0]
                    except:
                        print('creating person')
                        # time.sleep(2)
                        person = Person(first_name=first_name, last_name=last_name)
                        # p.Region_obj = 
                        person.save()
                        person.create_post()
                    # print(person)
                elif 'Deputy Chair' in bold.text:
                    print('dep')
                    name = bold.text.replace('Deputy Chair ', '').replace(':', '')
                    name = name.split()
                    print(name)
                    last_name = name[-1]
                    # first_name = bold.text.replace(last_name, '').strip()
                    if last_name in str(p.text).replace(str(bold.text), ''):
                        x = str(p.text).replace(str(bold.text), '').replace('Senator ','')
                        y = x.find(last_name)
                        z = x[:y].find('. ')+len('. ')
                        first_name = x[z:y].strip()
                    else:
                        first_name = name[0]
                    if '(Deputy Chair) in the chair' in p.text:
                        # print('tmp chair')
                        try:
                            r = Role.objects.filter(position='Senator', person__last_name__icontains=last_name)[0]
                            person = r.person
                            committeeMeeting.currentChair = person
                            committeeMeeting.save()
                        except:
                            try:
                                person = Person.objects.filter(first_name__icontains=first_name, last_name=last_name)[0]
                            except:
                                print('creating person')
                                person = Person(first_name=first_name, last_name=last_name)
                                # p.Region_obj = 
                                person.save()
                                person.create_post()            
                        # print('temp chair found')
                        # time.sleep(2)
                    else:
                        try:
                            r = Role.objects.filter(committee_key=committeeMeeting.committee, title='Deputy Chair')[0]
                            person = r.person
                            last_name = person.last_name
                        except:
                            try:
                                person = Person.objects.filter(first_name__icontains=first_name, last_name=last_name)[0]
                            except:
                                print('creating person')
                                person = Person(first_name=first_name, last_name=last_name)
                                # p.Region_obj = 
                                person.save()
                                person.create_post()
                            try:
                                r = Role.objects.filter(position='Senator', person=person)[0]
                            except:
                                r = Role(position='Senator', person=person, current=False)
                                # r.Region_obj =
                                r.save()

                    # print(person)
                elif 'The Chair' in bold.text:
                    print('chair')
                    # print(committeeMeeting.committee)
                    if committeeMeeting.currentChair:
                        person = committeeMeeting.currentChair
                    else:
                        # if last_name in str(p).replace(str(bold),''):
                        #     x = str(p).replace(str(bold), '')
                        #     y = x.find(last_name)
                        #     first_name = x[:y].strip()
                        # else:
                        #     first_name = name[0]
                        try:
                            r = Role.objects.filter(committee_key=committeeMeeting.committee, title='Chair')[0]
                            person = r.person
                        except:
                            try:
                                person = Person.objects.filter(first_name__icontains=first_name, last_name=last_name)[0]
                            except:
                                print('creating person')
                                person = Person(first_name=first_name, last_name=last_name)
                                # p.Region_obj = 
                                person.save()
                                person.create_post()
                            try:
                                r = Role.objects.filter(position='Senator', person=person)[0]
                            except:
                                r = Role(position='Senator', person=person, current=False)
                                # r.Region_obj =
                                r.save()
                    last_name = person.last_name
                    # print(person)
                elif 'Hon. Senators' in bold.text or 'An Hon. Senator' in bold.text:
                    # print('some senators')
                    samePerson = True
                    div = ''
                elif 'Senator' in bold.text:
                    # print('senator')
                    # print(p.text)
                    try:
                        name = bold.text.replace('Senator ', '').replace(':', '')
                        name = name.split()
                        # print(name)
                        last_name = name[-1]
                    except: #for errors in print
                        a = p.text.find(':')
                        name = p.text[:a].replace('Senator ', '')
                        name = name.split()
                        # print(name)
                        last_name = name[-1]
                    if last_name in str(p.text).replace(str(bold.text),''):
                        x = str(p.text).replace(str(bold.text), '').replace('Senator ','')
                        y = x.find(last_name)
                        z = x[:y].find('. ')+len('. ')
                        first_name = x[z:y].strip()
                    else:
                        first_name = name[0]
                    try:
                        r = Role.objects.filter(position='Senator', person__last_name__icontains=last_name)[0]
                        person = r.person
                        print(person)
                        if '(Chair) in the chair' in p.text:
                            # print('tmp chair')
                            committeeMeeting.currentChair = person
                            committeeMeeting.save()
                            # print('temp chair found')
                            # time.sleep(2)
                    except Exception as e:
                        try:
                            person = Person.objects.filter(first_name__icontains=first_name, last_name=last_name)[0]
                        except:
                            print('creating person')
                            print(first_name)
                            person = Person(first_name=first_name, last_name=last_name)
                            # p.Region_obj = 
                            person.save()
                            person.create_post()
                        try:
                            r = Role.objects.filter(position='Senator', person=person)[0]
                        except:
                            r = Role(position='Senator', person=person, current=False)
                            # r.Region_obj =
                            r.save()
                    if '(Chair) in the chair' in p.text:
                        # print('tmp chair')
                        committeeMeeting.currentChair = person
                        committeeMeeting.save()
                        # print('temp chair found')
                        # time.sleep(2)
                    # print(person)
                elif 'Mr.' in bold.text or 'Mrs.' in bold.text or 'Ms.' in bold.text:
                    print('Mr')
                    last_name = bold.text.replace('Mr. ', '').replace('Mrs. ', '').replace('Ms. ', '').replace('Mr.\xa0', '').replace('Mrs.\xa0', '').replace('Ms.\xa0', '').replace(': ', '').strip()
                    # print(last_name)
                    # print(speakers)
                    try:
                        person = speakers[last_name]
                        # print(person)
                    except Exception as e:
                        print(str(e))
                        # print(speakers)
                        name = last_name.split()
                        # print(name)
                        last_name = name[-1]
                        # print(last_name)
                        a = bold.text.find(last_name)
                        first_name = bold.text[:a].strip()
                        try:
                            person = Person.objects.filter(first_name__icontains=first_name, last_name=last_name)[0]
                        except:
                            print('creating person')
                            person = Person(first_name=first_name, last_name=last_name)
                            # p.Region_obj = 
                            person.save()
                            person.create_post()
                # elif ':' in bold.text and not 'Subject' in bold.text:
                #     print('unkown person')
                #     name = bold.text.replace(': ','')
                #     print(name)
                #     try:
                #         person = Person.objects.filter(last_name=name)[0]
                #     except:
                #         print('creating person')
                #         person = Person(last_name=name)
                #         person.save()
                    # person = None

                else:
                    # print('same')
                    samePerson = True
                    div = ''
                    # last_name = 'Unknown'
                # print(person)
                speakers[last_name] = person
                # print(speakers)
                # print('1')
                if not samePerson:
                    try:
                        # print('2')
                        content = str(p).replace(str(div), '')
                        c = CommitteeItem.objects.filter(committeeMeeting=committeeMeeting, person=person, Content__icontains=content)[0]
                        # print('cItem found')
                    except Exception as e:
                        # print(str(e))
                        # print('creating committeeItem')
                        if person:
                            c = CommitteeItem(committeeMeeting=committeeMeeting, person=person)
                        else:
                            c = CommitteeItem(committeeMeeting=committeeMeeting)
                        c.person_name = title.replace(': ','')
                        c.Content = ''
                        c.save()
            try: 
                # skip preamble with try/except
                if str(p).replace(str(div), '') not in c.Content:
                    try:
                        c.Content = c.Content + '\n' + str(p).replace(str(div), '')
                    except:
                        c.Content = str(p).replace(str(div), '')
                    committeeMeeting.people.add(person)
                    string =  re.sub('<[^<]+?>', '', c.Content)
                    words = re.findall(r'\w+', string)
                    c.wordCount = len(words)
                    c.meeting_title = committeeMeeting.Title
                    c.save() 
                    c.create_post()
                    # print('saved')
            except Exception as e:
                print(str(e))
    committeeMeeting.has_transcript = True
    print('has_transcript', committeeMeeting.has_transcript)
    people = CommitteeItem.objects.filter(committeeMeeting=committeeMeeting)
    C_people = {}
    for p in people:
        try:
            if not p.person.id in C_people:
                C_people[p.person.id] = 1
            else:
                C_people[p.person.id] += 1
        except Exception as e:
            print(str(e))
    C_people = sorted(C_people.items(), key=operator.itemgetter(1),reverse=True)
    C_people = dict(C_people)
    committeeMeeting.peopleText = json.dumps(C_people)
    committeeMeeting.save()
    print('comMeeting saved')
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()
    print('done')
    
def scrape_senate_committee_list(driver, session):
    element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="table-print"]/div[1]'))
    WebDriverWait(driver, 10).until(element_present)

    table = driver.find_element(By.XPATH, '//*[@id="table-print"]/div[1]')
    tbody = table.find_element(By.CSS_SELECTOR, 'tbody')
    trs = tbody.find_elements(By.CSS_SELECTOR, 'tr')
    committees = {}
    com_transcript = {}
    # videos = {}
    x = session.find('-')
    parl = session[:x]
    sess = session[x+len('-'):]
    print(parl)
    print(sess)
    time.sleep(3)
    for tr in trs:
        bill = None
        # print(tr.get_attribute('innerHTML'))
        tds = tr.find_elements(By.CSS_SELECTOR, 'td')
        dt = tds[0].find_element(By.CSS_SELECTOR, 'a')
        print(dt.text)
        # print(dt.get_attribute('href'))
        try:
            
            date_time = datetime.datetime.strptime(dt.text, '%b %d, %Y\n%I:%M %p %Z')
        except:
            date_time = datetime.datetime.strptime(dt.text, '%b %d, %Y\n%I:%M %p local time')
        # print(d)
        com = tds[1].find_element(By.CSS_SELECTOR, 'a')
        print(com.text)
        print(com.get_attribute('href'))
        com_link = com.get_attribute('href')
        a = com_link.find('committees/') + len('committees/')
        b = com_link[a:].find('/')
        code = com_link[a:a+b]
        # print(code)
        print(code.upper())
        try:
            studies_a = tds[2].find_element(By.CSS_SELECTOR, 'ul')
            studies_b = studies_a.find_element(By.CSS_SELECTOR, 'li')
            text = studies_b.text
            if 'Bill' in text:
                a = text.find(', ')
                b = text[:a].replace('Bill ', '')
                try:
                    bill = Bill.objects.filter(NumberCode=b).filter(ParliamentNumber=parl, SessionNumber=sess).filter(Q(OriginatingChamberName='Senate')|Q(OriginatingChamberName__icontains='House'))[0]
                    print(bill)
                except:
                    pass
            studies_c = studies_b.find_elements(By.CSS_SELECTOR, 'ul')
            for c in studies_c:
                text = text.replace(c.text, '').strip()
            # print(text.strip())
        except:
            text = None
        # print('----')
        if '(Special Joint)' in com.text:
            org = '(Special Joint)'
        else:
            org = 'Senate'
        try:
            committee = Committee.objects.filter(code=code.upper(), Organization=org, ParliamentNumber=parl, SessionNumber=sess)[0]
        except:
            committee = Committee(code=code.upper(), Organization=org, Title=com.text, govURL=com.get_attribute('href'), ParliamentNumber=parl, SessionNumber=sess)
            committee.save()
            committee.create_post()
        try:
            # start_time = datetime.datetime.strftime(date_time, '%Y-%m-%-d')
            # end_time = datetime.datetime.strftime(date_time, '%Y-%m-%-d') + datetime.timedelta(days=1)
            comMeeting = CommitteeMeeting.objects.filter(committee=committee, govURL=dt.get_attribute('href'))[0]
            print('meeting found')
            if bill and not comMeeting.bill:
                comMeeting.bill = bill
                comMeeting.save()
            if not comMeeting.Title:
                comMeeting.Title = text
                comMeeting.save()
        except Exception as e:
            print(str(e))
            comMeeting = CommitteeMeeting(committee=committee, Organization=org, date_time_start=date_time, Title=text, govURL=dt.get_attribute('href'), ParliamentNumber=committee.ParliamentNumber, SessionNumber=committee.SessionNumber)
            if bill:
                comMeeting.bill = bill
            comMeeting.save()
            comMeeting.create_post()
        # print(tds[4].get_attribute('innerHTML'))
        links = tds[4].find_elements(By.CSS_SELECTOR, 'a')
        # print(len(links))
        for l in links:
            # print(l.get_attribute('title'))
            if 'Video' in l.get_attribute('title'):
                # print('video')
                # print(l.get_attribute('href'))
                # print(l.get_attribute('href') + '&viewMode=3')
                comMeeting.embedURL = l.get_attribute('href') + '&viewMode=3'
                comMeeting.embedURL = comMeeting.embedURL.replace('http', 'https').replace('XRender', 'Harmony')
                # videos[com.text] = l.get_attribute('href')
                if not comMeeting.timeRange:
                    try:
                        time.sleep(2)
                        r = requests.get(l.get_attribute('href'))
                        soup = BeautifulSoup(r.content, 'html.parser')
                        dt = soup.find('div', {'id':'scheduledtime'})
                        comMeeting.timeRange = dt.text
                    except:
                        pass
            if 'Transcripts' in l.get_attribute('title'):
                # print('transcripts')
                com_transcript[comMeeting] = l.get_attribute('href')
            if 'Interim' in l.get_attribute('title'):
                # print('interim')
                # print(l.get_attribute('href'))
                com_transcript[comMeeting] = l.get_attribute('href')
            if 'Audio' in l.get_attribute('title'):
                # print('audio')
                # print(l.get_attribute('href'))
                comMeeting.embedURL = l.get_attribute('href') + '&viewMode=3'
                try:
                    if not comMeeting.timeRange:
                        time.sleep(1)
                        r = requests.get(l.get_attribute('href'))
                        soup = BeautifulSoup(r.content, 'html.parser')
                        dt = soup.find('div', {'id':'scheduledtime'})
                        # print(dt.text)
                        comMeeting.timeRange = dt.text
                except Exception as e:
                    print(str(e))
            # else:
            #     print('none')
        comMeeting.save()
        # print(comMeeting.timeRange)
        # print(comMeeting.embedURL)
        committees[committee] = com.get_attribute('href')
        print('------------------------')
    

    print('getting members')
    starting_url = driver.current_url
    for key, value in committees.items():
        # print('getting members')
        # script = "window.open('" + value + "' ,'_blank');"
        # driver.execute_script(script)
        # windows = driver.window_handles
        # driver.switch_to.window(windows[1])
        try:
            if not key.chair and key.Organization != '(Special Joint)':
                print(key)
                print(value)
                driver.get(value)
                
                element_present = EC.presence_of_element_located((By.CLASS_NAME, 'sc-committee-members-dynamic-content-list'))
                WebDriverWait(driver, 4).until(element_present)
                content = driver.find_element(By.CLASS_NAME, 'sc-committee-members-dynamic-content-list')
                people = content.find_elements(By.CLASS_NAME, 'col-md-8')
                for p in people:
                    try:
                        h = p.find_element(By.CSS_SELECTOR, 'h3')
                        # print(h.text)
                        title = h.text
                    except:
                        # print('no position')
                        title = 'Member'
                    a = p.find_element(By.CSS_SELECTOR, 'a')
                    # print(a.get_attribute('href'))
                    # print(a.text)
                    try:
                        senator = Role.objects.filter(gov_page=a.get_attribute('href'))[0]
                        try:
                            r = Role.objects.filter(person=senator.person, committee_key=key)[0]
                            r.current = True
                            r.group = key.Title
                            r.save()
                        except:
                            r = Role(person=senator.person, committee_key=key, position='Committee Member', title=title, group=key.Title, current=True)
                            # r.Region_obj =
                            r.save()
                        key.members.add(r)
                        if title == 'Chair':
                            key.chair = r
                        key.save()
                    except Exception as e:
                        print(str(e))
                        # person = None
            
                    
                # time.sleep(3)
                # driver.close()
                # print('---------------')
                time.sleep(3)
            else:
                # print(key.chair.person)
                print('--')
        except Exception as e:
            print(str(e))
    if driver.current_url != starting_url:
        driver.get(starting_url)
    print('getting transcripts')
    for key, value in com_transcript.items():
        if key.has_transcript == False:
            print(key)
            print(key.date_time_start)
            key.transcriptURL = value
            # key.save()
            try:
                get_senate_committee_transcript(key)
            except Exception as e:
                print(str(e))
            time.sleep(2)
    driver.quit()
    print('done senate committee scrape')
        # break

# def get_upcoming_senate_committees():
#     get_senate_committees(upcoming='upcoming')

def get_senate_committees(upcoming='past'):
    print('---------------------senate committees ', upcoming)
    parl = Parliament.objects.filter(country='Canada', organization='Federal').first()
    session = '%s-%s' %(parl.ParliamentNumber, parl.SessionNumber)
    url = 'https://sencanada.ca/en/committees/allmeetings/#?TabSelected=%s&filterSession=%s&PageSize=50' %(upcoming, session)
    # url = 'https://sencanada.ca/en/committees/allmeetings/#?TabSelected=PAST&filterSession=44-1&PageSize=10&SortOrder=DATEDESC&p=11'
    print("opening browser")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
    driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
    driver.get(url)
    # print('received link')
    # time.sleep(5)
    # try:
    # except:
    #     pass
    scrape_senate_committee_list(driver, session)
    print('done senate committee list')
    driver.quit()
    # get all
    # s = session
    # run = True
    # while run:
    #     arrows = driver.find_elements(By.CLASS_NAME, 'sen-pagination-buttons-arrow')
    #     if arrows:
    #         for arrow in arrows:
    #             a = arrow.find_element(By.CSS_SELECTOR, 'a')
    #             # print(a.get_attribute('aria-label'))
    #             if a.get_attribute('aria-label') == 'Next':
    #                 link = a.get_attribute('href')
    #                 scrape_senate_committee_list(driver, s)
    #                 print('click')
    #                 # arrow.click()
    #                 driver.get(link)
    #                 run = True
    #             else:
    #                 scrape_senate_committee_list(driver, s)
    #                 run = False
    #         time.sleep(5)
    #     else:
    #         scrape_senate_committee_list(driver, s)
    #         run = False
    get_senate_committees(upcoming='upcoming')

def get_all_senate_committees():
    sessions = ['44-1', '43-2', '43-1', '42-1', '41-2', '41-1', '40-3', '40-2', '40-1', '39-2','39-1','38-1', '37-3','37-2','37-1','36-2','36-1','35-2','35-1']
    # sessions = ['40-3', '40-2', '40-1', '39-2','39-1','38-1', '37-3','37-2','37-1','36-2','36-1','35-2','35-1']
    
    # url = 'https://sencanada.ca/en/committees/allmeetings/#?TabSelected=PAST&filterSession=44-1&PageSize=10&SortOrder=DATEDESC&p=11'
    print("opening browser")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
    driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
    for s in sessions:
        url = 'https://sencanada.ca/en/committees/allmeetings/#?filterSession=%s&PageSize=50&SortOrder=DATEDESC&p=1' %(s)
        print(url, '------------------------------------------------------')
        driver.get(url)
        element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="table-print"]/div[1]'))
        WebDriverWait(driver, 10).until(element_present)
        # try:
        #     next = driver.find_element(By.CLASS_NAME, 'sen-pagination-buttons-arrow')
        # except:
        #     next = None
        run = True
        while run:
            print('waiting 10...')
            time.sleep(10)
            next = None
            arrows = driver.find_elements(By.CLASS_NAME, 'sen-pagination-buttons-arrow')
            if arrows:
                for arrow in arrows:
                    a = arrow.find_element(By.CSS_SELECTOR, 'a')
                    if a.get_attribute('aria-label') == 'Next':
                        next = a.get_attribute('href')
            print('start scrape')
            scrape_senate_committee_list(driver, s)
            if next:
                print(next, '--------next-----------------')
                driver.get(next)
                element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="table-print"]/div[1]'))
                WebDriverWait(driver, 10).until(element_present)
                print(driver.current_url)
            else:
                run = False



        # run = True
        # while run:
        #     arrows = driver.find_elements(By.CLASS_NAME, 'sen-pagination-buttons-arrow')
        #     if arrows:
        #         for arrow in arrows:
        #             a = arrow.find_element(By.CSS_SELECTOR, 'a')
        #             # print(a.get_attribute('aria-label'))
        #             if a.get_attribute('aria-label') == 'Next':
        #                 link = a.get_attribute('href')
        #                 scrape_senate_committee_list(driver, s)
        #                 print('click')
        #                 # arrow.click()
        #                 driver.get(link)
        #                 run = True
        #             else:
        #                 scrape_senate_committee_list(driver, s)
        #                 run = False
        #         time.sleep(5)
        #     else:
        #         scrape_senate_committee_list(driver, s)
        #         run = False
        #         # print('stop')
        print('----------next session')
    driver.quit()

def get_senate_committee_work(value='latest'):
    print('----------------------senate work')
    if value == 'alltime':
        pass
    else:
        url = 'https://sencanada.ca/en/committees/reports/'
    print("opening browser")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    driver = webdriver.Chrome(options=chrome_options)
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
    driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
    driver.get(url)
    element_present = EC.presence_of_element_located((By.CLASS_NAME, 'widget-committees-reports'))
    WebDriverWait(driver, 10).until(element_present)
    reports = driver.find_element(By.CLASS_NAME, 'widget-committees-reports')
    lis = reports.find_elements(By.CSS_SELECTOR, 'li')
    if value == 'latest':
        lis = lis[:20]
    for li in lis:
        a = li.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        print(a)
        b = li.text.find('\n')
        c = li.text[b+len('\n'):].find('\n')
        activity = li.text[:b]
        # print('---')
        com = li.text[b+len('\n'):b+len('\n')+c].replace('The Standing Senate Committee on ', '').replace('The Standing Committee on ', '').replace('The Standing Joint Committee for ', '')
        print('-------', com)
        event = li.text[b+len('\n')+c+len('\n'):]
        d = event.find(' - ')
        eventTitle = event[:d]
        print(event)
        date = event[d+len(' - '):]
        # print(date)
        dt = datetime.datetime.strptime(date, '%B %Y')
        # print(dt)
        # print('')
        parl = Parliament.objects.filter(country='Canada', organization='Federal', start_date__lte=dt)[0]
        # print(parl)
        try:
            comMeeting = CommitteeMeeting.objects.filter(reportLink=a)[0]
            print('meeting found')
        except:
            try:
                print('creating meeting')
                com = Committee.objects.filter(Title__icontains=com, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber)[0]
                comMeeting = CommitteeMeeting(Organization='Senate', committee=com, reportLink=a, Title=activity, event=eventTitle, date_time_start=dt, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber)
                if 'Bill' in activity:
                    print('bill:')
                    x = activity.find('Bill')+len('Bill ')
                    if ',' in activity[x:]:
                        y = activity[x:].find(',')
                        z = activity[x:x+y]   
                    elif '-' in activity[x:]:
                        y = activity[x:].find('-')
                        if ' ' in activity[x+y:]:
                            w = activity[x+y:].find(' ')
                            z = activity[x+y-1:x+y+w]   
                        else:
                            z = activity[x+y-1:]   
                    # print(z)
                    bill = Bill.objects.filter(NumberCode=z, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber)[0]
                    comMeeting.bill = bill
                    print(bill)
                time.sleep(2)
                r = requests.get(a)
                soup = BeautifulSoup(r.content, 'html.parser')
                containers = soup.find_all('div', {'class':'container'})
                for container in containers:
                    if 'Report of the committee' in container.text:
                        # h3 = container.find("h3", string="Report of the committee")
                        div = container.find('div')
                        first_p = div.find('p')
                        # print(p.text)
                        try:
                            dt = datetime.datetime.strptime(first_p.text, '%A, %B %d, %Y')
                        except:
                            dt = datetime.datetime.strptime(first_p.text, '%B %d, %Y')
                        comMeeting.date_time_start = dt
                        print(dt)
                        print('---------------------------------')
                        content = str(div).replace(str(first_p), '')
                        # print(content)
                        comMeeting.report = content
                comMeeting.save()
                comMeeting.create_post()
            except Exception as e:
                print(str(e))
                print('timeout 20s')
                # time.sleep(20)
    driver.quit()

def get_senate_agendas(value='latest'):
    print('-------------------senate agenda')
    parl = Parliament.objects.filter(country='Canada', organization='Federal')[0]
    dt = datetime.datetime.now()
    l = 'https://senparlvu.parl.gc.ca/Harmony/en/View/EventListView/%s%s%s/307' %(dt.year, dt.month, dt.day)
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
    # caps["pageLoadStrategy"] = "eager"   # Do not wait for full page load
    driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
    # print(self.parlinfo_link)
    driver.get(l)
    def action(driver):
        element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="divEventList"]/div[2]/div[1]'))
        WebDriverWait(driver, 10).until(element_present)
        # signIn = driver.find_element(By.XPATH, '//*[@id="right-content"]/a')
        # r = requests.get(l)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # print(soup)
        divs = soup.find_all('div', {'class':'divEvent'})
        for div in divs:
            a = div.find('a')
            print(a['href'])
            x = a['href'].rfind('/')+len('/')
            code = a['href'][x:]
            date = a.find('div', {'class':'eventDate'}).text
            print(date)
            '--Thu, Feb 9, 2023 --'
            time = a.find('div', {'class':'eventTime'}).text
            print(time)
            x = time.find('-')
            st = time[:x]
            et = time[x+len('-'):]
            start_time = datetime.datetime.strptime(date + '--' + st, '%a, %b %d, %Y --%I:%M %p')
            print(start_time)
            end_time = datetime.datetime.strptime(date + '--' + et, '%a, %b %d, %Y --%I:%M %p')
            print(end_time)
            vid = 'https://senparlvu.parl.gc.ca/Harmony/en/PowerBrowser/PowerBrowserV2/%s%s%s/-1/%s?viewMode=3&globalStreamId=16' %(start_time.year, start_time.month, start_time.day, code)
            # parl = Parliament.objects.filter(start_time__lte=start_time)[0]
            try:
                agenda = Agenda.objects.filter(organization='Senate', date_time=start_time)[0]
            except:
                agenda = Agenda(organization='Senate', gov_level='Federal', date_time=start_time)
                agenda.end_date_time = end_time
                agenda.VideoURL = vid
                agenda.videoCode = code
                agenda.save()
                agenda.create_post()
            try:
                H = Hansard.objects.filter(agenda=agenda)[0]
            except:
                H = Hansard(agenda=agenda, Publication_date_time=start_time, Organization='Senate')
                H.ParliamentNumber=parl.ParliamentNumber
                H.SessionNumber=parl.SessionNumber
                H.save()
                H.create_post() 

            print('')
        print('done page')
    go = True
    while go:
        action(driver)
        if value == 'session':
            try:
                time.sleep(3)
                next = driver.find_element(By.XPATH, '//*[@id="btnNext"]').click()
            except:
                go = False
        else:
            go = False
    driver.quit()
    # sys.modules[__name__].__dict__.clear()
    # gc.collect()

def get_all_agendas():
    'https://www.ourcommons.ca/en/parliamentary-business/2001-01-29'
    # today = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
    start_date = '%s-%s-%s' %(2001, 1, 29)
    #rerun committee hansards from here
    # start_date = '%s-%s-%s' %(2020, 10, 15)
    start_date = '%s-%s-%s' %(2023, 3, 1)
    # start_date = '%s-%s-%s' %(2021, 7, 20)
    #run rest from here
    # start_date = '%s-%s-%s' %(2022, 4, 5)
    print(start_date)
    day = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    # print(isinstance(day, str))
    # print(day)
    plus_day = 1
    while day <= datetime.datetime.now():
        # print(day)
        # weekno = day.weekday()
        # print('day', weekno)
        # if weekno < 5:
        # print(isinstance(day, datetime))
        # print(isinstance(day, str))
        # print(isinstance(day, str))
        # year_date = dt + datetime.timedelta(days=plus_day)
        # year = year_date.year
        # print(year)
        # plus_day = 1
        # time.sleep(1)
        # u = 'https://www.ourcommons.ca/en/parliamentary-business/2022-12-12'


        day = datetime.datetime.strftime(day, '%Y-%m-%d')
        print(day)
        # url = 'https://www.ourcommons.ca/en/parliamentary-business/%s' %(day)
        # print('---------getting agenda')
        # print(url)
        # time.sleep(2)
        # try:
        #     A = Agenda.objects.filter(date_time=day, organization='House', gov_level='Federal')[0]
        #     print('agenda found')
        # except:
        #     print('agenda not found')
        # get_agenda(url)
        # print('')
        # print('-------getting debate hansard')
        # debate_url = 'https://www.ourcommons.ca/PublicationSearch/en/?View=D&Item=&ParlSes=from%sto%s&oob=&Topic=&Proc=&Per=&Prov=&Cauc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=2000000&PubType=37&xml=1' %(day, day)
        # # debate_url = 'https://www.ourcommons.ca/PublicationSearch/en/?View=D&Item=&ParlSes=from2002-05-02to2002-05-02&oob=&Topic=&Proc=&Per=&Prov=&Cauc=&Text=&RPP=15&order=&targetLang=&SBS=0&MRR=2000000&PubType=37&xml=1'
        # print(debate_url)
        # time.sleep(2)
        # try:
        #     get_house_hansard_or_committee('hansard', debate_url)
        # except Exception as e:
        #     print('not found')
        #     print(str(e))
        # com_url = 'https://www.ourcommons.ca/Committees/en/Meetings?meetingDate=%s' %(day) 
        # print('----------getting house committee list')
        # print(com_url)
        # time.sleep(2)
        # get_house_committee_list(com_url)
        # time.sleep(2)
        han_url = 'https://www.ourcommons.ca/PublicationSearch/en/?PubType=40017&xml=1&parlses=from%sto%s' %(day, day)
        print('-----------getting committee hansard')
        print(han_url)
        try:
            get_house_hansard_or_committee('committee', han_url)
        except Exception as e:
            print('not found')
            print(str(e))
        # print('')
        print('-------------------------------------------------------------------')
        day = datetime.datetime.strptime(day, '%Y-%m-%d')
        day = datetime.datetime.strftime(day + datetime.timedelta(days=plus_day), '%Y-%m-%d')
        print('next', day)
        day = datetime.datetime.strptime(day, '%Y-%m-%d')
        
def get_federal_match(request, person):
    parl = Parliament.objects.filter(country='Canada', organization='Federal')[0]
    reactions = Reaction.objects.filter(user=request.user, post__post_type='bill').filter(post__bill__province=None).order_by('-post__date_time')
    votes = {}
    my_votes = {}
    return_votes = []
    vote_matches = 0
    total_matches = 0
    match_percentage = None
    for r in reactions:
        try:
            bill = r.post.bill
            if r.isYea:
                votes[bill] = 'Yea'
            elif r.isNay:
                votes[bill] = 'Nay'
            # print(r.isYea, r.isNay)
        except:
            pass
    matched = []
    def match_vote(m, person, votes, bill, vote_matches, total_matches, return_votes):
        try:
            v = Vote.objects.filter(motion=m, person=person).order_by('-motion__date_time')[0]
            total_matches += 1
            return_votes.append(v)
            if v.VoteValueName == votes[bill]:
                vote_matches += 1
                # print('match')
            return 'match', vote_matches, total_matches, return_votes
        except Exception as e:
            pass
        return 'nomatch', vote_matches, total_matches, return_votes
    for bill in votes:
        # print('------', bill)
        # print(billVersion)
        # print(votes[billVersion])
        try:
            motions = Motion.objects.filter(bill=bill, ParliamentNumber=parl.ParliamentNumber, SessionNumber=parl.SessionNumber).order_by('-date_time')
            for m in motions:
                my_votes[m.id] = votes[bill]
                result, vote_matches, total_matches, return_votes = match_vote(m, person, votes, bill, vote_matches, total_matches, return_votes)
                if result == 'match':
                    matched.append(m)
                    break
        except Exception as e:
            print(str(e))
    # print(vote_matches, '/', total_matches)
    try:
        match_percentage = int((vote_matches / total_matches) * 100)
    except Exception as e:
        match_percentage = None
    # print(match_percentage)
    return match_percentage, total_matches, vote_matches, my_votes, return_votes

