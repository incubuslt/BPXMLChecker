import json
import re
from bs4 import BeautifulSoup

class XMLChecker(object):

    data = {}
    data['Errors'] = []
    data['Objects'] = []
    data['Process'] =[]
    dataObj = data['Objects']
    dataErr = data['Errors']
    dataPro = data['Process']

    def __init__(self, strFilePath_or_XMLString):
        self.strFilePath_or_XMLString = strFilePath_or_XMLString
        if strFilePath_or_XMLString[-4:] == ".xml":
            with open(self.strFilePath_or_XMLString) as fp:
                self.soup = BeautifulSoup(fp, 'lxml')
        else:
            self.soup = BeautifulSoup(strFilePath_or_XMLString, 'lxml')

        self.nodeProcess = self.soup.select("process")[0]
        self.processName = self.nodeProcess.get("name")
        procesDescription = self.nodeProcess.get("narrative")
        procesPublished = self.nodeProcess.get("published")
        procesBPversion = self.nodeProcess.get("bpversion")
        y = {"processName" : self.processName, "procesDescription" : procesDescription, "procesPublished" : procesPublished, "procesBPversion" : procesBPversion}
        self.dataPro.append(y)

    def checkMails(self):
        errorMails = self.soup.find_all(attrs={"expr": re.compile(r"[^@]+@[^@]+\.[^@]+") }) #regex validates mail format.
        for i in errorMails:
            nodeActionName = i.find_parent("stage").get("name")
            nodeActionPage = self.getNodePage(i).get("name")
            nodeExpretion = i.get("expr")
            y = {"errType" : "Mail", "risk" : "0", "nodeActionName" : nodeActionName, "nodeActionPage" : nodeActionPage, "nodeExpretion" : nodeExpretion}
            self.dataErr.append(y)

        errorMails = self.soup.find_all(attrs={"expression": re.compile(r"[^@]+@[^@]+\.[^@]+") })
        for i in errorMails:
            nodeActionName = i.find_parent("stage").get("name")
            nodeActionPage = self.getNodePage(i).get("name")
            nodeExpretion = i.get("expression")
            y = {"errType" : "Mail", "risk" : "0", "nodeActionName" : nodeActionName, "nodeActionPage" : nodeActionPage, "nodeExpretion" : nodeExpretion}
            self.dataErr.append(y)

    def getObjects(self):
        usedObjects = []
        for i in self.soup.select("resource"):
            usedObjects.append(i.get('object')) 
        usedObjects = list(dict.fromkeys(usedObjects))
        for i in usedObjects:
            y = {"name" : i}
            self.dataObj.append(y)

    def checkMandate(self):
        errorMandatory = self.soup.select("input[narrative*='mandatory' i][expr='' i]")
        for i in errorMandatory:
            nodeName = i.get('name')
            nodeAction = i.parent.parent
            nodeActionName = nodeAction.get("name")
            nodePage = nodeAction.find_previous_sibling("stage")
            while nodePage.get("type")!="SubSheetInfo":
                nodePage=nodePage.find_previous_sibling("stage")
            nodePageName = nodePage.get("name")
            y = {"errType" : "Mandatory Fields", "nodeName" : nodeName, "actionName" : nodeActionName, "pageNAme" : nodePageName}
            self.dataErr.append(y)

    def checkDescription(self):
        errorDescriptions = self.soup.select("stage[type='SubSheetInfo'] narrative")
        for i in errorDescriptions:
            if i.getText() == "":
                y = {"errType" : "Description", "risk" : "0", "status" : i.parent.get("name")}
                self.dataErr.append(y)

    def chackStopDecition(self):
        blStatus = "False" if len(self.soup.select("decision[expression*='IsStopRequested()']")) == 0 else "True"
        y = {"errType" : "StopRequest", "risk" : "1", "status" : blStatus}
        self.dataErr.append(y)

    def checkCredentials(self):
        Credentials = self.soup.select("input[expr='\""+self.processName+"\"'][name='Credentials Name']")
        blStatus = "False" if len(Credentials) == 0 else "True"
        y = {"errType" : "Credentials", "risk" : "2", "status" : blStatus}
        self.dataErr.append(y)

    def checkWorkQueue(self):
        WorkQueue = self.soup.select("input[expr='\""+self.processName+"\"'][name='Queue Name']")
        blStatus = "False" if len(WorkQueue) == 0 else "True"
        y = {"errType" : "Work Queue", "risk" : "2", "status" : blStatus}
        self.dataErr.append(y)

    def cheackExceptions(self):
        errorException = self.soup.select("exception:not([type='System Exception']):not([type='Business Exception'])")
        for i in errorException:
            nodeName = i.get('type')
            nodeAction = i.parent
            nodeActionName = nodeAction.get("name")
            nodePage = nodeAction.find_previous_sibling("stage")
            while nodePage.get("type")!="SubSheetInfo":
                nodePage=nodePage.find_previous_sibling("stage")
            nodePageName = nodePage.get("name")
            y = {"errType" : "Exception", "risk" : "0", "nodePageName" : nodePageName, "nodeAction" : nodeActionName, "nodeName" : nodeName, "status" : i.get("type")}
            self.dataErr.append(y)

    def checkStartEndStages(self, checkType):
        validList = ["Start", "End"]
        if not any(checkType in s for s in validList): 
            return

        thisCheckType = {}
        thisCheckType["Start"] = "input"
        thisCheckType["End"] = "output"

        usedCheck = thisCheckType[checkType]

        errorStarts = self.soup.select("stage[name='"+checkType+"'] > "+usedCheck+"s > "+usedCheck+"[narrative='']")
        for i in errorStarts:
            inputName = i.get("name")
            inputStore = i.get("stage")
            inputNarrative = i.get("narrative")
            nodePage = i.parent.parent
            nodePageName = self.getNodePage(nodePage).get("name")
            y = {"errType" : checkType + " Stage", "risk" : "0", "nodePageName" : nodePageName, "inputName" : inputName, "inputStore" : inputStore, "inputNarrative" : inputNarrative}
            self.dataErr.append(y)

    def checkPaths(self):
        errorDataItems = self.soup.find_all("initialvalue", text=re.compile(r"danskenet.net\\public\\div|i:\\div", re.IGNORECASE))
        for i in errorDataItems:
            dataItemValue = i.text
            dataItemName = i.parent.get("name")
            dataItemPageName = self.getNodePage(i).get("name")
            y = {"errType" : "Path", "risk" : "1", "dataItemName" : dataItemName, "dataItemValue" : dataItemValue, "dataItemPageName" : dataItemPageName}
            self.dataErr.append(y)

        errorCalculations = self.soup.select("calculation[expression*='i:\\\\div' i],calculation[expression*='danskenet.net\\\\public\\\\div' i]")
        for i in errorCalculations:
            calcExpression = i.get("expression")
            calcName = i.parent.get("name")
            calcPageName = self.getNodePage(i).get("name")
            y = {"errType" : "Path", "risk" : "1", "calcName" : calcName, "calcExpression" : calcExpression, "calcPageName" : calcPageName}
            self.dataErr.append(y)

        errorInputs = self.soup.select("input[expr*='i:\\\\div' i],input[expr*='danskenet.net\\\\public\\\\div' i]")
        for i in errorInputs:
            inputExpr = i.get("expr")
            inputName = i.get("name")
            inputActionName = i.parent.parent.get("name")
            inputPageName = self.getNodePage(i).get("name")
            y = {"errType" : "Path", "risk" : "1", "inputName" : inputName, "inputExpr" : inputExpr, "inputActionName" : inputActionName, "inputPageName" : inputPageName}
            self.dataErr.append(y)

    def addToJSON(self):
        print(json.dumps(self.data, indent=4, sort_keys=True))

    def getNodePage(self, nodePage):
        while nodePage.name!="stage":
            nodePage = nodePage.parent

        nodePage = nodePage.find_previous_sibling("stage", attrs={"type" : "SubSheetInfo"})
        if nodePage is None: 
                nodePage = self.nodeProcess
                return nodePage

        return nodePage
            
    def checkAll(self):
        self.checkMails()
        self.checkPaths()
        self.checkStartEndStages("Start")
        self.checkStartEndStages("End")
        #self.getObjects()
        self.checkMandate()
        self.checkDescription()
        self.chackStopDecition()
        self.checkCredentials()
        self.checkWorkQueue()
        self.cheackExceptions()
        self.addToJSON()


strFilePath_or_XMLString = "C:\\Users\\bc6612\\Desktop\\BPA Process - 03020 - SE LR Blocking.xml"

thisXMLChecker = XMLChecker(strFilePath_or_XMLString)

thisXMLChecker.checkAll()