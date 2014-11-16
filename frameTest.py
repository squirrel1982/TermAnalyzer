import wx
class SubclassDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self,None,-1,'dialog --- subclass',size=(300,100))
        okButton = wx.Button(self,-1,"OK",pos=(15,15))
        self.Bind(wx.EVT_BUTTON,self.OnClick,okButton)
        okButton.SetDefault()

        cancelButton = wx.Button(self,wx.ID_CANCEL,"Cancel",pos=(115,15))
    def onClick(self,event):
        self.Destry()
'''
if __name__ == "__main__":
    app = wx.PySimpleApp()
    app.MainLoop()
    dialog = SubclassDialog()
    result = dialog.ShowModal()
    
    if result == wx.ID_OK:
        pp('----')
    else:
        pp("CANCEL")
    dialog.Destroy()
    '''
