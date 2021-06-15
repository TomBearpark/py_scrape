#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 12 18:59:27 2021

@author: tombearpark
"""
#%%
# Scrape the ward names to loop over
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import time 
import pandas as pd

#%%
driver_location  = "/Users/tombearpark/Documents/chromedriver"
out_location     = "/Volumes/GoogleDrive/Shared drives/india_mortality/"

driver = webdriver.Chrome(driver_location)
driver.get("https://portal.mcgm.gov.in/irj/portal/anonymous/qldldregreport")
WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, 
                                        'Death Registration Report')))

print('sleeping for 5 seconds to be safe!')    
time.sleep(5)
search = driver.find_element_by_xpath('//*[@id="WD2E-btn"]')
search.click()
data    = driver.page_source
df_list = pd.read_html(data)
