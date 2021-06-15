#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 18:03:10 2021

@author: tombearpark
"""

import pandas as pd
import re
import os
import time
from datetime import date, timedelta
import glob
import sys
import pathlib

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions  
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

# send me a text if something goes wrong
from twilio.rest import Client
client = Client("AC3861620327ef49f8313593d982b3fb63", 
	"2cd21796005f3c5be0a6feb4537c34bf")

# Variables options

driver_location  = "/Users/tombearpark/Documents/chromedriver"
out_location     = "/Volumes/GoogleDrive/Shared drives/india_mortality/raw/"

#%% Query functions        

def get_driver(driver_location, options = Options()):
    # Initialise browser, load the home webpage 
    driver = webdriver.Chrome(driver_location, options = options)
    driver.get("https://portal.mcgm.gov.in/irj/portal/anonymous/qldldregreport")
    # Wait for iframe to be available, then go into it. 
    WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, 
                                        'Death Registration Report')))

    print('sleeping for 5 seconds to be safe!')    
    time.sleep(5)
    return(driver)

def make_query(ward_input, start_date_input, end_date_input, driver):
    
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="WD2E"]')))
        
    # Send in the relevant info, make the search
    ward = driver.find_element_by_xpath('//*[@id="WD2E"]')
    ward.clear()
    ward.send_keys(ward_input)
    
    date_start = driver.find_element_by_xpath('//*[@id="WD42"]')
    date_start.clear()
    date_start.send_keys(start_date_input)
    
    date_end = driver.find_element_by_xpath('//*[@id="WD46"]')
    date_end.clear()
    date_end.send_keys(end_date_input)
    
    search = driver.find_element_by_xpath('//*[@id="WDAC"]')
    search.click()
    
    print('clicked, taking a little break')
    time.sleep(3)
    
    return(driver)



#%% helper functions, for dealing with some parsing of html

def extract_df_list_from_html(driver):
    # Get all the data
    data    = driver.page_source
    df_list = pd.read_html(data)
    return(df_list)

def data_from_df_list(df_list):
    # Extract import information - its in the final dataframe in the list  
    df = df_list[len(df_list)-1]
    df = df.dropna('index', how = 'all') # remove rows with nothing in them
    return(df)

def num_records_from_df_list(df_list):
    # get the number of records in this query, that we will need to scroll through
    time.sleep(.1)
    r = df_list[1].iat[0,0]
    print("records: " + r)
    if 'Data not Found' in r:
        n_records = 0
    else:
        n_records = int(''.join(filter(str.isdigit, r)))
    return(n_records)

def get_df(driver):
    df_list = extract_df_list_from_html(driver)
    df      = data_from_df_list(df_list)
    return(df)


#%% Functions for running and saving the outputs

def write_fail(directory, line_to_write):
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    file_object = open(directory + '/bad_reads.txt', 'a')
    file_object.write("\n")
    file_object.write(line_to_write)
    file_object.close()

def get_file_name(out_location, ward_input, start_date_input, end_date_input):
    directory = out_location + "w" + ward_input + "/" + start_date_input[-4:]
    file_name =  (start_date_input.replace(".", "") + "_" + 
                    end_date_input.replace(".", "") )
    file_out = (directory + "/d" + file_name + ".csv")
    return(file_out)

def save_data(ward_input, start_date_input, 
              end_date_input, driver, out_location):
    
    time.sleep(.2)
    
    df_list = extract_df_list_from_html(driver)
    df      = data_from_df_list(df_list)
    n       = num_records_from_df_list(df_list)
    
    
    directory = out_location + "w" + ward_input + "/" + start_date_input[-4:]
    file_name =  (start_date_input.replace(".", "") + "_" + 
                    end_date_input.replace(".", "") )
        
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    if n <= 20:
        file_out = (directory + "/d" + file_name + ".csv")
        df.to_csv(os.path.join(file_out))
        print("written " + file_out)
    else:
        write_fail(directory, file_name + ", n = " + str(n))
        print('this one had n > 20')
        

def run_extract(ward_input, start_date_input, end_date_input, 
                driver, out_location):

    make_query(ward_input, start_date_input, end_date_input, driver)

    save_data(ward_input, start_date_input, end_date_input, driver, 
              out_location)
    
    return(driver)


#%% Very slow but working loop...

# Test on a single date-ward query
#start_date_input = '08.01.2009'
#end_date_input   = '08.01.2009'

# Test on a single year-ward, running a day at a time

#done...
#ward_input       = '50000227'

#running interactively...
# ward_input       = '50000042'
# year = 1997

#running as script: 
#ward_input      = '50000076'

if __name__ == "__main__":
    
    ward_input       = sys.argv[1]
    year             = int(sys.argv[2])
    start_date       = date(year, 1, 1)


    opts = Options()
    opts.headless = True
    driver = get_driver(driver_location, options = opts)

    for days in range(1, 366 * 33):
        
        print(days)
        start_date = start_date + timedelta(days = 1)
        print(start_date)
        start_date_input = start_date.strftime("%d.%m.%Y")
        
        end_date_input = start_date_input
        target = get_file_name(out_location, ward_input, start_date_input, end_date_input)
        if os.path.isfile(target):
            print('skipping, already have this one')
            continue
        
        time.sleep(0.5)
    
        # Stick in a try except thing - when it doesnt work it usually just needs 
        # a break
        try:
            run_extract(ward_input, start_date_input, end_date_input, 
                    driver, out_location)
            message = ward_input + "going well"
            bad = False
            continue
        
        except:
            print(start_date)
            print('issue has arisen, but hoping to reload and wait out the problem!')
            time.sleep(10)
            driver.close()
            del driver 
            print('driver deleted, stopping for 10 seconds')
            time.sleep(10)
            print('lets try again, restarting the process ')
            time.sleep(5)
            driver = get_driver(driver_location, options = opts)
            try:
                run_extract(ward_input, start_date_input, end_date_input, 
                    driver, out_location)
                message = "going well"
                
                bad = False
                print('woooo, error resolved itself!')
                continue
            except:
                message = ("Something went wrong with " + ward_input + 
                           " at date " + start_date)
                client.messages.create(
                    to="++44 7740 139523", from_="+14153600026", body=message)
                
                print('bad try! Check inputs, but probably its a page loading issue')
                file_name =  (start_date_input.replace(".", "") + "_" + 
                                end_date_input.replace(".", ""))
                directory = out_location + "w" + ward_input + "/" + start_date_input[-4:]
                write_fail(directory, file_name)  
    
                bad = True
                break
    
    
    
    if bad == False:
        client.messages.create(
                to="++44 7740 139523", from_="+14153600026", 
                body=("great news, ward ran! " + message))



