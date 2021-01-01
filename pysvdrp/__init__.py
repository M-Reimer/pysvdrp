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

import socket
import time
import cchardet
import pysvdrp.exceptions as ex

# This is the socket timeout we set initially
DEFAULT_TIMEOUT = 20

class SVDRPConnection:
    from pysvdrp.channels import list_channels, get_channel, move_channel, delete_channel
    from pysvdrp.plugins import list_plugins
    from pysvdrp.tools import set_channel_position
    from pysvdrp.epg import list_epg, clear_epg, put_epg

    def __init__(self, host: str = "127.0.0.1", port: int = 6419) -> None:
        """
        Establishes a SVDRP connection

        host: VDR host to connect to (default: 127.0.0.1)
        port: SVDRP port to use (default: 6419)
        """
        # Connect to VDR
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

        # Set timeout to prevent "blocking forever" situations
        self.socket.settimeout(DEFAULT_TIMEOUT)

        # Open a reading binary file handler.
        self._readfh = self.socket.makefile(mode="rb")

        # Read VDR's status welcome message
        self.encoding = "ascii"
        status, message = self._recvmsg()
        if status != 220:
            raise ex.SVDRException(message, status)

        # VDR returns 3 strings, each one separated with "; "
        hostinfo, hosttime, self.encoding = message.split("; ")

        # Parse hostinfo
        self.hostname, dummy, dummy, self.vdrversion = hostinfo.split(" ")
        major, minor, revision = self.vdrversion.split(".")
        self.vdrversnum = int(major) * 10000 + int(minor) * 100 + int(revision)

        # Parse hosttime
        self.vdrtime = self._asctime2time(hosttime)

        # Open a writing file handler
        self._writefh = self.socket.makefile(mode="w", encoding=self.encoding)

    # Properly disconnect from VDR to prevent "lost connection" log messages
    def __del__(self):
        # Give VDR 5 seconds to handle the "QUIT" command
        self.socket.settimeout(5)

        # Try to send "QUIT" now
        # We don't care about errors happening here
        try:
            self._send("QUIT")
        except:
            pass

        # Then properly close socket
        self.socket.close()

    # Converts the time format sent by VDR to seconds since epoch
    def _asctime2time(self, asctime: str) -> int:
        #Sun Dec 27 17:15:23 2020
        return time.mktime(time.strptime(asctime, "%a %b %d %H:%M:%S %Y"))

    # Receives a one-line message from VDR
    def _recvmsg(self):
        line = self._readfh.readline()

        # Try to decode with the encoding, used by VDR, first. If this fails
        # (bad DVB data) then try to detect the correct encoding.
        try:
            line = line.decode(self.encoding)
        except Exception as err:
            line = line.decode(cchardet.detect(line).get('encoding', 'ascii'), errors="surrogateescape")

        line = line.rstrip("\r\n")
        status = line[:3]
        cont = line[3:4]
        message = line[4:]

        status = int(status)
        if status == 451:
            raise ex.ActionAborted(message, status)
        elif status == 500:
            raise ex.CommandUnrecognized(message, status)
        elif status == 501:
            raise ex.ParameterError(message, status)
        elif status == 502:
            raise ex.CommandNotImplemented(message, status)
        elif status == 504:
            raise ex.ParameterNotImplemented(message, status)
        elif status == 550:
            raise ex.ActionNotTaken(message, status)
        elif status == 554:
            raise ex.TransactionFailed(message, status)
        elif 500 <= status < 600 :
            raise ex.SVDRPException(message, status)

        if cont == "-":
            status *= -1

        return status, message

    # Receives a list from VDR
    def _recvlist(self):
        status, message = self._recvmsg()
        data = [message]
        while status < 0:
            status, message = self._recvmsg()
            data.append(message)
        return status, data

    # Sends a command to VDR
    def _send(self, command: str):
        self._writefh.write(command + "\n")
        self._writefh.flush()
