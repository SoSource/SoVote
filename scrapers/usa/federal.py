


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




states = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming'
}


def get_representatives():
    starting_url = 'https://www.house.gov/representatives'
    
    try:
        print("opening browser")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        driver = webdriver.Chrome(options=chrome_options)
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
        driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
        driver.get(starting_url)

        element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="house-in-session"]'))
        WebDriverWait(driver, 10).until(element_present)

        soup = BeautifulSoup(driver.page_source, 'html.parser')


        '118th Congress, 2nd Session · '
        div = soup.find('div', {'id':'house-in-session'}).text
        a = div.find(' Congress, ')
        b = div[a+len(' Congress, '):].find(' Session')
        cong = div[:a]
        sess = div[a+len(' Congress, '):a+len(' Congress, ')+b]
        cong = cong.replace('st','').replace('nd','').replace('rd','').replace('th','')
        sess = sess.replace('st','').replace('nd','').replace('rd','').replace('th','')
        cong = int(cong)
        sess = int(sess)
        try:
            congress = Parliament.objects.filter(country='USA', organization='Federal', ParliamentNumber=cong, SessionNumber=sess)[0]
        except:
            dt = datetime.date.today()
            congress = Parliament(country='USA', organization='Federal', ParliamentNumber=cong, SessionNumber=sess, start_date=dt)
            congress.save()
            congress.end_previous('USA','Federal')

        content = soup.find('div', {'class':'view-content'})
        tables = content.find_all('table', {'class':'table'})
        congressmen = []
        for table in tables:
            state_name = table.find('caption').text
            print('------------------')
            print(state_name)
            try:
                state = Province.objects.filter(name=state_name)[0]
            except:            
                state = Province(name=state_name)
                state.save()

            tbody = table.find('tbody')
            trs = tbody.find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                riding_name = tds[0].text.replace('st','').replace('nd','').replace('rd','').replace('th','')
                print(riding_name)
                representative = tds[1]
                print(representative.text)
                x = representative.text.find(', ')
                first = representative.text[x+2:].strip()
                last = representative.text[:x].strip()
                print(first, last)
                a = representative.find('a')
                url = a['href']
                print(url)
                party = tds[2].text
                if party == 'R':
                    party_name = 'Republican'
                elif party == 'D':
                    party_name = 'Democrat'
                elif party == 'I':
                    party_name = 'Independent'
                else:
                    party_name = party
                print(party)
                officeRoom = tds[3].text
                print(officeRoom)
                phone = tds[4].text
                print(phone)
                assignment = tds[5].text
                print(assignment)
                try:
                    person = Person.objects.filter(gov_profile_page=url)[0]
                    person.first_name = first
                    person.last_name = last
                    print(person)
                except Exception as e:
                    # print(str(e))
                    try:
                        person = Person.objects.filter(first_name=first, last_name=last)[0]
                        person.website=url
                    except Exception as e:
                        print('creating person')
                        # print(str(e))
                        person = Person(first_name=first, last_name=last, gov_profile_page=url)
                        # person.Region_obj = 
                        url = 'https://www.congress.gov/search?q=%7B%22source%22%3A%22members%22%2C%22search%22%3A%22%s%22%7D' %(representative.text)
                        
                        driver.get(url)

                        element_present = EC.presence_of_element_located((By.ID, 'main'))
                        WebDriverWait(driver, 10).until(element_present)

                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        main = soup.find('div', {'id':'main'})
                        lis = main.find_all('li', {'class':'expanded'})
                        for li in lis:
                            found = False
                            required = [representative.text, state_name, riding_name, party_name,'Present']
                            for i in required:
                                if i not in li.text:
                                    found = False
                                    break
                                else:
                                    found = True
                            if found:
                                # print(li.text) 
                                heading = li.find('span', {'class':'result-heading'})
                                link = heading.find('a')['href']
                                person.gov_profile_page=link
                                print(link)
                                # '''https://www.congress.gov/member/jerry-carl/C001054?q=%7B%22search%22%3A%22carl%22%7D&s=1&r=1'''
                                q = link.find('?q=')
                                w = link[:q].rfind('/')
                                code = link[w+1:q]
                                link = link[:q]
                                print(code)
                                person.gov_iden = code
                                img = 'https://www.congress.gov/img/member/%s_200.jpg' %(code.lower())
                                print(img)
                                person.logo = img
                                break
                        search_name = state.name + ' congressional representative ' + person.first_last()
                        title = wikipedia.search(search_name)[0].replace(' ', '_')
                        u = 'https://en.wikipedia.org/wiki/' + title
                        person.wikipedia = u
                        # r = requests.get(u)
                        # soup = BeautifulSoup(r.content, 'html.parser')
                        # div = soup.find('div', {'id':'bodyContent'})
                        # img = div.find('img')['src']
                        person.save()
                        person.create_post()
                try:
                    riding = Riding.objects.filter(name=riding_name, province_name=state)[0]
                    # print(district)
                except:
                    # print('creating district')
                    riding = Riding(name=riding_name, province_name=state_name, province=state)
                    search_name = riding_name + ' congressional district of ' + state_name
                    title = wikipedia.search(search_name)[0].replace(' ', '_')
                    riding.wikipedia = 'https://en.wikipedia.org/wiki/' + title
                    riding.save()
                    riding.create_post()
                try:
                    rep = Role.objects.filter(position='Congressional Representative', person=person, riding=riding, parliament=congress)[0]
                    
                except:
                    print('creating representative')
                    rep = Role(position='Congressional Representative', person=person, gov_page=url, riding=riding, parliament=congress)
                    # person.Region_obj = 
                    rep.person_name = first + last
                # rep.email 
                # rep.address
                rep.telephone = phone.text
                rep.gov_page=url
                rep.office_name = officeRoom
                rep.current = True
                rep.save()
                try:
                    role = Role.objects.filter(person=person, title=assignment, parliament=congress)[0]
                except:
                    role = Role.objects.filter(person=person, title=assignment, parliament=congress)
                role.current = True
                role.save()

                try:
                    try:
                        party = Party.objects.filter(name=party_name, level='federal')[0]
                    except:
                        party = Party(name=party_name, level='federal')  
                        try:   
                            search_name = party.name + ' american federal political party'
                            link = wikipedia.search(search_name)[0].replace(' ', '_')
                            party.wikipedia = 'https://en.wikipedia.org/wiki/' + link
                        except:
                            pass
                        party.save()
                        party.create_post()
                    person.party = party
                    person.party_name = party.name
                    person.save()
                    rep.party = party
                    rep.party_name = party.name
                    rep.save()
                except Exception as e:
                    pass
                congressmen.append(person)
                
                    
                print('')
        people = Role.objects.filter(position='Congressional Representative')
        for p in people:
            if p.person not in congressmen:
                p.current = False
                p.save()
    
    except Exception as e:
        print(str(e))
    driver.quit()

def get_bills():
    base_url = 'https://www.congress.gov'
    url = base_url + '/search?q={%22congress%22:%22118%22,%22source%22:%22legislation%22,%22search%22:%22congressId:118%20AND%20billStatus:\%22Introduced\%22%22}&pageSort=latestAction%3Adesc'
    try:
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
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'basic-search-results-lists'))
        WebDriverWait(driver, 10).until(element_present)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        def get_text(bill, link):
            driver.get(base_url + link)
            element_present = EC.presence_of_element_located((By.ID, 'bill-summary'))
            WebDriverWait(driver, 10).until(element_present)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            div = soup.find('div', {'id':'bill-summary'})
            selector = div.find('div', {'class':'cdg-summary-wrapper'})
            summary = div.text.replace(selector.text, '')
            bill.summary = summary

            tabs = soup.find('ul', {'class':'tabs_links'})
            lis = tabs.find_all('li')
            for li in lis:
                if 'Text' in li.text:
                    a = li.find('a')
                    driver.get(base_url + a['href'])
                    break

            element_present = EC.presence_of_element_located((By.ID, 'bill-summary'))
            WebDriverWait(driver, 10).until(element_present)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            div = soup.find('div', {'id':'bill-summary'})
            selector = div.find('div', {'class':'cdg-summary-wrapper'})
            finalText = div.text.replace(selector.text, '')
            bill.bill_text_html = finalText
            toc_d = {}
            paragraphs = finalText.find_all('p')
            for p in paragraphs:
                if 'SECTION ' in p.text or 'SEC. ' in p.text:
                    toc_d[p.text] = p
            bill.bill_text_nav = json.dumps(dict(toc_d))
            version = soup.find('select', {'id':'textVersion'})
            options = version.find_all('option')
            for o in options:
                bill.bill_text_version = o.text
                break
            bill.save()
            return bill



        # congress = None
        congress = Parliament.objects.filter(country='USA', organization='Federal')[0]
        # print(soup)
        row = soup.find('ol', {'class':'basic-search-results-lists'})
        lis = row.find_all('li', {'class':'expanded'})
        n = 1
        for li in lis:
            print(n)
            n+=1
            # div = li.find('span', {'class':'visualIndicator'})
            # words = div.text.split(' ')
            # billType = ''
            # for word in words:
            #     billType = billType + word[0] + word[1:].lower()
            #     if len(words) > 1:
            #         billType = billType + ' '

            heading = li.find('span', {'class':'result-heading'})
            a = heading.find('a')
            billCode = a.text
            billLink = a['href']
            chamber = 'None'
            'JOINT RESOLUTION  S.J.Res.38'
            'RESOLUTION S.Res.518 '
            'RESOLUTION H.Res.956'
            'JOINT RESOLUTION H.J.Res.98'
            'LAW'
            'BILL'
            if 'H.R.' in a.text:
                chamber = 'House'
                billType = 'Bill'
            elif 'H.Res.' in a.text:
                chamber = 'House'
                billType = 'Resolution'
            elif 'H.J.Res.' in a.text:
                chamber = 'House'
                billType = 'Joint Resolution'
            elif 'S.J.Res' in a.text:
                chamber = 'Senate'
                billType = 'Joint Resolution'
            elif 'S.Res' in a.text:
                chamber = 'Senate'
                billType = 'Resolution'
            elif 'S.' in a.text:
                chamber = 'Senate'
                billType = 'Bill'
            print(chamber, billType)
            print(a.text)
            print(a['href'])
            header = heading.text.replace(a.text,'').replace(' — ','')
            print(header)
            x = header.find(' ')
            cong = header[:x].replace('st','').replace('nd','').replace('rd','').replace('th','')
            cong = int(cong)
            y = header.find(' (')
            year = header[y+1:].replace('(','').replace(')').strip()
            if congress.ParliamentNumber != cong:
                try: 
                    congress = Parliament.objects.filter(country='USA', organization='Federal', ParliamentNumber=cong)[0]
                except:
                    congress = Parliament(country='USA', organization='Federal', ParliamentNumber=cong, SessionNumber=1, start_date=datetime.datetime.now())
                    congress.save()
                    congress.end_previous('USA', 'Federal')

            title = li.find('span', {'class':'result-title'})
            print(title.text)
            items = li.find_all('span', {'class':'result-item'})
            try:
                bill = Bill.objects.filter(NumberCode=a.text, parliament=congress)[0]
            except:
                bill = Bill(NumberCode=billCode)
                bill.ParliamentNumber = congress.ParliamentNumber
                bill.SessionNumber = congress.SessionNumber
                bill.ShortTitle = header.text
                bill.type = billType
                bill.OriginatingChamberName = chamber
                if chamber == 'House':
                    bill.IsHouseBill = 'true'
                elif chamber == 'Senate':
                    bill.IsSenateBill = 'true'
                bill.parliament = congress
                bill.legis_link = billLink
                bill.save()
                bill.create_post()
            # if version == 'Became Law':
                if bill.IsSenateBill == 'true':
                    x = ['Introduced', 'Passed Senate', 'Passed House', 'To President', 'Became Law']
                else:
                    x = ['Introduced', 'Passed House', 'Passed Senate', 'To President', 'Became Law']
                for i in x:
                    try:
                        v = BillVersion.objects.filter(bill=bill, version=i)[0]
                    except:
                        v = BillVersion(bill=bill, version=i)
                        if i == 'Introduced':
                            v.empty = False
                            v.current = True
                            v.dateTime = bill.started
                        else:
                            v.empty = True
                        v.save()
                        v.create_post()
            old_latest = ''
            fetchText = False
            for item in items:
                if 'Sponsor:' in item.text:
                    sponsorItem = item
                    sponsors = sponsorItem.find_all('a')
                    sponsor = sponsors[0]
                    print(sponsor.text)
                    sponsorLink = sponsor['href']
                    '''https://www.congress.gov/member/david-trone/T000483?q=%7B%22search%22%3A%22congressId%3A118+AND+billStatus%3A%5C%22Introduced%5C%22%22%7D'''
                    print(sponsorLink)
                    q = sponsorLink.find('?q=')
                    w = sponsorLink[:q].rfind('/')
                    code = sponsorLink[w+1:q]
                    sponsorLink = sponsorLink[:q]
                    print(code)
                    try:
                        sponsorPerson = Person.objects.filter(gov_iden=code)[0]
                        bill.person = sponsorPerson
                    except:
                        x = sponsor.text.find(' [')
                        sponsorName = sponsor.text[:x]
                        bill.SponsorPersonName = sponsorName
                    print(sponsorItem.text)
                    txt = sponsorItem.text.replace('Sponsor: ', '').replace(sponsor.text,'')
                    try:
                        cosponsors = sponsors[1]
                        print('cosposonors', cosponsors.text, cosponsors['href'])
                        txt = txt.replace('Cosponsors: ', '').replace('(%s)'%(cosponsors.text),'')
                        if int(cosponsors.text) != len(bill.co_sponsors.all()):
                            driver.get(base_url + cosponsors['href'])
                            element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="main"]'))
                            WebDriverWait(driver, 10).until(element_present)
                            cosponsor_soup = BeautifulSoup(driver.page_source, 'html.parser')
                            div = cosponsor_soup.find('div', {'id':'main'})
                            trs = div.find_all('tr')
                            for tr in trs:
                                td = tr.find('td')
                                a = td.find('a')['href']
                                x = a.rfind('/')
                                code = a[x+1:]
                                try:
                                    coPerson = Person.objects.filter(gov_iden=code)[0]
                                    if coPerson not in bill.co_sponsors.all():
                                        bill.co_sponsors.add(coPerson)
                                except Exception as e:
                                    print(str(e))

                    except Exception as e:
                        print(str(e))
                    txt = txt.replace('(','').replace(')','').replace('Introduced ','')
                    print('--%s--' %(txt))
                    day = datetime.datetime.strptime(txt.strip(), '%m/%d/%Y')
                    print(day)
                    bill.started = day
                elif 'Committees:' in item.text:
                    committeeItem = item
                    committees = committeeItem.text.replace('Committees: ','')
                    if ';' in committees:
                        coms = committees.split(';')
                    else:
                        coms = ['%s' %(committees)]
                    org = None
                    bill.inCommittees = []
                    for c in coms:
                        # print('c',c)
                        if 'House - ' in c:
                            org = 'House'
                            c_title = c.replace('House - ','').replace(';','').strip()
                        elif 'Senate - ' in c:
                            org = 'Senate'
                            c_title = c.replace('Senate - ','').replace(';','').strip()
                        print(org, c_title)
                        try:
                            committee = Committee.objects.filter(Title=c_title, Organization=org, ParliamentNumber=congress.ParliamentNumber, SessionNumber=congress.SessionNumber)[0]
                        except:
                            committee = Committee(Title=c_title, Organization=org, ParliamentNumber=congress.ParliamentNumber, SessionNumber=congress.SessionNumber)
                            committee.save()
                            committee.create_post()
                        bill.inCommittees.add(committee)
                elif 'Committee Report:' in item.text:
                    committeeReport = item
                    a = committeeReport.find('a')
                    print('report', a.text)
                    print(a['href'])
                    meetingLink = base_url + a['href']
                    try:
                        comMeetting = CommitteeMeeting.objects.filter(govURL=meetingLink)[0]
                    except:
                        comMeetting = CommitteeMeeting(govURL=meetingLink, ParliamentNumber=congress.ParliamentNumber, SessionNumber=congress.SessionNumber)
                        comMeetting.save()
                        comMeetting.create_post()

                        driver.get(meetingLink)
                        element_present = EC.presence_of_element_located((By.ID, 'report'))
                        WebDriverWait(driver, 10).until(element_present)

                        report_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        overview = report_soup.find('div', {'class':'overview'})
                        trs = overview.find_all('tr')
                        for tr in trs:
                            if 'Accompanies' in tr.text:
                                NumberCode = tr.find('a').text
                                print(NumberCode)
                                try:
                                    bill = Bill.objects.filter(NumberCode=NumberCode)[0]
                                    comMeetting.bill = bill
                                except:
                                    bill = None
                            elif 'Committees' in tr.text:
                                a = tr.find('a')
                                title = a.text
                                org = None
                                if 'House' in title:
                                    org = 'House'
                                elif 'Senate' in title:
                                    org = 'Senate'
                                title = title.replace('House ','').replace('Senate ','').replace(' Committee','')
                                try:
                                    committee = Committee.objects.filter(title=title, Organization=org)[0]
                                    if not committee.govURL:
                                        committee.govURL = base_url + a['href']
                                        committee.save()
                                except:
                                    committee = Committee(Title=title, Organization=org, ParliamentNumber=congress.ParliamentNumber, SessionNumber=congress.SessionNumber)
                                    committee.save()
                                    committee.create_post()
                                comMeetting.committee = committee
                                comMeetting.Organization = org
                                print(org, '-', title)
                        div = report_soup.find('div', {'id':'report'})
                        pre = div.find('pre')
                        # print(pre)
                        comMeetting.report = pre
                        comMeetting.save()
                elif 'Latest Action:' in item.text:
                    latest = item
                    actionsLink = latest.find('a')
                    txt = latest.text.replace('Latest Action: ','').replace('(All Actions)','')
                    print(txt)
                    a = txt.find(' - ')
                    b = txt[a+3:].find(' ')
                    dt = txt[a+3:a+3+b]
                    day = datetime.datetime.strptime(dt.strip(), '%m/%d/%Y')
                    bill.LatestBillEventDateTime = day
                    latest = txt.replace(dt)
                    old_latest = bill.StatusNameEn
                    bill.StatusNameEn = latest
                    if '...' in txt:
                        print(actionsLink['href'])
                        
                        actions_url = base_url + actionsLink['href']
                        driver.get(actions_url)
                        element_present = EC.presence_of_element_located((By.ID, 'main'))
                        WebDriverWait(driver, 10).until(element_present)

                        actions_soup = BeautifulSoup(driver.page_source, 'html.parser')
                        main = actions_soup.find('div', {'id':'main'})
                        tbody = main.find('tbody')
                        trs = tbody.find_all('tr')
                        for tr in reversed(trs):
                            dt = tr.find('td', {'class':'date'}).text
                            #01/03/2024
                            date = datetime.datetime.strptime(dt.strip(), '%m/%d/%Y')
                            print(date)
                            actions = tr.find('td', {'class':'actions'})
                            span = actions.find('span')
                            txt = actions.text.replace(span.text,'').strip()
                            print(txt)
                            print(span.text.strip())
                            txt = txt + '\n' + span.text.strip()
                            print()
                            try:
                                billAction = BillAction.objects.filter(bill=bill, dateTime=date, text=txt)[0]
                            except:
                                billAction = BillAction(bill=bill, code=bill.NumberCode, dateTime=date, text=txt)
                                billAction.save()
                                billAction.create_post()


                elif 'Tracker:' in item.text:    
                    trackerItem = item
                    p = trackerItem.find('p', {'class':'hide_fromsighted'})
                    print(p.text)
                    def currentize_version(bill, version, dt):
                        versions = BillVersion.objects.filter(bill=bill)
                        for v in versions:
                            if v.version == version:
                                v.current = True
                                v.empty = False
                                v.dateTime = dt
                            else:
                                v.current = False
                            v.save()
                        try:
                            v = BillVersion.objects.filter(bill=bill, version=version)[0]
                        except:
                            v = BillVersion(bill=bill, version=version, code=bill.NumberCode)
                            v.save()
                            v.create_post()
                        v.current = True
                        v.empty = False
                        v.dateTime = dt
                        v.save()
                    status = p.text.replace('This bill has the status ')

                    if old_latest != latest:
                        bill.LatestCompletedBillStageDateTime = day
                        currentize_version(bill, status, day)
                    if 'Passed House' in p.text:
                        if not bill.PassedFirstChamberFirstReadingDateTime:
                            bill.PassedFirstChamberFirstReadingDateTime = day
                            bill.PassedFirstChamberFirstReading = 'true'
                            fetchText = True
                    elif 'Passed Senate' in p.text:
                        if not bill.PassedSecondChamberFirstReadingDateTime:
                            bill.PassedSecondChamberFirstReadingDateTime = day
                            bill.PassedSecondChamberFirstReading = 'true'
                            fetchText = True
                    elif 'Passed Senate' in p.text:
                        if not bill.PassedSecondChamberFirstReadingDateTime:
                            bill.PassedSecondChamberFirstReadingDateTime = day
                            bill.PassedSecondChamberFirstReading = 'true'
                            fetchText = True
                    elif 'President' in p.text:
                        if not bill.PassedThirdChamberDateTime:
                            bill.PassedThirdChamberDateTime = day
                            bill.PassedThirdChamber = 'true'
                            fetchText = True
                    elif 'Became Law' in p.text:
                        if not bill.ReceivedRoyalAssentDateTime:
                            bill.ReceivedRoyalAssentDateTime = day
                            bill.ReceivedRoyalAssent = 'true'
                            fetchText = True
            
            possible1 = '''A summary is in progress'''
            possible2 = '''after text becomes available'''
            possible3 = '''text has not been received'''
            if bill.bill_text_html == None or fetchText or possible1 in bill.summary or possible2 in bill.bill_text_html or possible3 in bill.bill_text_html:
                bill = get_text(bill, billLink)
            print('saving bill')
            bill.save()
            bill.update_post_time()



            print()
    except Exception as e:
        print(str(e))
    driver.quit()



def get_hansard(): #debate
    congress = Parliament.objects.filter(country='USA', organization='Federal').first()
    
    url = 'https://live.house.gov/'
    try:
        print("opening browser")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        driver = webdriver.Chrome(options=chrome_options)
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "normal"  #  Waits for full page load
        driver = webdriver.Chrome(desired_capabilities=caps, options=chrome_options)
        driver.get(url)

        element_present = EC.presence_of_element_located((By.XPATH, '//*[@id="activity-table"]/tbody'))
        WebDriverWait(driver, 10).until(element_present)

        soup = BeautifulSoup(driver.page_source, 'html.parser')    
    except Exception as e:
        print(str(e))

    driver.close()

    dt = soup.find('span', {'class':'display-date'})
    # WEDNESDAY, JANUARY 10, 2024
    today = datetime.datetime.strptime(dt.text, '%A, %B %m, %Y')
    print(today)
    
    table = soup.find('table', {'id':'activity-table'})
    body = table.find('tbody')
    trs = body.find_all('tr')
    A = None
    started = False
    ended = False
    position = 0
    for tr in reversed(trs):
        position += 1
        tds = tr.find_all('td')
        timeText = tds[0].text
        # 10:00:09 AM
        item_time = datetime.datetime.strptime(dt.text + '/' + timeText, '%A, %B %m, %Y/%I:%M:%S %p')
        billText = tds[1].text
        content = tds[2].text
        # print(item_time)
        # print(billText)
        # print(content)
        # print()
        if not A:
            try:
                A = Agenda.objects.filter(date_time__gte=date, date_time__lt=date + datetime.timedelta(days=1), gov_level='Federal', organization='House')[0]
            except:
                A = Agenda(date_time=item_time, gov_level='Federal', organization='House')
                A.current_status = 'Adjourned'
                A.save()
                A.create_post()
        if 'convened' in content.lower():
            started = True
            A.current_status = 'In Session'
        elif 'adjourned' in content.lower():
            ended = True
            A.current_status = content
            A.end_date_time = item_time
            A.save()
        try:
            agendaItem = AgendaItem.objects.filter(agenda=A, date_time=item_time, gov_level=A.gov_level, organization=A.organization)[0]
        except Exception as e:
            # print(str(e))
            agendaItem = AgendaItem(agenda=A, date_time=item_time, position=position, gov_level=A.gov_level, organization=A.organization)
            if billText:
                try:
                    bill = Bill.objects.filter(NumberCode=billText)[0]
                    agendaItem.bill = bill
                    agendaItem.agenda.bills.add(bill)
                    agendaItem.agenda.save()
                except:
                    bill = None
            agendaItem.save()
        


    try:
        H = Hansard.objects.filter(agenda=A)[0]
    except:
        H = None
    if started:
        if not H or H and H.completed_model == False:
            text = driver.find_element(By.XPATH, '//*[@id="transcript"]')
            text.click()
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            dt = soup.find('span', {'class':'display-date'})
            # WEDNESDAY, JANUARY 10, 2024
            date = datetime.datetime.strptime(dt.text, '%A, %B %m, %Y')
            print(date)
            table = soup.find('table', {'id':'transcript-table'})
            body = table.find('tbody')
            trs = body.find_all('tr')
            recognizedState = None
            H_terms = {}
            for tr in trs:
                ItemId = tr['data-uniqueid']
                tds = tr.find_all('td')
                name = tds[0].text
                timeText = tds[1].text
                # 10:00:09 AM
                date_time = datetime.datetime.strptime(dt.text + '/' + timeText, '%A, %B %m, %Y/%I:%M:%S %p')
                content = tds[2].text.replace('[...]', '')
                if 'RECOGNIZES' in content or 'RECOGNIZED' in content or 'RECOGNITION' in content:
                    for state in states.values():
                        if state.upper() in content:
                            recognizedState = state
                            break

                if not H:
                    try:
                        H = Hansard.objects.filter(agenda=A)[0]
                    except:
                        H = Hansard(agenda=A, ParliamentNumber=congress.ParliamentNumber, SessionNumber=congress.SessionNumber, Publication_date_time=date_time, Organization='House')
                        day = datetime.datetime.strftime(day, '%Y-%m-%d')
                        H.gov_page = url + '?date=%s' %(day)
                        H.save()
                        H.create_post()
                print(date_time)
                # print(name)
                # if recognizedState:
                #     print('---', recognizedState)
                # print(content)
                # print()
                first_name = None
                last_name = None
                title = None
                if '. ' in name:
                    a = name.find('. ')+2
                    last_name = name[:a]
                else:
                    names = name.split()
                    last_name = names[-1]
                    first_name = names[0]
                # elif 'The Clerk' in name or 'The Speaker Pro Tempore' in name or 
                if 'The Speaker' in name:
                    title = 'The Speaker'
                if title:
                    try:
                        r = Role.objects.filter(position=title, parliament=congress)[0]
                        person = r.person
                    except:
                        person = None
                if not person:
                    try:
                        r = Role.objects.filter(position='Congressional Representative').filter(person__last_name__icontains=last_name)
                        if r.count() > 1:
                            try:
                                r = Role.objects.filter(position='Congressional Representative', current=True, riding__province__name=recognizedState).filter(person__last_name__icontains=last_name)[0]
                                person = r.person
                            except:
                                r = None
                        else:
                            person = r[0].person

                    except:
                        try:
                            person = Person.objects.filter(full_name=name)[0]
                        except:
                            person = Person(full_name=name)
                            # person.Region_obj = 
                            person.first_name = first_name
                            person.last_name = last_name
                            person.save()
                            person.create_post()

                try:
                    h = HansardItem.objects.filter(hansard=H, person=person, Item_date_time=date_time)[0]
                    new = False
                except:
                    h = HansardItem(hansard=H, person=person, Item_date_time=date_time)
                    h.ItemId = ItemId
                    h.Content = content
                    h.Terms = []
                    h.save()
                    h.create_post()
                    new = True
                if new:
                    h = HansardItem.objects.filter(id=h.id)[0] #get keywords created in create_post
                if h.keywords:
                    for k in h.keywords[:10]:
                        text = k[0].upper() + k[1:]
                        if not text in H_terms:
                            H_terms[text] = 1
                        else:
                            H_terms[text] += 1
                
                H.has_transcript = True
                H.apply_terms(H_terms)
                people = HansardItem.objects.filter(hansard=H)
                H_people = {}
                for p in people:
                    if not p.person.id in H_people:
                        H_people[p.person.id] = 1
                    else:
                        H_people[p.person.id] += 1
                H_people = sorted(H_people.items(), key=operator.itemgetter(1),reverse=True)
                H_people = dict(H_people)
                H.peopleText = json.dumps(H_people)
                if ended:
                    H.completed_model = True
                    H.save()
                    sprenderize(H)
                else:
                    H.save()




