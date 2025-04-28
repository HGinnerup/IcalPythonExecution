import icalendar
from datetime import datetime, timedelta
import asyncio
import hashlib

class ExecutableCalendarEvent:
    """
    A class representing an executable calendar event.
    The description of the event is a Python script that will be executed. The script must contain two functions:
    onStart() and onEnd(). These functions will be executed when the event starts and ends, respectively.
    """
    def __init__(self, event: icalendar.Component):
        self.event = event
        self.loaded = False

        # self.start = event["DTSTART"].dt
        # self.end = event["DTEND"].dt
        # self.summary = event["SUMMARY"]
        # self.description = event["DESCRIPTION"]
        # self.location = event["LOCATION"]
        # self.url = event.get("URL", None)
        # self.recurrence_id = event.get("RECURRENCE-ID", None)


    @property
    def start(self) -> datetime:
        """Returns the start time of the event."""
        return self.event["DTSTART"].dt
    

    @property
    def end(self) -> datetime:
        """Returns the end time of the event."""
        return self.event["DTEND"].dt
    

    @property
    def name(self) -> str:
        """Returns the name of the event."""
        return self.event["SUMMARY"]
    
    
    @property
    def code(self) -> str:
        """Returns the code of the event."""

        return self._code
        # description = self.event.get("DESCRIPTION", None)
        # if description is None:
        #     return None
        
        # description = description.replace("\xa0", " ") # Replace non-breaking spaces with regular spaces

        # return description
        

    def __str__(self) -> str:
        return f"{self.name} ({self.start} - {self.end})"


    def __repr__(self) -> str:
        return f"ExecutableCalendarEvent({self.name})"
    

    def getTimeUntilStart(self) -> timedelta:
        """Returns the time until the event starts."""

        systemTimeZone = datetime.now().astimezone().tzinfo

        return self.start - datetime.now(tz=systemTimeZone)


    def getTimeUntilEnd(self) -> timedelta:
        """Returns the time until the event ends."""
        systemTimeZone = datetime.now().astimezone().tzinfo

        return self.end - datetime.now(tz=systemTimeZone)


    def load(self, signature_key=None) -> None:
        """Loads the event code into the globals dictionary."""

        description = self.event.get("DESCRIPTION", None) # Code is stored in the description field of the event
        if description is None:
            self._code = None
            self.loaded = True
            return None
        
        if signature_key is not None:
            first_newline = description.find("\n") # Find the first newline character
            
            signature = description[:first_newline] # First line of the description is the signature
            code = description[first_newline + 1:] # Rest of the description is the code

            expected_signature = hashlib.sha256((code + signature_key).encode()).hexdigest() # Check if the signature is valid
            if signature != expected_signature:
                raise Exception("Invalid signature. Expected: " + expected_signature + ", but got: " + signature + " - Code may have been tampered with.")

        else:
            code = description 
        
        code = code.replace("\xa0", " ") # Replace non-breaking spaces with regular spaces
        
        self._code = code
        self.loaded = True


    async def execute(self, verbose:bool = False) -> None:
        if not self.loaded:
            raise Exception("Event not loaded. Please load the event before executing.")
        
        if self.code is None:
            return None
        
        self.globals = {}
        exec(self.code, self.globals)
        
        if "onStart" in self.globals:
            await asyncio.sleep(self.getTimeUntilStart().total_seconds()) # By implementation of asyncio.sleep, negative seconds will run immediately
            if verbose:
                print(f"Starting {self.name}")
            self.globals["onStart"]()

        if "onEnd" in self.globals:
            await asyncio.sleep(self.getTimeUntilEnd().total_seconds()) # Will naturally only start waiting after onStart finished (if that exists)
            if verbose:
                print(f"Finishing {self.name}")
            self.globals["onEnd"]()
