#### ##     ## ########   #######  ########  ########  ######
 ##  ###   ### ##     ## ##     ## ##     ##    ##    ##    ##
 ##  #### #### ##     ## ##     ## ##     ##    ##    ##
 ##  ## ### ## ########  ##     ## ########     ##     ######
 ##  ##     ## ##        ##     ## ##   ##      ##          ##
 ##  ##     ## ##        ##     ## ##    ##     ##    ##    ##
#### ##     ## ##         #######  ##     ##    ##     ######

# Standard
import sys, os, platform

# Logging
import logging
import logging.config

# PyQt
from PyQt4 import QtCore

# DICOM
import dicom

class Correct(QtCore.QObject):

    def __init__(self):
        """Default Constructor
        """
        super(Correct, self).__init__()

        logger = logging.getLogger(__name__)
        logging.config.fileConfig("logging.ini", disable_existing_loggers=False)

        # Fist argument is filename
        inputfile = str(QtCore.QCoreApplication.arguments()[1])
        logger.debug("Input file for correction: " + inputfile)

        outputfile = str(QtCore.QCoreApplication.arguments()[2])
        logger.debug("Output corrected file: " + outputfile)

        # Open DICOM file
        ds = dicom.read_file(inputfile, force=True)

        if "TransferSyntaxUID" in ds.file_meta:
            # Philips Gemini PET/CT scanner (compressed files with private syntax UID)
            if ds.file_meta.TransferSyntaxUID == "1.3.46.670589.33.1.4.1":
                if platform.system() == "Linux":

                    command = ""
                    if os.path.isfile("./rle2img"):
                        command = "./rle2img"
                    elif os.path.isfile("./correct/rle2img"):
                        command = "./correct/rle2img"
                    else:
                        logger.error("Cannot find rle2img utility.")
                        
                    if command != "":
                        #logger.debug("Starting correction rle2img: " + command + " " + inputfile)

                        # Output default is outrle.dcm
                        process = QtCore.QProcess()
                        process.start(command + " " + inputfile)
                        # Wait until it is really finished
                        process.waitForFinished(-1)

                        #logger.debug("Correction rle2img finished.")

                        if os.path.isfile("outrle.dcm"):
                            inputfile = "outrle.dcm"
                        else:
                            logger.error("Correction rle2img did not generate the output: outrle.dcm")    

        # Use DICOM offise toolkit convert to fix common errors
        if platform.system() == "Linux":

            command = "dcmconv \"" + inputfile + "\" \"" + outputfile + "\""
            logger.debug("Starting correction dcmconv: " + command)

            process = QtCore.QProcess()
            process.start(command)
            # Wait until it is really finished
            process.waitForFinished(-1)

            if not os.path.isfile(outputfile):
                logger.error("Correction dcmconv did not generate the output: " + outputfile)

            # Cleanup intermediate file (if created)
            if inputfile == "outrle.dcm":
                os.remove("outrle.dcm")

##     ##    ###    #### ##    ##
###   ###   ## ##    ##  ###   ##
#### ####  ##   ##   ##  ####  ##
## ### ## ##     ##  ##  ## ## ##
##     ## #########  ##  ##  ####
##     ## ##     ##  ##  ##   ###
##     ## ##     ## #### ##    ##

def main():
    """Main function
    """
    app = QtCore.QCoreApplication(sys.argv)
    correct = Correct()
    app.quit()

if __name__ == '__main__':
    main()
    