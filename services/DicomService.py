#### ##     ## ########   #######  ########  ########  ######
 ##  ###   ### ##     ## ##     ## ##     ##    ##    ##    ##
 ##  #### #### ##     ## ##     ## ##     ##    ##    ##
 ##  ## ### ## ########  ##     ## ########     ##     ######
 ##  ##     ## ##        ##     ## ##   ##      ##          ##
 ##  ##     ## ##        ##     ## ##    ##     ##    ##    ##
#### ##     ## ##         #######  ##     ##    ##     ######

# System
import os, platform, shutil

# DICOM
import dicom

# Logging
import logging
import logging.config

# PyQt
from PyQt4 import QtCore

 ######  ######## ########  ##     ## ####  ######  ########
##    ## ##       ##     ## ##     ##  ##  ##    ## ##
##       ##       ##     ## ##     ##  ##  ##       ##
 ######  ######   ########  ##     ##  ##  ##       ######
      ## ##       ##   ##    ##   ##   ##  ##       ##
##    ## ##       ##    ##    ## ##    ##  ##    ## ##
 ######  ######## ##     ##    ###    ####  ######  ########

class DicomService:
    """DICOM service
    """

    def __init__(self):
        """Default constructor
        """
        self._logger = logging.getLogger(__name__)
        logging.config.fileConfig('logging.ini', disable_existing_loggers=False)

    def getPatientID(self, filename):
        """Read PatientID from DICOM file
        """
        ds = dicom.read_file(filename, force=True)
        if "PatientID" in ds:
            return ds.PatientID

    def getStudyInstanceUID(self, filename):
        """Read StudyInstanceUID from DICOM file
        """
        ds = dicom.read_file(filename, force=True)
        if "StudyInstanceUID" in ds:
            return ds.StudyInstanceUID

    def getSeriesInstanceUID(self, filename):
        """Read SeriesInstanceUID from DICOM file
        """
        ds = dicom.read_file(filename, force=True)
        if "SeriesInstanceUID" in ds:
            return ds.SeriesInstanceUID

    def getSopInstanceUID(self, filename):
        """Read  SOPInstanceUID from DICOM file
        """
        ds = dicom.read_file(filename, force=True)
        if "SOPInstanceUID" in ds:
            return ds.SOPInstanceUID

    def saveFile(self, directory, data):
        """Save dicom file on the server
        """
        directory = directory + os.sep

        # Read the FINISH flag of data and save to variable finish specify if current file is last file
        if data["FINISH"] == True:
            finish = True
        else:
            finish = False

        # Delete FINISH flag from data so it containts only dcm file
        data.pop("FINISH")

        # Write the data to file (should be just one file with each call)
        try:
            for elem in data:
                self._logger.info("Saving received file: " + directory + os.sep + elem)
                self._logger.info("Is last: " + str(finish))

                f = open(directory + os.sep + elem, 'wb')
                f.write(data[elem])
                f.close()

        except IOError, err:
            self._logger.error(str(err))
            return False

        # The following is the return from the server: allows for error handling, if all is ok, it should be True
        return True

    def importFile(self, source, importDestination):
        """Copy DICOM file to the folder for import into PACS
        """
        result = False
        try:
            shutil.copyfile(source, importDestination)
            result = True
        except IOError, err:
            self._logger.error(str(err))

        return result

    def storescuFile(self, aetitle, call, peer, port, filename, optProposeLossless=True, optRequired=True):
        """C-STORE to Storage Service Class Provider (SCP)
        """
        # Use DICOM offise toolkit convert to fix common errors
        if platform.system() == "Linux":

            # storescu proposes everything it can transfer without looking into the file
            # only uncompressed transfer syntaxes are proposed
            command = "storescu "
            command += "--aetitle " + aetitle+ " "
            command += "--call " + call + " "
            command += peer + " "
            command += str(port) + " "
            command += "\"" + filename + "\""
            
            # force to also propose the JPEG Lossless Transfer Syntax
            if optProposeLossless:
                command += " --propose-lossless"  
            # only proposes those SOP Classes  (presentation contexts) that can be found in the file
            if optRequired:
                command += " --required"

            # -v option for verbose output
            # -d option for debug output

            self._logger.debug("Starting store storescu: " + command)

            process = QtCore.QProcess()
            process.start(command)
            
            # Wait until it is really finished
            process.waitForFinished(-1)
            return True
            