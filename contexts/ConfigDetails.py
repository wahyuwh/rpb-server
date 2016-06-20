#### ##     ## ########   #######  ########  ########  ######Lo
 ##  ###   ### ##     ## ##     ## ##     ##    ##    ##    ##
 ##  #### #### ##     ## ##     ## ##     ##    ##    ##
 ##  ## ### ## ########  ##     ## ########     ##     ######
 ##  ##     ## ##        ##     ## ##   ##      ##          ##
 ##  ##     ## ##        ##     ## ##    ##     ##    ##    ##
#### ##     ## ##         #######  ##     ##    ##     ######

# System
import sys

# Config
from ConfigParser import *

# Singleton
from utils.SingletonType import SingletonType

class ConfigDetails(object):
    """Application configuration details
    """

    __metaclass__ = SingletonType

    def __init__(self):
        """Constructor
        """
        # Configuration file
        self.configFileName = "radplanbio-server.cfg"

        # Static burned in values
        self.name = "RadPlanBio - server web API"
        self.identifier = "RPB-SERVER-WEBAPI"
        self.version = "1.0.0.10"
        self.copyright = "2013-2015 German Cancer Consortium (DKTK)"

        # RPB
        self.rpbEnabled = True
        self.rpbHost = ""
        self.rpbPort = 9000
        self.rpbIncoming = ""
        self.rpbTempDir = "temp"
        self.rpbCorrectedDir = "corrected"
        self.rpbDownloadDir = "downloaded"
        self.rpbUnzipDir = "unzipped"

        # RPB DB
        self.rpbDbEnabled = True
        self.rpbDbUsername = ""
        self.rpbDbPassword = ""
        self.rpbDbName = ""
        self.rpbDbHost = ""
        self.rpbDbPort = 5432

        # OC DB
        self.ocDbEnabled = True
        self.ocDbUsername = ""
        self.ocDbPassword = ""
        self.ocDbName = ""
        self.ocDbHost = ""
        self.ocDbPort = 5432

        # DICOM
        self.dicomCorrect = True

        # PACS
        self.dicomVerifyimport = True
        self.dicomVerifyimportRepeat = 25

        # storescu
        self.storescuEnabled = True
        self.aetitle = ""
        self.call = ""
        self.peer = ""
        self.port = 5678

        # PID
        self.rpbPartnerPrefixSeparator = "-" # Subjects PIDs are prefixed with partner site identificator with prefix separator
       