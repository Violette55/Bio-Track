from tkinter import *
import cv2
import PIL.Image, PIL.ImageTk
import decord
import numpy as np
import math
from AnimalTA import UserMessages, User_help


class Scale(Frame):
    """This Frame allows the user  to define a scale by selecting two points in the video and indicating the distance between them IRL"""
    def __init__(self, parent, boss, main_frame, Video_file, **kwargs):
        Frame.__init__(self, parent, bd=5, **kwargs)
        self.parent=parent
        self.boss=boss
        self.main_frame=main_frame
        self.grid(row=0,column=0,rowspan=2,sticky="nsew")
        self.Vid = Video_file

        #Import messages
        self.Language = StringVar()
        f = open("Files/Language", "r")
        self.Language.set(f.read())
        self.LanguageO = self.Language.get()
        f.close()
        self.Messages = UserMessages.Mess[self.Language.get()]

        #Open video and take the first frame (after cropping)
        Which_part = 0
        if self.Vid.Cropped[0]:
            if len(self.Vid.Fusion) > 1:  # Si on a plus d'une video
                Which_part = [index for index, Fu_inf in enumerate(self.Vid.Fusion) if Fu_inf[0] <= self.Vid.Cropped[1][0]][-1]

        self.capture = decord.VideoReader(self.Vid.Fusion[Which_part][1], ctx=decord.cpu(0))
        self.Represent = self.capture[self.Vid.Cropped[1][0] - self.Vid.Fusion[Which_part][0]].asnumpy()
        del self.capture

        self.shape=(self.Represent.shape[0],self.Represent.shape[1])

        self.image_to_show=np.copy(self.Represent)

        self.zoom_sq=[0,0,self.Vid.shape[1],self.Vid.shape[0]]
        self.zoom_strength = 0.3

        self.Pt_select=None
        self.dist=0
        self.Mem_size="NA"
        self.ratio_val=StringVar()#Value calculated from the informations gave by user
        self.ratio_val.set("NA")
        self.ratio_text=StringVar()#Units of the ratio
        self.ratio_text.set("px/?")

        self.canvas_img = Canvas(self, bd=0, highlightthickness=0, relief='ridge')
        self.canvas_img.grid(row=0, column=0, sticky="nsew")
        Grid.columnconfigure(self, 0, weight=1)
        Grid.rowconfigure(self, 0, weight=1)

        #Help user and parameters
        self.HW=User_help.Help_win(self.parent, default_message=self.Messages["Scale2"], width=250)
        self.HW.grid(row=0, column=1,sticky="nsew")

        #Options
        self.canvas_bt_global=Canvas(self.parent, height=10, bd=0, highlightthickness=0, relief='ridge')
        self.canvas_bt_global.grid(row=1,column=1, sticky="nsew")

        self.UI_Size_label = Label(self.canvas_bt_global,text=self.Messages["Scale3"])
        self.UI_Size_label.grid(row=2,column=0)
        self.UI_Size=Entry(self.canvas_bt_global)
        self.regUI_Size = self.register(self.UI_Size_update)
        self.UI_Size.config(validate="focusout", validatecommand=(self.regUI_Size,"%P"))
        self.UI_Size.grid(row=2,column=1)
        self.UI_Size.bind("<Return>", self.remove_focus)

        self.Check_units=Listbox(self.canvas_bt_global, exportselection=0)
        self.Check_units.config(height=3)
        self.Check_units.insert(1, "m")
        self.Check_units.insert(2, "cm")
        self.Check_units.insert(3, "mm")
        self.Check_units.grid(row=2,column=2)
        self.Check_units.bind('<<ListboxSelect>>', self.update_ui)

        self.UI_ratio_label = Label(self.canvas_bt_global,text="Ratio:")
        self.UI_ratio_label.grid(row=4,column=0)

        self.ratio_val_label = Label(self.canvas_bt_global,textvariable=self.ratio_val)
        self.ratio_val_label.grid(row=4,column=1)

        self.ratio_post_label = Label(self.canvas_bt_global,textvariable=self.ratio_text)
        self.ratio_post_label.grid(row=4,column=2)

        #Validate once the scale is defined
        self.bouton_validate = Button(self.canvas_bt_global, text=self.Messages["Validate"], background="#6AED35", fg="black", command=self.validate)
        self.bouton_validate.grid(row=6, column=0, columnspan=3,sticky="nsew")

        #Parameters to show the image/calculate image reduction and canvas' size
        self.ratio=1
        self.final_width=750
        self.Size = self.Vid.shape
        self.canvas_img.bind("<Configure>", self.afficher)

        self.canvas_img.focus_force()
        self.liste_points = []
        self.unit=False

        self.UI_Size.insert(0, "NA")
        self.canvas_img.bind("<Button-1>", self.callback_mask)
        self.canvas_img.bind("<B1-Motion>", self.move_pt_mask)
        self.canvas_img.bind("<Control-1>", self.Zoom_in)
        self.canvas_img.bind("<Control-3>", self.Zoom_out)

        self.canvas_img.update()
        self.final_width = self.canvas_img.winfo_width()
        self.ratio = self.Size[1] / self.final_width

        self.afficher()

    def update_ui(self,event):
        #Update the label indicating the units
        self.unit=True
        list_item=self.Check_units.curselection()
        if len(list_item)>0:
            self.ratio_text.set("px/{}".format(["m","cm","mm"][list_item[0]]))

    def remove_focus(self, *arg):
        #Ensure the image has always the focus
        self.canvas_img.focus_set()

    def UI_Size_update(self, new_val):
        #Recalculates and updates the ratio value
        if new_val=="":
            self.UI_Size.delete(0, END)
            self.UI_Size.insert(0, self.Mem_size)
            return False
        else:
            try:
                float(new_val)
                self.UI_Size.delete(0, END)
                self.UI_Size.insert(0, new_val)
                self.Mem_size=new_val
                self.ratio_val.set(round(float(self.dist)/float(self.Mem_size),2))
                self.afficher()
                return True
            except:
                self.UI_Size.delete(0, END)
                self.UI_Size.insert(0, self.Mem_size)
                return False

    def validate(self):
        #Save the new ratio and close the Frame
        self.UI_Size_update(self.UI_Size.get())
        if self.Mem_size != "NA" and self.unit and self.dist>0: #We check that user filed all the boxes
            list_item = self.Check_units.curselection()

            if self.Vid.Track[0]:#If the parameters were not defined yet
                old_min=float(self.Vid.Track[1][3][0])* float(self.Vid.Scale[0]) ** 2
                old_max=float(self.Vid.Track[1][3][1])* float(self.Vid.Scale[0]) ** 2
                old_dist = float(self.Vid.Track[1][5] )* float(self.Vid.Scale[0])
            self.Vid.Scale[0] = float(self.ratio_val.get())
            self.Vid.Scale[1] = ["m","cm","mm"][list_item[0]]

            if self.Vid.Track[0]:
                self.Vid.Track[1][3][0]=old_min/ float(self.Vid.Scale[0]) ** 2
                self.Vid.Track[1][3][1]=old_max/ float(self.Vid.Scale[0]) ** 2
                self.Vid.Track[1][5]=old_dist/ float(self.Vid.Scale[0])

            self.End_of_window()

        #If some info are missing, a message will ask the user to do fill them.
        elif self.Mem_size == "NA":
            self.HW.change_default_message(self.Messages["Scale4"])
        elif not self.unit:
            self.HW.change_default_message(self.Messages["Scale5"])
        elif self.dist==0:
            self.HW.change_default_message(self.Messages["Scale6"])

    def End_of_window(self):
        #Close the window properly
        self.unbind_all("<Button-1>")
        self.boss.update()
        self.grab_release()
        self.HW.grid_forget()
        self.HW.destroy()
        self.canvas_bt_global.grid_forget()
        self.canvas_bt_global.destroy()
        self.main_frame.return_main()

    def move_pt_mask(self, event):
        #We move a selected point on the image.
        X=int(event.x * self.ratio + self.zoom_sq[0])
        Y=int(event.y * self.ratio + self.zoom_sq[1])
        if self.Pt_select is not None and X>0 and X<self.shape[1] and Y>0 and Y<self.shape[0]:
            self.liste_points[self.Pt_select]=[int(event.x * self.ratio + self.zoom_sq[0]),int(event.y * self.ratio + self.zoom_sq[1])]
            self.UI_Size_update(self.UI_Size.get())
            self.afficher()

    def callback_mask(self, event):
        #When user click on the frame:

        event.x = int(event.x * self.ratio + self.zoom_sq[0])
        event.y = int(event.y * self.ratio + self.zoom_sq[1])

        if len(self.liste_points)<1: #If it is the first point
            self.liste_points.append([event.x,event.y])
            self.Pt_select=0

        elif len(self.liste_points)<=2: #If there is already at least one point:
            self.Pt_select = None# we remove potential previous selection
            for j in range(len(self.liste_points)):# Check if a point is under the cursor
                    if math.sqrt((self.liste_points[j][0] - event.x) ** 2 + (self.liste_points[j][1] - event.y ) ** 2) < 10:
                        self.Pt_select = j
                        break

            #If not we either replace the last point or create it of there was only one defined
            if len(self.liste_points)<2 and self.Pt_select is None:
                self.liste_points.append([event.x,event.y])
                self.Pt_select=len(self.liste_points)-1

            if len(self.liste_points)==2 and self.Pt_select is None:
                self.liste_points.pop(1)
                self.liste_points.append([event.x, event.y])
                self.Pt_select=1

        self.afficher()
        self.UI_Size_update(self.UI_Size.get())

    def afficher(self, *args):
        #Show the image with the segment used to establich scale
        self.TMP_image_to_show=np.copy(self.image_to_show)

        if len(self.liste_points)>0:
            for pt in self.liste_points:
                self.TMP_image_to_show=cv2.circle(self.TMP_image_to_show,tuple(pt),max(1,round(3*self.ratio)),(255,0,0),-1)

        if len(self.liste_points)==2:
            self.dist=math.sqrt((self.liste_points[0][0]-self.liste_points[1][0])**2+(self.liste_points[0][1]-self.liste_points[1][1])**2)
            self.TMP_image_to_show=cv2.line(self.TMP_image_to_show,tuple(self.liste_points[0]),tuple(self.liste_points[1]),(255,0,0),max(1,round(1.5*self.ratio)))
            cv2.putText(self.TMP_image_to_show,str(round(self.dist,1))+" px",(self.liste_points[1][0]-50,self.liste_points[1][1]-25),cv2.FONT_HERSHEY_SIMPLEX,1*self.ratio,(255,255,255),int(6*self.ratio))
            cv2.putText(self.TMP_image_to_show, str(round(self.dist, 1)) + " px",(self.liste_points[1][0] - 50, self.liste_points[1][1] - 25), cv2.FONT_HERSHEY_SIMPLEX,1 * self.ratio, (0, 0, 0), int(3*self.ratio))

        best_ratio = max(self.Size[1] / (self.canvas_img.winfo_width()),self.Size[0] / (self.canvas_img.winfo_height()))
        prev_final_width=self.final_width
        self.final_width=int(self.Size[1]/best_ratio)
        self.ratio=self.ratio*(prev_final_width/self.final_width)

        self.image_to_show2=self.TMP_image_to_show[self.zoom_sq[1]:self.zoom_sq[3],self.zoom_sq[0]:self.zoom_sq[2]]

        self.TMP_image_to_show2 = cv2.resize(self.image_to_show2,(self.final_width, int(self.final_width * (self.Size[0] / self.Size[1]))))
        self.image_to_show3 = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.TMP_image_to_show2))
        self.canvas_img.create_image(0, 0, image=self.image_to_show3, anchor=NW)
        self.canvas_img.config(width=self.final_width, height=int(self.final_width * (self.Size[0] / self.Size[1])))

    def Zoom_in(self, event):
        #Zoom in the image
        self.new_zoom_sq=[0,0,0,0]
        PX=event.x/((self.zoom_sq[2]-self.zoom_sq[0])/self.ratio)
        PY=event.y/((self.zoom_sq[3]-self.zoom_sq[1])/self.ratio)

        event.x = event.x * self.ratio + self.zoom_sq[0]
        event.y = event.y * self.ratio + self.zoom_sq[1]
        ZWX = (self.zoom_sq[2]-self.zoom_sq[0])*(1-self.zoom_strength)
        ZWY = (self.zoom_sq[3]-self.zoom_sq[1])*(1-self.zoom_strength)

        if ZWX>100:
            self.new_zoom_sq[0] = int(event.x-PX*ZWX)
            self.new_zoom_sq[2] = int(event.x+(1-PX)*ZWX)
            self.new_zoom_sq[1] = int(event.y - PY*ZWY)
            self.new_zoom_sq[3] = int(event.y + (1-PY)*ZWY)

            self.ratio=ZWX/self.final_width
            self.zoom_sq=self.new_zoom_sq
            self.zooming = True
            self.afficher()

    def Zoom_out(self, event):
        #Zoom out from the image
        self.new_zoom_sq = [0, 0, 0, 0]
        PX = event.x / ((self.zoom_sq[2] - self.zoom_sq[0]) / self.ratio)
        PY = event.y / ((self.zoom_sq[3] - self.zoom_sq[1]) / self.ratio)

        event.x = event.x * self.ratio + self.zoom_sq[0]
        event.y = event.y * self.ratio + self.zoom_sq[1]
        ZWX = (self.zoom_sq[2] - self.zoom_sq[0]) * (1 + self.zoom_strength)
        ZWY = (self.zoom_sq[3] - self.zoom_sq[1]) * (1 + self.zoom_strength)

        if ZWX<self.Size[1] and ZWY<self.Size[0]:
            if int(event.x - PX * ZWX)>=0 and int(event.x + (1 - PX) * ZWX)<=self.Size[1]:
                self.new_zoom_sq[0] = int(event.x - PX * ZWX)
                self.new_zoom_sq[2] = int(event.x + (1 - PX) * ZWX)
            elif int(event.x + (1 - PX) * ZWX)>self.Size[1]:
                self.new_zoom_sq[0] = int(self.Size[1]-ZWX)
                self.new_zoom_sq[2] = int(self.Size[1])
            elif int(event.x - PX * ZWX)<0:
                self.new_zoom_sq[0] = 0
                self.new_zoom_sq[2] = int(ZWX)

            if int(event.y - PY * ZWY)>=0 and int(event.y + (1 - PY) * ZWY)<=self.Size[0]:
                self.new_zoom_sq[1] = int(event.y - PY * ZWY)
                self.new_zoom_sq[3] = int(event.y + (1 - PY) * ZWY)
            elif int(event.y + (1 - PY) * ZWY)>self.Size[0]:
                self.new_zoom_sq[1] = int(self.Size[0]-ZWY)
                self.new_zoom_sq[3] = int(self.Size[0])
            elif int(event.y - PY * ZWY)<0:
                self.new_zoom_sq[1] = 0
                self.new_zoom_sq[3] = int(ZWY)

            self.ratio = ZWX / self.final_width


        else:
            self.new_zoom_sq=[0,0,self.Vid.shape[1],self.Vid.shape[0]]
            self.ratio=self.Size[1]/self.final_width


        self.zoom_sq = self.new_zoom_sq
        self.zooming = False
        self.afficher()



"""
root = Tk()
root.geometry("+100+100")
Video_file=Class_Video.Video(File_name="D:/Post-doc/Experiments/Group_composition/Shoaling/Videos_conv_cut/Track_by_mark/Deinterlace/14_12_01.avi")
Video_file.Back[0]=True

im=cv2.imread("D:/Post-doc/Experiments/Group_composition/Shoaling/Videos_conv_cut/Track_by_mark/Deinterlace/14_12_01_background.bmp")
im=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
Video_file.Back[1]=im
interface = Scale(parent=root, boss=None, Video_file=Video_file)
root.mainloop()
"""