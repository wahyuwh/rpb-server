class CrfDicomField():

 ######   #######  ##    ##  ######  ######## ########  ##     ##  ######  ########  #######  ########   ######
##    ## ##     ## ###   ## ##    ##    ##    ##     ## ##     ## ##    ##    ##    ##     ## ##     ## ##    ##
##       ##     ## ####  ## ##          ##    ##     ## ##     ## ##          ##    ##     ## ##     ## ##
##       ##     ## ## ## ##  ######     ##    ########  ##     ## ##          ##    ##     ## ########   ######
##       ##     ## ##  ####       ##    ##    ##   ##   ##     ## ##          ##    ##     ## ##   ##         ##
##    ## ##     ## ##   ### ##    ##    ##    ##    ##  ##     ## ##    ##    ##    ##     ## ##    ##  ##    ##
 ######   #######  ##    ##  ######     ##    ##     ##  #######   ######     ##     #######  ##     ##  ######

    def __init__(self, oid, value, annotationType, eventOid, formOid, groupOid):
        """Default constructor
        """
        # Init members
        self._oid = oid
        self._label = ""
        self._description = ""
        self._value = value
        self._annotationType = annotationType
        self._eventOid = eventOid
        self._formOid = formOid
        self._groupOid = groupOid

########  ########   #######  ########  ######## ########  ######## #### ########  ######
##     ## ##     ## ##     ## ##     ## ##       ##     ##    ##     ##  ##       ##    ##
##     ## ##     ## ##     ## ##     ## ##       ##     ##    ##     ##  ##       ##
########  ########  ##     ## ########  ######   ########     ##     ##  ######    ######
##        ##   ##   ##     ## ##        ##       ##   ##      ##     ##  ##             ##
##        ##    ##  ##     ## ##        ##       ##    ##     ##     ##  ##       ##    ##
##        ##     ##  #######  ##        ######## ##     ##    ##    #### ########  ######

    @property
    def oid(self):
        """OID Getter
        """
        return self._oid

    @oid.setter
    def oid(self, oidValue):
        """OID Setter
        """
        if self._oid != oidValue:
            self._oid = oidValue

    @property
    def label(self):
        """Label Getter
        """
        return self._label

    @label.setter
    def label(self, value):
        """Label Setter
        """
        if self._label != value:
            self._label = value
    
    @property
    def value(self):
        """Value Getter
        """
        return self._value

    @value.setter
    def value(self, value):
        """Value Setter
        """
        if self._value != value:
            self._value = value

    @property
    def annotationType(self):
        """Annotation type Getter
        """
        return self._annotationType

    @annotationType.setter
    def annotationType(self, value):
        """Annotation type Setter
        """
        if self._annotationType != annotationType:
            self._annotationType = annotationType

    @property
    def eventOid(self):
        """EventOid Getter
        """
        return self._eventOid

    @eventOid.setter
    def eventOid(self, eventOid):
        """EventOid Setter
        """
        if self._eventOid != eventOid:
            self._eventOid = eventOid

    @property
    def formOid(self):
        """FormOid Getter
        """
        return self._formOid

    @formOid.setter
    def formOid(self, formOid):
        """FormOid Setter
        """
        if self._formOid != formOid:
            self._formOid = formOid

    @property
    def groupOid(self):
        """GroupOid Getter
        """
        return self._groupOid

    @groupOid.setter
    def groupOid(self, groupOid):
        """Group Setter
        """
        if self._groupOid != groupOid:
            self._groupOid = groupOid

