#### ##     ## ########   #######  ########  ########  ######
 ##  ###   ### ##     ## ##     ## ##     ##    ##    ##    ##
 ##  #### #### ##     ## ##     ## ##     ##    ##    ##
 ##  ## ### ## ########  ##     ## ########     ##     ######
 ##  ##     ## ##        ##     ## ##   ##      ##          ##
 ##  ##     ## ##        ##     ## ##    ##     ##    ##    ##
#### ##     ## ##         #######  ##     ##    ##     ######

# HTTP
import requests

# Standard
import os

# Logging
import logging
import logging.config

# Contexts
from contexts.ConfigDetails import ConfigDetails

 ######  ######## ########  ##     ## ####  ######  ########
##    ## ##       ##     ## ##     ##  ##  ##    ## ##
##       ##       ##     ## ##     ##  ##  ##       ##
 ######  ######   ########  ##     ##  ##  ##       ######
      ## ##       ##   ##    ##   ##   ##  ##       ##
##    ## ##       ##    ##    ## ##    ##  ##    ## ##
 ######  ######## ##     ##    ###    ####  ######  ########

class ConquestService:
    """Conquest PACS communication service
    """

    def __init__(self):
        """Default constructor
        """
        self._logger = logging.getLogger(__name__)
        logging.config.fileConfig('logging.ini', disable_existing_loggers=False)

        self._pacsMethodPrefix = "?mode="

##     ## ######## ######## ##     ##  #######  ########   ######
###   ### ##          ##    ##     ## ##     ## ##     ## ##    ##
#### #### ##          ##    ##     ## ##     ## ##     ## ##
## ### ## ######      ##    ######### ##     ## ##     ##  ######
##     ## ##          ##    ##     ## ##     ## ##     ##       ##
##     ## ##          ##    ##     ## ##     ## ##     ## ##    ##
##     ## ########    ##    ##     ##  #######  ########   ######

    def fileExists(self, pacsBaseUrl, patientID, studyInstanceUID, seriesInstanceUID, sopInstanceUID):
        """Verify whether specified unique file exists withing PACS database
        """
        result = False
        method = "rpbfileexists"

        url = pacsBaseUrl + self._pacsMethodPrefix + method
        url += "&PatientID=" + patientID
        url += "&StudyUID=" + studyInstanceUID
        url += "&SeriesUID=" + seriesInstanceUID
        url += "&SopUID=" + sopInstanceUID

        try:
            response = self._httpGetRequest(url)
            if response.status_code == 200:
                filesCount = int(response.json()["FoundFilesCount"])
                if filesCount == 1:
                    result = True
        except Exception as err:
            self._logger.error("Failed to communicate with PACS: " + str(err))

        return result

    def getAllStudies(self, pacsBaseUrl):
        """Get list of all DICOM studies within PACS
        """
        results = None
        method = "radplanbiostudies"

        url = pacsBaseUrl + self._pacsMethodPrefix + method

        try:
            response = self._httpGetRequest(url)
            if response.status_code == 200:
                results = response.json()
                result = True
        except Exception as err:
            self._logger.error("Failed to communicate with PACS: " + str(err))

        return result

    def downloadDicomStudy(self, pacsBaseUrl, patientID, studyInstanceUID, path):
        """Send a http request to Conquest web server in order to invoke download of the study
        """
        results = None
        method = "zipstudy"
        dum = ".zip"

        url = pacsBaseUrl + self._pacsMethodPrefix + method
        url = url + "&study=" + patientID + ":" + studyInstanceUID
        url = url + "&dum=" + dum

        self._logger.info("Downloading from: " + url)

        try:
            localFilename = path + os.sep + patientID + ":" + studyInstanceUID + ".zip"
            try:
                os.remove(localFilename)
            except OSError:
                self._logger.info("Zip not removed because does not exists.")

            # TODO:
            # Randomly generate folder name where to put the zip

            with open(localFilename, "wb") as handle:

                response = self._httpGetRequest(url)

                if response.status_code == 200:
                    self._logger.debug("Zip request OK.")

                    for block in response.iter_content(1024):
                        if not block:
                            break

                        handle.write(block)

                result = localFilename

        except Exception as err:
            self._logger.error("Failed to communicate with PACS: " + str(err))

        return result

    def downloadDicomSerie():
        """Sent a http request to Conquest web server in order to invoke download of the study series
        """
        pass

########  ########  #### ##     ##    ###    ######## ######## 
##     ## ##     ##  ##  ##     ##   ## ##      ##    ##       
##     ## ##     ##  ##  ##     ##  ##   ##     ##    ##       
########  ########   ##  ##     ## ##     ##    ##    ######   
##        ##   ##    ##   ##   ##  #########    ##    ##       
##        ##    ##   ##    ## ##   ##     ##    ##    ##       
##        ##     ## ####    ###    ##     ##    ##    ######## 

    def _httpGetRequest(self, url):
        """HTTP get request to Conquect PACS
        """
        contentLength = 0

        session = requests.Session()
        session.headers.update({ "Content-Type": "application/json",  "Content-Length": contentLength })

        response = session.get(url, verify=False)

        return response