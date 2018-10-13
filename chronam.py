# -*- coding: utf-8 -*-
"""
==============
chronam Module
==============
Module to query the http://chroniclingamerica.loc.gov API. Provides functions
to assemble the txt files for a given newspaper and issue held in the archive
into a dict keyed on the date ('YYYY-MM-DD')
------------------------------
Copyright (c) 2017 Andrew Pyle.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
------------------------------
"""

# TODO: API documentation, module dependencies
# TODO: Bugs 1. dwnld_newspaper() fails on network timeout
#            2. '-ed-2' suffix not robust to > 2 editions
# TODO Create Build Process: requirements.txt vs conda environment.yml, CD/CI?

import json
import os

from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


def validate_chronam_url(url):
    """"Naive check. Ensures that the url goes to a 
    chroniclingamerica.loc.gov newspaper and references the .json
    representation

    Params: url -> url of JSON file for newspaper to download: str
    Return: Boolean"""

    domain_check = 'chroniclingamerica.loc.gov/lccn/sn' in url
    json_check = '.json' in url
    return domain_check and json_check


def get_json(url):
    """Downloads json from url from chronliclingamerica.loc.gov and saves as a
    Python dict.

    Parameters: url -> url of JSON file for newspaper to download: str
    Returns:    json_dict -> dict: JSON from http request"""

    r = Request(url, headers={'User-Agent': 'Mozilla/5.0'})

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
        json_dict = json.load(data)
        return json_dict


def get_txt(url):
    """Downloads txt from url from chroniclingamerica.loc.gov and saves as
    python str.

    Relies on valid url supplied by get_json()

    Parameters: url -> url for OCR text returned by get_json(): str
    Returns:    retrieved_txt -> OCR text: str"""

    # TODO: return lists of missing & failed pages
    missing_pages = []
    failed_pages = []

    r = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
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


def display_newspaper(url):
    """Displays information and issues available for a given newspaper

    Parameters: url -> url of JSON file for newspaper: str
    Returns:    newspaper_json -> dict: JSON from http request"""

    newspaper_json = get_json(url)
    newspaper_string = ('{name} | Library of Congress No.: {lccn}'
        ' | {place_of_publication}\nPublished from {start_year} to'
        ' {end_year} by {publisher}').format(**newspaper_json)

    issues_string = ('Number of Issues Downloadable: {}\nFirst issue: {}\n'
                    'Last Issue: {}\n').format(
                        len(newspaper_json['issues']),
                        newspaper_json['issues'][0]['date_issued'],
                        newspaper_json['issues'][-1]['date_issued'])
    print(newspaper_string)
    print('------------------------')
    print(issues_string)


def download_page(url):  # url of page
    """Downloads the OCR text of a newspaper page. 
    Relies on valid url from assemble_issue()

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

    issue_string = ''.join(download_page(page['url']) for 
        page in get_json(url)['pages'])
    return issue_string  # str 'alltextforallpages'


def parse_date(datestring):
    """Converts YYYY-MM-DD string into date object

    Params: date -> str: 'YYYY-MM-DD'
    Return: return_date -> date"""

    date_fmt_str = '%Y-%m-%d'
    return_date = datetime.strptime(datestring, date_fmt_str).date()
    return return_date


# TODO: allow restarting of downloads -> the function checks if the issue is
#       in the data structure or not
def download_newspaper(url, start_date, end_date):
    """Downloads OCR text of a newspaper from chroniclingamerica.loc.gov by
    parsing the .json representation using the exposed API. Traverses
    the json from the newspaper .json url to each page and composes them into
    a dict of issues where {'date': 'issue text'}

    Params: url -> str: base url of newspaper. Ends in .json
            start_date -> date: date(year, month, day)
                          represents the first issue to download
            end_date   -> date: date(year, month, day)
                          represents the last issue to download
    Return: newspaper_issues -> dict: {'date': 'issue text'}"""

    newspaper_issues = {}

    # Terminal UI Print statements
    print('start date:', start_date)
    print('end date:', end_date)

    # Interface
    print('Getting issues:')

    try:
        for issue in get_json(url)['issues']:
            issue_date = parse_date(issue['date_issued'])
            if (issue_date >= start_date and issue_date <= end_date):
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


def lccn_to_disk(dir_name, downloaded_issue):
    """Saves a dict of downloaded issues to disk. Creates a directory:

    dir_name
        |--key1.txt
        |--key2.txt
        +--key3.txt

    Params: dir_name -> str: name of created directory for data
            downloaded_issue -> dict: {'YYYY-MM-DD': 'string of txt'}
    Returns: (int): number of files written in created directory"""

    # Make directory if it doesn't exist
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    # Make directory with proper appendix number if the original directory
    # already exists
    while not os.path.exists(dir_name):
        dir_copy_number = 1
        dir_name = '{} (copy {})'.format(dir_name, str(dir_copy_number))
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        else:
            dir_copy_number += 1
    
    # Write to disk
    number_of_files_written = 0
    for date, text in downloaded_issue.items():
        with open(os.path.join(dir_name, date + '.txt'), 'w') as f:
            f.write(text)
        number_of_files_written += 1
    
    return number_of_files_written







def validate_date_input(start_end):
    """For CLI UI - Ensures that user enters a valid date.
    Params: start_end -> str: 'start' or 'end', whether to prompt for 
                              start or end date.
    Return: return_date  -> date: validated date to pass to control flow"""

    return_date = None
    while return_date == None:
        try:
            return_date = parse_date(
                    input('What is the {} date to download?'
                          '(YYYY-MM-DD)\n> '.format(start_end)))
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

    news_info = get_json(url)
    display_newspaper(url)

    # looping, validated date input
    start_date = validate_date_input('start')
    end_date = validate_date_input('end')

    print()
    try:
        news_data = download_newspaper(url, start_date=start_date,
                                    end_date=end_date)
    except ValueError as e:
        return e

    lccn_to_disk(news_info['lccn'], news_data)

    # print('Data available in this session: news_data, news_info, start_date,'
    #       'end_date')
    # print()
    print('The data is also saved to disk in the working directory in a '
          'folder named the lccn number for the newspaper')

if __name__ == "__main__":
    main()
