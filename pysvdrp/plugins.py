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

# Returns a list of plugins loaded into VDR
def list_plugins(self):
    self._send("PLUG")
    status, data = self._recvlist()
    data.pop(0) # Remove first item ("Available plugins:")
    data.pop()  # Remove last item ("End of plugin list")
    result = Plugins()
    for line in data:
        name, version, dummy, description = line.split(" ", 3)
        result.append({
            "name": name,
            "version": version[1:],
            "description":  description
        })
    return result

# All this class does is to allow to use the "in" keyword to search for a
# plugin name directly.
class Plugins(UserList):
    def __contains__(self, obj):
        for item in self:
            if item["name"] == obj:
                return True
        return False
