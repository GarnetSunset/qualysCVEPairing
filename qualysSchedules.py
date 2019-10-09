import csv
import lxml.etree as ET
import os
import requests
import sys
import xlsxwriter

# IMPORTANT: this program needs about 150mb of space in the directory the script is kept in throughout it's runtime,
# from start to end, the space will be given back after the process has completed.
# I realize this isn't the most efficient way to handle this but I wrote this with legacy Python2 systems 
# without the ability to install modules in mind. If you'd like to make a fork using pandas, feel free. :)

if os.path.exists('config.ini'):
    with open('config.ini', 'r') as file:
        userpass = file.read().replace('\n','')
        double = userpass.split(':')
        username = double[0]
        password = double[1]
else:
    print("Please refer to the readme on how to curate a config")
    exit()

# Qualys API for Scan Schedules
QualysSchedAPI = 'https://qualysapi.qualys.com/api/2.0/fo/schedule/scan/'

headers = {
    'X-Requested-With': 'Curl',
}

params = (
    ('action', 'list'),
)

# Download Qualys Scan Schedules XML
with requests.Session() as s:
    download = s.get(QualysSchedAPI, headers=headers, params=params, auth=(username, password))
    open('ScanSchedules.xml', 'w+').write(download.content)
 
# Get Scan Schedules XML Root
count = 0
tree = ET.parse("ScanSchedules.xml")
root = tree.getroot()
outputlist = []
output = open('ScanSchedules.csv', 'wb')
csvwriter = csv.writer(output)

# Go through XML and pull out important stuff, put it in a CSV
for member in root.findall('RESPONSE/SCHEDULE_SCAN_LIST/SCAN'):
    IDlist = []
    if count == 0:
        ID = "Ticket ID"
        outputlist.append(ID)
        TITLE = member.find('TITLE').tag
        outputlist.append(TITLE)
        USERLOGIN = member.find('USER_LOGIN').tag
        outputlist.append(USERLOGIN)
        SCHEDULE_START_DATE_UTC = member.find('SCHEDULE/START_DATE_UTC').tag
        outputlist.append(SCHEDULE_START_DATE_UTC)
        SCHEDULE_NEXTLAUNCH_UTC = "NEXTLAUNCH_UTC"
        outputlist.append(SCHEDULE_NEXTLAUNCH_UTC)
        NETWORK_ID = member.find('NETWORK_ID').tag
        outputlist.append(NETWORK_ID)
        ISCANNER_NAME = member.find('ISCANNER_NAME').tag
        outputlist.append(ISCANNER_NAME)
        ASSET_GROUP_TITLE = member.find('ASSET_GROUP_TITLE_LIST/ASSET_GROUP_TITLE').tag
        outputlist.append(ASSET_GROUP_TITLE)
        OPTION_PROFILE_TITLE = member.find('OPTION_PROFILE/TITLE').tag
        outputlist.append(OPTION_PROFILE_TITLE)
        OPTION_PROFILE_DEFAULT_FLAG = member.find('OPTION_PROFILE/DEFAULT_FLAG').tag
        outputlist.append(OPTION_PROFILE_DEFAULT_FLAG)
        PROCESSING_PRIORITY = member.find('PROCESSING_PRIORITY').tag
        outputlist.append(PROCESSING_PRIORITY)
        SCHEDULE_MONTHLY = "SCANNED *X*LY"
        outputlist.append(SCHEDULE_MONTHLY)
        SCHEDULE_START_HOUR = member.find('SCHEDULE/START_HOUR').tag
        outputlist.append(SCHEDULE_START_HOUR)
        SCHEDULE_START_MINUTE = member.find('SCHEDULE/START_MINUTE').tag
        outputlist.append(SCHEDULE_START_MINUTE)
        SCHEDULE_TIME_ZONE_CODE = member.find('SCHEDULE/TIME_ZONE/TIME_ZONE_CODE').tag
        outputlist.append(SCHEDULE_TIME_ZONE_CODE)
        SCHEDULE_TIME_ZONE_DETAILS = member.find('SCHEDULE/TIME_ZONE/TIME_ZONE_DETAILS').tag
        outputlist.append(SCHEDULE_TIME_ZONE_DETAILS)
        SCHEDULE_DST_SELECTED = member.find('SCHEDULE/DST_SELECTED').tag
        outputlist.append(SCHEDULE_DST_SELECTED)
        TARGET = member.find('TARGET').tag
        outputlist.append(TARGET)
        csvwriter.writerow(outputlist)
        count = count + 1
    ID = member.find('ID').text
    IDlist.append(ID)
    TITLE = member.find('TITLE').text
    IDlist.append(TITLE)
    USERLOGIN = member.find('USER_LOGIN').text
    IDlist.append(USERLOGIN)
    SCHEDULE_START_DATE_UTC = member.find('SCHEDULE/START_DATE_UTC').text
    IDlist.append(SCHEDULE_START_DATE_UTC)
    try:
        SCHEDULE_NEXTLAUNCH_UTC = member.find('SCHEDULE/NEXTLAUNCH_UTC').text
        IDlist.append(SCHEDULE_NEXTLAUNCH_UTC)
    except:
        IDlist.append("")
    NETWORK_ID = member.find('NETWORK_ID').text
    IDlist.append(NETWORK_ID)
    ISCANNER_NAME = member.find('ISCANNER_NAME').text
    IDlist.append(ISCANNER_NAME)
    try:
        ASSET_GROUP_TITLE = member.find('ASSET_GROUP_TITLE_LIST/ASSET_GROUP_TITLE').text
        IDlist.append(ASSET_GROUP_TITLE)
    except:
        try:
            STARTIPS = member.find('USER_ENTERED_IPS/RANGE/START').text
            ENDIPS = member.find('USER_ENTERED_IPS/RANGE/END').text
            IDlist.append("START:" + STARTIPS + " END:" + ENDIPS)
        except:
            try:
                TAG_INCLUDE_SELECTOR = member.find('ASSET_TAGS/TAG_INCLUDE_SELECTOR').text
                TAG_SET_INCLUDE = member.find('ASSET_TAGS/TAG_SET_INCLUDE').text
                TAG_EXCLUDE_SELECTOR = member.find('ASSET_TAGS/TAG_EXCLUDE_SELECTOR').text
                TAG_SET_EXCLUDE = member.find('ASSET_TAGS/TAG_SET_EXCLUDE').text
                IDlist.append("Include Selector:" + TAG_INCLUDE_SELECTOR + " Set Include:" + TAG_SET_INCLUDE + " Exclude Selector:" + TAG_EXCLUDE_SELECTOR + " Set Exclude:" + TAG_SET_EXCLUDE)
            except:
                IDlist.append("")
    OPTION_PROFILE_TITLE = member.find('OPTION_PROFILE/TITLE').text
    IDlist.append(OPTION_PROFILE_TITLE)
    OPTION_PROFILE_DEFAULT_FLAG = member.find('OPTION_PROFILE/DEFAULT_FLAG').text
    IDlist.append(OPTION_PROFILE_DEFAULT_FLAG)
    PROCESSING_PRIORITY = member.find('PROCESSING_PRIORITY').text
    IDlist.append(PROCESSING_PRIORITY)
    try:
        SCHEDULE_MONTHLY = member.find('SCHEDULE/MONTHLY').tag
        IDlist.append(SCHEDULE_MONTHLY)
    except:
        try:
            SCHEDULE_WEEKLY = member.find('SCHEDULE/WEEKLY').tag
            IDlist.append(SCHEDULE_WEEKLY)
        except:
            try:
                SCHEDULE_DAILY = member.find('SCHEDULE/DAILY').tag
                IDlist.append(SCHEDULE_DAILY)
            except:
                IDlist.append("")
    SCHEDULE_START_HOUR = member.find('SCHEDULE/START_HOUR').text
    IDlist.append(SCHEDULE_START_HOUR)
    SCHEDULE_START_MINUTE = member.find('SCHEDULE/START_MINUTE').text
    IDlist.append(SCHEDULE_START_MINUTE)
    SCHEDULE_TIME_ZONE_CODE = member.find('SCHEDULE/TIME_ZONE/TIME_ZONE_CODE').text
    IDlist.append(SCHEDULE_TIME_ZONE_CODE)
    SCHEDULE_TIME_ZONE_DETAILS = member.find('SCHEDULE/TIME_ZONE/TIME_ZONE_DETAILS').text
    IDlist.append(SCHEDULE_TIME_ZONE_DETAILS)
    SCHEDULE_DST_SELECTED = member.find('SCHEDULE/DST_SELECTED').text
    IDlist.append(SCHEDULE_DST_SELECTED)
    TARGET = member.find('TARGET').text
    IDlist.append(TARGET)
    IDlist[:] = [commie.replace(',', ';') for commie in IDlist]
    utf8IDList = []
    for item in IDlist:
        utf8IDList.append(item.encode('utf-8'))
    csvwriter.writerow(utf8IDList)
output.close()

# Convert to XLSX, necessary for opening in Excel, as Excel can't handle many commas
wb = xlsxwriter.Workbook("ScanSchedules.csv".replace(".csv",".xlsx"))
ws = wb.add_worksheet("Scan Schedules")
with open("ScanSchedules.csv",'r') as csvfile:
    table = csv.reader(csvfile)
    i = 0
    for row in table:
        decoded = [item.decode('utf-8') if isinstance(item, basestring) else item for item in row]
        ws.write_row(i, 0, decoded)
        i += 1
wb.close()