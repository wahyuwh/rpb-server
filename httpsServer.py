#### ##     ## ########   #######  ########  ########  ######
 ##  ###   ### ##     ## ##     ## ##     ##    ##    ##    ##
 ##  #### #### ##     ## ##     ## ##     ##    ##    ##
 ##  ## ### ## ########  ##     ## ########     ##     ######
 ##  ##     ## ##        ##     ## ##   ##      ##          ##
 ##  ##     ## ##        ##     ## ##    ##     ##    ##    ##
#### ##     ## ##         #######  ##     ##    ##     ######

# Standard
import sys, time, os, platform, shutil, socket

# HTTP
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import BaseServer
from SocketServer import ThreadingMixIn

# CGI
import cgi

# JSON
import json

# Logging
import logging
import logging.config

# Regular expressions
import re

from OpenSSL import SSL

# Python serialisation/deserialisation
import cPickle as pickle

# PyQt
from PyQt4 import QtCore

# Zip
import zipfile

# Networking
import requests
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth

# Utils
from utils import first

# Contexts
from contexts.ConfigDetails import ConfigDetails

# Services
from services.DicomService import DicomService
from services.ConquestService import ConquestService
from services.AppConfigurationService import AppConfigurationService
from services.DataPersistanceService import DataPersistanceService

# OC services
from services.OCConnectInfo import OCConnectInfo
from services.OCWebServices import OCWebServices
from services.OCRestfulService import OCRestfulService
from services.OdmFileDataService import OdmFileDataService

# Domain
from services.DataPersistanceService import PartnerSite
from services.DataPersistanceService import PullDataRequest
from services.DataPersistanceService import Software
from domain.CrfDicomField import CrfDicomField

# Serializers
from services.DataPersistanceService import DefaultAccountSerializer
from services.DataPersistanceService import StudySerializer
from services.DataPersistanceService import OCStudySerializer
from services.DataPersistanceService import PartnerSiteSerializer
from services.DataPersistanceService import SoftwareSerializer
from services.DataPersistanceService import CrfFieldAnnotationSerializer
from services.DataPersistanceService import RTStructSerializer
from services.DataPersistanceService import PullDataRequestSerializer

 ######  ######## ########  ##     ## ######## ########
##    ## ##       ##     ## ##     ## ##       ##     ##
##       ##       ##     ## ##     ## ##       ##     ##
 ######  ######   ########  ##     ## ######   ########
      ## ##       ##   ##    ##   ##  ##       ##   ##
##    ## ##       ##    ##    ## ##   ##       ##    ##
 ######  ######## ##     ##    ###    ######## ##     ##

class SecureHTTPServer(HTTPServer):
    """SecureHTTPServer
    """

    def __init__(self, serverAddress, HandlerClass):
        """SecureHttpServer constructor

        serverAddress is touple from ip address and port
        HandlerClass is server request handler
        """
        self.logger = logging.getLogger(__name__)
        logging.config.fileConfig("logging.ini", disable_existing_loggers=False)

        BaseServer.__init__(self, serverAddress, HandlerClass)

        # Location of server.pem's => containing the server private key and the server certificate
        fpem = "server.pem"

        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_privatekey_file(fpem)
        ctx.use_certificate_file(fpem)

        self.socket = SSL.Connection(ctx, socket.socket(self.address_family, self.socket_type))
        self.server_bind()
        self.server_activate()

        self.appConfig = AppConfigurationService()

        if ConfigDetails().rpbEnabled:

            # Server file storrage target
            section = "RadPlanBioServer"
            if self.appConfig.hasOption(section, "server"):
                ConfigDetails().rpbIncoming = self.appConfig.get(section)["server"]
                self.logger.info("RadPlanBio https server: " + ConfigDetails().rpbIncoming)

            # RadPlanBio DB connection
            section = "RadPlanBioDB"
            username = self.appConfig.get(section)["username"]
            password = self.appConfig.get(section)["password"]
            dbname = self.appConfig.get(section)["dbname"]
            host = self.appConfig.get(section)["host"]
            port = self.appConfig.get(section)["port"]
            self.svcDb =  DataPersistanceService(username, password, dbname, host, port)
            self.logger.info("RadPlanBio database: " + dbname + "@" + host + ":" + port)

        # OpenClinica DB connection
        section = "OpenClinicaDB"
        if self.appConfig.hasSection(section):
            if self.appConfig.getboolean(section, "enabled"):
                ocusername = self.appConfig.get(section)["username"]
                ocpassword = self.appConfig.get(section)["password"]
                ocdbname = self.appConfig.get(section)["dbname"]
                ochost = self.appConfig.get(section)["host"]
                ocport = self.appConfig.get(section)["port"]
                self.svcDb.createOcDbConnection(ocusername, ocpassword, ocdbname, ochost, ocport)
                self.logger.info("OpenClinica database: " + ocdbname + "@" + ochost + ":" + ocport)

        # Correction of recieving DICOM data
        section = "DICOM"
        if self.appConfig.hasSection(section):
            if self.appConfig.hasOption(section, "correct"):
                ConfigDetails().dicomCorrect = self.appConfig.getboolean(section, "correct")
                self.logger.info("DICOM data correction enabled.")

        # Connecting to PACS
        section = "PACS"
        if self.appConfig.hasSection(section):
            if self.appConfig.hasOption(section, "verifyimport"):
                ConfigDetails().dicomVerifyimport = self.appConfig.getboolean(section, "verifyimport")
                self.logger.info("PACS file import verification enabled.")

        # Import with DICOM store feature
        section = "storescu"
        if self.appConfig.hasSection(section):
            self.logger.info("storescu (C-STORE) file import enabled.")
            if self.appConfig.hasOption(section, "enabled"):
                ConfigDetails().storescuEnabled = self.appConfig.getboolean(section, "enabled")
            if self.appConfig.hasOption(section, "aetitle"):
                ConfigDetails().aetitle = self.appConfig.get(section)["aetitle"]
            if self.appConfig.hasOption(section, "call"):
                ConfigDetails().call = self.appConfig.get(section)["call"]
            if self.appConfig.hasOption(section, "peer"):
                ConfigDetails().peer = self.appConfig.get(section)["peer"]
            if self.appConfig.hasOption(section, "port"):
                ConfigDetails().port = int(self.appConfig.get(section)["port"])

        # Init services
        self._svcPacs = ConquestService()
        self._svcOcWebServices = None
        self._svcOcRestfulService = None
        self._svcOdmMetaData = OdmFileDataService()

    def shutdown_request(self, request):
        """Server shutdown request
        """
        request.shutdown()

class ThreadingHTTPSServer(ThreadingMixIn, SecureHTTPServer):
    """Threading HTTPSServer

    This class is derived from ThreadingMixIn and SecureHTTPServer
    """
    pass

class SecureHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Main server request handler class
    """

    def setup(self):
        """ Setup the HTTP request handler, every time the request is made

        POST and GET methods
        """
        self.logger = logging.getLogger(__name__)
        logging.config.fileConfig("logging.ini", disable_existing_loggers=False)

        # Configuration
        self.appConfig = AppConfigurationService()

        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

        # Link services from http server
        self.svcDb = self.server.svcDb

        # Connectin to PACS
        if self.appConfig.hasSection("PACS"):
            if self.appConfig.getboolean("PACS", "verifyimport"):
                self._svcPacs = self.server._svcPacs

        self._svcOcWebServices = self.server._svcOcWebServices
        self._svcOcRestfulService = self.server._svcOcRestfulService
        self._svcOdmMetaData = self.server._svcOdmMetaData

        # Working folders
        self._tempDir = "temp"
        self._correctedDir = "corrected"

    # Helper methods

    def getPartnerSiteIdentifier(self, patientPseudonym):
        """Get site identifier from patient pseudonym
        """
        if self.pseudonymIndicatesMulticentreStudy(patientPseudonym):
            index = self.pseudonymSiteIdentificatorIndex(patientPseudonym)
            return patientPseudonym[0:index]            

    def pseudonymIndicatesMulticentreStudy(self, patientPseudonym):
        """Depending on the presense of site identifier in patient pseudonym deduce whether the study is multicentre
        """
        return self.pseudonymSiteIdentificatorIndex(patientPseudonym) != -1

    def pseudonymSiteIdentificatorIndex(self, patientPseudonym):
        """Try to find out site identifier in patient pseudonym
        """
        return patientPseudonym.find(
            ConfigDetails().rpbPartnerPrefixSeparator
        )

########   #######   ######  ########
##     ## ##     ## ##    ##    ##
##     ## ##     ## ##          ##
########  ##     ##  ######     ##
##        ##     ##       ##    ##
##        ##     ## ##    ##    ##
##         #######   ######     ##

    def do_POST(self):
        """Insert the data posted into the server (DICOM, JSON)
        """
        # Authentication data
        username = self.headers.getheader("Username")
        password = self.headers.getheader("Password")
        length = int(self.headers.getheader("content-length"))

        # Query the DB to authenticate the user
        authenticated = False
        session = self.svcDb.Session()
        account = self.svcDb.getDefaultAccountByUsername(session, username)

        # Authentication
        if account is not None:
            # First try portal password
            if account.password == password:
                authenticated = True
            # Than open clinica password
            else:
                self.logger.info("Authentication: trying OC user")
                # OpenClinica
                ocpassword = ""
                if (self.appConfig.get("OpenClinicaDB")["enabled"]):
                    ocsession = self.svcDb.ocSession()
                    ocpassword = self.svcDb.getAccountPasswordHash(ocsession, username)

                if ocpassword != "" and ocpassword == password:
                    authenticated = True

        self.logger.info("POST method: " + self.path)

        if authenticated:

########  ####  ######   #######  ##     ##
##     ##  ##  ##    ## ##     ## ###   ###
##     ##  ##  ##       ##     ## #### ####
##     ##  ##  ##       ##     ## ## ### ##
##     ##  ##  ##       ##     ## ##     ##
##     ##  ##  ##    ## ##     ## ##     ##
########  ####  ######   #######  ##     ##

            if None != re.search("/api/v1/uploadDicomData/", self.path):
                
                # self.rfile contains the body sent from the client
                data = self.rfile.read(length)
                self.logger.info("POST-CHECK:" + str(len(data)) + str(length))

                # if length from data and length from headers do not agree: break
                if len(data) != length:
                    self.logger.error("Received DICOM file data length does not agree.")

                    result = pickle.dumps("datalength")
                    self.send_response(200)
                    self.send_header("Content-Language", "English")
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(len(result)))
                    self.end_headers()
                    self.wfile.write(result)

                    return None

                # Load received data with pickle (as it was saved with pickle on the client)
                data = pickle.loads(data)

                # Extract filename
                dicomFileName = None
                for filename in data:
                    if filename != "FINISH":
                        dicomFileName = filename

                svcDicom = DicomService()
                # Temp save for DICOM correction utility
                resultTempSave = svcDicom.saveFile(self._tempDir, data)

                patientId = svcDicom.getPatientID(self._tempDir + os.sep + dicomFileName)
                studyUid = svcDicom.getStudyInstanceUID(self._tempDir + os.sep + dicomFileName)
                seriesUid = svcDicom.getSeriesInstanceUID(self._tempDir + os.sep + dicomFileName)
                sopUid = svcDicom.getSopInstanceUID(self._tempDir + os.sep + dicomFileName)

                saveSucessfull = False
                result = None
                # Apply DICOM correction before importing to PACS
                if ConfigDetails().dicomCorrect:
                    
                    # Start DICOM correction (RadPlanBio-correct)
                    process = QtCore.QProcess()

                    # Input (from temp) output (to corrected)
                    args = "\"" + self._tempDir + os.sep + dicomFileName + "\" \"" + self._correctedDir  + os.sep + dicomFileName + "\""
                    #self.logger.info("Starting DICOM correction tool (with args): " + args)

                    if platform.system() == "Linux":
                        if os.path.isfile("./correct/RadPlanBio-correct"):
                            process.start("./correct/RadPlanBio-correct " + args)
                        elif os.path.isfile("./correct/mainCorrect.py"):
                            process.start("python ./correct/mainCorrect.py " + args)
                    elif os.path.isfile("./correct/mainCorrect.py"):
                        process.start("python ./correct/mainCorrect.py " + args)

                    # Wait until it is really finished
                    process.waitForFinished(-1)
                    #self.logger.info("DICOM correction tool finished, back to main server.")

                    # DICOM C-STORE
                    if ConfigDetails().storescuEnabled:
                        # Sent to PACS
                        saveSucessfull = svcDicom.storescuFile(ConfigDetails().aetitle, ConfigDetails().call, ConfigDetails().peer, ConfigDetails().port, self._correctedDir  + os.sep + dicomFileName)                        
                        result = pickle.dumps(saveSucessfull)

                    # Copy to PACS import folder
                    else:
                        saveSucessfull = svcDicom.importFile(self._correctedDir  + os.sep + dicomFileName, ConfigDetails().rpbIncoming + os.sep + dicomFileName)
                        #self.logger.info("File copied to PACS import folder (after correct) with result: " + str(resultSave))

                        # Remove the corrected file after import
                        if saveSucessfull:
                            os.remove(self._correctedDir + os.sep + dicomFileName)

                        result = pickle.dumps(saveSucessfull)
                # Direct import to PACS - without correction
                else:
                    # DICOM C-STORE
                    if ConfigDetails().storescuEnabled:
                        saveSucessfull = svcDicom.storescuFile(ConfigDetails().aetitle, ConfigDetails().call, ConfigDetails().peer, ConfigDetails().port, self._tempDir + os.sep + dicomFileName)
                        result = pickle.dumps(saveSucessfull)
                    # Copy to PACS import folder
                    else:
                        saveSucessfull = svcDicom.importFile(self._tempDir + os.sep + dicomFileName, ConfigDetails().rpbIncoming + os.sep + dicomFileName)
                        #self.logger.info("File copied to PACS import folder (directly without correct) with result: " + str(resultSave))
                        result = pickle.dumps(saveSucessfull)

                if saveSucessfull:
                    # Remove the temp file
                    os.remove(self._tempDir + os.sep + dicomFileName)

                    # Verify the existence of file withing PACS
                    if ConfigDetails().dicomVerifyimport:
                        i = 0
                        fileImportSucess = False
                        for i in range(0, ConfigDetails().dicomVerifyimportRepeat):
                            fileImportSucess = self._svcPacs.fileExists(account.partnersite.pacs.pacsbaseurl, patientId, studyUid, seriesUid, sopUid)
                            self.logger.info("[" + str(i) + "] Verify file import into PACS with result: " + str(fileImportSucess))
                            if fileImportSucess: 
                                break

                        if fileImportSucess:
                            # Remove from corrected after sucessfull import
                            if ConfigDetails().dicomCorrect:                                
                                os.remove(self._correctedDir + os.sep + dicomFileName)

                            result = pickle.dumps(fileImportSucess)
                        else:
                            # In case of DICOM C-STORE
                            if ConfigDetails().storescuEnabled:
                                # Sent to PACS with second set of options
                                saveSucessfull = svcDicom.storescuFile(ConfigDetails().aetitle, ConfigDetails().call, ConfigDetails().peer, ConfigDetails().port, self._correctedDir  + os.sep + dicomFileName, False, True)

                                if saveSucessfull:
                                    if ConfigDetails().dicomVerifyimport:
                                        i = 0
                                        fileImportSucess = False
                                        for i in range(0, ConfigDetails().dicomVerifyimportRepeat):
                                            fileImportSucess = self._svcPacs.fileExists(account.partnersite.pacs.pacsbaseurl, patientId, studyUid, seriesUid, sopUid)
                                            self.logger.info("[" + str(i) + "] Verify file import into PACS with result: " + str(fileImportSucess))
                                            if fileImportSucess: 
                                                break

                                        if fileImportSucess:
                                            # Remove from corrected after sucessfull import
                                            if ConfigDetails().dicomCorrect:                                
                                                os.remove(self._correctedDir + os.sep + dicomFileName)

                                            result = pickle.dumps(fileImportSucess)
                                        else:
                                            result = pickle.dumps("PACS")
                                            self.logger.error("DICOM file was not imported.")

                    else:
                        # Remove from corrected if no verification
                        if ConfigDetails().dicomCorrect:
                            os.remove(self._correctedDir + os.sep + dicomFileName)                            

                self.send_response(200)
                self.send_header("Content-Language", "English")
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(result)))
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v1/addPullDataRequest/", self.path):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == "application/json":
                    length = int(self.headers.getheader("content-length"))

                    #data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)

                    dic = json.loads(self.rfile.read(length))
                    serializer = PullDataRequestSerializer()
                    obj = serializer.deserialize(dic)

                    # create pullDataRequest object in DB
                    session = self.svcDb.Session()

                    ourSite = self.svcDb.getPartnerSiteByName(session, obj.sentToSite.sitename)
                    fromSite = self.svcDb.getPartnerSiteByName(session, obj.sentFromSite.sitename)

                    pullDataRequest = PullDataRequest()
                    pullDataRequest.subject = obj.subject
                    pullDataRequest.message = obj.message
                    pullDataRequest.created = obj.created
                    pullDataRequest.senttositeid = ourSite.siteid
                    pullDataRequest.sentfromsiteid = fromSite.siteid

                    session.add(pullDataRequest)
                    session.commit()

                self.send_response(200)
                self.end_headers()
            else:
                self.logger.info("POST - page not found.")
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
        else:
            self.logger.info("POST - not authenticated.")
            self.send_response(403)
            self.send_header("Content-Type", "appilcation/json")
            self.end_headers

        self.svcDb.Session.remove()

        return

 ######   ######## ########
##    ##  ##          ##
##        ##          ##
##   #### ######      ##
##    ##  ##          ##
##    ##  ##          ##
 ######   ########    ##

    def do_GET(self):
        """Query local RadPlanBio DB and report the results in JSON format
        """
        # Authentication data
        username = self.headers.getheader("Username")
        password = self.headers.getheader("Password")
        clearpass = self.headers.getheader("Clearpass")

        # Query the DB to authenticate the user
        authenticated = False
        session = self.svcDb.Session()
        account = self.svcDb.getDefaultAccountByUsername(session, username)

        # Authentication
        if account is not None:
            # First try portal password
            if account.password == password:
                authenticated = True
            # Than open clinica password
            else:
                self.logger.info("Authentication: trying OC user")
                # OpenClinica
                ocpassword = ""
                if (self.appConfig.get("OpenClinicaDB")["enabled"]):
                    ocsession = self.svcDb.ocSession()
                    ocpassword = self.svcDb.getAccountPasswordHash(ocsession, username)

                if ocpassword != "" and ocpassword == password:
                    self.logger.info("Authentication: oc authentication success")
                    authenticated = True

        self.logger.info("GET method: " + self.path)

        if authenticated:
            if None != re.search("/api/v1/authenticateUser/*", self.path):
                serializer = DefaultAccountSerializer()
                dic = serializer.serialize(account)
                result = json.dumps(dic)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v1/getMyDefaultAccount/*", self.path):
                if account is not None:
                    serializer = DefaultAccountSerializer()
                    listOfDics = []
                    dic = serializer.serialize(account)
                    result = json.dumps(dic)

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(result)

 ######  ######## ##     ## ########  ##    ##
##    ##    ##    ##     ## ##     ##  ##  ##
##          ##    ##     ## ##     ##   ####
 ######     ##    ##     ## ##     ##    ##
      ##    ##    ##     ## ##     ##    ##
##    ##    ##    ##     ## ##     ##    ##
 ######     ##     #######  ########     ##

            elif None != re.search("/api/v1/getStudyByOcIdentifier/*", self.path):
                ocIdentifier = self.path.split("/")[-1]
                decodedIdentifier = ocIdentifier.decode("utf-8")

                session = self.svcDb.Session()
                study = self.svcDb.getStudyByOcIdentifier(session, decodedIdentifier)

                if study is not None:
                    serializer = StudySerializer()
                    listOfDics = []
                    dic = serializer.serialize(study)
                    result = json.dumps(dic)

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(result)

########  ########  ######  ######## ########  ##     ##  ######  ########
##     ##    ##    ##    ##    ##    ##     ## ##     ## ##    ##    ##
##     ##    ##    ##          ##    ##     ## ##     ## ##          ##
########     ##     ######     ##    ########  ##     ## ##          ##
##   ##      ##          ##    ##    ##   ##   ##     ## ##          ##
##    ##     ##    ##    ##    ##    ##    ##  ##     ## ##    ##    ##
##     ##    ##     ######     ##    ##     ##  #######   ######     ##

            elif None != re.search("/api/v1/getAllRTStructs/*", self.path):
                session = self.svcDb.Session()
                structs = self.svcDb.getAllRTStructs(session)

                serializer = RTStructSerializer()
                listOfDics = []

                for rtstruct in structs:
                    dic = serializer.serialize(rtstruct)
                    listOfDics.append(dic)

                result = json.dumps(listOfDics)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)

 ######  ########  ########       ###    ##    ## ##    ##  #######  ########    ###    ######## ####  #######  ##    ##  ######
##    ## ##     ## ##            ## ##   ###   ## ###   ## ##     ##    ##      ## ##      ##     ##  ##     ## ###   ## ##    ##
##       ##     ## ##           ##   ##  ####  ## ####  ## ##     ##    ##     ##   ##     ##     ##  ##     ## ####  ## ##
##       ########  ######      ##     ## ## ## ## ## ## ## ##     ##    ##    ##     ##    ##     ##  ##     ## ## ## ##  ######
##       ##   ##   ##          ######### ##  #### ##  #### ##     ##    ##    #########    ##     ##  ##     ## ##  ####       ##
##    ## ##    ##  ##          ##     ## ##   ### ##   ### ##     ##    ##    ##     ##    ##     ##  ##     ## ##   ### ##    ##
 ######  ##     ## ##          ##     ## ##    ## ##    ##  #######     ##    ##     ##    ##    ####  #######  ##    ##  ######

            elif None != re.search("/api/v1/getCrfFieldsAnnotationForStudy/*", self.path):
                studyid = self.path.split("/")[-1]
                session = self.svcDb.Session()
                annotations = self.svcDb.getCrfFieldAnnotationsForStudy(session, studyid)

                serializer = CrfFieldAnnotationSerializer()
                listOfDics = []

                for a in annotations:
                    dic = serializer.serialize(a)
                    listOfDics.append(dic)

                result = json.dumps(listOfDics)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v1/getDicomStudyCrfAnnotationsForStudy/*", self.path):
                studyid = self.path.split("/")[-1]
                session = self.svcDb.Session()
                annotations = self.svcDb.getDicomStudyCrfAnnotationsForStudy(session, studyid)

                serializer = CrfFieldAnnotationSerializer()
                listOfDics = []

                for a in annotations:
                    dic = serializer.serialize(a)
                    listOfDics.append(dic)

                result = json.dumps(listOfDics)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v1/getDicomPatientCrfAnnotationsForStudy/*", self.path):
                studyid = self.path.split("/")[-1]
                session = self.svcDb.Session()
                annotations = self.svcDb.getDicomPatientCrfAnnotationsForStudy(session, studyid)

                serializer = CrfFieldAnnotationSerializer()
                listOfDics = []

                for a in annotations:
                    dic = serializer.serialize(a)
                    listOfDics.append(dic)

                result = json.dumps(listOfDics)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v1/getDicomReportCrfAnnotationsForStudy/*", self.path):
                studyid = self.path.split("/")[-1]
                session = self.svcDb.Session()
                annotations = self.svcDb.getDicomReportCrfAnnotationsForStudy(session, studyid)

                serializer = CrfFieldAnnotationSerializer()
                listOfDics = []

                for a in annotations:
                    dic = serializer.serialize(a)
                    listOfDics.append(dic)

                result = json.dumps(listOfDics)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)
                
########     ###    ########  ######## ##    ## ######## ########      ######  #### ######## ########
##     ##   ## ##   ##     ##    ##    ###   ## ##       ##     ##    ##    ##  ##     ##    ##
##     ##  ##   ##  ##     ##    ##    ####  ## ##       ##     ##    ##        ##     ##    ##
########  ##     ## ########     ##    ## ## ## ######   ########      ######   ##     ##    ######
##        ######### ##   ##      ##    ##  #### ##       ##   ##            ##  ##     ##    ##
##        ##     ## ##    ##     ##    ##   ### ##       ##    ##     ##    ##  ##     ##    ##
##        ##     ## ##     ##    ##    ##    ## ######## ##     ##     ######  ####    ##    ########
    
            elif None != re.search("/api/v1/getAllPartnerSites/*", self.path):
                session = self.svcDb.Session()
                sites = self.svcDb.getAllPartnerSites(session)

                serializer = PartnerSiteSerializer()
                listOfDics = []

                for site in sites:
                    dic = serializer.serialize(site)
                    listOfDics.append(dic)

                result = json.dumps(listOfDics)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v1/getAllPartnerExceptName/*", self.path):
                exceptSiteName = self.path.split("/")[-1]
                session = self.svcDb.Session()
                sites = self.svcDb.getAllPartnerExceptName(session, exceptSiteName)

                listOfDics = []
                for site in sites:
                    serializer = PartnerSiteSerializer()
                    dic = serializer.serialize(site)
                    listOfDics.append(dic)

                results = json.dumps(listOfDics)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(results)
            elif None != re.search("/api/v1/getPartnerSiteByName/*", self.path):
                siteName = self.path.split("/")[-1]

                session = self.svcDb.Session()
                site = self.svcDb.getPartnerSiteByName(session, siteName)

                if site is not None:
                    serializer = PartnerSiteSerializer()
                    dic = serializer.serialize(site)
                    result = json.dumps(dic)

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(result)
            # Deprecated
            elif None != re.search("/api/v1/getMySite/*", self.path):
                session = self.svcDb.Session()
                site = self.svcDb.getMySite(session)
                if site is not None:
                    serializer = PartnerSiteSerializer()
                    dic = serializer.serialize(site)
                    result = json.dumps(dic)

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(result)
                else:
                    self.send_response(400, 'Bad Request: record does not exist')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
      
 ######   #######  ######## ######## ##      ##    ###    ########  ######## 
##    ## ##     ## ##          ##    ##  ##  ##   ## ##   ##     ## ##       
##       ##     ## ##          ##    ##  ##  ##  ##   ##  ##     ## ##       
 ######  ##     ## ######      ##    ##  ##  ## ##     ## ########  ######   
      ## ##     ## ##          ##    ##  ##  ## ######### ##   ##   ##       
##    ## ##     ## ##          ##    ##  ##  ## ##     ## ##    ##  ##       
 ######   #######  ##          ##     ###  ###  ##     ## ##     ## ########

            elif None != re.search("/api/v1/getLatestSoftware/*", self.path):
                name = self.path.split("/")[-1]

                session = self.svcDb.Session()
                software = self.svcDb.getLatestSoftwareByName(session, name)

                if software is not None:
                    serializer = SoftwareSerializer()
                    dic = serializer.serialize(software)
                    result = json.dumps(dic)

                    self.send_response(200)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(result)

########     ###     ######   ######  
##     ##   ## ##   ##    ## ##    ## 
##     ##  ##   ##  ##       ##       
########  ##     ## ##        ######  
##        ######### ##             ## 
##        ##     ## ##    ## ##    ## 
##        ##     ##  ######   ######  
            
            elif None != re.search("/api/v1/getAllDicomStudies/*", self.path):
                baseUrl = account.partnersite.pacs.pacsbaseurl
                endpoint = "?mode=radplanbiostudies"

                s = requests.Session()
                s.headers.update({ "Accept": "application/json"})

                r = s.get(baseUrl + endpoint)

                resultCode = r.status_code

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(r.json())
            elif None != re.search("/api/v1/getDicomStudiesByPatientId/*", self.path):
                patientId = self.path.split("/")[-1]

                baseUrl = account.partnersite.pacs.pacsbaseurl
                endpoint = "?mode=radplanbiostudies" + "patientidmatch=" + patientId

                s = requests.Session()
                s.headers.update({ 'Accept': 'application/json'})

                r = s.get(baseUrl + endpoint)

                resultCode = r.status_code

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(r.json())
            
            elif None != re.search(".*/api/v1/patients/.*/dicomStudies/.*/dcm/.*", self.path):
                dicomPatientId = self.path.split("/")[-5]
                dicomStudyInstaceUid = self.path.split("/")[-3]
                filename = self.path.split("/") [-1]

                fileToRead = ConfigDetails().rpbUnzipDir + os.sep + username + os.sep + dicomPatientId + os.sep + dicomStudyInstaceUid + os.sep + filename
                if os.path.isfile(fileToRead): 
                    f = open(fileToRead, "rb")
                    self.send_response(200)
                    self.send_header("Content-Language", "English")
                    self.send_header("Content-Type", "application/octet-stream")
                    self.end_headers()
                    self.wfile.write(f.read())
            elif None != re.search(".*/api/v1/patients/.*/dicomStudies/.*/clean", self.path):
                dicomPatientId = self.path.split("/")[-4]
                dicomStudyInstaceUid = self.path.split("/")[-2]
                
                shutil.rmtree("./" + ConfigDetails().rpbUnzipDir + os.sep + username + os.sep + dicomPatientId + os.sep + dicomStudyInstaceUid)

                result = '{ "result":' + str(True).lower()  + ' }'

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search(".*/api/v1/patients/.*/dicomStudies/.*/unzip", self.path):
                dicomPatientId = self.path.split("/")[-4]
                dicomStudyInstaceUid = self.path.split("/")[-2]
               
                # Asking for DICOM data in this RPB instance however in which PACS
                if self.pseudonymIndicatesMulticentreStudy(dicomPatientId):
                    identifier = self.getPartnerSiteIdentifier(dicomPatientId)
                    session = self.svcDb.Session()
                    site = self.svcDb.getPartnerSiteByIdentifier(
                        session, 
                        identifier
                    )
                else:
                    site = account.partnersite 
                    
                baseUrl = site.pacs.pacsbaseurl

                # TODO: add session ID to the path (to fix the case when the user is logged in multiple times and downloading the same study)
                downloadPath = ConfigDetails().rpbDownloadDir + os.sep + username

                if os.path.isdir(downloadPath) == False:
                    os.mkdir(downloadPath)
                
                zippedDataPath = self._svcPacs.downloadDicomStudy(baseUrl, dicomPatientId, dicomStudyInstaceUid, downloadPath)

                # Folder structure for unzipped files
                zfile = zipfile.ZipFile(zippedDataPath)
                unzippedDataPath = "./" + ConfigDetails().rpbUnzipDir + os.sep + username

                if os.path.isdir(unzippedDataPath) == False:
                    os.mkdir(unzippedDataPath)

                unzippedDataPath = unzippedDataPath + os.sep + dicomPatientId 

                if os.path.isdir(unzippedDataPath) == False:
                    os.mkdir(unzippedDataPath)

                unzippedDataPath = unzippedDataPath + os.sep + dicomStudyInstaceUid

                if os.path.isdir(unzippedDataPath) == False:
                    os.mkdir(unzippedDataPath)
                
                zfile.extractall(unzippedDataPath)

                os.remove(zippedDataPath)

                f = []
                for (dirpath, dirnames, filenames) in os.walk(unzippedDataPath):
                    f.extend(filenames)
                    break

                stringJson = '{ "Patients": [ '
                stringJson = stringJson + '{ '
                stringJson = stringJson + '"UniqueIdentifier": "' + dicomPatientId + '", '
                stringJson = stringJson + '"Studies": [ '
                stringJson = stringJson + '{ '
                stringJson = stringJson + '"StudyInstanceUid": "' + dicomStudyInstaceUid + '", '
                stringJson = stringJson + '"Files": [ '
                i = 0
                for filename in f:
                    if i == 0:
                        stringJson = stringJson + '{ '
                    else:
                        stringJson = stringJson + ', { '
                    
                    # subject serverie public URL for request routing)
                    # e.g. https://radplanbio.uniklinikum-dresden.de/serverieDD/api/v1....
                    baseUrl = site.serverie.publicurl

                    stringJson = stringJson + '"WebApiUrl" : "' + baseUrl + '/api/v1/patients/' + dicomPatientId + '/dicomStudies/' + dicomStudyInstaceUid + '/dcm/' + filename + '"' 
                    #stringJson = stringJson + '"WebApiUrl" : "' + "localhost:9000" + '/api/v1/patients/' + dicomPatientId + '/dicomStudies/' + dicomStudyInstaceUid + '/dcm/' + filename + '"'
                    stringJson = stringJson + ' }'

                    i = i + 1

                # Closing structure                    
                stringJson = stringJson + '] } ] } ] }'

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(stringJson)
            elif None != re.search(".*/api/v1/studies/.*/dicomStudies", self.path):
                
                # For multiple studies I need multiple identifiers
                studyIdentifier = self.path.split("/")[-2]

                # Read partner site of logged user
                baseUrl = account.partnersite.edc.soapbaseurl

                session = self.svcDb.ocSession()
                passwordHash = self.svcDb.getAccountPasswordHash(session, account.ocusername)

                # Create connection artifact to users main OpenClinica SOAP
                ocConnectInfo = OCConnectInfo(baseUrl, account.ocusername, passwordHash)
                self._svcOcWebServices = OCWebServices(ocConnectInfo)

                # Is it parent study or study site
                selectedStudy = None
                selectedSite = None
                success, studies = self._svcOcWebServices.listAllStudies()

                if success:
                    self.logger.debug("SOAP studies size: " + str(len(studies)))
                    selectedStudy = first.first(study for study in studies if study.identifier().encode("utf-8") == studyIdentifier)                    

                # Site was selected
                if selectedStudy is None:
                    for s in studies:
                        if s.sites:
                            for site in s.sites:
                                if site.identifier == studyIdentifier:
                                    selectedSite = site
                                    selectedStudy = s
                                    break

                # Load study metadata
                sucess, studyMetadata = self._svcOcWebServices.getStudyMetadata(selectedStudy)

                # RPB study entity
                session = self.svcDb.Session()
                study = self.svcDb.getStudyByOcIdentifier(session, selectedStudy.identifier())

                # Load subject for whole study or only site if it is multicentre study
                # oid is study OID (monocentre study) or site study OID (multi-centre study)
                subjects = None
                isMultiCentre = False
                if selectedSite is not None:
                    oid = selectedSite.oid
                    subjects = self._svcOcWebServices.listAllStudySubjectsByStudySite([selectedStudy, selectedSite, studyMetadata])
                    isMultiCentre = True
                elif selectedStudy is not None:
                    oid = selectedStudy.oid()
                    subjects = self._svcOcWebServices.listAllStudySubjectsByStudy([selectedStudy, studyMetadata])
                    isMultiCentre = False

                self.logger.debug("SOAP subjects count: " + str(len(subjects)))

                self._svcOcRestfulService = OCRestfulService(account.ocusername, clearpass)
                
                # Subjects has to be enhanced with values from REST services
                subjectsREST = self._svcOcRestfulService.getStudyCasebookSubjects([account.partnersite.edc.edcbaseurl, oid])
                self.logger.debug("REST subjects count: " + str(len(subjectsREST)))

                # Synchronise subjects
                for ss in subjects:
                    for sREST in subjectsREST:
                        if sREST.studySubjectId == ss.label():
                            ss.oid = sREST.oid

                # Load DICOM annotation for that study
                session = self.svcDb.Session()
                dicomAnnotations = self.svcDb.getDicomStudyCrfAnnotationsForStudy(session, study.id)
                           
                stringJson = '{ "Patients": [ '
                i = 0
                for subject in subjects:

                    # Events values has to be enhanced with values from REST services
                    eventsREST = self._svcOcRestfulService.getStudyCasebookEvents([account.partnersite.edc.edcbaseurl, oid, subject.oid])
                    self.logger.debug("REST events count: " + str(len(eventsREST)))

                    # Syncrhonise events
                    for event in subject.events:
                        for e in eventsREST:
                            if e.eventDefinitionOID == event.eventDefinitionOID and e.startDate.isoformat() == event.startDate.isoformat():
                                event.status = e.status
                                event.studyEventRepeatKey = e.studyEventRepeatKey
                                event.setForms(e.forms)
                    
                    try:
                        # Starting new patient
                        if i == 0:
                            stringJson = stringJson + '{ '
                        else:
                            stringJson = stringJson + ', { '
                       
                        # Load site accoring site identifier in subject pseudonym
                        if isMultiCentre:
                            identifier = self.getPartnerSiteIdentifier(
                                subject.subject.uniqueIdentifier
                            )
                            session = self.svcDb.Session()
                            site = self.svcDb.getPartnerSiteByIdentifier(
                                session, 
                                identifier
                            )
                        else:
                            site = account.partnersite

                        stringJson = stringJson + '"SubjectKey": "' + subject.oid + '", '
                        stringJson = stringJson + '"StudySubjectID": "' + subject.label() + '", '
                        stringJson = stringJson + '"UniqueIdentifier": "' + subject.subject.uniqueIdentifier + '", '
                        stringJson = stringJson + '"Studies": [ '
                        
                        for event in subject.events:
                            j = 0
                            for crfAnnotation in dicomAnnotations:
                                if crfAnnotation.eventdefinitionoid == event.eventDefinitionOID:
                                    if event.hasScheduledCrf(crfAnnotation.formoid):

                                        # Load study instace uids data
                                        session = self.svcDb.ocSession()
                                        value = self.svcDb.getCrfItemValueV2(
                                            session, 
                                            oid, 
                                            subject.subject.uniqueIdentifier, 
                                            event.eventDefinitionOID, 
                                            event.studyEventRepeatKey, 
                                            crfAnnotation.formoid, 
                                            crfAnnotation.crfitemoid
                                        )

                                        # Only when there is actually some data
                                        if value is not None and value is not "":
                                            self.logger.debug("DICOM StudyInstanceUID according to eCRF annotation: " + str(value))
                                            field = CrfDicomField(
                                                crfAnnotation.crfitemoid,
                                                value,
                                                crfAnnotation.annotationtype.name,
                                                crfAnnotation.eventdefinitionoid,
                                                crfAnnotation.formoid,
                                                crfAnnotation.groupoid
                                            )

                                            # Load label from metadata
                                            itemMeta = self._svcOdmMetaData.loadCrfItem(crfAnnotation.formoid, crfAnnotation.crfitemoid, studyMetadata)
                                            if itemMeta is not None:
                                                self.logger.debug("DICOM StudyInstanceUID eCRF label: " + itemMeta.label)
                                                field.label = itemMeta.label

                                            
                                            # Starting new DICOM study
                                            if j == 0:
                                                stringJson = stringJson + '{ '
                                            else:
                                                stringJson = stringJson + ', { '

                                            stringJson = stringJson + '"StudyInstanceUid": "' + value + '"'
                                            stringJson = stringJson + ', "StudyEventOid": "' + field.eventOid + '"'
                                            stringJson = stringJson + ', "ItemOid": "' + field.oid + '"'
                                            stringJson = stringJson + ', "Label": "' + field.label + '"'
                                            
                                            # subject serverie public URL + application (for request routing)
                                            # e.g. https://radplanbio.uniklinikum-dresden.de/serverieDD/
                                            stringJson = stringJson + ', "WebApiUrl" : "' + site.serverie.publicurl + '/api/v1/patients/' + subject.subject.uniqueIdentifier + '/dicomStudies/' + value + '"' 

                                            stringJson = stringJson + '}'
                                            j = j + 1

                                            self.logger.debug(stringJson)
                                        else:
                                             self.logger.debug("No UID imported into eCRF.")
                    except Exception, err:
                        self.logger.error(str(err))

                    # End studies array, end patient
                    stringJson = stringJson + '] }'
                    i = i + 1

                # End patients array, end json root
                stringJson = stringJson + '] }'

                self.logger.debug(stringJson)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(stringJson)  

 #######   ######  
##     ## ##    ## 
##     ## ##       
##     ## ##       
##     ## ##       
##     ## ##    ## 
 #######   ######  

            elif None != re.search("/api/v1/getCrfItemValue/*", self.path):
                command = self.path.split("/")
                #/api/v1/getCrfItemValue/studyid/subjectPid/studyEventOid/formOid/itemOid

                studySiteOid = command[-5]
                subjectPid = command[-4]
                studyEventOid = command[-3]
                formOid = command[-2]
                itemOid = command[-1]

                session = self.svcDb.ocSession()
                value = self.svcDb.getCrfItemValueV1(session, studySiteOid, subjectPid, studyEventOid, formOid, itemOid)

                dic = { "itemOid" : itemOid, "itemValue" : value }
                result = json.dumps(dic)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(result)))
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v2/getCrfItemValue/*", self.path):
                command = self.path.split("/")
                #/api/v2/getCrfItemValue/studyid/subjectPid/studyEventOid/studyEventRepeatKey/formOid/itemOid

                studySiteOid = command[-6]
                subjectPid = command[-5]
                studyEventOid = command[-4]
                studyEventRepeatKey = command[-3]
                formOid = command[-2]
                itemOid = command[-1]

                session = self.svcDb.ocSession()
                value = self.svcDb.getCrfItemValueV2(session, studySiteOid, subjectPid, studyEventOid, studyEventRepeatKey, formOid, itemOid)

                dic = { "itemOid" : itemOid, "itemValue" : value }
                result = json.dumps(dic)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(result)))
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v1/getOCAccoutPasswordHash/*", self.path):
                session = self.svcDb.ocSession()
                passwordHash = self.svcDb.getAccountPasswordHash(session, account.ocusername)

                dic = { "ocPasswordHash" : passwordHash }
                result = json.dumps(dic)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(result)
            elif None != re.search("/api/v1/getOCStudyByIdentifier/*", self.path):
                ocStudyIdentifer = ocUsername = self.path.split("/")[-1]

                session = self.svcDb.ocSession()
                study = self.svcDb.getOCStudyByIdentifier(session, ocStudyIdentifer)

                if study is not None:
                    serializer = OCStudySerializer()
                    dic = serializer.serialize(study)
                    result = json.dumps(dic)

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(result)   
            elif None != re.search("/api/v1/getUserActiveStudy/*", self.path):
                ocUsername = self.path.split("/")[-1]

                session = self.svcDb.ocSession()
                study = self.svcDb.getUserActiveStudy(session, ocUsername)

                if study is not None:
                    serializer = OCStudySerializer()
                    dic = serializer.serialize(study)
                    result = json.dumps(dic)

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(result)
            elif None != re.search("/api/v1/changeUserActiveStudy/*", self.path):
                newActiveStudyId = self.path.split("/")[-1]  
                ocUsername = self.path.split("/")[-2]   

                session = self.svcDb.ocSession()
                updateResult = self.svcDb.changeUserActiveStudy(session, ocUsername, int(newActiveStudyId))

                result = '{ "result":' + str(updateResult).lower()  + ' }'

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(result)
            else:
                self.logger.info("GET - page not found.")
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
        else:
            self.logger.info("GET - not authenticated.")
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers

        self.svcDb.Session.remove()

        return

 ######  ########    ###    ########  ########
##    ##    ##      ## ##   ##     ##    ##
##          ##     ##   ##  ##     ##    ##
 ######     ##    ##     ## ########     ##
      ##    ##    ######### ##   ##      ##
##    ##    ##    ##     ## ##    ##     ##
 ######     ##    ##     ## ##     ##    ##

def startServer(HandlerClass = SecureHTTPRequestHandler, ServerClass = ThreadingHTTPSServer):
    """startServer function

    SecureHTTPRequestHander - main sever request handler logic
    ThreadingHTTPSServer - server class
    """
    logger = logging.getLogger(__name__)
    logging.config.fileConfig("logging.ini", disable_existing_loggers=False)

    # Server info  
    logger.info(ConfigDetails().name)
    logger.info(ConfigDetails().identifier)
    logger.info(ConfigDetails().version)
    logger.info(ConfigDetails().copyright)

    appConfig = AppConfigurationService(ConfigDetails().configFileName)
    
    section = "RadPlanBioServer"
    if appConfig.hasSection(section):
        if appConfig.hasOption(section, "enabled"):
            ConfigDetails().rpbEnabled = appConfig.getboolean(section, "enabled")
            if ConfigDetails().rpbEnabled:
                if appConfig.hasOption(section, "host"):
                    ConfigDetails().rpbHost = appConfig.get(section)["host"]
                if appConfig.hasOption(section, "port"):
                    ConfigDetails().rpbPort = int(appConfig.get(section)["port"])

                # Server address as touple ip address, port
                serverAddress = (ConfigDetails().rpbHost, ConfigDetails().rpbPort)
                httpd = ServerClass(serverAddress, HandlerClass)

                # Get socket info
                sa = httpd.socket.getsockname()
                
                # Init info               
                logger.info("Server serving HTTPS on " + sa[0] + " port " + str(sa[1]) + " ...")

                # Run infinite server body loop
                httpd.serve_forever()

def main():
    """Main function
    """
    currentExitCode = startServer()

##     ##    ###    #### ##    ##
###   ###   ## ##    ##  ###   ##
#### ####  ##   ##   ##  ####  ##
## ### ## ##     ##  ##  ## ## ##
##     ## #########  ##  ##  ####
##     ## ##     ##  ##  ##   ###
##     ## ##     ## #### ##    ##

# Main funtion
if __name__ == '__main__':
    main()