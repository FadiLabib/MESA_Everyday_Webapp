# MIT License
# MESA © 2019
# PSU Capstone 2018-2019

# modified from google dev
# https://developers.google.com/calendar/quickstart/python 

from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime as d
import json

# --


# --

MAX_EVENTS = 400

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

MONTHS = ['None', 'January', 'February', 'March', 
          'April', 'May', 'June', 'July', 
          'August', 'September', 'October', 'November',
          'December']

CAL_COLORS = {
              '1' : 'PALE_BLUE',
              '2' : 'PALE_GREEN',
              '3' : 'PURPLE',
              '4' : 'PALE_RED',
              '5' : 'YELLOW',
              '6' : 'ORANGE',
              '7' : 'CYAN',
              '8' : 'GRAY',
              '9' : 'BLUE',
              '10': 'GREEN',
              '11': 'RED',
              # '12' : 'LIGHT GRAY',
             }

MESA_COLORS = {
               # '3' : {'r':232,'g':224,'b':215,'hex':'e7e0d7'}, # purple (!MESA)
               '6' : {'r':255,'g':158,'b':21,'hex':'ff9e15'}, # orange
               '8' : {'r':114,'g':102,'b':88,'hex':'716558'}, # grey
               '9' : {'r':130,'g':149,'b':177,'hex':'8195b1'}, # blue
               '10' : {'r':191,'g':215,'b':48,'hex':'bed62f'}, # green
               # '11' : {'r':235,'g':78,'b':70,'hex':'ea4e46'}, # red
               # NOT USED, NO LIGHT GRAY IN G CAL
               #'12' : {'r':232,'g':224,'b':215,'hex':'e7e0d7'}, # No light grey
              }

BADGE_COLORS = {
                # '3' : 'mauve un-named badge', # Purple (!MESA)
                '6' : 'MESA Expert', # Orange
                '8' : 'Career Pro', # Grey
                '9' : 'College Knowledge', # Blue
                '10' : 'Professional Development', # Green
                # '11' : 'red un-named badge', # Red (!MESA)
                # '12' : 'light grey un-named badge', # No Light Grey
               }

BADGE_IDS = {
             # '3' : 'mauve un-named badge', # Purple (!MESA)
             '6' : 4, # Orange
             '8' : 2, # Grey
             '9' : 1, # Blue
             '10' : 3, # Green
             # '11' : 'red un-named badge', # Red (!MESA)
             # '12' : 'light grey un-named badge', # No Light Grey
            }

# --


# --

def parse_time_string(date_str):
    """
        input:
          '2018-11-18T18:30:00-08:00' 

        output:
          {'y':2018,'t':11,'d':18,'h':18,'m':30}
    """

    t = {}

    # print(json_obj)
    tokens = date_str.split('T')

	  # pull the first half with the date info
	  # parse it by hyphens
    date_obj = tokens[0].split('-')
    t['yr'] = int(date_obj[0])
    t['mt'] = int(date_obj[1])
    t['dy'] = int(date_obj[2]) 

    # pull the second half of the date 
    # parse it by hyphens then by colons
    try:
        time_obj = tokens[1].split('-')
        time_obj = time_obj[0].split(':')
        t['hr'] = int(time_obj[0])
        t['mn'] = int(time_obj[1])
    except:
        t['hr'] = 0
        t['mn'] = 0
         
		# return the dict obj
    # print("passed obj:", json_obj, '\nparsed obj:',t)
    return t 

# --


# --

def add_time_tuples(event):
    """
      parses the time values in an event and 
      creates a tuple with the month(mt), 
      day(dy), year(yr), hour(hr) and minute(mn) 
      for the start and end times of the event.

      input:
        event['start'] = 
          '2018-11-18T18:30:00-08:00' 

      output:
        event['start_tuple'] =
            {'yr':2018,'mt':11,'dy':18,'hr':18,'mn':30}
    """

    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))

    start_tuple = parse_time_string(start)
    end_tuple = parse_time_string(end)

    event['start_tuple'] = start_tuple
    event['end_tuple'] = end_tuple
    # print(start_tuple,end_tuple,"\n")

# --

def add_time_strings(event):
    """
      adds the date as a string to an event using
      its time tuple value

      input:
        event['start_tuple'] =
            {'yr':2018,'mt':11,'dy':18,'hr':18,'mn':30} 

      output:
        event['start_string'] =
            "November-18-2018 18:30" 

    """

    start_tuple = event['start_tuple']
    end_tuple = event['end_tuple']

    start_string = MONTHS[start_tuple['mt']] \
                   + '-' + str(start_tuple['dy']) \
                   + '-' + str(start_tuple['yr']) \
                   + ' ' + str(start_tuple['hr']) \
                   + ':' + str(start_tuple['mn']).zfill(2)

    end_string = MONTHS[end_tuple['mt']] \
                 + '-' + str(end_tuple['dy']) \
                 + '-' + str(end_tuple['yr']) \
                 + ' ' + str(end_tuple['hr']) \
                 + ':' + str(end_tuple['mn']).zfill(2)

    date_string = str(end_tuple['yr']) \
                  + '/' + str(end_tuple['mt']) \
                  + '/' + str(end_tuple['dy']) \

    event['start_string'] = start_string
    event['end_string'] = end_string
    event['date_string'] = date_string

# --


# --

def add_remain_days(event):
    """
      parses an events time tuple for its
      starting time, and calculates the 
      remaining days until it starts.

      input:
        event['start_tuple'] =
            {'y':2018,'t':11,'d':18,'h':18,'m':30}

      output:
        event['remain_days'] = 18
    """

    today = d.datetime.today()

    # parse the date_time string and get a dict back
    t = event['start_tuple']
		
		# create a datetime obj with the data from dict
    event_day = d.datetime(hour=t['hr'], minute=t['mn'], day=t['dy'], month=t['mt'], year=t['yr'])

    # pull the current day
    today = d.datetime.today()

    # convert todays date to be midnight
    today = d.datetime.combine(today, d.datetime.min.time())

    # print(event_day)
    # print(today)
    event['remain_days'] = (event_day - today).days

# --


# --

def get_event_list():
    """
      Shows basic usage of the Google Calendar API.
      Prints the start and name of the next 10 events on the user's calendar.

      Prints the next 10 events after today, and adds them to a list of the 
      next 30 days.
    """

    # grab the users token (has user's access and refresh tokens)
		# if they dont exist then they are created upon autorization
    store = file.Storage('MESAeveryday/credentials/token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('MESAeveryday/credentials/mesa_cal_creds.json', SCOPES)
        creds = tools.run_flow(flow, store)

    # get a HTTP connection to googles calendar
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Call the Calendar API
    now = d.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    events_result = service.events().list(calendarId='pdx.edu_e91ro1012j2f2qhuornmch3dtg@group.calendar.google.com', 
                                            timeMin=now,
                                            maxResults=MAX_EVENTS, 
                                            singleEvents=True,
                                            orderBy='startTime').execute()
    # grab the results
    events = events_result.get('items', [])
   
    for event in events:
        add_time_tuples(event)
        add_time_strings(event)
        add_remain_days(event)
        if 'colorId' in event: 
            event['calColor'] = CAL_COLORS[event['colorId']]
            if event['colorId'] in MESA_COLORS: 
                event['mesaColor'] = MESA_COLORS[event['colorId']]
                event['badgeColor'] = BADGE_COLORS[event['colorId']]
                event['badgeId'] = BADGE_IDS[event['colorId']]
            else:
                event['mesaColor'] = 'Not a MESA Color'
                event['badgeColor'] = 'No MESA Badge'
                event['badgeId'] = 0

        else:
            event['calColor'] = 'None'
            event['mesaColor'] = 'None'
            event['badgeColor'] = 'None'

        if 'location' not in event: 
            event['location'] = 'No Location Provided'
 
    # if we have not found any events print
    # failure.
    if not events:
        print('No upcoming events found.')

    return events

# --


# --

def searchEvents(events, keywords):
    """
        for all words in a given phrase, 
        search all events for those words,
        and add all matching phrases to the 
        set.
    """

    matches = []

    # # go through all of the passed in events
    for event in events:

        # # set the notin bool to false
        # # this will trip if a word isnt
        # # present in the events name
        notin = False
        
        # # go through all words and check
        # # them against the events name
        for word in keywords:
            if 'summary' in event:
                if word.lower() not in event['summary'].lower():
                    notin = True
            else:
                notin = True

        # # if we havent tripped the bit,
        # # add the event to the set
        if not notin:
            matches += [event]
        
    # # return all events that have matched
    return matches          

# --


# --

def get_mesa_events(events):
    """
    parses a list of events and pulls any events that 
    are a mesa badge color into a list of the different
    types of badges. 
        input:
            [[event], [event1], [event2]]
            * event1['colorId'] = 9 *
            * CAL_COLORS[9] = Blue *
            * BADGE_IDS[9] = 5 (College Knowledge) *

        output:
            ['5':[event1], '':[], ...]
    """

    # # make a empty dictionary
    MESA_EVENTS = {}

    # # fill it with empty lists under the different
    # # badge names (ie. {'MESA Expert'=[], } )
    for key in BADGE_IDS:
        MESA_EVENTS[BADGE_IDS[key]] = []

    # # tie the different events with their colors
    # # to their different badges in the dictionary
    for event in events:
        if 'colorId' in event:
            if event['colorId'] in BADGE_COLORS:
                etype = BADGE_IDS[event['colorId']]
                MESA_EVENTS[etype] += [event]
                

    # # return the dictionary
    return MESA_EVENTS

# --


# --

def main():
    """
      Shows basic usage of get_event_list.
    """

    events = get_event_list()
    upcoming_events = [event for event in events if (event['remain_days'] < 7)]
    print(upcoming_events)

    for event in events[:6]:
        # print(event)
        print(events.index(event))
        if 'calColor' in event: 
            print('calendar color:',event['calColor'])
        if 'mesaColor' in event: 
            print('mesa color:',event['mesaColor'])
        if 'summary' in event: 
            print('summary:', event['summary'])
        if 'location' in event: 
            print('location', event['location'])
        if 'start_string' in event: 
            print('time:', event['start_string'],'to',event['end_string'])
        print('Days Left:',event['remain_days'],'\n')
    
    MesaDays = searchEvents(events, ['Mesa','Day'])

    for day in MesaDays:
        print("match:", day['start_string'])

    print('')

    mesa_events = get_mesa_events(events)
    for event_type in mesa_events:
        print(event_type, ":", mesa_events[event_type])

# --


# --

if __name__ == '__main__':
    main()

# --

