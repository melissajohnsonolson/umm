# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 16:39:47 2019

@author: johns
"""

from __future__ import print_function
import bs4
from bs4 import BeautifulSoup
import requests
from six.moves.urllib import parse
import pandas as pd
import numpy as np
from docx import Document
import re
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import random
import time

os.chdir('C:/Users/johns/Documents/Machine Learning/science funding project')

"""Here we set up a way to scrap career and program information from the careeronestop
site. It first requires expanding lists followed by scrapping to get the name for
every career. That name is then used to generate a url string that will allow us to
scrape program information for each career"""

#url = 'https://www.careeronestop.org/Toolkit/Careers/Occupations/occupation-profile.aspx?newsearch=true'
#driver = webdriver.Chrome()
#driver.get(url)
#driver.find_element_by_class_name('module-title').click()
#driver.implicitly_wait(30)
#parents = driver.find_elements_by_class_name('OccupationParent')
#parent_length = len(parents)
#for i in range(0,parent_length):
#    time.sleep(5)
#    parents = driver.find_elements_by_class_name('OccupationParent')
#    parents[i].click()
#page = BeautifulSoup(driver.page_source)

#def has_click_on_and_data_id(tag):
#    return tag.has_attr('onclick') and tag.has_attr('data-id')
#occupations = [item['onclick'] for item in page.findAll(has_click_on_and_data_id)]
#occupations  = pd.DataFrame([re.search(r'\((.*?)\)',s).group(1) for s in occupations])
#occupations = occupations[0].str.split('\', \'', expand = True)
#occupations.columns = ['Career','SOC']
#occupations['Career'] = occupations['Career'].str.strip('\'')
#occupations['SOC'] = occupations['SOC'].str.strip('\'')

#data = pd.DataFrame(columns = ['Career','SOC', 'Programs'])
#for j in range(668,len(occupations)):
 #   url1 = occupations['Career'][j].replace(' ', '%20')
  #  url2 = occupations['SOC'][j].replace('-', '').replace('.','')
   # url_check = 'https://www.careeronestop.org/Toolkit/Careers/Occupations/occupation-profile.aspx?keyword='+url1+'&onetcode='+url2+'&location=UNITED%20STATES'
   # response = requests.get(url_check)
   # time.sleep(0.5)
   # pagex = BeautifulSoup(response.text, 'html.parser' )
   # li = pagex.find('ul', {'id': 'programsThatPrepareYouList1Pane'})
   # if li:
   #     children = li.findChildren("li" , recursive=False)
   # if children:
   #     programs = [item.text for item in children]
   # else:
   #     programs = ['None']
   # data.loc[len(data) + 1] = [occupations['Career'][j],occupations['SOC'][j], programs]
#data.to_csv('occupations with programs.csv', index = False)

"""The above script is only run once and the data was saved as a csv. We reload it here.
We also need to clean up the Programs columns so that we can create a list of programs
as the original data simply saved as a single string"""

data = pd.read_csv('occupations with programs.csv')    
data['SOC'] = data['SOC'].apply(lambda x: re.sub('\.\d{2}$', '', x))    
data['Programs'] = data['Programs'].apply(lambda x: x.replace('[',''))
data['Programs'] = data['Programs'].apply(lambda x: x.replace(']',''))
#data['Programs'] = data['Programs'].apply(lambda x: x.replace('\'',''))
#data['Programs'] = data['Programs'].apply(lambda x: x.replace(', and',', '))
#data['Programs'] = data['Programs'].str.strip()     
data['Programs'] = data['Programs'].apply(lambda x: x.split('\''))
data['Programs'] = data['Programs'].apply(lambda x:[i for i in x if i != str('')])
data['Programs'] = data['Programs'].apply(lambda x:[i for i in x if i != str(', ')])
data['Programs'] = data['Programs'].apply(lambda x: [y.strip() for y in x])



"""From the BLS database we load in the education requirements for each occupation.
We then select the jobs that need a Bachelors degree and 5 years or less experience
This data is taken from table 5.4 at 
https://www.bls.gov/emp/documentation/education-training-system.htm"""

experience = pd.read_csv('education and job requirements.csv').dropna()   
experience = experience[experience['Degree'].str.contains('Bachelor\'s degree')] 
experience = experience[~experience['Experience'].str.contains('5 years or more')]    
#We merge the experience data with the program and occupation data
total = pd.merge(data, experience, how = 'inner', on = 'SOC')
total = total[['Career', 'SOC', 'Programs','Degree', 'Experience']]

"""Here we are going to scrape the majors from Morris that are associated
with each program. This also comes from the CareerOneStop site. This only takes
the first 10 entries, not all entries"""
#test = [items for items in [item for item in total['Programs']]]
#flat_list = [item for sublist in test for item in sublist]
#flat_list = pd.DataFrame(flat_list)
#programs = list(flat_list[0].unique())

#program_key = pd.DataFrame(columns = ('School', 'Major','Program'))
#for i in range(358, len(programs)):
#    url1 = programs[i].replace(' ', '%20')
#    url_tot = 'https://www.careeronestop.org/Toolkit/Training/find-local-training.aspx?keyword='+url1+'&location=Morris,%20MN&ajax=0&post=y&lang=en'
#    page = requests.get(url_tot)
#    t = BeautifulSoup(page.text, 'html.parser')
#    table = t.findAll('table')
#    if table:
#        rows = table[0].findChildren('tr')
#        if rows:
 #           for i in range(1, len(rows)):
 #               cells = rows[i].findChildren('td')
 #               school = cells[0].text
 #               major = cells[1].text
 #               program_key.loc[len(program_key.index)] = [major,programs[i]]





"""Load and Prepare the list key of majors and programs that was gathered
from online"""

program_key = pd.read_csv('site majors and programs.csv')
program_key = program_key.groupby('Major', as_index=False)['Program'].agg({'list':(lambda x: list(x))})
#We will create a 'flat list' of all programs to be used for filtering
flat_list = [items for items in [item for item in program_key['Program']]]
#flat_list = [str(item) for sublist in test for item in sublist]
flat_list = pd.DataFrame(flat_list)
programs_incl = list(flat_list[0].unique())
programs_incl = [x for x in programs_incl if str(x) != 'nan']

"""Now we want to figure out the jobs from total by progam - if the program is
in the program list above, we keep that job. If not, we remove the job as we're
only interested in jobs that corresspond to a major"""

target_jobs = total[total['Programs'].apply(lambda x: any(b in programs_incl for b in x))].copy()

"""Now we want to tie a major to each job"""

def major_match(jobs):
    maj=[]
    for i in range(0,len(program_key)):
        if any([job in program_key['Program'][i] for job in jobs]):
            maj.append(program_key['Major'][i])
    return maj
        

target_jobs['majors']=target_jobs['Programs'].apply(major_match)

"""Now we tie the target jobs with the jobs data. The jobs data comes from May 2018
Metropolitan and nonmetropolitan area excel file at https://www.bls.gov/oes/tables.htm
I filtered out the results for Minnesota from the metropolitan and nonmetropolitan
data sets and combined into a single csv file that's loaded below."""

jobs = pd.read_csv('jobs data.csv')
jobs = jobs[['AREA_NAME', 'OCC_CODE', 'OCC_TITLE',
       'TOT_EMP', 'A_MEDIAN']]
#We need to do some cleaning to make the total employment number and median annual
#wage numbers numeric
jobs['TOT_EMP'] = jobs['TOT_EMP'].apply(lambda x: x.replace(',','')).replace('**', 0)
jobs['TOT_EMP'] = pd.to_numeric(jobs['TOT_EMP'])
jobs['A_MEDIAN'] = jobs['A_MEDIAN'].replace('#', '0').apply(lambda x: x.replace(',','')).replace('*', 0)
jobs['A_MEDIAN'] = pd.to_numeric(jobs['A_MEDIAN'])

"""Now can merge the target_jobs with the jobs data."""
jobs_and_majors = pd.merge(target_jobs, jobs, how = 'inner', left_on ='Career', right_on= 'OCC_TITLE' )
jobs_and_majors =jobs_and_majors[['Career', 'SOC', 'Programs', 'Degree', 'Experience', 'majors',
       'AREA_NAME', 'TOT_EMP','A_MEDIAN']]
jobs_and_majors.rename(columns={'AREA_NAME':'Area', 'TOT_EMP': 'Total Employment', 'A_MEDIAN':'Median Annual Earnings'}, inplace = True)
#Here we expand the majors list so that each row has a single major attached to it.
s = jobs_and_majors.apply(lambda x: pd.Series(x['majors']),axis=1).stack().reset_index(level=1, drop=True)
s.name = 'majors'
jobs_and_majors = jobs_and_majors.drop('majors', axis=1).join(s).reset_index(drop = True)
county_key = pd.read_csv('County Key.csv')
jobs_and_majors = pd.merge(county_key, jobs_and_majors, left_on = 'Code', right_on = 'Area', how = 'left')
jobs_and_majors = jobs_and_majors[['County','Career', 'SOC', 'Programs', 'Degree', 'Experience',
       'Area', 'Total Employment', 'Median Annual Earnings', 'majors']]
jobs_and_majors=jobs_and_majors[jobs_and_majors['Total Employment'] >0]
jobs_and_majors.to_csv('jobs set.csv', index = False)