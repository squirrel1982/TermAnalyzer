# -*- coding: utf-8 -*-
import wx
import pymssql
import wx.grid
import copy
import os
from xlrd import open_workbook
from xlwt import Workbook

class TestDialog(wx.Dialog):
    def __init__(
            self, parent, ID, title, size=(500,200), pos=(200,200),
            style=wx.DEFAULT_DIALOG_STYLE,
            ):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI object using the Create
        # method.
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, ID, title, pos, size, style)
        
        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.PostCreate(pre)
        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, "Please input user account and password")
        sizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "User:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.user_text = wx.TextCtrl(self, -1, "su", size=(80,-1))
        box.Add(self.user_text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Password:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.pwd_text = wx.TextCtrl(self, -1, "123", size=(80,-1))
        box.Add(self.pwd_text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "DataBase:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.db_text = wx.TextCtrl(self, -1, "car_database",size=(80,-1))
        box.Add(self.db_text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Table:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.table_text = wx.TextCtrl(self, -1, "original_info", size=(80,-1))
        box.Add(self.table_text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "ID column:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.id_text = wx.TextCtrl(self, -1, "id", size=(80,-1))
        box.Add(self.id_text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        label = wx.StaticText(self, -1, "Text Column:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.text_text = wx.TextCtrl(self, -1, "ab",size=(80,-1))
        box.Add(self.text_text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        
        btnsizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self,wx.ID_OK)
        ok_btn.SetDefault()
        btnsizer.AddButton(ok_btn)

        cancel_btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(cancel_btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)       
        self.SetSizer(sizer)

        
class AbstractModel(object):
    def __init__(self):
        self.listeners=[]
    def addListeners(self,listenerFunc):
        self.listeners.append(listenerFunc)
    def removeListeners(self,listenerFunc):
        self.listeners.remove(listenerFunc)
    def update(self):
        for eachFunc in self.listeners:
            eachFunc(self)

class SimpleName(AbstractModel):
    def __init__(self,m):
        AbstractModel.__init__(self)
        self.m = m
    def set(self,m):
        self.m = m
        self.update()
    def get(self):
        return self.m
from topia.termextract import extract
import re
class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None,-1,"Term Analysis Software",size=(900,700))
        
        
        #store patent records
        
        self.model = SimpleName([])
        self.model.addListeners(self.OnUpdate)
        self.dictionaries = []
        self.con_words ={}
        nb = wx.Notebook(self)
        self.p = wx.Panel(nb)
        self.p1 = wx.Panel(nb)
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menuBar.Append(menu,"File")
        openFileItem = menu.Append(-1,"Open File")
        link2DBItem = menu.Append(-1,"Link To Database")
        # Put components on p1
        self.Output  = wx.StaticText(self.p, -1, "Please input user account and password",pos=(300,0))
        self.Bind(wx.EVT_MENU,self.OnOpenFile,openFileItem)
        self.Bind(wx.EVT_MENU,self.OnLink2DB,link2DBItem)
        
        menu1 = wx.Menu()
        menuBar.Append(menu1,"Configure")
        dictLocItem = menu1.Append(-1,"Dict Location ")
        self.Bind(wx.EVT_MENU,self.OnOpenFile,dictLocItem)
        
        self.SetMenuBar(menuBar)
        #add Button into frame
        # termExtraction Button
        termExtractButton = self.buildOneButton(self.p,"Term Extraction",self.OnTermExtract,pos=(0,5),size=(110,40))
        createDictButtion = self.buildOneButton(self.p,"Creat Dictionary",self.OnCreateDict,pos=(112,5),size=(110,40))
        #add grid into frame
        self.grid = wx.grid.Grid(self.p,-1,pos=(0,50),size =(855,455),style = wx.WANTS_CHARS)
        self.grid.CreateGrid(20,3)
        colLabels =["ID","text","terms"]
        self.grid.SetColSize(0,125)
        self.grid.SetColSize(1,410)
        self.grid.SetColSize(2,235)
        for i in range(len(colLabels)):
            self.grid.SetColLabelValue(i,colLabels[i])
        #load dicts from default address
        self.loadDicts()
        #put components on p2
        self.tree = wx.TreeCtrl(self.p1,-1,pos=(0,50),size =(185,535))
        self.root = self.tree.AddRoot("Dictionaries")
        for i in range(len(self.dictionaries)):
            self.AddTreeNode(self.root,str(self.dictionaries[i][0]))
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        # add grid on p2
        self.grid1 = self.createGridByNum(self.p1,-1)
            
        self.modifyDictButton = self.buildOneButton(self.p1,"Modify Dict",self.OnModifyDict,pos=(0,5),size=(110,40))
        self.modifyDictButton.Disable()
        self.importDictButton = self.buildOneButton(self.p1,"Import Dict",self.OnImportDict,pos=(110,5),size=(110,40))
        self.exportDictButton = self.buildOneButton(self.p1,"Export Dict",self.OnExportDict,pos=(220,5),size=(110,40))
        self.exportDictButton.Disable()
        
        
        wx.StaticText(self.p1,-1,"Sort Data By:",pos = (200,60),size = (80,30))
        self.choice1 = wx.Choice(self.p1,-1,pos = (280,60),size = (85,28),choices=['Term','Frequency'])
        self.choice1.SetSelection(0)
        self.choice1.Bind(wx.EVT_CHOICE,self.OnChoiceSelect)
        
        nb.AddPage(self.p, "Texts Analysis")
        nb.AddPage(self.p1, "Dictionary Management")
        

        
    def loadDicts(self):
        f = open('config.txt','r')
        self.dictionariesAddr = f.read()
        
        dictionariesFiles = os.listdir(self.dictionariesAddr)
        for i in dictionariesFiles:
            self.dictionaries.append(self.readInDict(self.dictionariesAddr+'\\'+str(i)))
            #wx.MessageBox(self.dictionariesAddr+'\\'+str(i))
            
            
    def readInDict(self,dictAddr):
        dictionary = [dictAddr[dictAddr.rfind('\\')+1:dictAddr.rfind('.')]]
        dictTmp = []
        wb = open_workbook(dictAddr)
        for s in wb.sheets():
            for row in range(s.nrows):
                values=[]
                for col in range(s.ncols):
                    values.append(s.cell(row,col).value)
                dictTmp.append(values)
        
        dictionary.append(dictTmp) 
        return dictionary
    def writeDictToFile(self,dict,addr=None):
        #judge whether dict exist
        
        wb = Workbook()
        ws = wb.add_sheet('dictionary')
        for i in range(len(dict[1])):
            for j in range(2):
                ws.row(i).write(j,dict[1][i][j])
        if(addr==None):
            wb.save(self.dictionariesAddr+'\\'+dict[0]+'.xls')
        else:
            wb.save(addr)
    def createGridByNum(self,parent,id,rowsNum=20,colLabels =["term","frequency"],pos=(190,100),size=(350,435)):
        grid1 = wx.grid.Grid(self.p1,-1,pos,size,style = wx.WANTS_CHARS)
        grid1.CreateGrid(rowsNum,len(colLabels))
        grid1.SetColSize(0,150)
        grid1.SetColSize(1,100)
        for i in range(len(colLabels)):
            grid1.SetColLabelValue(i,colLabels[i])
        return grid1

    def OnTermExtract(self,event):
        extractor = extract.TermExtractor()
        for i in range(len(self.model.m)):
            self.model.m[i]=list(self.model.m[i])
        for i in self.model.m:
            b=extractor(i[1])
            # lowerCase
            c= [j[0].lower() for j in b]
            # remove
            pattern = re.compile(r'\(.*\)|\.|,|/|\\')
            s = set([pattern.sub(r'',k).strip() for k in c])
            s.discard('')
            i.append(list(s))
        self.recordsIntoGrid(self.model.m)
        #self.store_texts_record(self.model.m)
    def OnCreateDict(self,event):
        #create a dialog,ask user to name a dictionary
        
        self.all_stems = []
        for i in self.model.m:
            self.all_stems+=i[2]
        #remove words occured only once 
        dialog = wx.TextEntryDialog(None,"Enter name to this dictionary:",style=wx.OK|wx.CANCEL)
        if dialog.ShowModal()==wx.ID_OK:
            dictName = dialog.GetValue().strip()
            dictionarySet = set([ i for i in self.all_stems if self.all_stems.count(i)!=1])       
            self.dictionary = [[i,self.all_stems.count(i)] for i in dictionarySet]
            self.dictionaries.append([dictName,self.dictionary])
            i = len(self.dictionaries)-1
            self.AddTreeNode(self.tree.GetRootItem(),dictName)
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        #
# every page has 20 records,and 10 signals like 1,2,3,4,....,10
    def createButtonBar(self,m,yPos=506):
        buttonBar =[]
        xPos = 856
        dataLen = len(m)
        pageNum = dataLen/20+1
        #create button |<,<<,>>,>|
        if pageNum>10:
            #create >>,>| button
            showPageNum = 10
            for i in range(showPageNum):
                pos = (xPos-(showPageNum+2-i)*30,yPos)
                button = self.buildOneButton(self.p,str(i+1),self.OnXBtnPoint,pos)
                buttonBar.append(button)        
            pos = (xPos-2*30,yPos)
            button = self.buildOneButton(self.p,">>",self.onNxtBtn,pos)
            buttonBar.append(button)
            pos =(xPos-1*30,yPos)
            button = self.buildOneButton(self.p,">|",self.onEndBtn,pos)
            buttonBar.append(button)
        else:
            showPageNum = pageNum
            for i in range(showPageNum):
                pos = (xPos-(showPageNum-i)*30,yPos)
                button = self.buildOneButton(self.p,str(i+1),self.OnXBtnPoint,pos)
                buttonBar.append(button)  
        return buttonBar
    def buildOneButton(self,parent,label,handler,pos=(0,0),size=(30,30)):
        button = wx.Button(parent,-1,label,pos,size)
        self.Bind(wx.EVT_BUTTON,handler,button)
        
        return button
    def OnUpdate(self,model):
        self.recordsIntoGrid(model.m)
        #self.Output
        self.buttonBar = self.createButtonBar(model.m)
    def recordsIntoGrid(self,m):
        dataLen = len(m)
        if dataLen>20:
            dataLen=20
        for i in range(dataLen):
            for j in range(len(m[i])):
                self.grid.SetCellValue(i,j,str(m[i][j]))
    def recordsIntoGrid2(self,m):
        dataLen = len(m)
        for i in range(dataLen):
            for j in range(len(m[i])):
                self.grid1.SetCellValue(i,j,str(m[i][j]))
    def OnXBtnPoint(self,event):
        label = event.GetEventObject().GetLabel()
        self.Output.SetLabel(label)
        #update grid
        labelNum = int(label)
        self.recordsIntoGrid(self.model.m[(labelNum-1)*20:labelNum*20])
        #evt_ID = event.GetID()
        
    def onPreBtn(self,event):
        #check buttonBar,if it dont have |<,<< buttons,add them into buttonBar
        xPos=856
        yPos=506
        #update buttonBar
        #label_keepNextBtn = 0  
        label_keepPreBtn = 1  
        #dataLen = len(self.model.m)
        #check if buttonBar have >>,>| buttons
        label = self.buttonBar[2].GetLabel()
        labelNum = int(label)
        if ((labelNum-1)*20-200)==0:
            label_keepPreBtn = 0
            
        for iButton in self.buttonBar:
            iButton.Destroy()
        self.buttonBar = []
        showPageNum = 12
        if label_keepPreBtn==1:
            pos =(xPos-(showPageNum+2)*30,yPos)
            button = self.buildOneButton(self.p,"|<",self.onBgnBtn,pos)
            self.buttonBar.append(button)
            pos =(xPos-(showPageNum+1)*30,yPos)
            button = self.buildOneButton(self.p,"<<",self.onPreBtn,pos)
            self.buttonBar.append(button)
            for i in range(showPageNum-2):
                pos =(xPos-(showPageNum-i)*30,yPos)
                button = self.buildOneButton(self.p,str(i-10+labelNum),self.OnXBtnPoint,pos)
                self.buttonBar.append(button)
            pos = (xPos-2*30,yPos)
            button = self.buildOneButton(self.p,">>",self.onNxtBtn,pos)
            self.buttonBar.append(button)
            pos =(xPos-1*30,yPos)
            button = self.buildOneButton(self.p,">|",self.onEndBtn,pos)
            self.buttonBar.append(button)
        else:           
            for i in range(showPageNum-2):
                pos =(xPos-(showPageNum-i)*30,yPos)
                button = self.buildOneButton(self.p,str(i-10+labelNum),self.OnXBtnPoint,pos)
                self.buttonBar.append(button)
            pos = (xPos-2*30,yPos)
            button = self.buildOneButton(self.p,">>",self.onNxtBtn,pos)
            self.buttonBar.append(button)
            pos =(xPos-1*30,yPos)
            button = self.buildOneButton(self.p,">|",self.onEndBtn,pos)
            self.buttonBar.append(button)              
        #update grid
        self.recordsIntoGrid(self.model.m[(labelNum-11)*20:(labelNum-1)*20])
    def onNxtBtn(self,event):
        #check buttonBar,if it dont have |<,<< buttons,add them into buttonBar
        xPos=856
        yPos=506
        #update buttonBar   
        dataLen = len(self.model.m)
        #check how much pages left
        label = self.buttonBar[0].GetLabel()
        if label=='|<':
            label = self.buttonBar[2].GetLabel()
        labelNum = int(label)
        if ((labelNum-1)*20+400)<dataLen:
            showPageNum = 10
        else:
            showPageNum = (dataLen-((labelNum-1)*20+200))/20+1
        for iButton in self.buttonBar:
            iButton.Destroy()
        self.buttonBar = []
        if showPageNum==10:
            pos =(xPos-(showPageNum+4)*30,yPos)
            button = self.buildOneButton(self.p,"|<",self.onBgnBtn,pos)
            self.buttonBar.append(button)
            pos =(xPos-(showPageNum+3)*30,yPos)
            button = self.buildOneButton(self.p,"<<",self.onPreBtn,pos)
            self.buttonBar.append(button)
            for i in range(showPageNum):
                pos =(xPos-(showPageNum+2-i)*30,yPos)
                button = self.buildOneButton(self.p,str(i+10+labelNum),self.OnXBtnPoint,pos)
                self.buttonBar.append(button)
            pos = (xPos-2*30,yPos)
            button = self.buildOneButton(self.p,">>",self.onNxtBtn,pos)
            self.buttonBar.append(button)
            pos =(xPos-1*30,yPos)
            button = self.buildOneButton(self.p,">|",self.onEndBtn,pos)
            self.buttonBar.append(button)
        else:
            pos =(xPos-(showPageNum+2)*30,yPos)
            button = self.buildOneButton(self.p,"|<",self.onBgnBtn,pos)
            self.buttonBar.append(button)
            
            pos =(xPos-(showPageNum+1)*30,yPos)
            button = self.buildOneButton(self.p,"<<",self.onPreBtn,pos)
            self.buttonBar.append(button)
            
            for i in range(showPageNum):
                pos =(xPos-(showPageNum-i)*30,yPos)
                button = self.buildOneButton(self.p,str(i+10+labelNum),self.OnXBtnPoint,pos)
                self.buttonBar.append(button)                
        #update grid
        if (labelNum+10)*20>dataLen:
            self.recordsIntoGrid(self.model.m[(labelNum+9)*20:])
        else:
            self.recordsIntoGrid(self.model.m[(labelNum+9)*20:(labelNum+10)*20])
        
    def onBgnBtn(self,event):
        pass
    def onEndBtn(self,event):
        pass
# get id_texts and put them into MyFrame
    def store_texts_record(self,m):
        self.model.set(m)
        
        
    def OnOpenFile(self,event):
        dialog = wx.DirDialog(None,"Choose a  directory:",style =wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal()==wx.ID_OK:
            f = open('config.txt','w')
            f.write(dialog.GetPath())
            f.close()
            
            
    def OnImportDict(self,event):
        openFileDialog = wx.FileDialog(self, "Open dictionary file", "", "",
                                       "Excel files (*.xls)|*.xls", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return     # the user changed idea...
        # proceed loading the file chosen by the user
        # this can be done with e.g. wxPython input streams:
        fileAddr = openFileDialog.GetPath()
        self.dictionaries.append(self.readInDict(fileAddr))
        
        self.tree.Destroy()
        self.tree = wx.TreeCtrl(self.p1,-1,pos=(0,50),size =(185,535))
        self.root = self.tree.AddRoot("Dictionaries")
        
        for i in range(len(self.dictionaries)):
            self.AddTreeNode(self.root,str(self.dictionaries[i][0]))
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        return
            
    def OnLink2DB(self,event):
        DBConnectDlg = TestDialog(None,-1,"Connect DataBase")
        result = DBConnectDlg.ShowModal()
        if result == wx.ID_OK:
            #no necessory to deepcopy
            self.con_words['user'] = DBConnectDlg.user_text.GetValue()
            self.con_words['pwd'] = DBConnectDlg.pwd_text.GetValue()
            self.con_words['db'] = DBConnectDlg.db_text.GetValue()
            self.con_words['table'] = DBConnectDlg.table_text.GetValue()
            self.con_words['id'] = DBConnectDlg.id_text.GetValue()
            self.con_words['text'] = DBConnectDlg.text_text.GetValue()
            records = self.connectDB()
            
            self.store_texts_record(records)
            
        else:
            pass
        
        #self.words = DBConnectDlg.words
        DBConnectDlg.Destroy()

    def connectDB(self):
        #connect
        conn=pymssql.connect(host=".",user=self.con_words['user'].strip(),password=self.con_words['pwd'].strip(),database=self.con_words['db'].strip())
        self.Output.SetLabel(self.con_words['user']+" "+self.con_words['pwd']+" "+self.con_words['db']+" ")
        cursor = conn.cursor();
        sql = "select top 300 "+self.con_words['id']+","+self.con_words['text']+" from "+self.con_words['table']
        
        cursor.execute(sql)
        m=cursor.fetchall()
        self.Output.SetLabel(str(len(m)))
        return m
    def OnModifyDict(self,event):

        dialog3 = ModifyDictDialog(None, -1, "Edit Dictionary: "+self.dictionaries[self.num][0],self)
        result = dialog3.ShowModal()
        if result == wx.ID_OK:
            #update dict
            m = dialog3.getDataFromGrid1()
            self.dictionaries[self.num][1] = dialog3.reconcileDict(m)
            #update treeNode
        else:
            pass
        
        self.writeDictToFile(self.dictionaries[self.num])  
        self.tree.Destroy()
        self.tree = wx.TreeCtrl(self.p1,-1,pos=(0,50),size =(185,535))
        self.root = self.tree.AddRoot("Dictionaries")
        
        
        for i in range(len(self.dictionaries)):
            self.AddTreeNode(self.root,str(self.dictionaries[i][0]))
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        #self.words = DBConnectDlg.words
        dialog3.Destroy()

    def OnExportDict(self,evt):
        dialog = wx.FileDialog(self, "Export "+self.dictionaries[self.num][0]+" dictionary", "", "",
                                   "Excel files (*.xls)|*.xls", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_CANCEL:
            return
        path = dialog.GetPath()
        # 存入myFrame.dictionary
        #m = self.getDataFromGrid1()
        #self.myFrame.dictionaries.append([dialog.GetValue(),self.reconcileDict(m)])
        self.writeDictToFile(self.dictionaries[self.num],path)
    #have sth to do with treeCtrl BEGIN
    def AddTreeNodes(self,parentItem,items):
        for item in items:
            if type(item) ==str:
                self.tree.AppendItem(parentItem,item)
            else:
                newItem = self.tree.AppendItem(parentItem,item[0])
                self.AddTreeNodes(newItem,item[1])
    def AddTreeNode(self,parentItem,item):
        newItem = self.tree.AppendItem(parentItem,item)
    def GetItemText(self,item):
        if item:
            return self.tree.GetItemText(item)
        else:
            return ""
    def OnItemExpanded(self,evt):
        print "OnItemExpanded:",self.GetItemText(evt.GetItem())
    def OnItemCollapsed(self,evt):
        itemName = self.GetItemText(evt.GetItem())
        self.recordsIntoGrid2(self.dictionaries[int(itemName)])
    def OnActivated(self,evt):
        pass
    
    def OnSelChanged(self,evt):
        #judge whether item has children
        self.num = -1
        item =evt.GetItem()
        #wx.MessageBox(self.GetItemText(item))
        if self.tree.ItemHasChildren(item)==False:
            dictName = self.GetItemText(item)
            self.grid1.Destroy()
            #wx.MessageBox(dictName)
            self.num = self.getDictNumByName(dictName)
            #wx.MessageBox(str(self.num))
            self.grid1 = self.createGridByNum(self.p1,-1,len(self.dictionaries[self.num][1]))
            
            self.dictionaries[self.num][1].sort(cmp=lambda x,y: cmp(x[0].lower(), y[0].lower()))
            self.recordsIntoGrid2(self.dictionaries[self.num][1])
            
            self.modifyDictButton.Enable()
            self.exportDictButton.Enable()
        else:
            self.modifyDictButton.Disable()
            self.exportDictButton.Disable()
            self.grid1.ClearGrid()
            
    def getDictNumByName(self,name):
        
        result = -1
        for i in range(len(self.dictionaries)):
            if self.dictionaries[i][0]==name:
                result = i
                break
        return result
        
    def OnChoiceSelect(self,evt):
         
        result =self.choice1.GetStringSelection()
         
        #wx.Message(type(result))
        
        if result=='Term':
            # order by name
            self.dictionaries[int(self.num)][1].sort(cmp=lambda x,y: cmp(x[0].lower(), y[0].lower()))
            self.recordsIntoGrid2(self.dictionaries[int(self.num)][1])
        else:
            self.dictionaries[int(self.num)][1].sort(cmp=lambda x,y: cmp(x[1], y[1]), reverse=True)
            self.recordsIntoGrid2(self.dictionaries[int(self.num)][1])
        
    # merge the same words into one word and add each words' frequencies together

        
class ModifyDictDialog(wx.Dialog):
    def __init__(
            self, parent, ID, title,myFrame,size=(540,550),pos=(20,20),
            style=wx.DEFAULT_DIALOG_STYLE
            ):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI object using the Create
        # method.
 
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, ID, title, pos, size, style)
        #
        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.PostCreate(pre)
        # Now continue with the normal construction of the dialog
        # contents
        #label = wx.StaticText(self, -1, "Dictionary:"+myFrame.num)
 
        self.myFrame = myFrame
 
        self.dictionary = copy.deepcopy(myFrame.dictionaries[int(myFrame.num)][1])
        self.grid1 = self.createEditGrid(self,-1,len(self.dictionary))
 
        self.dictionary.sort(cmp=lambda x,y: cmp(x[0].lower(), y[0].lower()))
        self.recordsIntoGrid1(self.dictionary)
        attr = wx.grid.GridCellAttr()
 
        editor_1 = wx.grid.GridCellBoolEditor()
 
        attr.SetEditor(editor_1)
 
        #self.grid1.SetColAttr(2,attr)
        #attr.SetRenderer(wx.grid.GridCellBoolRenderer())
        self.grid1.SetColAttr(2,attr)
        #self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,self.OnMouseLeftDown,self.grid1) 
        ok_btn = wx.Button(self,wx.ID_OK,pos=(405,30),size=(100,40))
        #make frequecy column ReadOnly
        
        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(True)
        self.grid1.SetColAttr(1,attr)
        '''
        attr = wx.grid.GridCellAttr()
        editor = wx.grid.GridCellTextEditor()
        attr.SetEditor(editor)
        self.grid1.SetColAttr(0,attr)
        '''
        saveAs_btn = wx.Button(self, -1,"Save as",pos=(405,70),size=(100,40))
        self.Bind(wx.EVT_BUTTON,self.OnSaveAs,saveAs_btn)
        
        del_btn = wx.Button(self,-1,"Delete",pos=(405,110),size=(100,40))
        self.Bind(wx.EVT_BUTTON,self.OnDelete,del_btn)
        
        cancel_btn = wx.Button(self, wx.ID_CANCEL,pos=(405,150),size=(100,40))
        
        self.choice1 = wx.Choice(self,-1,pos =(0,0),size = (85,28),choices=['Term','Frequency'])
        self.choice1.SetSelection(0)
        self.choice1.Bind(wx.EVT_CHOICE,self.OnChoiceSelect)
    def createEditGrid(self,parent,ID,rowsNum,pos=(0,30),size=(400,430),style = wx.WANTS_CHARS):
        grid1 = wx.grid.Grid(parent,ID,pos,size,style)
        grid1.CreateGrid(rowsNum,3)
        grid1.SetColSize(0,150)
        grid1.SetColSize(1,100)
        grid1.SetColSize(2,50)
        colLabels =['Term','Freq','Del']
        for i in range(3):
            grid1.SetColLabelValue(i,colLabels[i])
        return grid1
    def recordsIntoGrid1(self,m):
        dataLen = len(m)
        for i in range(dataLen):
            for j in range(len(m[i])):
                self.grid1.SetCellValue(i,j,str(m[i][j]))
    # get data[term][freq] from grid1
    def getDataFromGrid1(self):
        #get records length
        
        #get records column
        rows = self.grid1.GetNumberRows()
        result = []
        for i in range(rows):
            tmpCol = []
            for j in range(2):
                if j==0:
                    tmpCol.append(self.grid1.GetCellValue(i,j))
                else:
                    tmpCol.append(int(float(self.grid1.GetCellValue(i,j))))
            result.append(tmpCol)
        return result
                
        
    def OnMouseLeftDown(self,event):
        row = event.GetRow()
        column = event.GetCol()
        # Column 'Delete'
        if column==2:
            if str(self.grid1.GetCellValue(row,column)) == '0':
                self.grid1.SetCellValue(row, column, '1')
            else:
                self.grid1.SetCellValue(row, column, '0')
        # if column==0,you can edit this cell
        #elif column==0:
        #   attr = wx.grid.GridCellAttr()
        #  attr.SetReadOnly(False)
        # self.grid1.SetCellAttr(row,column,attr)
    def OnSaveAs(self,evt):
        dialog = wx.TextEntryDialog(None,"Save As New Dictionary:",style=wx.OK|wx.CANCEL)
        if dialog.ShowModal() == wx.ID_CANCEL:
            return
        if dialog.ShowModal()==wx.ID_OK:
            # 存入myFrame.dictionary
            m = self.getDataFromGrid1()
            self.myFrame.dictionaries.append([dialog.GetValue(),self.reconcileDict(m)])
            self.writeDictToFile([dialog.GetValue(),copy.deepcopy(self.dictionary)])  
    def OnDelete(self,evt):
        
        rowNum = self.grid1.GetNumberRows()
         
        for i in range(rowNum):
            if self.grid1.GetCellValue(rowNum-i-1,2)=='1':
                del self.dictionary[rowNum-i-1]
                self.grid1.DeleteRows(rowNum-i-1,1)
        #self.grid1 = self.createEditGrid(self,-1,len(self.dictionary))
        #self.recordsIntoGrid1(self.dictionary)
                
            
    def OnChoiceSelect(self,evt):
        
        result =self.choice1.GetStringSelection()
 
        #wx.Message(type(result))
        
        if result=='Term':
            # order by name
            self.dictionary.sort(cmp=lambda x,y: cmp(x[0].lower(), y[0].lower()))
            self.recordsIntoGrid1(self.dictionary)
        else:
            self.dictionary.sort(cmp=lambda x,y: cmp(x[1], y[1]), reverse=True)
            self.recordsIntoGrid1(self.dictionary)

    def reconcileDict(self,m):
        s = set(i[0] for i in m)
        result = []
        for i in s:
            sum = 0
	    for j in m:
	        if i==j[0]:
	            sum+=int(j[1])
	    result.append([i,sum])
	return result

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = MyFrame()
    frame.Show()
    app.MainLoop()