from collections import UserList

def list_channels(self, withgroups: bool = False):
    """
    Requests a channel list from VDR.
    Returned is a list of "Channel" objects where each object represents one
    channel.

    withgroups: If "True" the returned list contains the group separators
    """
    self._send("LSTC" + (" :groups" if withgroups else ""))
    status, data = self._recvlist()
    result = Channels()
    groupid = 0
    for line in data:
        number, channelstring = line.split(" ", 1)
        channel = Channel(channelstring, number)
        if (channel.groupsep):
            groupid += 1
            channel.groupnumber = groupid
        result.append(channel)
    return result


def get_channel(self, channel):
    """
    Requests information for one channel. The result is returned as a
    "Channel" object.

    channel: The channel to request. Either a channel number or channel id
    """
    self._send("LSTC " + str(channel))
    status, message = self._recvmsg()
    number, channelstring = message.split(" ", 1)
    return Channel(channelstring, number)


def move_channel(self, source, target):
    """
    Moves channel with the current channel number "source" to channel
    number "target"
    """
    self._send("MOVC " + str(source) + " " + str(target))
    status, message = self._recvmsg()

    if status != 250:
        raise SVDRPError(message, status)

    parts = message.split('"')
    return int(parts[1]), int(parts[3])

def delete_channel(self, channel):
    """
    Deletes given channel. "channel" may be either a channel number, a channel
    id or an "Channel" object whose channel id is used.
    """

    # If "Channel" object is given, get the channel id
    if isinstance(channel, Channel):
        channel = channel.channelid

    # TODO: Allow this to pass directly for VDR versions with allow channelids
    # directly for "DELC"
    if isinstance(channel, str):
        channel = self.get_channel(channel).number

    self._send("DELC " + str(channel))
    status, message = self._recvmsg()

    if status != 250:
        raise SVDRPError(message, status)


# Objects of type "Channel" encapsulate the information of one channel
class Channel:
    def __init__(self, channelstring: str = "", number: int = 0):
        if not channelstring:
            return

        self.number = int(number)

        # Handle group separators
        self.groupsep = False
        if (channelstring.startswith(":")):
            self.groupsep = True
            self.name = channelstring[1:]
            if self.name.startswith("@"):
                number, self.name = self.name[1:].split(maxsplit = 1)
                self.number = int(number)
            self.shortname = self.name
            return

        fullname, frequency, self.parameters, self.source, srate, self.vpid, self.apid, self.tpid, self.caid, sid, nid, tid, rid = channelstring.split(":")

        # Split name
        self.provider = ""
        self.shortname = ""
        if ";" in fullname:
            fullname, self.provider = fullname.split(";", 1)
        if "," in fullname:
            fullname, self.shortname = fullname.split(",", 1)
        self.name = fullname

        self.frequency = int(frequency)
        self.srate = int(srate)
        self.sid = int(sid)
        self.nid = int(nid)
        self.tid = int(tid)
        self.rid = int(rid)

    @property
    def isatsc(self) -> bool:
        return self.source.startswith("A")
    @property
    def iscable(self) -> bool:
        return self.source.startswith("C")
    @property
    def issat(self) -> bool:
        return self.source.startswith("S")
    @property
    def isterr(self) -> bool:
        return self.source.startswith("T")

    def _transponder(self) -> int:
        tf = self.frequency
        while tf > 20000:
            tf /= 1000;
        if (self.issat):
            p = self.parameters
            if (p):
                if p.startswith("H"):
                    tf += 100000
                elif p.startswith("V"):
                    tf += 200000
                elif p.startswith("L"):
                    tf += 300000
                elif p.startswith("R"):
                    tf += 400000
        return tf

    @property
    def channelid(self):
        if (self.groupsep):
            return "GROUP" + str(self.groupnumber)

        parts = [
            self.source,
            str(self.nid),
            (str(self.tid) if (self.nid or self.tid) else str(self._transponder())),
            str(self.sid)
        ]
        if self.rid:
            parts.append(self.rid)
        return "-".join(parts)

    # Re-merges channel info into a channel string
    def __str__(self):
        if self.groupsep:
            if self.number:
                return ":@{} {}".format(self.number, self.name)
            else:
                return ":" + self.name

        fullname = self.name
        if self.shortname:
            fullname += "," + self.shortname
        if self.provider:
            fullname += ";" + self.provider
        return ":".join([
            fullname,
            str(self.frequency),
            self.parameters,
            self.source,
            str(self.srate),
            self.vpid,
            self.apid,
            self.tpid,
            self.caid,
            str(self.sid),
            str(self.nid),
            str(self.tid),
            str(self.rid)
        ])


# "Special" list for channels with custom "find" methods
class Channels(UserList):
    def find_by_number(self, aNumber):
        for index, channel in enumerate(self):
            if channel.number == aNumber:
                return index;
        raise ValueError("Channel number '" + str(aNumber) + "' is not in channel list");

    def find_by_channelid(self, aID):
        for index, channel in enumerate(self):
            if channel.channelid == aID:
                return index;
        raise ValueError("Channel ID '" + str(aID) + "' is not in channel list");
