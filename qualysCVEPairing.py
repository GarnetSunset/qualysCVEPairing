import csv
import lxml.etree as ET
import os
import requests

# IMPORTANT: this program needs about 150mb of space in the directory the script is kept in throughout it's runtime,
# from start to end, the space will be given back after the process has completed.
# I realize this isn't the most efficient way to handle this but I wrote this with legacy Python2 systems 
# without the ability to install modules in mind. If you'd like to make a fork using pandas, feel free. :)

if os.path.exists('config.ini'):
    with open('config.ini', 'r') as file:
        userpass = file.readlines()
        double = userpass[0].split(':')
        username = double[0]
        password = double[1]
else:
    print("Please refer to the readme on how to curate a config")
    quit()

# Qualys API for knowledgebase
QualysURL = 'https://qualysapi.qualys.com/api/2.0/fo/knowledge_base/vuln/'

# CSV format CVE listing.
CVE_CSV = 'https://cve.mitre.org/data/downloads/allitems.csv'

headers = {
    'X-Requested-With': 'curl',
}

params = (
    ('action', 'list'),
    ('details', 'All'),
)

# Download Qualys XML
with requests.Session() as s:
    download = s.get(QualysURL, headers=headers, params=params, auth=(username, password))
    open('vulnTrash.xml', 'w+').write(download.content)
    dom = ET.parse('vulnTrash.xml')
    xslt = ET.parse('kb_v2-cve2csv.xsl')
    transform = ET.XSLT(xslt)
    newdom = transform(dom)
    csvWrite = open("kb_v2-cve.csv", "w")
    csvWrite.write(newdom)
    csvWrite.close()

# Download Latest CVE Listing.
with requests.Session() as s:
    download = s.get(CVE_CSV)
    open('trashsoon.csv', 'w+').write(download.content)
 
# Convert CVE CSV into list for comparison.
with open('trashsoon.csv', 'rb') as f:
    reader = csv.reader(f)
    cve_list = list(reader)

# Convert Qualys QID CSV into list for comparison.
with open('kb_v2-cve.csv', 'rb') as f:
    reader = csv.reader(f)
    qid_list = list(reader)

# Delete trash files.
os.remove('trashsoon.csv') 
os.remove('vulnTrash.xml')

# Curate a list of QIDs to CVEs and write to a CSV of it's own.
with open('qualysCVEPairs.csv', 'wb') as csvfile:
    csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    csvWriter.writerow(['QID', 'CVE-ID', 'CVE-URL', 'CVE-DESC'])
    for row in cve_list:
        cveNum = row[0]
        desCVE = row[2].replace(',', '')
        if "CVE-" in cveNum:
            for row in qid_list:
                QID = None
                url = None
                if row[1] == cveNum:
                    QID = row[0]
                    url = row[2]
                if QID != None:
                    csvWriter.writerow([QID, cveNum, url, desCVE])
            
