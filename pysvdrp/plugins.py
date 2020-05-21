from collections import UserList

# Returns a list of plugins loaded into VDR
def list_plugins(self):
    self._send("PLUG")
    status, data = self._recvlist()
    data.pop(0) # Remove first item ("Available plugins:")
    data.pop()  # Remove last item ("End of plugin list")
    result = PluginList([])
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
class PluginList(UserList):
    def __contains__(self, obj):
        for item in self:
            if item["name"] == obj:
                return True
        return False
