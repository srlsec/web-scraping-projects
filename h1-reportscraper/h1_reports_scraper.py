import time
import csv
from selenium.webdriver import Chrome, ChromeOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests, argparse
import pandas as pd
import terminal_banner, termcolor, platform, datetime, os


banner_text = """

  _    __   _____                       _          _____                                
 | |  /_ | |  __ \                     | |        / ____|                               
 | |__ | | | |__) |___ _ __   ___  _ __| |_ ___  | (___   ___ _ __ __ _ _ __   ___ _ __ 
 | '_ \| | |  _  // _ \ '_ \ / _ \| '__| __/ __|  \___ \ / __| '__/ _` | '_ \ / _ \ '__|
 | | | | | | | \ \  __/ |_) | (_) | |  | |_\__ \  ____) | (__| | | (_| | |_) |  __/ |   
 |_| |_|_| |_|  \_\___| .__/ \___/|_|   \__|___/ |_____/ \___|_|  \__,_| .__/ \___|_|   
                      | |                                              | |              
                      |_|                                              |_|              

"""
desc = "Hackerone Reports scraper for bug bounty hunters."
dev_info = """
v1.1
Developed by: Sarathlal Srl
Credits : Ivan Modin 
"""
if(platform.system() == 'Windows'):
    os.system('cls')
    driver = 'C:\chromedriver\chromedriver.exe'
if (platform.system() == 'Linux'):
    os.system('clear')
    driver = '/usr/local/bin/chromedriver'
    
banner = terminal_banner.Banner(banner_text)
print(termcolor.colored(banner.text,'cyan'), end="")
print(termcolor.colored(desc,'white', attrs=['bold']), end = "")
print(termcolor.colored(dev_info,'yellow'))

chrome_options = Options()
chrome_options.add_argument("--log-level=3") 
chrome_options.add_argument("--headless")
chrome_options.add_argument("--ignore-certificate-errors-spki-list")

argp = argparse.ArgumentParser(usage = "h1_reports_scraper.py -q QUERY -o FILENAME")
argp.add_argument("-q","--query")
argp.add_argument("-o","--output",required= True)
parser = argp.parse_args()
query = parser.query
output = parser.output

page_loading_timeout = 10

options = ChromeOptions()
options.add_argument('no-sandbox')
options.add_argument('headless')
driver = webdriver.Chrome(executable_path=driver, options=chrome_options)

hacktivity_url = f'https://hackerone.com/hacktivity?querystring={query}&order_field=latest_disclosable_activity_at&filter=type%3Apublic'
try:
    driver.get(hacktivity_url)
except requests.ConnectionError:
    print("[-] Can't connect to the server. Are you connected to the internet?")
    exit()

driver.implicitly_wait(page_loading_timeout)

def extract_reports(raw_reports):
    reports = []
    tablelist = []
    for raw_report in raw_reports:

        html = raw_report.get_attribute('innerHTML')

        try:
            index = html.index('/reports/')
        except ValueError:
            continue
        link = 'https://hackerone.com'
        for i in range(index, index + 50):
            if html[i] == '"':
                break
            else:
                link += html[i]

        json_info = (link + '.json')
        j = requests.get(json_info)
        json_info = j.json()
        
        title = json_info['title']
        program = json_info['team']['profile']['name']
        upvotes = int(json_info['vote_count'])
        bounty = float(json_info['bounty_amount']) if json_info['has_bounty?'] else 0.0
        vuln_type = json_info['weakness']['name'] if 'weakness' in json_info else ''
        created_at = json_info['created_at']
        
        data = {
                "Title": title,
                "Link": f'{link}/',
                "Program": program,
                "Upvotes": upvotes,
                "Bounty": bounty,
                "Vuln_type": vuln_type,
                "Created date": created_at,
            }
        print(data)
        tablelist.append(data)
        reports.append(link)
        
    df = pd.DataFrame(tablelist)
    df.to_csv(f'{output}.csv')
        
def fetch():
    counter = 0
    page = 0
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(page_loading_timeout)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            counter += 1
            if counter > 1:
                break
        else:
            counter = 0
        last_height = new_height
        
        raw_reports = driver.find_elements_by_class_name('fade')
        extract_reports(raw_reports)
    driver.close()


if __name__ == '__main__':
    fetch()