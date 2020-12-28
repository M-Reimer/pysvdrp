#    pysvdrp - Python SVDRP binding to control a running VDR instance
#    Copyright (C) 2020  Manuel Reimer <manuel.reimer@gmx.de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from collections import UserList
from collections import UserDict
from pysvdrp.channels import Channel
from pysvdrp.exceptions import SVDRPError

def list_epg(self, channel = '', filter = ''):
    """
    Gets EPG data. The EPG data is returned as "Schedules" object

    channel: Optional channel to get EPG for (EPG for all channels if not given)
             May be one of "channel number", "channel id" and "Channel object"
    filter: [ now | next | at <Time> ]
    """

    # If "Channel" object is given, get the channel id
    if isinstance(channel, Channel):
        channel = channel.channelid

    cmd = ["LSTE"]
    if channel:
        cmd.append(str(channel))
    if filter:
        cmd.append(filter)
    self._send(" ".join(cmd))
    status, data = self._recvlist()
    data.pop() # Remove "End of EPG data"

    schedules = Schedules()
    schedules.read(iter(data))
    return schedules

def clear_epg(self, channel = ""):
    """
    Clears epg data

    channel: Optional channel to clear EPG for (all channels if not given)
             May be one of "channel number", "channel id" and "Channel object"
    """

    # If "Channel" object is given, get the channel id
    if isinstance(channel, Channel):
        channel = channel.channelid

    cmd = ["CLRE"]
    if channel:
        cmd.append(str(channel))
    self._send(" ".join(cmd))
    status, message = self._recvmsg()

    if status != 250:
        raise SVDRPError(message, status)

def put_epg(self, data):
    self._send("PUTE")
    status, message = self._recvmsg()
    if status != 354:
        raise SVDRPError(message, status)

    for line in str(data).split("\n"):
        if line.strip() != "":
            self._send(line)
    self._send(".")

    status, message = self._recvmsg()
    if status != 250:
        raise SVDRPError(message, status)



class Schedules(UserDict):
    def __setitem__(self, key, value):
        UserDict.__setitem__(self, key, value)
        value.channelid = key

    def read(self, iterator: iter):
        for line in iterator:
            if line[0] == "C":
                schedule = Schedule()
                channelid, schedule.channelname = line.split(" ", 2)[1:]
                self[channelid] = schedule
                schedule.read(iterator)
            elif line[0] == "c":
                pass
            else:
                raise ValueError("Unknown tag while parsing EPG Schedules: " + line[0])

    def __str__(self):
        result = ""
        for channelid, schedule in self.items():
            result += " ".join(["C", channelid, schedule.channelname]) + "\n"
            result += str(schedule)
            result += "c\n"
        return result


class Schedule(UserList):
    def __init__(self, initlist=None):
        UserList.__init__(self, initlist)
        self.channelname = ""

    def read(self, iterator: iter):
        for line in iterator:
            if line[0] == "E":
                event = Event()
                event.eventid, event.starttime, event.duration, event.tableid, event.version = line.split(" ")[1:]
                self.append(event)
                event.read(iterator)
            elif line[0] == "e":
                pass
            elif line[0] == "c":
                return
            else:
                raise ValueError("Unknown tag while parsing EPG Schedules: " + line[0])

    def __str__(self):
        result = ""
        for event in self:
            result += " ".join(map(str, ["E", event.eventid, event.starttime, event.duration, event.tableid, event.version])) + "\n"
            result += str(event)
            result += "e\n"
        return result


class Event:
    def __init__(self):
        self.tableid = 0
        self.version = 0

    def read(self, iterator: iter):
        for line in iterator:
            if line[0] == "T":
                self.title = line[2:]
            elif line[0] == "S":
                self.shorttext = line[2:]
            elif line[0] == "D":
                self.description = line[2:].replace("|", "\n")
            elif line[0] == "G":
                self.contents = line[2:].split(" ")
            elif line[0] == "R":
                self.parentalrating = line[2:]
            elif line[0] == "X":
                if not hasattr(self, "components"):
                    self.components = []
                self.components.append(line[2:])
            elif line[0] == "V":
                self.vps = line[2:]
            elif line[0] == "@":
                self.aux = line[2:]
            elif line[0] == "e":
                return
            else:
                raise ValueError("Unknown tag while parsing EPG: " + line[0])

    @property
    def starttime(self):
        return self._starttime

    @starttime.setter
    def starttime(self, value):
        self._starttime = int(value)

        # We do automagic event id generation here if not already set
        # taken from xmltv2vdr.pl
        if not hasattr(self, "eventid"):
            self.eventid = int(value / 60 % 0xFFFF)

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = int(value)

    def __str__(self):
        result = ""
        if hasattr(self, "title"):
            result += "T " + self.title.replace("\n", " ") + "\n"
        if hasattr(self, "shorttext"):
            result += "S " + self.shorttext.replace("\n", " ") + "\n"
        if hasattr(self, "description"):
            result += "D " + self.description.replace("\n", "|") + "\n"
        if hasattr(self, "contents"):
            result += "G " + " ".join(self.contents) + "\n"
        if hasattr(self, "parentalrating"):
            result += "R " + self.parentalrating + "\n"
        if hasattr(self, "components"):
            for component in self.components:
                result += "X " + component + "\n"
        if hasattr(self, "vps"):
            result += "V " + self.vps + "\n"
        if hasattr(self, "aux"):
            result += "@ " + self.aux + "\n"
        return result
