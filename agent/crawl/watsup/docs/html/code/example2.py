from watsup.winGuiAuto import findControl,setEditText, findTopWindow,clickButton
import os
import os.path

FILENAME='atestfile.txt'

def main():
    # delete any occurrence of this file from the disk
    if os.path.exists(FILENAME):
        os.remove(FILENAME)
        
    form=findTopWindow(wantedText='Simple Form')
    button=findControl(form,wantedText='Create file')
    editbox=findControl(form,wantedClass='TEdit')
    
    # enter a filename:
    setEditText(editbox,[FILENAME])
    clickButton(button)
    
    # now check that the file is there
    if os.path.exists(FILENAME):
        print 'file %s is present' %FILENAME
    else:
        print "file %s isn't there" % FILENAME     

if __name__=='__main__':
    main()