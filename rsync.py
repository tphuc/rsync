#!/usr/bin/env python3
import os.path
import argparse
import difflib
from os import link
from os import symlink

""" 
os.utime : modification time  (st_atime, st_mtime)
os.path.realpath:
os.chmod : set file permission
argparse module
os.path module
os.difflib module
os.open, os.read, os.write, os.sendfile, os.lseek
os.mkdir
os.stat module
os.symlink, os.link, os.readlink
os.scandir
os.unlink
os.utime, os.chmod
"""

""" create argument """
parser = argparse.ArgumentParser()
parser.add_argument('-u', action='store_true')
parser.add_argument('-c', action='store_true')
#parser.add_argument('files', type=str, nargs = 2)
args = parser.parse_args()  # Namespace Object
args = vars(args) # Convert Namespace to Dict


class File:
    def __init__ (self, name):
        self.name = name
        #f = open(self.name, 'a+')
    def get_realpath(self):
        """return the source file if the current file is a symlink"""
        return os.path.realpath(self.name)



    def isFile(self):
        return os.path.isfile(self.name)
    
    def isSymlink(self):
        return os.path.islink(self.name)
    
    def createSymlink(self, source):
        os.symlink(source, self.name)

    def createHardlink(self, source, dest):
        os.link(source, dest)
    
    def isHardLink(self):
        return not self.isSymlink() and os.stat(self.name).st_ino > 1
    




file1 = File("file1")
file_sym = File("hard1")
print(file_sym.isHardLink())

