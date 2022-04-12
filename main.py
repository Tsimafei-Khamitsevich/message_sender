# -*- coding: utf-8 -*-

from selenium import webdriver
import time
import os
import shutil
import re
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime

# paths : 
    
# folder that stores files to be sended
sms_fld = "files_to_send"
# my flash drive
from_path = 'F:\\SMS'
# full path to 'sms_fld'
to_path = os.path.join(os.getcwd(), sms_fld)
# folder that stores previously sended files
archive_fld = 'sended'


def standartize_file_names(path):
    """
    Renames files so that they comply
    with standarts
    
    Standarts:
        No double or more consecutive spaces
        No dots at the end of file name before
    extension
    """
    
    file_names = os.listdir(path)
    space_pattern = re.compile(r"\s{2,}")
    dot_pattern = re.compile(r"\.$")
    
    for file_name in file_names:
        
        name, ext = os.path.splitext(file_name)
        new_name = space_pattern.sub(
            " ", dot_pattern.sub("", name)
            )
        
        old_file_path = os.path.join(path, file_name)
        new_file_path = os.path.join(path, new_name + ext)
        os.rename(old_file_path, new_file_path)
        
    
def open_browser():
    """
    Opens Firefox browser
    """
    
    driver = webdriver.Firefox(executable_path="geckodriver")
    driver.maximize_window()
    return driver

    
def login(driver):
    """
    Login on https://mobilemarketing.by/login
    webpage by using login and password stored 
    in credentials.txt file
    """
    
    credentials = extract_config_from_file("credentials.txt")
        
    driver.get("https://mobilemarketing.by/login")
    driver.find_element(by=By.XPATH, value="//input[@id='username']").send_keys(credentials['login'])
    driver.find_element(by=By.XPATH, value="//input[@id='password']").send_keys(credentials['password'])
    driver.find_element(by=By.XPATH, value="//button[@id='process']").click()
    
    return driver


def list_files(standartize, path):
    """
    Returns file names stored in directory, 
    provided through variable 'path'.
    
    standartize (bool): standartization
    involves replace double or more spaces 
    with one
    """
    
    file_names = os.listdir(path)
    if standartize:
        file_names = [os.path.splitext(file)[0] for file in file_names]
        return [' '.join(file.split()) for file in file_names]
    else:
        return file_names


def extract_config_from_file(file_name):
    """
    Reads variables stored in file
    and returns them in dictionary.
    """
    
    keys, values = [], []
    data = []
    with open(file_name, "r", encoding="utf-8") as f:
        
        for line in f.readlines():
            line = line.strip("\n")
            data.append(line.split(": ", maxsplit=1))
            
        f.close()
        
    return dict(data)


def load_files(driver):
    """
    !!!Does not work properly!!!
    
    Loads files to the website
    one by one.
    """
    
    # config = extract_config_from_file("config.txt")
    # path_external = os.path.join(config["path_to_app"], sms_fld)
    
    path_external = os.path.join(os.getcwd(), sms_fld)
    
    file_names = list_files(False)
    
    loaded_files = []
    wait = WebDriverWait(driver, 20, 5)
    
    for file in file_names:
        
        file_path = os.path.join(path_external, file)
    
        driver.get("https://smsline.by/iface/main#/base/load")
        
        uploader = driver.find_element(
            by=By.XPATH, 
            value="/html/body/div[2]/div[2]/div[2]/div/div/div/div/div[1]/form/div/div[1]/span[1]/input")
        uploader.send_keys(file_path)
       
        
        button = driver.find_element(by=By.XPATH, 
                                              value="//button[@class='btn btn-primary']")
        driver.execute_script("arguments[0].click()", button)
        
        
        div1 = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@class='panel panel-danger'] | //div[@class='panel panel-success']")
            ))
        div = div1.find_element(by=By.XPATH,
                                         value=".//div[@class='panel-heading']")
            
        mes = div.text
        ind = mes.find(":")
        
        
        print(div)
        print(mes)
        print(mes[:ind])
        print(ind)
                
        if mes[:ind] == "База успешно загружена":
            loaded_files.append(file)
            print(f"successfully loaded {file}")
            
        elif mes[:ind] == "Ошибка загрузки файла":
            print(f"load error {file}")
        
        else:
            print("")
            raise Exception ("Uploading files: unknown message")
        
        driver.find_element(by=By.XPATH, 
                                     value="//button[@class='btn btn-primary col-lg-2 pull-right']").click()
    
    return driver, loaded_files


def load_all_files(driver):
    """
    Loads the files onto the website, after
    checks load status.
    Returns list of loaded files.
    """
    
    path_external = os.path.join(os.getcwd(), sms_fld)
    
    file_names = list_files(False, sms_fld)
    
    
    wait = WebDriverWait(driver, 60, 5)
    
    driver.get("https://smsline.by/iface/main#/base/load")
    
    uploader = driver.find_element(
        by=By.XPATH, 
        value="/html/body/div[2]/div[2]/div[2]/div/div/div/div/div[1]/form/div/div[1]/span[1]/input")
    
    for file in file_names:
        file_path = os.path.join(path_external, file)
        uploader.send_keys(file_path)
        
    button = driver.find_element(by=By.XPATH, value="//button[@class='btn btn-primary']")
    driver.execute_script("arguments[0].click()", button)
    
    div = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[@class='modal-body ng-scope']")
        ))
    div = div.find_elements_by_xpath(".//div[@class='panel-heading']")
    
    loaded, load_error = [], []
    unknown_name, unknown_mes = [], []
    
    for i in div:
        try:
            i = i.text
        except:
            print("exception")
            print(i)
            continue
        
        status = {"success": "База успешно загружена: ",
                  "error": "Ошибка загрузки файла: "}
        
        if i.find(status["success"]) != -1:
            name = extract_file_name(i, status["success"])
            if name in file_names:
                loaded.append(name)
            else:
                unknown_name.append(name)
                
        elif i.find(status["error"]) != -1:
             name = extract_file_name(i, status["error"])
             if name in file_names:
                 load_error.append(name)
             else:
                 unknown_name.append(name)
        else:
            unknown_mes.append(i)
    
    report_load(loaded, load_error, unknown_name, unknown_mes)
    
    driver.find_element(by=By.XPATH, value="//button[@class='btn btn-primary col-lg-2 pull-right']").click()
    
    return driver, loaded


def report_load(loaded, load_error, unknown_name, unknown_mes):
    """
    Prints out files by category.
    The categories are:
        - loaded
        - not loaded
        - file name in the message does not
    corresponde to any loaded file name
        - fails to extract Load status from mess
    """
    
    print('-------------------------------------------------')
    print("Load report:")
    print(f"Successfully loadded: {loaded}")
    print(f"Not loadded: {load_error}")
    print(f"Extracted name is not recognised: {unknown_name}")
    print(f"Fails to extract Load status from mess: {unknown_mes}")
    print('-------------------------------------------------')
    print()
    

def discard_extension(file):
    """
    Returns a file name without extension
    """
    
    # first version
    # pattern = re.compile("(.+?)(\.xlsx|\.+xls)")
    # return pattern.search(file).group(1)
    
    # bug: if there are already no extension 
    # it will cut up file name
    return os.path.splitext(file)[0]
    
     
def discard_extensions(files):
    """
    Maps list of file names to discard_extension
    function
    """
    return list(map(discard_extension, files))


def extract_file_name(s, status):
    """
    Extracts file name from message
    without extension.
    
    s: message
    status: status part of the message
    """
    s = s.replace(status, "")
    pattern = re.compile(".+?\.(xlsx|xls)")
    return pattern.search(s).group(0)
    

def to_datetime_object(chunks):
    """
    Takes iterable of broken into
    parts file name and converts
    datatime part into datetime
    object. Finally returns updated
    iterable.
    """
    
    return (chunks[0], 
            datetime.strptime(chunks[1], "%Y-%m-%d %H:%M:%S"), 
            chunks[2])

def select_file_name_to_send_version_1(select, file):
    """
    !!!Not fully developed!!!
    
    Intend to have the same functionality
    as 'select_file_name_to_send' function
    has
    """
    
    matches = []
    pattern = re.compile("^((" + file + ")|(" + file + ") \((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)" + ")$")
    
    for option in select.options[:100:-1]:
        
        text = option.get_attribute("text")
        val = option.get_attribute("value")
        match = pattern.match(text)
        if match:
            # print(val, ' ', match.group(0))
            matches.append(list(match.group(1, 4)) + [val])
    
    print(matches)
    print()
            
    chosen = None
    with_date = list(filter(lambda x: x[1]!=None, matches))
    
    if with_date:
        with_date = list(map(to_datetime_object, with_date))
        with_date.sort(key=lambda x: x[1], reverse=True)
        chosen = with_date[0]
    else:
        chosen = matches[0]
        
    #sorted(matches, key=lambda x: x[1])
    
    print(with_date)
    print()
    #print(with_date[0])
    print()
    print(chosen)
    

def select_file_name_to_send(select, file):
    """
    Chooses last loaded file name.
    In case with repetetive file names,
    it will be file that has latest 
    load date.
    In case with one file,
    it will be the file.
    """
    
    pattern = re.compile("^((" + file + ")|(" + file + ") \((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\)" + ")$")
    
    for option in select.options[:100:-1]:
        
        text = option.get_attribute("text")
        match = pattern.match(text)
        if match:
            return option.get_attribute("value")
        
    return None


def send_sms(driver, loaded_files):
    """
    Repetetivly sends files provided
    in 'loaded_files' variable
    """
    
    loaded_files = discard_extensions(loaded_files)
    
    for file in loaded_files:
        
        driver.get("https://smsline.by/iface/main#/spam/new")
        
        wait = WebDriverWait(driver, 120)
        wait.until(EC.invisibility_of_element(
            (By.XPATH, "//div[@class='loading-shadow ng-isolate-scope vhidden']")
            ))
        sel = wait.until(EC.element_to_be_clickable(
            (By.NAME, "selectIssn_0")
            ))
        time.sleep(2)
        sel = Select(sel)
        
        # extracting data to fulfill sending form with
        message_details = extract_config_from_file('message_details.txt')
        
        sel.select_by_visible_text(message_details['service_number'])
        
        sel = Select(driver.find_element(by=By.NAME, value="selectBase"))
        
        value = select_file_name_to_send(sel, file)
        
        if value:
            sel.select_by_value(value)
        else:
            sel.select_by_visible_text(file)
        
        driver.find_element(
            by=By.XPATH,
            value="//textarea[@name='inputText_0']"
            ).send_keys(message_details['message_text'])
        
        driver.find_element(
            by=By.XPATH,
            value="/html/body/div[2]/div[2]/div[2]/div/div/form/div[6]/div/button"
            ).click()
        time.sleep(5)


def move_sended_files(loaded_files):
    """
    Moves sended files from 'files_to_send'
    to 'sended' directory
    """
    
    try:
        shutil.rmtree(archive_fld)
    except FileNotFoundError:
        print(f'Folder {archive_fld} not found')
        
    os.mkdir(archive_fld)
    time.sleep(2)
    
    move_files(sms_fld, archive_fld)
    
    """
    for file in loaded_files:
        old_file = os.path.join(path, file)
        new_file = os.path.join(archive_fld, file)
        os.rename(old_file, new_file)
    """
    
def move_files(from_path, to_path):
    """
    Moves files from one directory
    to another
    """
    files = os.listdir(from_path)
    
    for file in files:
        old = os.path.join(from_path, file)
        new = os.path.join(to_path, file)
        shutil.move(old, new)
                                  

def main():
    
    print('Should I move files from flash drive to project folder?(y/n)')
    if 'y' == input():
        move_files(from_path, to_path)
        
    standartize_file_names(sms_fld)
    
    driver = open_browser()
    
    driver = login(driver)
    driver, loaded_files = load_all_files(driver)
    
    #loaded_files = list_files(False, sms_fld)
    #print(loaded_files)
    
    send_sms(driver, loaded_files)
    
    move_sended_files(loaded_files)
    print("done")
    
    # driver.close()


if __name__ == "__main__":
    main()