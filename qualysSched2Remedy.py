import csv
import datetime
import difflib
import gzip
import logging
import logging.handlers
import lxml.etree as ET
import os
import requests
import socket
import sys
from fnmatch import fnmatch
from suds.client import Client
from suds.cache import NoCache
if (sys.version_info < (3, 0)):
    import codecs

# GarnetSunset
# Qualys Schedules to Remedy Tickets
## Remedy is like having my toes shoved in a door
## Let's make sure I never have to touch it again.

def qualys2remedy():
    if os.path.exists('config.ini'):
        configFile = {}
        with open('config.ini', 'r') as file:
            for line in file:
                (key, val) = line.split('=')
                configFile[str(key)] = val.rstrip("\n").rstrip("\r").replace('"','')
            double = configFile['loginInfo'].split(':')
            username = double[0]
            password = double[1]
            timestamps = configFile['blockDates'].replace(' ','').split(',')
            CMURLPROD = configFile['prodWSDL']
            CMURLQA = configFile['qaWSDL']
            prodvsqa = configFile['env']
    else:
        print("Please refer to the readme on how to curate a config")
        quit() 

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
        open('ScanSchedules.xml', 'wb').write(download.content)
        if "Bad Login" in str(download.content):
            print("Your password is dead or something like that, please go check your logs")
            quit()
        print(download.content)

     # Check for existing ScanSched.csv
    diffMe = False
    if os.path.isfile('ScanSchedules.csv'):
        try:   
            os.remove('ScanSchedules_last.csv')
        except:
            pass
        os.rename('ScanSchedules.csv', 'ScanSchedules_last.csv')
        diffME = True
    else:
        temp = open('ScanSchedules_last.csv', 'wb')    

    # Get Scan Schedules XML Root
    try:
        output = open('ScanSchedules.csv', 'w+', newline='', encoding='utf8')
    except:
        output = codecs.open('ScanSchedules.csv', 'w', encoding='utf8')
    csvwriter = csv.writer(output)
    
    # open xml for schedules
    with open('ScanSchedules.xml') as fd:
        scansch = xmltodict.parse(fd.read(), process_namespaces=True, dict_constructor=dict)  
    
    # open xml for scans
    with open('Scans.xml') as fd:
        scans = xmltodict.parse(fd.read(), process_namespaces=True, dict_constructor=dict)            
    
    # make CSVs
    boilerPlate = ["Ticket ID","Short_Description","Requestor","START_DATE_UTC","Change_Start_Time","Expected End Time","NETWORK_ID","ISCANNER_NAME","ASSET_GROUP_TITLE","TITLE","DEFAULT_FLAG","PROCESSING_PRIORITY","SCANNED *X*LY","START_HOUR","START_MINUTE","TIME_ZONE_CODE","TIME_ZONE_DETAILS","DST_SELECTED","TARGET"]
    csvwriter.writerow(boilerPlate)
    for schedules in scansch['SCHEDULE_SCAN_LIST_OUTPUT']['RESPONSE']['SCHEDULE_SCAN_LIST']['SCAN']:
        try:
            SCHEDULE_NEXTLAUNCH_UTC = schedules["SCHEDULE"]["NEXTLAUNCH_UTC"]
        except:
            SCHEDULE_NEXTLAUNCH_UTC = ""
        try:
            ASSET_GROUP_TITLE = schedules["ASSET_GROUP_TITLE_LIST"]["ASSET_GROUP_TITLE"]
        except:
            try:
                STARTIPS = schedules["USER_ENTERED_IPS"]["RANGE"]["START"]
                ENDIPS = schedules["USER_ENTERED_IPS"]["RANGE"]["END"]
                ASSET_GROUP_TITLE = "START:" + STARTIPS + " END:" + ENDIPS
            except:
                try:
                    TAG_INCLUDE_SELECTOR = schedules["ASSET_TAGS"]["TAG_INCLUDE_SELECTOR"]
                    TAG_SET_INCLUDE = schedules["ASSET_TAGS"]["TAG_SET_INCLUDE"]
                    TAG_EXCLUDE_SELECTOR = schedules["ASSET_TAGS"]["TAG_EXCLUDE_SELECTOR"]
                    TAG_SET_EXCLUDE = schedules["ASSET_TAGS"]["TAG_SET_EXCLUDE"]
                    ASSET_GROUP_TITLE = "Include Selector:" + TAG_INCLUDE_SELECTOR + " Set Include:" + TAG_SET_INCLUDE + " Exclude Selector:" + TAG_EXCLUDE_SELECTOR + " Set Exclude:" + TAG_SET_EXCLUDE
                except:
                    ASSET_GROUP_TITLE = ""
        try:
            SCHEDULE_LY = schedules["SCHEDULE"]["MONTHLY"]
            SCHEDULE_LY = "MONTHLY"
        except:
            try:
                SCHEDULE_LY = schedules["SCHEDULE"]["WEEKLY"]
                SCHEDULE_LY = "WEEKLY"
            except:
                try:
                    SCHEDULE_LY = schedules["SCHEDULE"]["DAILY"]
                    SCHEDULE_LY = "DAILY"
                except:
                    SCHEDULE_LY = ""
        changeEnd = ""
        for key in scans['SCAN_LIST_OUTPUT']['RESPONSE']['SCAN_LIST']['SCAN']:
            if schedules["TITLE"].replace(' ','') == key['TITLE'].replace(' ','') and SCHEDULE_NEXTLAUNCH_UTC != "NEXTLAUNCH_UTC" and SCHEDULE_NEXTLAUNCH_UTC != "":
                Change_Start_Time = datetime.datetime.strptime(SCHEDULE_NEXTLAUNCH_UTC, '%Y-%m-%dT%H:%M:%S')
                gotOne = True
                if key['DURATION'] != "Pending":
                    if "day" in key['DURATION']:
                        day = key['DURATION'].split('day')
                        numberOfDays = re.sub("[^0-9]", "", day[0])
                        timeBits = re.sub("[^0-9:]", "", day[1])
                        duration = datetime.datetime.strptime(timeBits, '%H:%M:%S')
                        durSeconds = (duration.hour * 60 + duration.minute) * 60 + duration.second + (int(numberOfDays) * 86400)
                        changeEnd = str(Change_Start_Time + datetime.timedelta(seconds=durSeconds)).replace(' ','T')+"-05:00"
                    else:
                        duration = datetime.datetime.strptime(key['DURATION'], '%H:%M:%S')
                        durSeconds = (duration.hour * 60 + duration.minute) * 60 + duration.second
                        changeEnd = str(Change_Start_Time + datetime.timedelta(seconds=durSeconds)).replace(' ','T')+"-05:00"
                else:    
                    changeEnd = str(Change_Start_Time + datetime.timedelta(hours=4)).replace(' ','T')+"-05:00"
        bigList = [schedules["ID"],schedules["TITLE"],schedules["USER_LOGIN"],schedules["SCHEDULE"]["START_DATE_UTC"],SCHEDULE_NEXTLAUNCH_UTC,changeEnd,schedules["NETWORK_ID"],schedules["ISCANNER_NAME"],ASSET_GROUP_TITLE,schedules["OPTION_PROFILE"]["TITLE"],schedules["OPTION_PROFILE"]["DEFAULT_FLAG"],schedules["PROCESSING_PRIORITY"],SCHEDULE_LY,schedules["SCHEDULE"]["START_HOUR"],schedules["SCHEDULE"]["START_MINUTE"],schedules["SCHEDULE"]["TIME_ZONE"]["TIME_ZONE_CODE"],schedules["SCHEDULE"]["TIME_ZONE"]["TIME_ZONE_DETAILS"],schedules["SCHEDULE"]["DST_SELECTED"],schedules["TARGET"]]
        utf8IDList = []
        for item in bigList:
            utf8IDList.append(str(item).replace(',',';'))
        if SCHEDULE_NEXTLAUNCH_UTC != "":
            csvwriter.writerow(utf8IDList)

    # Delete the XML
    newshit = []
    now = datetime.datetime.now()
    with open('ScanSchedules_last.csv', 'r') as t1, open('ScanSchedules.csv', 'r') as t2:
        fileone = t1.readlines()
        filetwo = t2.readlines()
        if len(filetwo) == 1:
            os.remove('ScanSchedules.csv')
            shutil.move('ScanSchedules_last.csv', 'ScanSchedules.csv')
            print("No luck in downloading a CSV")
            quit()
    for line in filetwo:
        compare = line.split(',')
        if "Change_Start_Time" not in compare[4]:
            dt = datetime.datetime.strptime(compare[4], '%Y-%m-%dT%H:%M:%S')
            if line not in fileone and now < dt:
                newshit.append(line)
    
    # Establish the global variables
    remedysubmitter = 'WebServiceReadOnly'  # Remedy submitter must ALWAYS be WebServiceReadOnly
    global resultdict
    
    # Based on prodvsqa argument, set Change Management URL accordingly
    if prodvsqa == 'PROD':
        CMURL = CMURLPROD
    else:
        CMURL = CMURLQA

    resultrow = {}

    for line in newshit:
        currentOne = line.split(',')
        if "External" not in currentOne[1]:
            if "Short_Description" not in currentOne[1]:
                resultrow['AssociatedDivision'] = configFile['AssociatedDivision']
                resultrow['ResponsibleGroup'] = configFile['ResponsibleGroup']
                resultrow['Country'] = configFile['Country']
                resultrow['Impact'] = configFile['Impact']
                resultrow['ImpactCategory'] = configFile['ImpactCategory']
                resultrow['Requestor_Phone'] = configFile['Requestor_Phone']
                resultrow['Requestor'] = configFile['Requestor']
                resultrow['Short_Description'] = configFile['ShortDescPrefix']+currentOne[1]+" - "+currentOne[0]
                resultrow['Status'] = configFile['Status']
                resultrow['Submitter'] = remedysubmitter
                resultrow['RequestorEmail'] = configFile['RequestorEmail']
                resultrow['KnownImpact'] = configFile['KnownImpact']
                resultrow['CustFacing_CustSupporting'] = configFile['CustFacing_CustSupporting']
                resultrow['TypeOfChange'] = configFile['TypeOfChange']
                resultrow['prodvsqa'] = configFile['env']
                resultrow['Region'] = configFile['Region']
                resultrow['ResponsibleIndividual'] = configFile['ResponsibleIndividual']
                resultrow['ChangeControlCategory'] = configFile['ChangeControlCategory']
                resultrow['ChangeDescription'] = configFile['ChangeDescription']
                    
                dt = datetime.datetime.strptime(currentOne[4], '%Y-%m-%dT%H:%M:%S')
                if is_dst(dt):
                    Change_Start_Time = dt - datetime.timedelta(hours=4) 
                    resultrow['Change_Start_Time'] = str(Change_Start_Time).replace(' ','T')+configFile['timeChange']
                else:
                    Change_Start_Time = dt - datetime.timedelta(hours=5)
                    resultrow['Change_Start_Time'] = str(Change_Start_Time).replace(' ','T')+configFile['timeChange']
                    
                matched = False
                for key in scans['SCAN_LIST_OUTPUT']['RESPONSE']['SCAN_LIST']['SCAN']:
                    if currentOne[1].replace(' ','') == key['TITLE'].replace(' ',''):
                        matched = True
                        if key['DURATION'] != "Pending":
                            if "day" in key['DURATION']:
                                day = key['DURATION'].split('day')
                                numberOfDays = re.sub("[^0-9]", "", day[0])
                                timeBits = re.sub("[^0-9:]", "", day[1])
                                duration = datetime.datetime.strptime(timeBits, '%H:%M:%S')
                                durSeconds = (duration.hour * 60 + duration.minute) * 60 + duration.second + (int(numberOfDays) * 86400)
                                resultrow['Change_Stop_Time'] = str(Change_Start_Time + datetime.timedelta(seconds=durSeconds)).replace(' ','T')+"-05:00"
                            else:
                                duration = datetime.datetime.strptime(key['DURATION'], '%H:%M:%S')
                                durSeconds = (duration.hour * 60 + duration.minute) * 60 + duration.second
                                resultrow['Change_Stop_Time'] = str(Change_Start_Time + datetime.timedelta(seconds=durSeconds)).replace(' ','T')+"-05:00"
                        else:    
                            resultrow['Change_Stop_Time'] = str(Change_Start_Time + datetime.timedelta(hours=4)).replace(' ','T')+"-05:00"  
                if matched == False:
                    resultrow['Change_Stop_Time'] = str(Change_Start_Time + datetime.timedelta(hours=4)).replace(' ','T')+"-05:00"
                    
                if resultrow['prodvsqa'] == 'PROD':
                    prodvsqa = 'PROD'
                else:
                    prodvsqa = 'QA'
                
                resultrow['Back-out_Instructions'] = configFile['Back-out_Instructions']
                resultrow['ReasonForChange'] = configFile['ReasonForChange']
                resultrow['Changes_Planned'] = configFile['Changes_Planned'] + currentOne[1]
                try:
                    cmresult = remedy_cm_create(prodvsqa, resultrow, CMURL)
                        
                except Exception as e:
                    print(str(e))
    else:
        quit()

def remedy_cm_create(prodvsqa, arglist, CMURL):
    """Function to Create a Remedy Change Management ticket
    The prodvsqa parameter, if set to QA will use the QA server for the creation, otherwise prod.
    The arglist is a dictionary of key/value pairs to be set in the CM.  The keys must correspond
    to the keys used in the Change Management WSDL for creating a new Ticket
    """
    # This code stolen from the kick ass L.Bur, with permission, I do not assume responsibility for this code, nor do I support it.

    try:
        cmclient = Client(CMURL, cache=NoCache())
    except Exception as myexception:
        raise Exception('CM_CreateClientCreate:' + str(myexception))
    
    cmOpCreate = cmclient.factory.create('OpCreate')
    cmOpCreate = dict([(str(key),val) for key,val in cmOpCreate])
    
    cmOpCreateRequired = {}
    cmOpCreateRequired['AssociatedDivision'] = True
    cmOpCreateRequired['Back-out_Instructions'] = True
    cmOpCreateRequired['Change_Start_Time'] = True
    cmOpCreateRequired['Change_Stop_Time'] = True
    cmOpCreateRequired['Changes_Planned'] = True
    cmOpCreateRequired['Country'] = True
    cmOpCreateRequired['CustFacing_CustSupporting'] = True
    cmOpCreateRequired['Impact'] = True
    cmOpCreateRequired['ReasonForChange'] = True
    cmOpCreateRequired['Requestor'] = True
    cmOpCreateRequired['Requestor_Phone'] = True
    cmOpCreateRequired['RequestorEmail'] = True
    cmOpCreateRequired['ResponsibleGroup'] = True
    cmOpCreateRequired['Short_Description'] = True
    cmOpCreateRequired['Status'] = True
    cmOpCreateRequired['Submitter'] = True
    cmOpCreateRequired['TypeOfChange'] = True
    cmOpCreateRequired['KnownImpact'] = True

    for key in list(cmOpCreate):
            
        if key in arglist:
            cmOpCreate[key] = arglist[key]

        elif key in cmOpCreateRequired:
            raise Exception('CM_Create:Required_Field_Missing:' + key)

        else:
            del cmOpCreate[key]

    try:
        cmresult = cmclient.service.OpCreate(**cmOpCreate)
    except Exception as myexception:
        raise Exception('CM_Create:' + str(myexception))

    return cmresult
    
    syslogmsgbeginbase = 'scriptruntime' + keysep + delim + scriptruntime + delim + sep + 'SearchName' + keysep + delim + arghash['searchName'] + delim + sep + 'searchCount' + keysep + delim + arghash['searchCount'] + delim + sep + 'searchPath' + keysep + delim + arghash['searchPath'] + delim + sep

    try:
        resultstatus = get_search_results(arghash['searchPath']);
    except Exception as myexception:
        syslogmessage = syslogmsgbeginbase + 'ScriptStatus' + keysep + delim + 'Fail_GetResults_Exception:' + str(myexception) + delim
        logorprint(syslogmessage, mylogfile)
        quit()
        
    if resultstatus == None:

        for resultrow in resultdict:

            resultrow['Submitter'] = remedysubmitter
            if not 'Requestor' in resultrow:
                resultrow['Requestor'] = remedyrequestor
            if not 'Status' in resultrow:
                resultrow['Status'] = remedydefaultstatus
            
            if 'prodvsqa' in resultrow:
                if resultrow['prodvsqa'] == 'PROD':
                    prodvsqa = 'PROD'
                else:
                    prodvsqa = 'QA'
                
                mystarttime = resultrow['Change_Start_Time'][5:7] + '/' + resultrow['Change_Start_Time'][8:10] + '/' + resultrow['Change_Start_Time'][0:4] + ' ' + resultrow['Change_Start_Time'][11:13] + ':' + resultrow['Change_Start_Time'][14:16] + ':' + resultrow['Change_Start_Time'][17:19]
                print(mystarttime)
                mystoptime = resultrow['Change_Stop_Time'][5:7] + '/' + resultrow['Change_Stop_Time'][8:10] + '/' + resultrow['Change_Stop_Time'][0:4] + ' ' + resultrow['Change_Stop_Time'][11:13] + ':' + resultrow['Change_Stop_Time'][14:16] + ':' + resultrow['Change_Stop_Time'][17:19]
                print(mystoptime)
                cmoplist['Qualification'] = cmoplist['Qualification'] + ' AND \'Change Start Time\' = "' + mystarttime + '" AND \'Change Stop Time\' = "' + mystoptime + '"'
                       

                if foundcm == 1 and len(cmresult) > 1:
                    syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_MoreThan1CMReturned' + delim + sep + syslogmsgsearchresults
                    logorprint(syslogmessage, mylogfile)
                
                elif resultrow['scriptaction'] == 'CancelCM' and foundcm == 0:
                    syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_CancelNotFound' + delim + sep + syslogmsgsearchresults
                    logorprint(syslogmessage, mylogfile)
                    
                elif resultrow['scriptaction'] == 'CreateCM' and foundcm == 1:
                    syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_CreateAlreadyExists' + delim + sep + syslogmsgsearchresults
                    logorprint(syslogmessage, mylogfile)
                
                elif resultrow['scriptaction'] == 'CancelCM' and foundcm == 1:

                    myrequestid = cmresult[0]['Request_ID']
                    cmopset = {}
                    cmopset['Request_ID'] = myrequestid
                    cmopset['Status'] = 'Cancelled' 
                    cmopset['Cancelled'] = 'Yes'
                    cmopset['RequestedWindow'] = resultrow['RequestedWindow']
                    
                    syslogmsgbegin = syslogmsgbegin + 'CM_Ticket_Created' + keysep + delim + myrequestid + delim + sep

                    try:
                        remedy_cm_update(prodvsqa, cmopset) 

                    except Exception as myexception:
                        syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_CMApprovedToCancel_Exception:' + str(myexception) + delim + sep + syslogmsgsearchresults
                        logorprint(syslogmessage, mylogfile)
                        continue

                    if resultrow['sendnotify'] == '1':
                        cmopset = {}
                        cmopset['Request_ID'] = myrequestid
                        cmopset['TriggerNotifyCustomer'] = 'Yes'
                        
                        try:
                            cmresult = remedy_cm_update(prodvsqa, cmopset)
                        
                        except Exception as myexception:
                            syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_CMCancelNotify_Exception:' + str(myexception) + delim + sep + syslogmsgsearchresults
                            logorprint(syslogmessage, mylogfile)
                            continue

                    syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Success' + delim + syslogmsgsearchresults
                    logorprint(syslogmessage, mylogfile)
                
                elif resultrow['scriptaction'] == 'RescheduleCM' and foundcm == 1:

                    mystarttime = cmresult[0]['Change_Start_Time']
                    mystarttime = mystarttime.strftime('%Y-%m-%dT%H:%M:%S-04:00')
                    mystoptime = cmresult[0]['Change_Stop_Time']
                    mystoptime = mystoptime.strftime('%Y-%m-%dT%H:%M:%S-04:00')
                    
                    if resultrow['Change_Start_Time'] == mystarttime and resultrow['Change_Stop_Time'] == mystoptime:

                        syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_AlreadyRescheduled' + delim + sep + syslogmsgsearchresults
                        logorprint(syslogmessage, mylogfile)
                        
                    else:
                    
                        myrequestid = cmresult[0]['Request_ID']
                        cmopset = {}
                        cmopset['Request_ID'] = myrequestid
                        cmopset['Status'] = 'Re-Scheduling' 

                        syslogmsgbegin = syslogmsgbegin + 'CM_Ticket_Created' + keysep + delim + myrequestid + delim + sep
                        
                        try:
                            remedy_cm_update(prodvsqa, cmopset) 

                        except Exception as myexception:
                            syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_CMApprovedToReschedule_Exception:' + str(myexception) + delim + sep + syslogmsgsearchresults
                            logorprint(syslogmessage, mylogfile)
                            continue
                            
                        cmopset = {}
                        cmopset['Request_ID'] = myrequestid
                        cmopset['Change_Start_Time'] = resultrow['Change_Start_Time']
                        cmopset['Change_Stop_Time'] = resultrow['Change_Stop_Time']
                        cmopset['Rescheduled'] = 'Yes'
                        cmopset['RequestedWindow'] = resultrow['RequestedWindow']

                        try:
                            remedy_cm_update(prodvsqa, cmopset) 

                        except Exception as myexception:
                            syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_CMRescheduleChangeTimes_Exception:' + str(myexception) + delim + sep + syslogmsgsearchresults
                            logorprint(syslogmessage, mylogfile)
                            continue

                        if resultrow['sendnotify'] == '1':
                            cmopset = {}
                            cmopset['Request_ID'] = myrequestid
                            cmopset['TriggerNotifyCustomer'] = 'Yes'
                            
                            try:
                                cmresult = remedy_cm_update(prodvsqa, cmopset)
                            
                            except Exception as myexception:
                                syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_CMRescheduleNotify_Exception:' + str(myexception) + delim + sep + syslogmsgsearchresults
                                logorprint(syslogmessage, mylogfile)
                                continue
                        
                        cmopset = {}
                        cmopset['Request_ID'] = myrequestid
                        cmopset['Status'] = 'Requested' 

                        try:
                            cmresult = remedy_cm_update(prodvsqa, cmopset)
                        
                        except Exception as myexception:
                            syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_CMRescheduleRequested_Exception:' + str(myexception) + delim + sep + syslogmsgsearchresults
                            logorprint(syslogmessage, mylogfile)
                            continue

                        syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Success' + delim + syslogmsgsearchresults
                        logorprint(syslogmessage, mylogfile)

                elif foundcm == 0 and ( resultrow['scriptaction'] == 'RescheduleCM' or resultrow['scriptaction'] == 'CreateCM' ):

                    try:
                        cmresult = remedy_cm_create(prodvsqa, resultrow)
                        
                    except Exception as myexception:
                        print(str(Exception))
                        continue
            else:
                syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_Unknown_scriptaction' + delim + syslogmsgsearchresults
                logorprint(syslogmessage, mylogfile)
    else:
        syslogmessage = syslogmsgbegin + 'ScriptStatus' + keysep + delim + 'Fail_GetResults_Without_Exception' + delim
        logorprint(syslogmessage, mylogfile)
        quit()

def logorprint(logstring, mylogfile):
    """Function for print (if DEBUG), otherwise log
    """
    with open(mylogfile, 'a') as out_file:
        out_file.write(logstring + '\n')
    return

def is_dst(dt):
    if dt.year < 2007:
        raise ValueError()
    dst_start = datetime.datetime(dt.year, 3, 8, 2, 0)
    dst_start += datetime.timedelta(6 - dst_start.weekday())
    dst_end = datetime.datetime(dt.year, 11, 1, 2, 0)
    dst_end += datetime.timedelta(6 - dst_end.weekday())
    return dst_start <= dt < dst_end

if __name__ == '__main__':
    """Dummy main executable to allow this to be a module or a script
    """
    qualys2remedy()
