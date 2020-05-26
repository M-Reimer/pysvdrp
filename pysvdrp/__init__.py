import socket
import datetime
import cchardet

# This is the socket timeout we set initially
DEFAULT_TIMEOUT = 20

class SVDRPConnection:
    from pysvdrp.channels import list_channels, get_channel, move_channel, delete_channel
    from pysvdrp.plugins import list_plugins
    from pysvdrp.tools import set_channel_position

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
            raise SVDRError(message, status)

        # VDR returns 3 strings, each one separated with "; "
        hostinfo, hosttime, self.encoding = message.split("; ")

        # Parse hostinfo
        self.hostname, dummy, dummy, self.vdrversion = hostinfo.split(" ")
        major, minor, revision = self.vdrversion.split(".")
        self.vdrversnum = int(major) * 10000 + int(minor) * 100 + int(revision)

        # Parse hosttime
        self.vdrtime = self._asctime2datetime(hosttime)

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

    # Converts the time format sent by VDR to a python datetime object
    def _asctime2datetime(self, asctime: str):
        monthconv = {value: index for index, value in enumerate([
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ])}
        dummy, monthname, day, timestr, year = asctime.split()
        hour, minute, second = timestr.split(":")
        return datetime.datetime(
            year = int(year),
            month = monthconv[monthname] + 1,
            day = int(day),
            hour = int(hour),
            minute = int(minute),
            second = int(second)
        )

    # Receives a one-line message from VDR
    def _recvmsg(self):
        line = self._readfh.readline()

        # Try to decode with the encoding, used by VDR, first. If this fails
        # (bad DVB data) then try to detect the correct encoding.
        try:
            line = line.decode(self.encoding)
        except Exception as err:
            line = line.decode(cchardet.detect(line).get('encoding', 'ascii'), errors="surrogateescape")

        line.rstrip("\n")
        status = line[:3]
        cont = line[3:4]
        message = line[4:]

        if status.startswith("5"):
            raise SVDRPError(status + " " + message, int(status))

        status = int(status)
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


class SVDRPError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status
