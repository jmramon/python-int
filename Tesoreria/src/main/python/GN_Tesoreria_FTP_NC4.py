import ftplib 
import configparser
import logging
import subprocess
import os
import glob
import shutil
import fnmatch

from logging.handlers import RotatingFileHandler
from time import sleep

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
        downloadPath            = gn['downloadPath']
        filematch               = gn['filematch']
        deleteFromOrigin        = gn['deleteFromOrigin']
        netDrive                = gn['net.drive'];
        netUser                 = gn['net.user'];
        netPassword             = gn['net.password'];
        netPath                 = gn['net.path'];
        destinationpath         = gn['destinationpath'];
        secondsForCloseNetUse   = gn['secondsForCloseNetUse'];
        historyBackupPath       = gn['historyBackupPath'];
        logsPath                = gn['logsPath'];
        
        #Incializamos el logger
        log_file = LOGGER_LOGPATH
        LOGGER = create_rotating_log(logsPath)
        
        #Iniciamos el proceso
        LOGGER.info("INCIO proceso GN_Tesoreria_FTP_NC4.py")
        
        #Obtenemos los ficheros del FTP
        anyFile = retrieveFilesFromFTP(ftpURL, ftpUser,ftpPassword,ftpPath,downloadPath,filematch,deleteFromOrigin)
        
        if anyFile:
            #Abrimos la conexion de red
            openNetUse(netDrive, netPath, netUser, netPassword)
            
            #Copiamos los ficheros
            copyFiles(downloadPath, destinationpath, filematch)
            
            #Esperamos un minuto a que se copien los ficheros antes de cerrar
            sleep(int(secondsForCloseNetUse));
            
            #Cerramos la conexion de red
            closeNetUse(netDrive)
    
            #Copiamos los ficheros a backup
            copyFiles(downloadPath,historyBackupPath, filematch)
            
            #Borramos los ficheros del FTP
            deleteFilesFromFTP(ftpURL, ftpUser,ftpPassword,ftpPath,downloadPath,filematch,deleteFromOrigin)
            
            #Borramos los ficheros de download
            removeFiles(downloadPath)

        LOGGER.info("FIN proceso GN_Tesoreria_FTP_NC4.py")
    
    except Exception as e:
        LOGGER.exception("Se ha producido un error")

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

def closeNetUse(netDrive):
    # Disconnect anything on M
    LOGGER.info(r'Cerramos la conexion de red:'+netDrive)
    subprocess.call(r'net use '+netDrive+' /del /y', shell=True)
    
def openNetUse(netDrive,netPath,netUser,netPassword):
    # Connect to shared drive, use drive letter M
    '''Ver por qué esto no funciona
    LOGGER.info(r'NET USE '+netDrive+' "'+netPath+'" '+netPassword+' /USER:'+netUser)
    command = r'NET USE '+netDrive+' "+'+netPath+'" '+netPassword+' /USER:'+netUser
    subprocess.call(command, shell=True)
    '''
    
    LOGGER.info(r'Abrimos la conexion de red  K: "\\172.16.1.15\GRUPO\Dpto. Administracion\COMUN\DTO.CONTABILIDAD Y FINANZAS\BARRIDOS_CONTABLES')
    subprocess.call(r'NET USE K: "\\172.16.1.15\GRUPO\Dpto. Administracion\COMUN\DTO.CONTABILIDAD Y FINANZAS\BARRIDOS_CONTABLES" EDITRAN /USER:GRUPONORTE\EDITRAN', shell=True)

def retrieveFilesFromFTP(ftpURL, ftpUser,ftpPassword,ftpPath,downloadPath,filematch,borrar):

        ftp = ftplib.FTP_TLS(ftpURL)
        ftp.login(ftpUser,ftpPassword)

        ftp.cwd(ftpPath)  # change directory to /pub/

        filenames = ftp.nlst()  # get filenames within the directory
        
        if filenames:
            LOGGER.info("Vamos a descargar los siguientes ficheros:"+', '.join(filenames))

            downloaded = []
            skipped = 0
    
            for filename in ftp.nlst(filematch):
                if filename not in downloaded:
                    fhandle = open(downloadPath+"\\"+filename, 'wb')
                    ftp.retrbinary('RETR ' + filename, fhandle.write)
                    fhandle.close()
                    downloaded.append(filename)
                else:
                    skipped += 1
            ftp.quit()
            LOGGER.info("Se han descargado los siguientes ficheros:"+', '.join(downloaded))
            return True
        else:
            LOGGER.info("No hay ficheros para descargar:"+', '.join(filenames))
            return False

        

def deleteFilesFromFTP(ftpURL, ftpUser,ftpPassword,ftpPath,downloadPath,filematch,borrar):

        ftp = ftplib.FTP_TLS(ftpURL)
        ftp.login(ftpUser,ftpPassword)

        ftp.cwd(ftpPath)  # change directory to /pub/

        filelist = glob.glob(downloadPath+"/*")
        LOGGER.info("Vamos a descargar los siguientes ficheros:"+', '.join(filelist))
        
        for f in filelist:
            f2 = open(f)
            name = os.path.basename(f2.name)
            ftp.delete(name)
        ftp.quit()
        
        LOGGER.info("Se han descargado los siguientes ficheros:"+', '.join(filelist))
        
  
def copyFiles(srcdir,dstdir,filematch):
    
    def failed(exc):
        raise exc

    for dirpath, dirs, files in os.walk(srcdir, topdown=True, onerror=failed):
        for file in fnmatch.filter(files, filematch):
            shutil.copy2(os.path.join(dirpath, file), dstdir)
        break # no recursion

def removeFiles(srcdir):
    
    filelist = glob.glob(srcdir+"/*")
    for f in filelist:
        os.remove(f)

if __name__ == '__main__':
    main()