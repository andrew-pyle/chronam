# -*- coding: utf-8 -*-
"""
==============
chronam Module
==============
Module to query the http://chroniclingamerica.loc.gov API. Provides functions
to assemble the txt files for a given newspaper and issue held in the archive
into a dict keyed on the date ('YYYY-MM-DD')
------------------------------
Copyright (c) 2017-2018 Andrew Pyle.

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

from requests import Session
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


# TODO: allow restarting of downloads -> the function checks if the issue is
#       in the data structure or not
def download_newspaper(url, start_date, end_date, session):
    """Downloads OCR text of a newspaper from chroniclingamerica.loc.gov 
    
    Parses the JSON representation returned by the API. Traverses the JSON: 
        newspaper -> issue -> page -> OCR text
    Concatenates all text into a string and returns a dict of issues keyed on
    issue date with concatenated issue text as values.

    Args:
        url (str): URL of JSON representation of newspaper. Ends in '.json'
        start_date (datetime.date): date of first issue to download
        end_date (datetime.date): date of last issue to download
    
    Returns:
        newspaper_issues (dict): {'date': 'issue text'}

    Raises:
        ValueError: If HTTP response cannot be parsed as a JSON file
        ConnectionError: Raised for network problems, but not for HTTP response
            codes, like 404, 500, etc.)
        HTTPError: Raised for unsuccessful HTTP response
        Timeout: Raised if request does not receive a response from the server
            for 10 sec.
    """

    newspaper_issues = {}

    # Terminal UI Print statements
    print('start date:', start_date)
    print('end date:', end_date)
    print('Getting issues:')
    
    for issue in session.get(url).json()['issues']:
        issue_date = parse_date_YYYY_MM_DD(issue['date_issued'])
        if (issue_date >= start_date and issue_date <= end_date):
            if issue['date_issued'] not in newspaper_issues:
                print(issue['date_issued'])
                newspaper_issues[issue['date_issued']] = \
                    assemble_issue(issue['url'], session)
            else:
                print(issue['date_issued'] + '-ed-2')
                newspaper_issues[issue['date_issued'] + '-ed-2'] = \
                    assemble_issue(issue['url'], session)

    return newspaper_issues # dict {'date_issued': 'alltextforallpages'}


def assemble_issue(url, session):  # url of issue
    """Assembles the OCR text for each page of a newspaper.
    
    Relies on valid url from dwnld_newspaper()

    Params: url -> url of newspaper issue: str
    Return: txt -> OCR text of all pages in newspaper: str"""

    # Concatenate the OCR text for each page in the issue.
    return ''.join(download_ocr_text(page['url'], session) for 
        page in session.get(url).json()['pages'])


def download_page(url, session):  # url of page
    """Downloads the OCR text of a newspaper page. 
    Relies on valid url from assemble_issue()

    Args:
        url (str): url of JSON representation of newspaper page
        session (requests.Session): Session object for HTTP request. Allows
            use of already established peristent TCP connection.
    Returns:
        str: URL of OCR text representation of newspaper page
    """
    return session.get(url).json()['text']


def download_ocr_text(url, session):
    """Downloads OCR text of newspaper from url of text file.
    """
    ocr_text_url = session.get(url).json()['text']
    return session.get(ocr_text_url).text


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


def get_newspaper_url_by_lccn(lccn):
    url = 'http://chroniclingamerica.loc.gov/lccn/{}.json'.format(lccn)
    if validate_chronam_url(url) is True:
        return url
    else:
        raise ValueError('No JSON representation for this LCCN found at '
                         'chroniclingamerica.loc.gov')


def validate_chronam_url(url):
    """"Naive check. Ensures that the url goes to a 
    chroniclingamerica.loc.gov newspaper and references the .json
    representation

    Params: url -> url of JSON file for newspaper to download: str
    Return: Boolean"""

    domain_check = 'chroniclingamerica.loc.gov/lccn/sn' in url
    json_check = '.json' in url
    return domain_check and json_check


def parse_date_YYYY_MM_DD(datestring):
    """Converts YYYY-MM-DD string into date object

    Params: date -> str: 'YYYY-MM-DD'
    Return: return_date -> date"""

    date_fmt_str = '%Y-%m-%d'
    return_date = datetime.strptime(datestring, date_fmt_str).date()
    return return_date


def makedirs_with_rename(dir_name, copy_number=0):
    """Creates directory while avoiding name collisions recursively.

    Creates directory at current working directory, with name of
    `dir_name`. If `dir_name` already exists, appends a unique suffix to
    `dir_name` and tries to write again. Recursion ends when a directory is
    created on disk.

    Args:
        dir_name (str): Directory name to create. Used if no name collision
            exists.
        copy_number (int): Used to recursively create unique name suffix.
            Does not need to be supplied; only exists for use in recursive
            calls.

    Returns:
        (str): Name of directory written to disk
    """
    # Use dir_name first, then add new suffix if that directory already exists
    dir_name_attempt = dir_name if copy_number == 0 else '{} (copy {})'.format(
        dir_name, str(copy_number))

    # Recursively either create directory or get a new suffix and try again
    try:
        os.makedirs(dir_name_attempt)
        return dir_name_attempt
    except FileExistsError:
        dir_name_used = makedirs_with_rename(dir_name, copy_number+1)
    return dir_name_used


def lccn_to_disk(dir_name, downloaded_issue):
    """Write a dict of downloaded issues to disk at current working directory.

    Saves a directory named by the dir_name parameter at os.getcwd(). Raises
    FileNotFoundError if directory named by parameter `dir_name` does not
    already exist. Parameter `downloaded_issue` is unpacked and saved. Each
    dict key is the filename and the dict value is the text file contents.

    dir_name
        |--key1.txt
        |--key2.txt
        ∟--key3.txt

    Args:
        filepath (str): location on disk to save dir_name. Defaults to current
            working directory.
        dir_name (str): name of created directory for data
        downloaded_issue (dict): {'YYYY-MM-DD': 'string of newspaper txt'}

    Returns:
        int: number of files written in created directory

    Raises:
        FileNotFoundError: Raised if a directory named by parameter `dir_name`
            does not exist.
        IOError: Raised if writing file fails.
    """
    number_of_files_written = 0
    for date, text in downloaded_issue.items():
        # Write file relative to current working directory
        with open(os.path.join(dir_name, date + '.txt'), 'w') as f:
            f.write(text)
        number_of_files_written += 1

    return number_of_files_written

# TODO Exception logging?
# TODO Set requests session timeout
# TODO requests raise_for_status() & HTTPError
def cli_interface():
    with Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        try:
            ui_greeting()
            lccn = ui_get_newspaper_lccn()
            url = get_newspaper_url_by_lccn(lccn)
            ui_display_newspaper(url, session)
            start_date = ui_date_input('start')
            end_date = ui_date_input('end')
            newspaper_ocr_text = download_newspaper(url, 
                                                    start_date=start_date,
                                                    end_date=end_date,
                                                    session=session)
            ui_save_newspaper_text_to_disk(lccn, newspaper_ocr_text)
        except ValueError as e:
            print('Exiting due to error:', e)
        except IOError as e:
            print('Error writing to file:', e)


def ui_greeting():
    print('Welcome to Chronicling America Downloader')


# Deprecated in favor of accepting LCCNs from CLI.
# See ui_get_newspaper_lccn() & get_newspaper_url_by_lccn()
def ui_get_newspaper_url():
    url = input('enter a url: ')
    if validate_chronam_url(url) is True:
        return url
    else:
        raise ValueError('Invalid url for chroniclingamerica.loc.gov OCR '
                         'newspaper (url must end in .json)')


def ui_get_newspaper_lccn():
    lccn = input('enter a Library of Congress No. (LCCN): ')
    return lccn.strip().lower()


# TODO Make robust to missing kwargs in JSON returned by get_json()
def ui_display_newspaper(url, session):
    """Displays information and issues available for a given newspaper

    Parameters: url -> url of JSON file for newspaper: str
    Returns:    newspaper_json -> dict: JSON from http request
    """
    newspaper_json = session.get(url).json()
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


# TODO Make error ondates before start or after end date of newspaper
def ui_date_input(start_end):
    """For CLI UI - Ensures that user enters a valid date.
    
    Args: 
        start_end (str): 'start' or 'end', whether to prompt for 
            start or end date.
    Returns:
        return_date (date): validated date to pass to control flow"""

    return_date = None
    while return_date == None:
        try:
            return_date = parse_date_YYYY_MM_DD(
                    input('What is the {} date to download?'
                          '(YYYY-MM-DD)\n> '.format(start_end)))
        except ValueError:
            print('Invalid Date')
            continue
    return return_date


# TODO Put "no merge" limitation for newspapers into readme.md
def ui_save_newspaper_text_to_disk(dir_name, newspaper_text_by_date):
    """Saves data to disk at current working directory and prints UI messages.

    Makes new directory named by the `dir_name` parameter, adding a suffix to
    avoid naming collisions. Does not merge issues from current call into an
    equally named directory already present on disk.

    Args:
        dir_name (str): Name of directory in which to save newspaper text
            files. Creates directory if it doesn't exist. Adds unique suffix to
            `dir_name` if a directory with the name already exists.
        newspaper_text_by_date (dict): Dict where keys are filenames and values
            are text file contents to save.

    Returns:
        Nothing. Has side-effects on filesystem.

    Raises:
        IOError: Bubbles up from `lccn_to_disk()` if writing files fails.
        FileNotFoundError: Bubbles up from `lccn_to_disk()` if supplied
            `dir_name` doesn't exist.
    """
    # Create a directory in current working directory with recursive naming to
    # avoid collisions
    dir_name = makedirs_with_rename(dir_name)
    # Write to disk in created directory
    number_of_files_written = lccn_to_disk(dir_name, newspaper_text_by_date)
    # Show filesystem changes to user
    print('{} file(s) written to disk'.format(number_of_files_written))
    real_path = os.path.join(os.getcwd(), dir_name)
    print('Data saved to: `{}`'.format(real_path))


if __name__ == "__main__":
    cli_interface()
