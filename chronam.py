"""Module Docstring"""

# TODO: Function docstrings: params and inputs
#       API documentation, dependencies

import json
import os

from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


def validate_newspaper_url(url):
    """"
    Ensures that the url goes to a chroniclingamerica.loc.gov newspaper
    with a .json representation which can be parsed programmatically
    """
    domain_chk = 'chroniclingamerica.loc.gov/lccn/sn' 
    json_chk = '.json'
    if domain_chk in url and json_chk in url:
        return True
    else:
        return False


def get_json(url):
    '''Downloads json from url from chronliclingamerica.loc.gov and saves as a
    Python dict. 
    
    Parameters: url -> str
    Returns:    dict'''
    
    # catch invalid urls
    try:
        r = Request(url)
    except ValueError as e:
        raise ValueError(e)
            
    # Catch non-chronam urls
    if validate_newspaper_url(url) is not True:
        #print(validate_newspaper_url(url))
        raise ValueError('Invalid url for chroniclingamerica.loc.gov OCR '
                         'newspaper (url must end in .json')
    try:
        data = urlopen(r)
    except URLError as e:
        if hasattr(e, 'reason'):
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
            print('url: ', url)
        elif hasattr(e, 'code'):
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
            print('url: ', url)
    else:
        # read().decode('utf-8') is necessary for Python 3.4
        json_dict = json.loads(data.read(), encoding='utf-8')
        return json_dict


# needs url validation (?)
def get_txt(url):
    '''Downloads txt from url from chroniclingamerica.loc.gov and saves as
    python str. 
    Parameters: url -> str
    Returns:    string'''
    
    missing_pages = []
    failed_pages = []

    r = Request(url)
    try:
        data = urlopen(r)
    except URLError as e:
        if hasattr(e, 'reason'):
            print('We failed to reach a server.')
            print('Reason: ', e.reason)
            print('url: ', url)
            retrieved_txt = 'Likely Missing Page: Not digitized, published'
            missing_pages.append(url)
            
        elif hasattr(e, 'code'):
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
            print('url: ', url)
            retrieved_txt = 'Server didn\'t return any text'
            failed_pages.append(url)
    else:
        retrieved_txt = data.read().decode('utf-8')
    return retrieved_txt


def disp_newspaper(url, return_json=False):
    '''Displays issues available for a given newspaper which has been
    "inspected" using chron_amer_inspect(url) for a given newspaper url
    
    Parameters: issues -> dict {issues: url}
    Returns:    print: Name of Newspaper, Location, lccn, Start Year,
                       Publisher,
                       First Issue, Last Issue, Total Number of issues,'''
    
    try:
        newspaper_json = get_json(url)
    except ValueError as e:
        print(e)
        return

    newspaper_string = ('{} | Library of Congress No.: {} | {}\nPublished '
                       'from {} to {} by {}').format(
                           newspaper_json['name'],
                           newspaper_json['lccn'],
                           newspaper_json['place_of_publication'], 
                           newspaper_json['start_year'], 
                           newspaper_json['end_year'],
                           newspaper_json['publisher'])

    issues_string = ('Number of Issues Downloadable: {}\nFirst issue: {}\n'
                    'Last Issue: {}\n').format(
                        len(newspaper_json['issues']),
                        newspaper_json['issues'][0]['date_issued'], 
                        newspaper_json['issues'][-1]['date_issued'])
    print(newspaper_string)
    print('\n', end='')
    print(issues_string)
    
    if return_json is True:
        return newspaper_json
    
    
def dwnld_page(url):  # url of page
    """ """
    txt_url = get_json(url)['text']
    txt = get_txt(txt_url)
    
    return txt

def assemble_issue(url):  # url of issue
    """ """
    issue_string = ''    
    for page in get_json(url)['pages']:
        issue_string += dwnld_page(page['url'])
    
    return issue_string  # string 'alltextforallpages'

 # TODO: Dir already exists exception handling
def lccn_to_disk(newspaper_json, downloaded_issue):
    """Params: newspaper_json -> dict returned by inspect_issues(url)
               downloaded_issue -> dict returned by dwnld_newspaper()"""
    dir_name = newspaper_json['lccn']
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    for date, text in downloaded_issue.items():
        with open(os.path.join(dir_name, date + '.txt'), 'w') as f:
            f.write(text)
    
    return

# TODO: pass exception handling up to main()
# TODO: save_to_file param
def dwnld_newspaper(url, start_date=None, end_date=None, save_to_file=False):  
    """
    """
    newspaper_issues = {}
    date_fmt_str = '%Y-%m-%d'
    
    # Parse arguments to date() objects
    try:
        start_date_p = datetime.strptime(start_date, date_fmt_str).date()
        end_date_p = datetime.strptime(end_date, date_fmt_str).date()
    except ValueError as e:
        print('Invalid Date entered')
        return
    
    try:
        newspaper_json = get_json(url)
    except ValueError as e:
        print(e)
        return
    
    # Debug Print statements
    print('start date:', start_date_p)
    print('end date:', end_date_p)
    
    # Interface
    print('Getting issues:')
    
    for issue in get_json(url)['issues']:
        if (issue['date_issued'] >= start_date and 
                issue['date_issued'] <= end_date):
            if issue['date_issued'] not in newspaper_issues:
                print(issue['date_issued'])
                newspaper_issues[issue['date_issued']] = \
                    assemble_issue(issue['url'])
            else:
                print(issue['date_issued'] + '-ed-2')
                newspaper_issues[issue['date_issued'] + '-ed-2'] = \
                    assemble_issue(issue['url'])

#    if save_to_file is True:
#        with open()
    
    return newspaper_issues # dict {'date_issued': 'alltextforallpages'}

# TODO: allow restarting of downloads -> the function checks if the issue is              
#       in the data structure or not


#if __name__ == "__main__":
#    print('Welcome to Chronicling America Downloader')
#    url = input('enter a url: ')
#    
#    print()
##    news_info = inspect_issues(url)
##    disp_newspaper(news_info)
#    news_info = disp_newspaper(url, return_json=True)
#    
#    start_date = input('What is the start date to download? (YYYY-MM-DD) > ')
#    end_date = input('What is the last date to download? (YYYY-MM-DD) > ')
#    print()
#    
#    news_data = dwnld_newspaper(url, start_date=start_date, end_date=end_date)
#    lccn_to_disk(news_info, news_data)
#    
#    print('Data available in this session: news_data, news_info, start_date, end_date')
#    print()
#    print('the data is also saved to disk in the working directory in a folder named the lccn number for the newspaper')
    
    
    















            
