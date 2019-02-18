import os, shutil, sys,fnmatch


def moveFiles(srcdir,dstdir,filepattern):
    
    def failed(exc):
        raise exc

    for dirpath, dirs, files in os.walk(srcdir, topdown=True, onerror=failed):
        for file in fnmatch.filter(files, filepattern):
            shutil.copy2(os.path.join(dirpath, file), dstdir)
        break # no recursion


def main():
    
    srcDir = "C:\\tmp\\in";
    dstDir = "C:\\tmp\\out";
    filepattern = "GNORTE.NC4.EXPORT*";
    
    moveFiles(srcDir, dstDir, filepattern)

if __name__ == '__main__':
    main()