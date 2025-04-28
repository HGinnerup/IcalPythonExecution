import urllib.request

import icalendar
import recurring_ical_events
from datetime import datetime

from calendar_helpers.ExecutableCalendarEvent import ExecutableCalendarEvent
import asyncio


ical_url = "https:// ... basic.ics" # URL to the iCalendar file. 
hash_key = "abcdefg..." # Hash key for the event code. This is used to verify the integrity of the code before executing it.



ical_string = ""
for line in urllib.request.urlopen(ical_url):
    ical_string += line.decode("utf-8")




async def run_calendar_server(ical_string: str, hash_key: str = None) -> None:
    ical = icalendar.Calendar.from_ical(ical_string)
    query = recurring_ical_events.of(ical)

    events_upcoming: recurring_ical_events.CalendarQuery.after = query.after(datetime.now()) # Events that end later than now (Includes currently active events)

    for event in events_upcoming:
        executableEvent = ExecutableCalendarEvent(event)
        print(f"Event: {executableEvent.name} ({executableEvent.start} - {executableEvent.end})")
        waitTime = executableEvent.getTimeUntilStart()
        print(f"Waiting for {waitTime} seconds until event starts.")
        await asyncio.sleep(waitTime.total_seconds())

        try:
            executableEvent.load(signature_key=hash_key) # Load the event code into the globals dictionary
        except Exception as e:
            print(f"Error loading event: {e}")
            continue

        asyncio.ensure_future(executableEvent.execute(verbose=True))

asyncio.run(run_calendar_server(ical_string, hash_key=hash_key))



