#    Jyn: Simple Jython native code access layer
#    Copyright (C) 2010 projectmoon
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
jyn: Simple Jython native access layer 
A (very) simple module that enables native code in Jython via the use of JNA.
This module is similar to the standard Python ctypes module, but it is not as
extensive or powerful.

Import the Library class from this module and initialize it with the name or
path of the library you wish to bring into the Jython scripting environment.
Instances of class Library expect native function calls as attributes of the
instance. Example: To use printf:
lib = jyn.libc()
lib.printf("Hello world\n") 

Requires jna.jar to work.
'''
from com.sun.jna import NativeLibrary, Platform, Pointer, Memory
from java.lang import IllegalArgumentException, UnsatisfiedLinkError
from java.lang import String, Integer, Long, Float, Byte, Void

#Remap some JNA classes to make them less annoying to import
Pointer = Pointer
Memory = Memory
 
#Number file descriptors for stdin, stdout, and stderr
#TODO: Fix these so they represent the actual FILE* objects, if possible
stdin = 0
stdout = 1
stderr = 2

class Buffer(object):
    """A generic Buffer class to use for functions wanting buffers, such as libc's read()"""
    def __init__(self, size):
        self._buf = Memory(size)
        self._buf.clear(size)
        self.size = size
    
    def asString(self, start = 0, size = -1):
        """Attempt to convert this buffer to text. start and length parameters can be specified.
        If length is not specified, the originally declared size of the buffer will be used."""
        if size <= 0:
            size = self.size
        
        bytes = self._buf.getByteArray(start, size) 
        return String(bytes)
        
class Library(object):
    """Initialize to create a new mapping to a system library, by passing in the name or path of the library."""     
    def __init__(self, libname):
        self._lib = NativeLibrary.getInstance(libname)

    def __getitem__(self, key):
        return self.__dict__[key]
    
    def __setitem__(self, key, value):
        self.__dict__[key] = value
    
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            try:
                func = self._lib.getFunction(attr)
                self._createWrapper(func)
            except UnsatisfiedLinkError:
                raise KeyError("Function \"" + attr + "\" not found in library")
           
            return self[attr]
    
    def _createWrapper(self, func):
        self[func.name] = WrappedNativeFunction(func)

class WrappedNativeFunction(object):
    """
    Represents a native function found in the library. Similar to ctypes, each
    WrappedNativeFunction has a restype attribute attached to it. This defaults
    to the Python int type. Other types accepted are: str, long, float, and None
    (for void). If the function returns something else such as a pointer or a
    struct, you will need to implement the Pointer or Structure classes from JNA
    as appropriate.
    
    See https://jna.dev.java.net/javadoc/overview-summary.html for more info.
    """
    
    #Map python types to Java types for return types and arguments. JNA does
    #not like Jython's types.
    _argMap = {
       str : String,
       int : Integer,
       long : Long,
       float : Float,
       None : Void
    }
    
    def __init__(self, func):
        self._func = func
        self.name = func.name
        self.restype = int
        self.argtypes = []
        
    def __call__(self, *args):
        try:
            #Handle return type mapping
            restype = self.restype
            if self.restype in self._argMap:
                restype = self._argMap[self.restype]
                
            #Convert from tuple to list, and handle Buffer -> Memory obj translation
            args = list(args)
            for arg in args:
                if isinstance(arg, Buffer):
                    args[args.index(arg)] = arg._buf
                    
            return self._func.invoke(restype, args)
        except IllegalArgumentException, e:
            raise TypeError(e.message)
            
    def __str__(self):
        return self._func.toString()      

def libc():
    """Convenience function to return the system's C library."""
    if Platform.isWindows():
        return Library("msvcrt")
    else:
        return Library("c")