#    pysvdrp - Python SVDRP binding to control a running VDR instance
#    Copyright (C) 2021  Manuel Reimer <manuel.reimer@gmx.de>
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

# Generic SVDRP exception every SVDRP based response bases on
class SVDRPException(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status

# 451 Requested action aborted: local error in processing
class ActionAborted(SVDRPException):
    pass

# 500 Syntax error, command unrecognized
class CommandUnrecognized(SVDRPException):
    pass

# 501 Syntax error in parameters or arguments
class ParameterError(SVDRPException):
    pass

# 502 Command not implemented
class CommandNotImplemented(SVDRPException):
    pass

# 504 Command parameter not implemented
class ParameterNotImplemented(SVDRPException): #504
    pass

# 550 Requested action not taken
class ActionNotTaken(SVDRPException): #550
    pass

# 554 Transaction failed
class TransactionFailed(SVDRPException): #554
    pass

# Handling Plugin reply codes needs more work. Probably not all of them
# should actually throw an Exception. Especially code 900.
#
# 900 Default plugin reply code
# 901..999 Plugin specific reply codes
#class PluginException(SVDRPException):
#    pass
