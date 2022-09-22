from tkinter import *
import cv2
import PIL.Image, PIL.ImageTk
import decord
import numpy as np
import math
import random
from AnimalTA import UserMessages, Function_draw_mask as Dr, User_help


class Mask(Frame):
    """In this Frame, the user will have the possibility to indicate the arenas in which the targets can be found. It will later work as a mask and facilitate target's identification."""
    def __init__(self, parent, boss, main_frame, proj_pos, Video_file,portion=False, **kwargs):
        Frame.__init__(self, parent, bd=5, **kwargs)
        self.parent=parent
        self.proj_pos=proj_pos
        self.main_frame=main_frame
        self.boss=boss
        self.portion=portion
        self.grid(row=0,column=0,rowspan=2,sticky="nsew")

        if self.portion:#If we are just changing the arenas for a part of the video (during corrections)
            Grid.columnconfigure(self.parent, 0, weight=1)
            Grid.rowconfigure(self.parent, 0, weight=1)
            self.parent.geometry("1200x750")

        #Import messages
        self.Vid = Video_file
        self.Language = StringVar()
        f = open("Files/Language", "r")
        self.Language.set(f.read())
        self.LanguageO = self.Language.get()
        f.close()
        self.Messages = UserMessages.Mess[self.Language.get()]

        #Relative to size of the image
        self.zoom_sq=[0,0,self.Vid.shape[1],self.Vid.shape[0]]
        self.zoom_strength = 0.3


        self.liste_points=[]
        ##This is a list of all the Arenas, the structure is the following:
        #[
        # [[Xs], [Ys], (R, G, B), Shape], --> Arena 1, Xs and Ys are the coordinates of the points used to define the arenas. Shape can be: ellipse, rectangle or polygon
        # [[Xs], [Ys], (R, G, B), Shape], --> Arena 2
        # ...]

        self.Pt_select=[]
        #Indicate which is the selected point. Structure:
        #[ArenaID, PtID] with IDs being integers from 0

        #If a background was defined, the user will draw over it.
        if self.Vid.Back[0]:
            self.background=self.Vid.Back[1]
        else:#If not, we take the first frame as image (after cropping).
            Which_part = 0
            if self.Vid.Cropped[0]:
                if len(self.Vid.Fusion) > 1:  # Si on a plus d'une video
                    Which_part = [index for index, Fu_inf in enumerate(self.Vid.Fusion) if Fu_inf[0] <= self.Vid.Cropped[1][0]][-1]

            self.capture = decord.VideoReader(self.Vid.Fusion[Which_part][1])
            self.background = self.capture[self.Vid.Cropped[1][0] - self.Vid.Fusion[Which_part][0]].asnumpy()
            del self.capture
            self.background=cv2.cvtColor(self.background,cv2.COLOR_RGB2GRAY)

        self.image_to_show=np.copy(self.background)
        self.Shape_ar = IntVar(self)# When opening the window, which kind of shape should be first selected?
        try:
            self.Shape_ar.set(self.main_frame.mask_shape)#If there was info about that, we take the saved kind of shape
        except:
            self.Shape_ar.set(1)#Else, we put the first one (ellipse)
        self.view_mask = False

        # Video name and option menu to jump from one video to the other:
        if not self.portion:
            self.canvas_video_name = Canvas(self, bd=2, highlightthickness=1, relief='flat')
            self.canvas_video_name.grid(row=0, column=0, sticky="nsew")

            self.dict_Names = {self.main_frame.list_projects[i].Video.Name: self.main_frame.list_projects[i] for i in
                               range(0, len(self.main_frame.list_projects))}

            self.liste_videos_name = [V.Name for V in self.main_frame.liste_of_videos]
            holder = StringVar()
            holder.set(self.Vid.Name)
            self.bouton_change_vid = OptionMenu(self.canvas_video_name, holder, *self.dict_Names.keys(),
                                                command=self.change_vid)
            self.bouton_change_vid.config(font=("Arial", 15))
            self.bouton_change_vid.grid(row=0, column=0, sticky="we")
        Grid.rowconfigure(self, 0, weight=1)  ########NEW


        #Canvas to show img
        self.canvas_img = Canvas(self, bd=0, highlightthickness=0, relief='ridge')
        self.canvas_img.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.canvas_img.bind("<Control-1>", self.Zoom_in)
        self.canvas_img.bind("<Control-3>", self.Zoom_out)
        self.canvas_img.bind('<Return>', self.New_ar_mask)
        self.canvas_img.bind("<Button-1>", self.callback_mask)
        self.canvas_img.bind("<B1-Motion>", self.move_pt_mask)
        self.canvas_img.bind("<Key>", self.suppress_mask)
        Grid.columnconfigure(self, 0, weight=1)  ########NEW
        Grid.rowconfigure(self, 1, weight=1)  ########NEW
        self.ratio=1
        self.final_width=750
        self.Size = self.Vid.shape
        self.canvas_img.bind("<Configure>", self.afficher)

        #Help user and parameters
        self.HW=User_help.Help_win(self.parent, default_message=self.Messages["Mask10"])
        self.HW.grid(row=0, column=1,sticky="nsew")

        ##Parameters
        self.canvas_User_params = Canvas(self.parent, width=200, height=0, bd=0, highlightthickness=0, relief='ridge')
        self.canvas_User_params.grid(row=1,column=1, sticky="nsew")

        #Widgets
        self.bouton_efface = Button(self.canvas_User_params, text=self.Messages["Mask2"], fg="black", command=self.remove_ind)

        self.bouton_add_mask_ar = Button(self.canvas_User_params, text=self.Messages["Mask7"], fg="black", command=self.New_ar_mask)
        self.bouton_remove_mask_ar = Button(self.canvas_User_params, text=self.Messages["Mask8"], fg="black",
                                            command=self.Remove_ar_mask)
        self.bouton_remove_mask_one_ar = Button(self.canvas_User_params, text=self.Messages["Mask9"], fg="black",
                                            command=self.suppress_one_ar_mask)

        self.bouton_validate = Button(self.canvas_User_params, text=self.Messages["Validate"], background="#6AED35", fg="black", command=self.validate)
        self.B_Validate_NContinue=Button(self.canvas_User_params, text=self.Messages["Validate_NC"],bg="#6AED35", command=lambda: self.validate(follow=True))

        self.NB_Arenas=StringVar(value="0")
        Label_nb_Arenas=Label(self.canvas_User_params, text=self.Messages["Mask11"])
        nb_Arenas = Label(self.canvas_User_params, textvariable=self.NB_Arenas)

        self.Label_shapes = Label(self.canvas_User_params, text=self.Messages["Mask3"])

        self.shape1 = Radiobutton(self.canvas_User_params, text=self.Messages["Mask4"],indicatoron=0, width=25, variable=self.Shape_ar, value=1,
                                  command=lambda : self.Change_SM_val(self.Shape_ar,1))

        self.shape2 = Radiobutton(self.canvas_User_params, text=self.Messages["Mask5"],indicatoron=0, width=25,
                                  variable=self.Shape_ar, value=2, command=lambda : self.Change_SM_val(self.Shape_ar,2))

        self.shape3 = Radiobutton(self.canvas_User_params, text=self.Messages["Mask6"],indicatoron=0, width=25,
                                  variable=self.Shape_ar, value=3, command=lambda : self.Change_SM_val(self.Shape_ar,3))



        #Grids
        Label_nb_Arenas.grid(row=0, column=0, sticky="e")
        nb_Arenas.grid(row=0, column=1, sticky="w")

        self.Label_shapes.grid(row=1, columnspan=2)
        self.shape1.grid(row=2, columnspan=2)
        self.shape2.grid(row=3, columnspan=2)
        self.shape3.grid(row=4, columnspan=2)

        self.bouton_add_mask_ar.grid(row=5, column=0)
        self.bouton_remove_mask_one_ar.grid(row=5, column=1)
        self.bouton_remove_mask_ar.grid(row=6, columnspan=2)
        self.bouton_efface.grid(row=7, columnspan=2)
        self.bouton_validate.grid(row=8, columnspan=2,sticky="nsew")
        if not self.portion:
            self.B_Validate_NContinue.grid(row=9,columnspan=2, sticky="ewsn")

        self.canvas_User_params.grid_rowconfigure((0,1,2,3,4,5,6,7,8,9), weight=3, uniform="row")

        self.canvas_img.update()
        self.final_width = self.canvas_img.winfo_width()
        self.ratio = self.Size[1] / self.final_width

        self.canvas_img.focus_force()

        self.Which_ar = None
        if not self.Vid.Mask[0]:#If there were no arenas defined yet
            self.liste_points = [[[], [], (0, 0, 0), 0]]
        else:
            self.liste_points = self.Vid.Mask[1] # else, we draw the existing shapes
            self.dessiner_Formes()
            if len(self.liste_points)>0:#If there were no shapes (i.e. user went in this option but did not change anything)
                self.Which_ar=len(self.liste_points)-1
            else:
                self.liste_points = [[[], [], (0, 0, 0), 0]]
        self.afficher()

    def Zoom_in(self, event):
        #Zoom in in the image
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
            self.dessiner_Formes()
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
                self.new_zoom_sq[3] = self.new_zoom_sq[1] + int(ZWY)

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
        self.dessiner_Formes()
        self.afficher()

    def validate(self, follow=False):
        #Save the information about arenas defined and delete this frame. If follow=True, a new frame with the next video is opened
        self.Vid.Mask[0] = True# The mask is done
        if len(self.liste_points)>0 and not len(self.liste_points[len(self.liste_points)-1][0])>1:
            self.liste_points.pop()# We remove the last point (not associated with coordinates yet)

        if not self.portion:
            self.boss.update_mask()
            self.Vid.Mask[1] = self.liste_points
            #We count the number of Arenas defined
            mask = Dr.draw_mask(self.Vid)
            Arenas, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if len(Arenas) < len(self.Vid.Track[1][6]):#We uodate the number of arenas to be tracked
                self.Vid.Track[1][6]=self.Vid.Track[1][6][0:(len(Arenas))]
            elif len(Arenas) > len(self.Vid.Track[1][6]):
                self.Vid.Track[1][6] = self.Vid.Track[1][6]+ [self.Vid.Track[1][6][-1]]*(len(Arenas) - len(self.Vid.Track[1][6]))

        if self.portion:
            self.boss.PortionWin.grab_set()

        self.End_of_window()
        if follow and self.proj_pos < len(self.main_frame.list_projects)-1:
            self.main_frame.list_projects[self.proj_pos + 1].mask_vid()

        self.main_frame.mask_shape=self.Shape_ar.get()

    def change_vid(self, vid):
        #Jump from one video to the other
        self.End_of_window()
        self.dict_Names[vid].mask_vid()

    def End_of_window(self):
        #Close the Frame properly
        self.unbind_all("<Button-1>")
        self.grab_release()
        self.canvas_User_params.grid_forget()
        self.canvas_User_params.destroy()
        self.HW.grid_forget()
        self.HW.destroy()
        if not self.portion:
            self.boss.update()
            self.main_frame.return_main()
        if self.portion:
            self.parent.destroy()

    def suppress_one_ar_mask(self):
        #Supress the current arena
        if len(self.Pt_select) > 0 : #If there are no point selected yet, nothing happen
            if len(self.liste_points)<2:#If there was only one arena, the list of points is emptied
                self.liste_points = [[[], [], (0,0,0) ,0]]
                self.Which_ar=None
            else:#Else, only the current arena is removed
                self.liste_points[self.Pt_select[0]]=[[],[],(0,0,0),0]

            self.Pt_select=[]
            self.dessiner_Formes()#We show the arenas
            self.afficher()

    def Remove_ar_mask(self):
        #Remove all the arenas
        self.liste_points = [[[], [], (0,0,0),0]]
        self.image_to_show = self.background
        self.Pt_select=[]
        self.afficher()
        self.Which_ar = None

    def suppress_mask(self, event):
        #Remove the selected point
        if event.keysym == "Delete" and len(self.Pt_select) > 0:
            del self.liste_points[self.Pt_select[0]][0][self.Pt_select[1]]
            del self.liste_points[self.Pt_select[0]][1][self.Pt_select[1]]
            self.Pt_select=[]
            self.dessiner_Formes()#Show the result
            self.afficher()

    def move_pt_mask(self, event):
        #Move a selected point
        if len(self.Pt_select) > 0:
            self.liste_points[self.Pt_select[0]][0][self.Pt_select[1]]=event.x * self.ratio + self.zoom_sq[0]
            self.liste_points[self.Pt_select[0]][1][self.Pt_select[1]]=event.y * self.ratio + self.zoom_sq[1]
            self.dessiner_Formes()#Show the result
            self.afficher()

    def New_ar_mask(self, b="_"):
        #Create a new arena (i.e. indicates that the last one is finished)
        if self.Which_ar != None:
            if len(self.liste_points[self.Which_ar][0])<2:#If the current arena was not defined (i.e. user add les than two points)
                self.liste_points[self.Which_ar]=[[],[], self.random_color(),0] #We continue on the same, just remove the point if there was one and change the color
            else: #If not, we create a new arena
                self.Which_ar = len(self.liste_points)
                self.liste_points.append([[], [],self.random_color(),self.Shape_ar.get()])

        self.Pt_select=[]
        self.dessiner_Formes()
        self.afficher()

    def dessiner_Formes(self):
        #Prepare empty image
        self.image_to_show = cv2.cvtColor(self.background, cv2.COLOR_GRAY2RGB)

        #Draw the shapes
        for j in range(len(self.liste_points)):
            if self.liste_points[j][3]==1:
                if len(self.liste_points[j][0]) > 1:
                    self.image_to_show, _ = Dr.Draw_elli(self.image_to_show, self.liste_points[j][0], self.liste_points[j][1],self.liste_points[j][2],thick=round(2*self.ratio))
                for i in range(len(self.liste_points[j][0])):
                    self.image_to_show = cv2.circle(self.image_to_show,(int(self.liste_points[j][0][i]), int(self.liste_points[j][1][i])), round(4*self.ratio),self.liste_points[j][2], -1)

            elif self.liste_points[j][3]==2:
                if len(self.liste_points[j][0])>1:
                    self.image_to_show, _= Dr.Draw_rect(self.image_to_show, self.liste_points[j][0], self.liste_points[j][1],self.liste_points[j][2],thick=round(2*self.ratio))
                for i in range(len(self.liste_points[j][0])):
                    self.image_to_show = cv2.circle(self.image_to_show,(int(self.liste_points[j][0][i]), int(self.liste_points[j][1][i])), round(4*self.ratio),self.liste_points[j][2], -1)

            elif self.liste_points[j][3]==3:
                if len(self.liste_points[j][0])>1:
                    self.image_to_show, _ = Dr.Draw_Poly(self.image_to_show, self.liste_points[j][0], self.liste_points[j][1],self.liste_points[j][2],thick=round(2*self.ratio))
                for i in range(len(self.liste_points[j][0])):
                    self.image_to_show = cv2.circle(self.image_to_show,(int(self.liste_points[j][0][i]), int(self.liste_points[j][1][i])), round(4*self.ratio),self.liste_points[j][2], -1)

        if len(self.Pt_select) > 0:#Selected point is highlighted
            self.image_to_show = cv2.circle(self.image_to_show, (
            int(self.liste_points[self.Pt_select[0]][0][self.Pt_select[1]]),
            int(self.liste_points[self.Pt_select[0]][1][self.Pt_select[1]])), round(4*self.ratio), self.liste_points[self.Pt_select[0]][2], -1)

            self.image_to_show = cv2.circle(self.image_to_show,(int(self.liste_points[self.Pt_select[0]][0][self.Pt_select[1]]), int(self.liste_points[self.Pt_select[0]][1][self.Pt_select[1]])), round(4*self.ratio),(0,0,0), round(2*self.ratio))

    def callback_mask(self, event):
        event.x=event.x * self.ratio + self.zoom_sq[0]
        event.y = event.y * self.ratio + self.zoom_sq[1]

        if self.Which_ar == None:#If it is the first point created
            self.Which_ar = 0
            self.liste_points[self.Which_ar][2]=self.random_color()
            self.liste_points[self.Which_ar][3] = self.Shape_ar.get()

        else:# We check if the user clicked on an existing point
            self.Pt_select=[]
            for j in range(len(self.liste_points)):
                if len(self.Pt_select)>0:
                    break
                for i in range(len(self.liste_points[j][0])):
                    if math.sqrt((self.liste_points[j][0][i]-event.x)**2 + (self.liste_points[j][1][i]-event.y)**2)<7:
                        self.Pt_select=(j,i)#Point selectionné viens de l'arene j et c'est le point numero i
                        self.Which_ar=j
                        self.Shape_ar.set(self.liste_points[j][3])
                        break

        #If we did not press on an existing point, we add a new one
        if len(self.Pt_select)<1:
            self.liste_points[self.Which_ar][0].append(event.x)
            self.liste_points[self.Which_ar][1].append(event.y)
            self.Pt_select=(self.Which_ar,len(self.liste_points[self.Which_ar][0])-1)
            if len(self.liste_points[self.Which_ar][0])<2:
                self.liste_points[self.Which_ar][3]=self.Shape_ar.get()

        self.dessiner_Formes()#Show the result
        self.afficher()

    def Change_SM_val(self, var, val):
        #Change the sahpe of an existing shape
        var.set(val)
        if len(self.Pt_select)>0:
            self.liste_points[self.Pt_select[0]][3]=val
        elif self.Which_ar!=None:
            self.liste_points[self.Which_ar][3] = val

        self.dessiner_Formes()
        self.afficher()

    def afficher(self, *args):
        #Show the image
        best_ratio = max(self.Size[1] / (self.canvas_img.winfo_width()),
                         self.Size[0] / (self.canvas_img.winfo_height()))
        prev_final_width=self.final_width
        self.final_width=int(self.Size[1]/best_ratio)
        self.ratio=self.ratio*(prev_final_width/self.final_width)

        self.image_to_show2 = self.image_to_show[self.zoom_sq[1]:self.zoom_sq[3], self.zoom_sq[0]:self.zoom_sq[2]]
        self.TMP_image_to_show2 = cv2.resize(self.image_to_show2,
                                             (self.final_width, int(self.final_width * (self.Size[0] / self.Size[1]))))
        self.image_to_show3 = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.TMP_image_to_show2))
        self.canvas_img.create_image(0, 0, image=self.image_to_show3, anchor=NW)
        self.canvas_img.config(width=self.final_width, height=int(self.final_width * (self.Size[0] / self.Size[1])))

    def draw_binaries(self, img):
        #Draw a binary image (the mask)
        for i in range(len(self.liste_points)):
            New_col = (255)
            if len(self.liste_points[i][0]) > 0:
                if self.liste_points[i][3] == 1:
                    img, _ = Dr.Draw_elli(img, self.liste_points[i][0],
                                                         self.liste_points[i][1], New_col, -1)

                elif self.liste_points[i][3] == 2 and len(self.liste_points[i][0]) > 1:
                    img, _ = Dr.Draw_rect(img, self.liste_points[i][0],
                                                         self.liste_points[i][1], New_col, -1)

                elif self.liste_points[i][3] == 3 and len(self.liste_points[i][0]) > 1:
                    img, _ = Dr.Draw_Poly(img, self.liste_points[i][0],
                                                         self.liste_points[i][1], New_col, -1)

        if np.any(img[:,:]>0):
            Arenas, _ = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            self.NB_Arenas.set(len(Arenas))
        else:
            self.NB_Arenas.set(1)
        return(img)

    def remove_ind(self):
        #Show the binary image if it wasn't visible, else return to normal view
        if not self.view_mask:
            self.New_ar_mask()
            self.image_to_show = np.zeros_like(self.background)
            self.image_to_show =self.draw_binaries(self.image_to_show)

            self.view_mask=True
            self.afficher()
        else:
            self.image_to_show = cv2.cvtColor(self.background, cv2.COLOR_GRAY2RGB)
            self.view_mask = False
            self.dessiner_Formes()
            self.afficher()

    def random_color(self):
        #Choose a random color to be assigned to the shape
        levels = range(32, 256, 32)
        levels = str(tuple(random.choice(levels) for _ in range(3)))
        return (tuple(int(s) for s in levels.strip("()").split(",")))


'''
root = Tk()
root.geometry("+100+100")
Video_file=Class_Video.Video(File_name="D:/Post-doc/Experiments/Group_composition/Shoaling/Videos_conv_cut/Track_by_mark/Deinterlace/14_12_01.avi")
Video_file.Back[0]=True
im=cv2.imread("D:/Post-doc/Experiments/Group_composition/Shoaling/Videos_conv_cut/Track_by_mark/Deinterlace/14_12_01_background.bmp")
im=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
Video_file.Back[1]=im
interface = Mask(parent=root, main_frame=root,proj_pos=1, boss=None, Video_file=Video_file)
root.mainloop()
'''