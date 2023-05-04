from tkinter import *
from AnimalTA.A_General_tools import UserMessages
from AnimalTA.E_Post_tracking.b_Analyses import Interface_details_ana, Interface_deformation


class Row_Ana(Frame):
    '''This is a frame that display the information about the different possibilities of video analyses.'''
    def __init__(self, main, parent, checkvar, value, position, **kw):
        Frame.__init__(self, parent, **kw)
        self.parent=parent
        self.main=main
        self.checkvar=checkvar
        self.columnconfigure(0, weight=100)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.position = position
        self.value=value

        f = open(UserMessages.resource_path("AnimalTA/Files/Language"), "r", encoding="utf-8")
        Language = (f.read())
        f.close()
        Messages = UserMessages.Mess[Language]

        #List of the possibilities for video analyses.
        self.Ana_liste = dict(
            Basics=Messages["Ana_dict1"],
            Spatial=Messages["Ana_dict2"],
            InterInd=Messages["Ana_dict3"],
            Exploration=Messages["Ana_dict4"]
        )

        self.main.Add_ana.update()
        self.config(width=self.main.Add_ana.winfo_width()-2, height=150)
        self.grid_propagate(True)
        checkB=Checkbutton(self, text=self.Ana_liste[value], variable=self.checkvar, onvalue=value, offvalue=0, wraplength=150, command=self.main.modif_image)
        checkB.grid(row=0, column=0, sticky="w")

        Change_param=Button(self, text="P", command=self.change_params)
        Change_param.grid(row=0, column=1, sticky="e")

        self.main.modif_image()
        self.config(height=checkB.winfo_height()+5)

    def change_params(self):
        self.checkvar.set(self.value)
        if self.value=="Basics":
            newWindow = Toplevel(self.main.master)
            interface = Interface_details_ana.Details_basics(parent=newWindow, main=self.main)
        elif self.value=="Spatial":
            self.main.overlay=None
            newWindow = Toplevel(self.main.master)
            interface = Interface_details_ana.Details_spatial(parent=newWindow, main=self.main)
        elif self.value=="Exploration":
            self.main.overlay=None
            newWindow = Toplevel(self.main.master)
            interface = Interface_details_ana.Details_explo(parent=newWindow, main=self.main)
        elif self.value=="InterInd":
            self.main.overlay=None
            newWindow = Toplevel(self.main.master)
            interface = Interface_details_ana.Details_inter(parent=newWindow, main=self.main)
