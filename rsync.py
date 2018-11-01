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
    #check if list of entry is exist
    for entry in ls:
        if not os.path.isfile(entry) and not os.path.isdir(entry):
            return False
    return True

def process_content_arg(entry_ls):
    ls = []
    special = []
    for entry in entry_ls:
        if entry[len(entry)-1] == '/':
            fd = Entry(entry[:-1])
            for subpath in fd.scan_dir():
                ls.append(entry+subpath)
                special.append(entry+subpath)
        else:
            ls.append(entry)

    return (ls, special)

def sync(src, dst, U_option=False, C_option=False):
    if dst.isExist():
        if U_option:
            if src.mtime() < dst.mtime():
                dst.set_mode(src.mode())
                dst.set_utime(src.atime(), src.mtime())
                return 0 #do nothing
        if not C_option:
            if src.mtime() == dst.mtime() and src.atime() == dst.atime():
                return 0 #do nothing
    """ the magic function """
    # Preserve the links "
    if src.isHardLink() or src.isSymlink():
        if src.isHardLink():
            dst.createHardlink(src.get_realpath())
        if src.isSymlink():
            dst.createSymlink(src.get_realpath())
        """ Set Attribute """
        dst.set_mode(src.mode())
        dst.set_utime(src.atime(), src.mtime())
    else:
        if src.isFile(): # If Entry is File
            #Check if files is not exist, we create a new one:
            if not dst.isFile():
                f = open(dst.name, 'w+')
                f.write(src.get_data())
                f.close()
            #if dest file exists, use checksum
            else:
                if src.md5() == dst.md5():
                    return 0
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
                sync(src_entry, dst_entry, U_option, C_option)

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
        return os.stat(self.name).st_nlink > 1 and self.isFile()

    def mtime(self):
        return os.stat(self.name).st_mtime

    def atime(self):
        return os.stat(self.name).st_atime

    def mode(self):
        return os.stat(self.name).st_mode

    def inode(self):
        return os.stat(self.name).st_ino

    """ symlink and hardlink """
    def createSymlink(self, source):
        if self.isExist():
            if self.inode() != os.stat(source).st_ino:
                os.unlink(self.name)
                os.symlink(source, self.name)
        else:
            os.symlink(source, self.name)

    def createHardlink(self, source):
        if self.isExist():
            if self.inode() != os.stat(source).st_ino:
                os.unlink(self.name)
                os.link(source, self.name)
        else:
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


###############################
def process_various_arguments(EntryArg, Entry_content_fd, U_option, C_option, R_option):
    if not has_exist(EntryArg[:-1]):
        print('Some files could not be transfered')
        return 0
    
    dst_fd = Entry(EntryArg[len(EntryArg)-1])
    if not dst_fd.isExist():
        os.mkdir(dst_fd.name)
    EntryArg.pop()

    for entry in EntryArg:
        src_entry = Entry(entry)
        dst_entry = Entry(dst_fd.name + '/' + entry)

        if entry in Entry_content_fd:
            dst_entry = Entry(dst_fd.name + '/' + entry[entry.find('/') + 1:])
        sync(src_entry, dst_entry, U_option, C_option)


def process_two_argument(EntryArg, Entry_content_fd, U_option, C_option, R_option):
    src = Entry(EntryArg[0])
    dst = Entry(EntryArg[1])

    if src.isDir():
        if not R_option:
            print("skipping directory "+src.name)
            return 0
        if not dst.isExist():
            os.mkdir(dst.name)
        dst = Entry(EntryArg[1] + '/' + EntryArg[0])
        sync(src, dst, U_option, C_option)      
    elif src.isFile():
        if dst.isDir():
            dst = Entry(EntryArg[1] + '/' + EntryArg[0])
        sync(src, dst, U_option, C_option)

    elif len(Entry_content_fd):
        dst = Entry(EntryArg[1] + '/' + EntryArg[0][EntryArg[0].find('/') + 1:])
        sync(src, dst, U_option, C_option)
    else:
        print('rsync: link_stat "' + EntryArg[0] + '" failed: No such file or directory (2)')
        return 0


#######################################
if __name__ == '__main__':
    """ create argument """
    file_parser = argparse.ArgumentParser(add_help=False)
    file_parser.add_argument('files', type=str, nargs = '*')
    parser = argparse.ArgumentParser(add_help=False, parents=[file_parser], prefix_chars=' ')
    parser.add_argument('-u', action='store_false')
    parser.add_argument('-c', action='store_false')
    parser.add_argument('-r', action='store_false')
    args = parser.parse_args()  # Namespace Object
    args = vars(args) # Convert Namespace to Dict

    """ Get file argument from argparse """
    args_ls = []

    """ Get options (-u, -c) """
    bU_option = args['-u']
    bC_option = args['-c']
    bR_option = args['-r']
    for e in args['files']:
        if e != '-u' and e != '-c' and e != '-r':
            args_ls.append(e)
        else:
            if e == '-u':
                bU_option = True
            elif e == '-c':
                bC_option = True
            elif e == '-r':
                bR_option = True
    (EntryArg, Entry_content_fd) = process_content_arg(args_ls)



    """ process rsync """
    if len(EntryArg) > 2:
        process_various_arguments(EntryArg, Entry_content_fd, bU_option, bC_option, bR_option)

    elif len(EntryArg) == 2:
        process_two_argument(EntryArg, Entry_content_fd, bU_option, bC_option, bR_option)

    else:
        print('value != ""')