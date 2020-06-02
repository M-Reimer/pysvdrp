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
        cmd.append(channel)
    if filter:
        cmd.append(filter)
    self._send(" ".join(cmd))
    status, data = self._recvlist()
    data.pop() # Remove "End of EPG data"
    return _parse_epg(data)


def _parse_epg(data):
    schedules = Schedules()
    for line in data:
        if line[0] == "C":
            schedule = Schedule()
            dummy, channelid, schedule.channelname = line.split(" ", 2)
            schedules[channelid] = schedule
            print(schedules)
        elif line[0] == "c":
            schedule = None
        elif line[0] == "E":
            event = Event()
            dummy, event.eventid, event.starttime, event.duration, event.tableid, event.version = line.split(" ")
            schedule.append(event)
        elif line[0] == "e":
            event = None
        elif line[0] == "T":
            event.title = line[2:]
        elif line[0] == "S":
            event.shorttext = line[2:]
        elif line[0] == "D":
            event.description = line[2:]
        elif line[0] == "G":
            event.contents.append(line[2:])
        elif line[0] == "R":
            event.parentalrating = line[2:]
        elif line[0] == "X":
            event.components.append(line[2:])
        elif line[0] == "V":
            event.vps = line[2:]
        elif line[0] == "@":
            event.aux = line[2:]
        else:
            raise ValueError("Unknown tag while parsing EPG: " + line[0])
    return schedules


class Schedules(UserDict):
    def __setitem__(self, key, value):
        UserDict.__setitem__(self, key, value)
        value.channelid = key


class Schedule(UserList):
    def __init__(self, initlist=None):
        UserList.__init__(self, initlist)
        self.tableid = 0
        self.version = 0


class Event:
    def __init__(self, epgdata = []):
        epgdata = iter(epgdata)
        self.contents = []
        self.components = []
