#!/usr/bin/env python3
import os.path
import argparse
import difflib
from os import scandir
from os import stat
from os import link
from os import symlink
from os import chmod
from os import mkdir
from os import sendfile
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
def Str(s):
    """ c onvert DirEntry to str """
    s = str(s)
    return s[11:-2]

def has_exist(ls):
    for entry in ls:
        if not os.path.isfile(entry) and not os.path.isdir(entry):
            return False
    return True

def process_entry_args(entry_ls):
    ls = []
    for entry in entry_ls:
        if entry[len(entry)-1] == '/':
            fd = Entry(entry[:-1])
            for subpath in fd.scan_dir():
                ls.append(subpath)
        else:
            ls.append(entry)
    return ls

def sync(src, dst):

    """ the magic function """
    # Preserve the links "
    if src.isHardLink() or src.isSymlink():
        if src.isHardLink():
            dst.createHardlink(src.get_realpath(), dst.name)
        if src.isSymlink():
            dst.createSymlink(src.get_realpath(), dst.name)
    else:
        if src.isFile(): # If Entry is File
            #Check if files is not exist, we create a new one:
            if not dst.isFile():
                f = open(dst.name, 'w+')
                f.write(src.get_data())
                f.close()
            #if dest file exists, use checksum
            else:
                if not src.md5() == dst.md5():
                    checksum(src, dst)
                elif src.size() < dst.size():
                    # if size of dest is greater, rewrite dest
                    f = open(dst.name, 'w+')
                    f.write(src.get_data())
                    f.close()
                else:
                    checksum(src, dst)
            
            """ Set Attribute """
            dst.set_mode(src.mode())
            dst.set_utime(src.atime(), src.mtime())
            
        else:   # If entry is Directory
            

            if not os.path.isdir(dst.name):
                os.mkdir(dst.name)

            
            """ Set Attribute """
            dst.set_mode(src.mode())
            dst.set_utime(src.atime(), src.mtime())

            for entry in src.scan_dir(): 
                src_entry = Entry(src.name + '/' + entry)
                dst_entry = Entry(dst.name + '/' + entry)
                sync(src_entry, dst_entry)

def checksum(src, dst):

    src_o = os.open(src.name, os.O_RDWR)
    dst_o = os.open(dst.name, os.O_RDWR)

    """ checksum algorithm to modified dst file """
    for i in range(src.size()):
        src_r = os.read(src_o, 1) # read 1 byte from src
        dst_r = os.read(dst_o, 1) # read 1 byte from dst


        # If 2 bytes are different, rewrite that byte on dest:
        if src_r.decode('utf-8') != dst_r.decode('utf-8'):
            if dst_r.decode('utf-8') != '':
                os.lseek(dst_o, -1 ,1)
            os.write(dst_o, src_r)
            """ 
            optional method :
                os.sendfile(dst_o, src_o, i, 1)
            """

""" create argument """
file_parser = argparse.ArgumentParser(add_help=False)
file_parser.add_argument('files', type=str, nargs = '*')
parser = argparse.ArgumentParser(add_help=False, parents=[file_parser], prefix_chars=' ')
parser.add_argument('-u', action='store_true')
parser.add_argument('-c', action='store_true')
args = parser.parse_args()  # Namespace Object
args = vars(args) # Convert Namespace to Dict

""" Get file argument from argparse """
EntryArg = []

""" Get options (-u, -c) """
bU_option = args['-u']
bC_option = args['-c']
for e in args['files']:
    if e != '-u' and e != '-c':
        EntryArg.append(e)
    else:
        if e == '-u':
            bU_option = True
        else:
            bC_option = True
EntryArg = process_entry_args(EntryArg)




"""
notes:
    - Hardlink doesn't work with DIRECTORY
    - Create links required source file exist, destination file does not exist
    - If rsync not found destination file/dir, new file/dir will be created
"""

    
class Entry:

    def __init__ (self, name):
        self.name = name

    """ Attribute """
    def get_realpath(self):
        """return the source file if the current file is a symlink"""
        return os.path.realpath(self.name)

    def isFile(self):
        return os.path.isfile(self.name)
    
    def isDir(self):
        return os.path.isdir(self.name)

    def isExist(self):
        return self.isFile() or self.isDir()

    def isSymlink(self):
        return os.path.islink(self.name)
    
    def isHardLink(self):
        return not self.isSymlink() and os.stat(self.name).st_nlink > 1 and self.isFile()
    
    def mtime(self):
        return os.stat(self.name).st_mtime
    
    def atime(self):
        return os.stat(self.name).st_atime

    def mode(self):
        return os.stat(self.name).st_mode
    
    """ symlink and hardlink """
    def createSymlink(self, source):
        os.symlink(source, self.name)

    def createHardlink(self, source):
        if os.path.isfile(source):
            os.link(source, self.name)

    """ SET TIME and PERMISSION """
    def set_utime(self, atime, mtime):
        os.utime(self.name , (atime, mtime))
    
    def set_mode(self, mode):
        os.chmod(self.name, mode)

    """ FILE CONTENT """
    def get_data(self):
        """ only work with file """
        # check if file exists
        if self.isFile():
            f = open(self.name, 'r')
            data = f.read()
            f.close()
            return data
        else:
            return None
    
    """ DIRECTORY CONTENT """
    def get_tree(self, current_dir = None):
        """ only for directory """
        if not self.isFile():
            """ create a list of all entry """
            tree = []
            if current_dir == None: # 1st call
                current_dir = self.name
            
            for entry in os.scandir(current_dir):
                entry = Str(entry)
                tree.append(current_dir + '/' + entry)
                "Check if entry is a Sub Directory"
                if os.path.isdir(current_dir + '/' + entry) is True:
                    for entry in self.get_tree(current_dir + '/' + entry):
                        tree.append(entry)
            return tree

    def scan_dir(self):
        """ return the current content of directory with depth 1 """
        tree = []
        for entry in os.scandir(self.name):
            entry = Str(entry)
            tree.append(entry)
        return tree
    
    def size(self):
        return os.stat(self.name).st_size
    def md5(self):
        import hashlib
        return hashlib.md5(self.get_data().encode('utf-8')).hexdigest()






if __name__ == '__main__':

    """ If num arguments > 2, then the last argument is the Directory. """
    if len(EntryArg) > 2:
        if not has_exist(EntryArg[:-1]):
            raise "Some files could not be transfered "
        else:

            dest_dir =  EntryArg[len(EntryArg)-1]
            if not os.path.isdir(dest_dir):
                os.mkdir(dest_dir) # Create destination dir by last argument
            EntryArg.pop() # pop destination directory
            
            for entry in EntryArg:

                src_entry = Entry(entry) 
                dst_entry = Entry(dest_dir + '/' + entry)

                # Skip over non-existing file
                if src_entry.isExist():
                    sync(src_entry, dst_entry)
                else:
                    continue

    elif len(EntryArg) == 2:
        src_entry = Entry(EntryArg[0])
        dst_entry = Entry(EntryArg[1])

        #check if source file is directory
        if src_entry.isDir():
            dst_entry = Entry(EntryArg[1] + '/' + EntryArg[0])
            if not os.path.isdir(EntryArg[1]):
                os.mkdir(EntryArg[1])

         # Skip over non-existing file
        if src_entry.isExist():
            sync(src_entry, dst_entry)
        else:
            raise "File doesn't exists"

    
                
                
