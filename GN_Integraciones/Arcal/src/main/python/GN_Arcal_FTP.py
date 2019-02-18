'''
Created on 8 oct. 2018

@author: jmramon
'''

import configparser
import logging
import os
import fnmatch
import shutil
import uuid
import datetime
import subprocess

from ftplib import FTP_TLS
from logging.handlers import RotatingFileHandler
from time import sleep

from pathlib import Path

LOGGER_LOGPATH="GN_Tesoreria_FTP_NC4.log"
LOGGER = logging.getLogger("Rotating Log")

def main():
    
    try:
        #Leemos la configuracion
        gn = readConfig()
        ftpURL                  = gn['ftp.url']
        ftpUser                 = gn['ftp.user']
        ftpPassword             = gn['ftp.password']
        ftpPath                 = gn['ftp.path']
        localPath               = gn['localPath']
        filematch               = gn['filematch']
        logsPath                = gn['logsPath'];
        historyBackupPath       = gn['historyBackupPath'];
        
        #Incializamos el logger
        LOGGER = create_rotating_log(logsPath)
        
        #Iniciamos el proceso
        LOGGER.info("INCIO proceso GN_Arcal_FTP.py")
        
        #Obtenemos los ficheros del FTP
        uploadFilesToFTP(ftpURL, ftpUser,ftpPassword,ftpPath,localPath,filematch,historyBackupPath)
        
        LOGGER.info("FIN proceso GN_Arcal_FTP.py")
    
    except Exception as e:
        LOGGER.exception(e,"Se ha producido un error")


def uploadFilesToFTP(ftpURL, ftpUser,ftpPassword,ftpPath,localPath,filematch,historyBackupPath):
    
    ftps = FTP_TLS(ftpURL)
    ftps.set_debuglevel(1)
    ftps.set_pasv(False)
    ftps.connect(port=21, timeout=80)
    ftps.login(ftpUser, ftpPassword)
    ftps.prot_p()
    ftps.ccc()
    try:
        ftps.cwd(ftpPath)
    except Exception:
        ftps.mkd(ftpPath)
        
    for (localPathDir, _, files) in os.walk(localPath):
        newdir=ftpPath
        try:
            ftps.cwd(newdir)
        except Exception:
            ftps.mkd(newdir)
        
        LOGGER.info("filematch="+filematch)
        
        for f in fnmatch.filter(files, filematch):
            fileLocalPath = os.path.join(localPathDir, f);
            file = open(fileLocalPath,'rb')
            ftps.storbinary('STOR '+f, file,blocksize=8192)
            file.close()
            LOGGER.info("Fichero transferido #:# "+fileLocalPath);
            sleep(1)
            now = datetime.datetime.now()
            historyBackupPathYear = os.path.join(historyBackupPath,str(now.year))
            
            try:
                os.stat(historyBackupPathYear)
            except:
                os.mkdir(historyBackupPathYear)
            
            moveFilesUUID(fileLocalPath,historyBackupPathYear)
                
    ftps.close()

def create_rotating_log(path):
    """
    Creates a rotating log
    """
    logger = logging.getLogger("Rotating Log")
    logging.basicConfig(format='%(asctime)s %(message)s')
    logger.setLevel(logging.INFO)

    # add a rotating handler
    handler = RotatingFileHandler(path, maxBytes=10*1024*1024,
                                  backupCount=5)
    
    FORMAT = "%(asctime)-15s %(message)s"
    fmt = logging.Formatter(FORMAT,datefmt='%d-%m-%Y %H:%M:%S')
    handler.setFormatter(fmt)

    logger.addHandler(handler)

    return logger

def readConfig():
    # Leemos el fichero de configuracion
    parser = configparser.ConfigParser()
    parser.read('config.ini')
    # leemos la extension gn
    gn = parser['gn']
    return gn

def moveFilesUUID(filePath,dstdir):
    
    def failed(exc):
        raise exc
    
    p = Path(filePath)
    newFileName = "{}_{}".format(p.stem, 1) +"_"+uuid.uuid1().__str__()+ ".pdf";
    LOGGER.info("newFileName:"+newFileName);
    p.rename(Path(p.parent, newFileName))
    #shutil.move(Path(p.parent, newFileName), Path(dstdir, newFileName))
    moveFileCmd(p.parent.__str__()+"\\"+newFileName.__str__() ,dstdir.__str__())
    
def moveFileCmd(filePath,dstdir): 
    
    moveFileCmdStr="move "+filePath+" "+dstdir
    
    LOGGER.info("moveFileCmdStr:"+moveFileCmdStr)
    
    os.system(moveFileCmdStr)
    
    #subprocess.call(["move", filePath, dstdir])

if __name__ == '__main__':
    main()