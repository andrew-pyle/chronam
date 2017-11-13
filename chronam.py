"""
==============
chronam Module
==============
Module to query the http://chroniclingamerica.loc.gov API. Provides functions to assemble the txt
files for a given newspaper and issue held in the archive into a dict keyed on the date
('YYYY-MM-DD')
------------------------------
Copyright (c) 2017 Andrew Pyle.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
------------------------------
"""

# TODO: Function docstrings: params and inputs
#       API documentation, dependencies

import json
import os

from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


def validate_chronam_url(url):
    """"Naive check. Ensures that the url goes to a chroniclingamerica.loc.gov newspaper
    and references the .json representation

    Params: url -> url of JSON file for newspaper to download: str
    Return: Boolean"""

    domain_chk = 'chroniclingamerica.loc.gov/lccn/sn'
    json_chk = '.json'
    if domain_chk in url and json_chk in url:
        return True
    else:
        return False


def get_json(url):
    """Downloads json from url from chronliclingamerica.loc.gov and saves as a
    Python dict.

    Parameters: url -> url of JSON file for newspaper to download: str
    Returns:    json_dict -> dict representation of JSON from http request: dict"""

    r = Request(url)

    # Catch non-chronam urls
    if validate_chronam_url(url) is not True:
        raise ValueError('Invalid url for chroniclingamerica.loc.gov OCR '
                         'newspaper (url must end in .json)')
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


# TODO: return missing & failed pages
def get_txt(url):
    """Downloads txt from url from chroniclingamerica.loc.gov and saves as
    python str.

    Relies on valid url supplied by get_json()

    Parameters: url -> url for OCR text returned by get_json(): str
    Returns:    retrieved_txt -> OCR text: str"""

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

 # TODO remove return_json param.
def disp_newspaper(url, return_json=False):
    """Displays information and issues available for a given newspaper

    Parameters: url -> url of JSON file for newspaper: str
    Returns:    newspaper_json -> dict representation of JSON from http request: dict"""

    try:
        newspaper_json = get_json(url)
    except ValueError as e:
        return e

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
    """Downloads the OCR text of a newspaper page. Relies on valid url from assemble_issue()

    Params: url -> url of OCR text of page: str
    Return: txt -> OCR text of a newspaper page: str"""

    txt_url = get_json(url)['text']
    txt = get_txt(txt_url)
    return txt

def assemble_issue(url):  # url of issue
    """Assembles the OCR text for each page of a newspaper.
    Relies on valid url from dwnld_newspaper()

    Params: url -> url of newspaper issue: str
    Return: txt -> OCR text of all pages in newspaper: str"""

    issue_string = ''
    for page in get_json(url)['pages']:
        issue_string += dwnld_page(page['url'])
    return issue_string  # str 'alltextforallpages'


# TODO: allow restarting of downloads -> the function checks if the issue is
#       in the data structure or not
def dwnld_newspaper(url, start_date, end_date):
    """Downloads OCR text of a newspaper from chroniclingamerica.loc.gov by
    parsing the .json representation using the exposed REST API. Traverses
    the json from the newspaper .json url to each page and composes them into
    a dict of issues where {'date': 'issue text'}

    Params: url -> str: base url of newspaper. Ends in .json
            start_date -> datetime.date object: represents the first issue to download
            end_date   -> datetime.date object: represents the last issue to download
    Return: newspaper_issues -> dict: {'date': 'issue text'}"""

    newspaper_issues = {}
    # Terminal UI Print statements
    print('start date:', start_date)
    print('end date:', end_date)

    # Interface
    print('Getting issues:')

    try:
        for issue in get_json(url)['issues']:
            if (parse_date(issue['date_issued']) >= start_date and
                    parse_date(issue['date_issued']) <= end_date):
                if issue['date_issued'] not in newspaper_issues:
                    print(issue['date_issued'])
                    newspaper_issues[issue['date_issued']] = \
                        assemble_issue(issue['url'])
                else:
                    print(issue['date_issued'] + '-ed-2')
                    newspaper_issues[issue['date_issued'] + '-ed-2'] = \
                        assemble_issue(issue['url'])
        return newspaper_issues # dict {'date_issued': 'alltextforallpages'}

    except ValueError as e:
        return e


def parse_date(date):
    """Converts YYYY-MM-DD string into datetime.date object

    Params: date -> str: YYYY-MM-DD
    Return: return_date -> datetime.date"""

    date_fmt_str = '%Y-%m-%d'
    return_date = datetime.strptime(date, date_fmt_str).date()
    return return_date


# TODO: Dir already exists exception handling
def lccn_to_disk(dir_name, downloaded_issue):
   """Saves a dict of downloaded issues to disk. Creates a directory:

   dir_name
     |--key1.txt
     |--key2.txt
     +--key3.txt

   Params: dir_name -> str: name of created directory for data
           downloaded_issue -> dict: {'YYYY-MM-DD': 'string of txt'}"""

   if not os.path.exists(dir_name):
       os.makedirs(dir_name)
   for date, text in downloaded_issue.items():
       with open(os.path.join(dir_name, date + '.txt'), 'w') as f:
           f.write(text)
   return


def validate_date_input(start_end):
    """For CLI UI - Ensures that user enters a valid date.
    Params: start_end -> str: 'start' or 'end', whether to prompt for start or end date.
    Return: return_date  -> datetime.date: validated date to pass to control flow"""

    return_date = None
    while return_date == None:
        try:
            return_date = parse_date(input('What is the {} date to download?'
                                '(YYYY-MM-DD) > '.format(start_end)))
        except ValueError:
            print('Invalid Date')
            continue
    return return_date

def main():
    """Basic Use Case. Called when file is run.
    Example Terminal interaction:
        input: .json newspaper url
        output: info blurb of newspaper
        input: start date
        input: end date
        output: saves issues to disk in a directory named the lccn number"""

    print('Welcome to Chronicling America Downloader')
    url = input('enter a url: ')
    print()

    # TODO: bad: co-opted usage
    news_info = disp_newspaper(url, return_json=True)

    # looping, validated date input
    start_date = validate_date_input('start')
    end_date = validate_date_input('end')

    print()
    try:
        news_data = dwnld_newspaper(url, start_date=start_date,
                                    end_date=end_date)
    except ValueError as e:
        return e

    lccn_to_disk(news_info['lccn'], news_data)

    print('Data available in this session: news_data, news_info, start_date, '
          'end_date')
    print()
    print('The data is also saved to disk in the working directory in a '
          'folder named the lccn number for the newspaper')

if __name__ == "__main__":
    main()
