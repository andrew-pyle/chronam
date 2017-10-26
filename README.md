# chronam
Python module for downloading OCR text from http://chroniclingamerica.loc.gov/

This module assumes that you have spent some time on the [Chronicling America](http://chroniclingamerica.loc.gov/) site and wish to download a newspaper's OCR text programmatically from the [API](http://chroniclingamerica.loc.gov/about/api/).

This module will not search, download pdfs, images, etc. It is a simple tool which will save you some clicks and quickly import newspaper issue plain text from the site.

## Basic Usage
chronam.py is an executable Python script, and will start the basic use case automatically. The module runs the basic workflow with an interactive terminal session and saves the data to the working directory.

```bash
$ cd location/of/chronam/module
$ ls
LICENSE		README.md	chronam.py	docs
$ python chronam.py
```

Alternately, run the script with an IDE, like [Spyder](https://github.com/spyder-ide/spyder). It has an integrated IPython terminal. (In [Spyder](https://github.com/spyder-ide/spyder), open the chronam.py file in the editor and press <kbd>F5</kbd>)

## Example of Basic Usage
```b
Welcome to Chronicling America Downloader
enter a url: http://chroniclingamerica.loc.gov/lccn/sn84026994.json

The Charleston daily news. | Library of Congress No.: sn84026994 | Charleston, S.C.
Published from 1865 to 1873 by Cathcart, McMillan & Morton

Number of Issues Downloadable: 2641
First issue: 1865-08-21
Last Issue: 1873-04-05

What is the start date to download?(YYYY-MM-DD) > 1865-08-21
What is the end date to download?(YYYY-MM-DD) > 1865-08-25

start date: 1865-08-21
end date: 1865-08-25
Getting issues:
1865-08-21
1865-08-22
1865-08-23
Data available in this session: news_data, news_info, start_date, end_date

The data is also saved to disk in the working directory in a folder named
the lccn number for the newspaper
```

The data will be saved to a folder
![data saved to folder](/docs/images/dir.png?raw=true)

## Importing chronam
The module also exposes several useful functions for importing OCR text data into your python environment.

See the source code function docstrings for all the details. An [API reference](/docs/api.md) is coming soon.
```python
from chronam import disp_newspaper
```
Generates an informational blurb about the newspaper:
```b
The Charleston daily news. | Library of Congress No.: sn84026994 | Charleston, S.C.
Published from 1865 to 1873 by Cathcart, McMillan & Morton
------------------------
Number of Issues Downloadable: 2641
First issue: 1865-08-21
Last Issue: 1873-04-05
```
---------------------
```python
from chronam import lccn_to_disk
```
Saves an in-memory dict of newspaper issues to disk.

------------------------
```python
from chronam import dwnld_newspaper
```
Downloads and assembles in memory all the pages of the issues of a newspaper in a specified date range.
