# qualysSched2Remedy

I consider remedy the bane of my position so I curated this (with the help of L.Bur) to make a nice way to never have to look at or touch it again. 

# qualysCVEPairing

I made this so that anyone that works with Qualys can get a constantly updating list of CVES, their descriptions, and their QIDs. 
This should make it so it's possible to be ingested into splunk via a clean CSV. 

# qualysSchedules

A way to curate a CSV containing all future scans. (Also makes an xlsx because excel doesn't like high amounts of commas in a cell, which a large list of IPs can do.)

Feel free to let me know what I can do to make this a lil more clean. My plan is to turn these all into modules soon.

## kb_v2-cve2csv.xsl

This is a file created by Qualys that allows an XML file to be converted into a CSV. If anyone from Qualys wishes to have this file taken down, let me know. Contact me via my Twitter of the same handle. My messages are open and I'm more than willing, but I didn't see anything barring this. :)

## Config.ini
Open the config and input the required fields. 
If you aren't using the remedy features you'll only need to fill out the username password field.
