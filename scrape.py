#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 18:03:10 2021

@author: tombearpark
"""
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import re
import os
import time
from datetime import date, timedelta
import glob
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import exceptions  
from selenium.webdriver.common.action_chains import ActionChains


# Variables options

driver_location  = "/Users/tombearpark/Documents/chromedriver"
out_location     = "/Volumes/GoogleDrive/Shared drives/india_mortality/"
ward_input       = '50000227'

#%% Query functions        

def get_driver(driver_location):
    # Initialise browser, load the home webpage 
    driver = webdriver.Chrome(driver_location)
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
    
    time.sleep(2)
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


#%% Run the whole thing, save a csv, this is just for a 20 point situation, 
# as I cant get the scrolling to work at the moment

def write_fail(directory, line_to_write):
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_object = open(directory + '/bad_reads.txt', 'a')
    file_object.write("\n")
    file_object.write(line_to_write)
    file_object.close()

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
        

def run_extract(ward_input, start_date_input, end_date_input, 
                driver, out_location):

    try:
        make_query(ward_input, start_date_input, end_date_input, driver)
    except:
        
        print('hoping to wait out the problem!')
        time.sleep(10)
        driver.close()
        driver = get_driver(driver_location)
        make_query(ward_input, start_date_input, end_date_input, driver)
    finally: 
        save_data(ward_input, start_date_input, end_date_input, driver, 
                  out_location)


#%% Very slow but working loop...

# Test on a single date-ward query
#start_date_input = '08.01.2009'
#end_date_input   = '08.01.2009'

# Test on a single year-ward, running a day at a time
start_date = date(1987, 12, 30)

driver = get_driver(driver_location)

for days in range(1, 366 * 30):
    print(days)
    
    time.sleep(0.5)
    start_date = start_date + timedelta(days = 1)
    print(start_date)
    start_date_input = start_date.strftime("%d.%m.%Y")
    end_date_input = start_date_input
    
    # Stick in a try except thing - when it doesnt work it usually just needs 
    # a break
    try:
        run_extract(ward_input, start_date_input, end_date_input, 
                driver, out_location)
    except:
        print(start_date)
        print('bad try! Check inputs, but probably its a page loading issue')
        file_name =  (start_date_input.replace(".", "") + "_" + 
                        end_date_input.replace(".", ""))
        directory = out_location + "w" + ward_input + "/" + start_date_input[-4:]
        write_fail(directory, file_name)  
        
        
        
#%% Everything below here is unfinished and (probably) doesn't work

# missing 08.01.2009!!-






# Join all files together for fun! 
path = "/Volumes/GoogleDrive/Shared drives/india_mortality/w50000227/"
all_files = glob.glob(os.path.join(path, "*.csv"))
df_from_each_file = (pd.read_csv(f) for f in all_files)
concatenated_df   = pd.concat(df_from_each_file, ignore_index=True)
concatenated_df = concatenated_df[concatenated_df.columns.drop(
    list(concatenated_df.filter(regex='Unnamed')))]
out = concatenated_df.dropna(0, how = 'all')




#%% Trying to do something fancier - so far doesn't work
def scroll_down(length, driver):
        i = 1
        sleep_time = 2
        while i < length + 1:
            s = driver.find_element_by_xpath('//*[@id="WDB4-scrollV-Nxt"]')
            actions = ActionChains(driver)
            actions.move_to_element(s).perform()
            print(i)
            wait = WebDriverWait(driver, 10)
            scroller = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="WDB4-scrollV-Nxt"]')))
            time.sleep(0.2)
            # This little hack needed: https://stackoverflow.com/questions/27003423/staleelementreferenceexception-on-python-selenium
            try:
                scroller.click()
                i = i + 1
            except exceptions.StaleElementReferenceException as e:
                print(e)
                time.sleep(sleep_time)
                pass

## Trying to work out how to scroll, so can pluck mutiple days at a time

    
driver = make_query(ward_input, start_date_input, end_date_input)

# Extract the data 
df_list = extract_df_list_from_html(driver)
df      = data_from_df_list(df_list)
n       = num_records_from_df_list(df_list)

# check - this should be a 20 row dataframe
len(df[df.columns[0]]) == 20

#scroll_down(20, driver)

num = 0


while num < n:
    print("-- " + str(num) + " -- ")
    if num + 20 < n:
        scroller = driver.find_element_by_xpath('//*[@id="WDB4-scrollV-Nxt"]')
        scroll_down(20, driver)
        df = df.append(get_df(driver))
        num = num + 20
        len(df[df.columns[0]]) == num
    else:
        scroller = driver.find_element_by_xpath('//*[@id="WDB4-scrollV-Nxt"]')
        print(n - num)
        scroll_down(n - num, driver)
        df = df.append(get_df(driver))
        len(df[df.columns[0]]) == n
        







