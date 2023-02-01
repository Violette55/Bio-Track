from tkinter import *
from AnimalTA.E_Post_tracking import Coos_loader_saver as CoosLS
from AnimalTA.A_General_tools import Class_Lecteur, Function_draw_mask as Dr, UserMessages, Class_stabilise
import numpy as np
import cv2
from scipy.signal import savgol_filter
from tkinter import filedialog
from PIL import ImageFont, ImageDraw, Image

class Lecteur(Frame):
    """This Frame allow the user to export a video that has been modified by AnimalTA.
    The video can be the original one, the stabilised one or with the trajectories displayed.
    The trajectories can be the original ones of the smoothed ones.
    The Identity of the individuals can also be displayed.
    """
    def __init__(self, parent, boss, main_frame, Vid, Video_liste, **kwargs):
        Frame.__init__(self, parent, bd=5, **kwargs)
        self.parent=parent
        self.main_frame=main_frame
        self.boss=boss
        self.Video_liste=Video_liste
        self.Vid=Vid
        self.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.Pos = []
        self.timer=0
        self.cache=False
        self.show_ID=False
        self.mask = Dr.draw_mask(Vid)
        self.kernel = np.ones((3, 3), np.uint8)

        #Import messages
        self.Language = StringVar()
        f = open(UserMessages.resource_path("AnimalTA/Files/Language"), "r", encoding="utf-8")
        self.Language.set(f.read())
        self.LanguageO = self.Language.get()
        self.Messages = UserMessages.Mess[self.Language.get()]
        f.close()

        Right_Frame=Frame(self)
        Right_Frame.grid(row=0, column=1)

        self.CheckVar=IntVar(value=0)

        #Whether the identity should appear on the video or not
        self.Show_ID_B=Button(Right_Frame, text=self.Messages["Save_Vid5"], command=self.change_show_ID)
        self.Show_ID_B.grid(row=0, sticky="w")

        #No modification except cropping
        Only_cropped=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=0, text=self.Messages["Save_Vid1"], command=self.change_type)
        Only_cropped.grid(row=1, sticky="w")


        #Cropping and stabilization
        if self.Vid.Stab[0]:
            Stab=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=1, text=self.Messages["Save_Vid2"], command=self.change_type)
            Stab.grid(row=2, sticky="w")

        #Greyscaled
        Grey=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=2, text=self.Messages["Track3"], command=self.change_type)
        Grey.grid(row=3, sticky="w")

        #Flicker correction
        if self.Vid.Track[1][7]:
            Flicker_Corr=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=3, text=self.Messages["Param14"], command=self.change_type)
            Flicker_Corr.grid(row=4, sticky="w")


        #Light correction
        if self.Vid.Track[1][7]:
            Light_Corr=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=4, text=self.Messages["Param10"], command=self.change_type)
            Light_Corr.grid(row=4, sticky="w")

        #Background substraction
        if self.Vid.Back[0]:
            Back=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=5, text=self.Messages["Names7"], command=self.change_type)
            Back.grid(row=5, sticky="w")

        #Threshold
        Thresh=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=6, text=self.Messages["Names1"], command=self.change_type)
        Thresh.grid(row=6, sticky="w")

        #Erosion
        if self.Vid.Track[1][1]>0:
            Erosion=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=7, text=self.Messages["Names2"], command=self.change_type)
            Erosion.grid(row=7, sticky="w")

        #Dilation
        if self.Vid.Track[1][2] > 0:
            Dilation=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=8, text=self.Messages["Names3"], command=self.change_type)
            Dilation.grid(row=8, sticky="w")

        #Display trajectories
        if self.Vid.Tracked:
            With_track=Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=9, text=self.Messages["Save_Vid3"], command=self.change_type)
            With_track.grid(row=9, sticky="w")

            self.Coos_brutes, self.who_is_here = CoosLS.load_coos(self.Vid)
            self.Coos=self.Coos_brutes.copy()
            self.NB_ind=len(self.Vid.Identities)

            #If the trajectories were smoothed, we propose to display smoothed trajectories
            if self.Vid.Smoothed[0]>0:
                self.smooth_coos()
                With_track_smooth = Checkbutton(Right_Frame, variable=self.CheckVar, onvalue=10, text=self.Messages["Save_Vid4"], command=self.change_type)
                With_track_smooth.grid(row=10, sticky="w")

            #Length of trajectories tail can also be modified
            self.tail_size = DoubleVar(value=10)
            self.max_tail = IntVar()
            self.max_tail.set(min([self.Vid.Frame_nb[1], 600]))
            self.Scale_tail = Scale(Right_Frame, from_=0, to=self.max_tail.get(), variable=self.tail_size, resolution=0.5, orient="horizontal", label=self.Messages["Control4"], command=self.modif_image)

        #Save the video
        self.Save_Vid_Button=Button(Right_Frame, text=self.Messages["GButton18"], command=self.save_vid, background="#6AED35")
        self.Save_Vid_Button.grid(row=11, column=0, columnspan=2)

        #Return to the main menu without saving
        self.Save_Return_Button=Button(Right_Frame, text=self.Messages["GButton11"], command=self.End_of_window, background="red")
        self.Save_Return_Button.grid(row=15, column=0, columnspan=2)

        #Video reader
        self.Vid_Lecteur= Class_Lecteur.Lecteur(self, self.Vid)
        self.Vid_Lecteur.grid(row=0, column=0, sticky="nsew")
        Grid.columnconfigure(self, 0, weight=1)  ########NEW
        Grid.rowconfigure(self, 0, weight=1)  ########NEW

        self.Vid_Lecteur.canvas_video.update()
        self.Vid_Lecteur.update_image(self.Vid_Lecteur.to_sub)
        self.Vid_Lecteur.bindings()
        self.Scrollbar=self.Vid_Lecteur.Scrollbar

        if self.Vid.Cropped[0]:
            self.to_sub = round(((self.Vid.Cropped[1][0]) / self.Vid_Lecteur.one_every))
        else:
            self.to_sub = 0


        self.loading_canvas=Frame(Right_Frame)
        self.loading_canvas.grid(row=13, column=0, columnspan=2)
        self.loading_state=Label(self.loading_canvas, text="")
        self.loading_state.grid(row=0, column=0)

        self.loading_bar=Canvas(self.loading_canvas, height=10)
        self.loading_bar.create_rectangle(0, 0, 400, self.loading_bar.cget("height"), fill="red")
        self.loading_bar.grid(row=0, column=1)

        self.bouton_hide = Button(Right_Frame, text=self.Messages["Do_track1"], command=self.hide)

    def change_show_ID(self):
        #Whether the identities should appear or not
        if self.show_ID:
            self.show_ID=False
            self.Show_ID_B.config(background="SystemButtonFace")
        else:
            self.show_ID=True
            self.Show_ID_B.config(background="grey")
        self.modif_image()

    def hide(self):
        #To minimise the window
        self.cache = True
        self.boss.update_idletasks()
        self.boss.overrideredirect(False)
        self.boss.state('iconic')

    def show_load(self):
        #Show the progress of the saving process
        self.loading_bar.delete('all')
        self.loading_bar.create_rectangle(0, 0, 400, self.loading_bar.cget("height"), fill="red")
        self.loading_bar.create_rectangle(0, 0, self.timer*400, self.loading_bar.cget("height"), fill="blue")
        self.loading_bar.update()

    def save_vid(self):
        #Export the video. To that aim, the video is played and every image is changed according to the parameters set by user.
        #The resulting video is saved in a file defined by user
        self.Vid_Lecteur.stop()
        self.Vid_Lecteur.unbindings()
        #Ask user where to save the video
        file_to_save = filedialog.asksaveasfilename(defaultextension=".avi", initialfile="Untitled_video.avi", filetypes=(("Video", "*.avi"),))

        if len(file_to_save)>0:
            self.bouton_hide.grid(row=20, column=0, columnspan=2)
            self.bouton_hide.grab_set()

            if self.Vid.Cropped[0]:
                start = self.Vid.Cropped[1][0]
                end = self.Vid.Cropped[1][1]
                self.Vid_Lecteur.Scrollbar.active_pos = int(self.Vid.Cropped[1][0] / self.Vid_Lecteur.one_every) - 1
            else:
                start = 0
                end = self.Vid.Frame_nb[1] - 1
                self.Vid_Lecteur.Scrollbar.active_pos=0

            frame_width = int(self.Vid.shape[1])
            frame_height = int(self.Vid.shape[0])
            frame_rate = self.Vid.Frame_rate[1]
            size = (frame_width, frame_height)
            result = cv2.VideoWriter(file_to_save, cv2.VideoWriter_fourcc(*'XVID'), frame_rate, size)

            for frame in range(int(start), int(end) + self.Vid_Lecteur.one_every):
                try:
                    self.timer = (frame - start) / ((end+ self.Vid_Lecteur.one_every )- start - 1)
                    self.show_load()
                    new_img=self.Vid_Lecteur.move1(aff=False)
                    new_img=cv2.cvtColor(new_img,cv2.COLOR_BGR2RGB)
                    result.write(new_img)

                except:
                    pass
            result.release()

            self.End_of_window()
            #In the end, the Frame is destroyed and we go back to main menu
            self.loading_bar.grab_release()
            if self.cache:
                self.boss.update_idletasks()
                self.boss.state('normal')
                self.boss.overrideredirect(True)

    def End_of_window(self):
        #Propoer close pf the Frame
        self.unbind_all("<Button-1>")
        try:
            self.Vid_Lecteur.proper_close()
        except:
            pass
        self.grab_release()
        self.main_frame.return_main()

    def modif_image(self, img=[], aff=True, **kwargs):
        #Change the image according to the parameters set by user
        if len(img) <= 10:
            new_img=np.copy(self.last_empty)
        else:
            self.last_empty = img
            new_img = np.copy(img)

        #Stabilise
        if self.CheckVar.get()>0 and self.Vid.Stab[0]:
            new_img = Class_stabilise.find_best_position(Vid=self.Vid, Prem_Im=self.Vid_Lecteur.Prem_image_to_show, frame=new_img, show=False)

        #Greyscale
        if self.CheckVar.get()>1 and self.CheckVar.get()<8:
            new_img=cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)

        #Correct flicker
        if self.CheckVar.get()>2 and self.Vid.Track[1][9]  and self.CheckVar.get()<8 and int(self.Scrollbar.active_pos) > round(((self.Vid.Cropped[1][0]) / self.Vid_Lecteur.one_every)):
            diff = int(self.Scrollbar.active_pos - (self.Vid.Cropped[1][0] / self.Vid_Lecteur.one_every))
            for elem in range(self.Scrollbar.active_pos - min(2, diff), self.Scrollbar.active_pos):
                new_img = cv2.cvtColor(self.Vid_Lecteur.update_image(elem, return_img=True), cv2.COLOR_BGR2GRAY)
                TMP_image_to_show2 = cv2.addWeighted(new_img, 0.5, TMP_image_to_show2, 1 - 0.5, 0)

        #Light_correction
        if self.CheckVar.get()>3 and self.Vid.Track[1][7]  and self.CheckVar.get()<8:
            grey = np.copy(new_img)
            if self.Vid.Mask[0]:
                bool_mask = self.mask[:, :, 0].astype(bool)
            else:
                bool_mask = np.full(grey.shape, True)
            grey2 = grey[bool_mask]

            # Inspired from: https://stackoverflow.com/questions/57030125/automatically-adjusting-brightness-of-image-with-opencv
            brightness = np.sum(grey2) / (255 * grey2.size)  # Mean value
            ratio = brightness / self.Vid_Lecteur.or_bright
            new_img = cv2.convertScaleAbs(grey, alpha=1 / ratio, beta=0)

        #Background
        if self.CheckVar.get()>4 and self.CheckVar.get()<8:
            if self.Vid.Back[0]:
                new_img = cv2.subtract(self.Vid.Back[1], new_img) + cv2.subtract(new_img, self.Vid.Back[1])

        if self.CheckVar.get()>5 and self.CheckVar.get()<8:
            if self.Vid.Back[0]:
                _, new_img = cv2.threshold(new_img, self.Vid.Track[1][0], 255, cv2.THRESH_BINARY)
            else:
                odd_val = int(self.Vid.Track[1][0]) + (1 - (int(self.Vid.Track[1][0]) % 2))
                new_img = cv2.adaptiveThreshold(new_img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, odd_val,10)

            # Mask
            if self.Vid.Mask[0]:
                new_img = cv2.bitwise_and(new_img, new_img, mask=self.mask)

        # Erosion
        if self.CheckVar.get()>6 and self.Vid.Track[1][1] > 0 and self.CheckVar.get()<8:
            new_img = cv2.erode(new_img,self.kernel, iterations=self.Vid.Track[1][1])

        # Dilation
        if self.CheckVar.get()>7 and self.Vid.Track[1][2] > 0 and self.CheckVar.get()<8:
            new_img = cv2.dilate(new_img, self.kernel, iterations=self.Vid.Track[1][2])

        #Show trajectories
        if self.CheckVar.get()>8:
            if self.Vid.Cropped[0]:
                to_remove = int(round((self.Vid.Cropped[1][0]) / self.Vid_Lecteur.one_every))
            else:
                to_remove = 0

            for ind in range(self.NB_ind):
                color = self.Vid.Identities[ind][2]
                for prev in range(min(int(self.tail_size.get() * self.Vid.Frame_rate[1]), int(self.Scrollbar.active_pos - to_remove))):
                    if int(self.Scrollbar.active_pos - prev) > round(((self.Vid.Cropped[1][0]) / self.Vid_Lecteur.one_every)) and int(self.Scrollbar.active_pos) <= round(((self.Vid.Cropped[1][1]) / self.Vid_Lecteur.one_every)):
                        if self.Coos[ind][int(self.Scrollbar.active_pos - 1 - prev - to_remove)][
                            0] != "NA" and \
                                self.Coos[ind][int(self.Scrollbar.active_pos - prev - to_remove)][
                                    0] != "NA":
                            TMP_tail_1 = (int(
                                self.Coos[ind][int(self.Scrollbar.active_pos - 1 - prev - to_remove)][
                                    0]),
                                          int(self.Coos[ind][
                                                  int(self.Scrollbar.active_pos - 1 - prev - to_remove)][1]))

                            TMP_tail_2 = (
                            int(self.Coos[ind][int(self.Scrollbar.active_pos - prev - to_remove)][0]),
                            int(self.Coos[ind][int(self.Scrollbar.active_pos - prev - to_remove)][1]))
                            new_img = cv2.line(new_img, TMP_tail_1, TMP_tail_2, color, max(int(3*self.Vid_Lecteur.ratio),1))

                if self.Scrollbar.active_pos >= round(((self.Vid.Cropped[1][0]) / self.Vid_Lecteur.one_every)) and self.Scrollbar.active_pos < int(((self.Vid.Cropped[1][1]) / self.Vid_Lecteur.one_every) + 1):
                    center = self.Coos[ind][self.Scrollbar.active_pos - to_remove]
                    if center[0] != "NA":
                        new_img = cv2.circle(new_img, (int(center[0]), int(center[1])),radius=max(int(4 * self.Vid_Lecteur.ratio), 1), color=color, thickness=-1)
                        if self.show_ID:
                            fontpath = "./simsun.ttc"
                            if self.Vid_Lecteur.ratio < 10:
                                font = ImageFont.truetype(fontpath, max(1, int(self.Vid_Lecteur.ratio * 30)))
                                stroke_width = max(1, int(self.Vid_Lecteur.ratio * 1))
                            else:
                                font = ImageFont.truetype(fontpath, 1)
                                stroke_width = 1
                            new_img = Image.fromarray(new_img)
                            draw = ImageDraw.Draw(new_img)
                            draw.text((int(float(center[0])+10*self.Vid_Lecteur.ratio), int(float(center[1])+10*self.Vid_Lecteur.ratio)), self.Vid.Identities[ind][1], font=font, fill=(255, 255, 255, 0), stroke_width=stroke_width)
                            draw.text((int(float(center[0])+10*self.Vid_Lecteur.ratio), int(float(center[1])+10*self.Vid_Lecteur.ratio)), self.Vid.Identities[ind][1], font=font, fill=(color ))
                            new_img = np.array(new_img)
        if aff:
            self.Vid_Lecteur.afficher_img(new_img)
        else:
            return(new_img)

    def change_type(self):
        #Update the options available according to what kind of video the user want as an output
        if self.CheckVar.get() > 8: #If user wants trajectories to be visible, we allow to choose for tail size
            self.Scale_tail.grid(row=1, column=1,rowspan=10)
        elif self.Vid.Tracked:
            self.Scale_tail.grid_forget()
        if self.CheckVar.get()==9:#If user wants original trajectories
            self.Coos=self.Coos_brutes
        elif self.CheckVar.get()==10:#If user wants smoothed trajectories
            self.Coos=self.Coos_smoothed
        self.modif_image()




    def smooth_coos(self):
        #Apply the smoothing filter to the trajectories
        self.Coos_smoothed=self.Coos.copy()
        for ind in range(len(self.Coos_brutes)):
            ind_coo=[[np.nan if val=="NA" else val for val in row ] for row in self.Coos_brutes[ind]]
            ind_coo=np.array(ind_coo, dtype=np.float)
            for column in range(2):
                Pos_NA = np.where(np.isnan(ind_coo[:, column]))[0]
                debuts = [0]
                fins = []
                if len(Pos_NA) > 0:
                    diff = ([Pos_NA[ele] - Pos_NA[ele - 1] for ele in range(1, len(Pos_NA))])
                    fins.append(Pos_NA[0])
                    for moment in range(len(diff)):
                        if diff[moment] > 1:
                            fins.append(Pos_NA[moment + 1])
                            debuts.append(Pos_NA[moment])
                    debuts.append(Pos_NA[len(Pos_NA) - 1])
                    fins.append(len(ind_coo[:, column]))

                    for seq in range(len(debuts)):
                        if len(ind_coo[(debuts[seq] + 1):fins[seq], column]) >= self.Vid.Smoothed[0]:
                            ind_coo[(debuts[seq] + 1):fins[seq], column] = savgol_filter(
                                ind_coo[(debuts[seq] + 1):fins[seq], column], self.Vid.Smoothed[0],
                                self.Vid.Smoothed[1], deriv=0, delta=1.0, axis=- 1,
                                mode='interp', cval=0.0)
                else:
                    ind_coo[:, column] = savgol_filter(ind_coo[:, column],
                                                                       self.Vid.Smoothed[0],
                                                                       self.Vid.Smoothed[1], deriv=0, delta=1.0, axis=- 1,
                                                                       mode='interp', cval=0.0)
            ind_coo=ind_coo.astype(np.float)
            ind_coo=ind_coo.tolist()
            ind_coo=[["NA" if np.isnan(val) else val for val in row] for row in ind_coo]
            self.Coos_smoothed[ind]=ind_coo

    def pressed_can(self, Pt, Shift=False):
        pass

    def moved_can(self, Pt):
        pass

    def released_can(self, Pt):
        pass