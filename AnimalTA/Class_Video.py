import numpy as np
import ntpath
from AnimalTA.A_General_tools import UserMessages, Class_stabilise, Function_draw_mask as Dr, Message_simple_question as MsgBox
import os
import cv2
import pickle


# Import language
f = open(UserMessages.resource_path(os.path.join("AnimalTA","Files","Language")), "r", encoding="utf-8")
Language=(f.read())
f.close()
Messages = UserMessages.Mess[Language]

class Video:
    '''
    This class is used to save the information about the videos.
    '''
    def __init__(self, File_name, Folder, shape=None, nb_fr=None, fr_rate=None):
        self.File_name=File_name #The name and path to the video file
        self.Folder=Folder #The folder in which the project is stored
        self.Name = ntpath.basename(self.File_name)#The name of the video
        self.User_Name=self.Name

        if shape==None:#If we did not furnish the file data (i.e. if the video was converted)
            capture=cv2.VideoCapture(self.File_name)#We choose to use Opencv and not decord here because opencv is much faster at initiation. But, opencv is not calculating correcty the number of frames in videos, also this value is recalculated later.
            shape=(int(capture.get(4)),int(capture.get(3)))#The width/height of the frames
            nb_fr = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            fr_rate = capture.get(cv2.CAP_PROP_FPS)

        self.shape = shape
        self.or_shape = self.shape#In old version, it was not possible to crop spacially the videos, this is to avoid problems of compatibility

        self.Frame_nb=[nb_fr,nb_fr]  #The number of frame inside the file. 0 is the original number, 1 is the number after concatenation
        self.Frame_rate=[fr_rate,fr_rate]#First is the original fps, second the modified one (user option)

        self.corrected = False #When the video is implemented, the trackings have not been corrected
        self.Fusion=[[0,self.File_name]] #If videos are concatenated, the will be save here. The patern is [[0, name of 1st video],[number of frame before the second video (duration of 1st video) + 1, name of 2nd video],[number of frame before the thrid video (duration of 1st video + 2nd video)+1, name of 3rd video],...]

        self.Rotation=0

        self.Cropped=[False,[0,self.Frame_nb[0]-1]]#0 whether the video has been cropped or not, 1 where the video begins and stops after cropping [frame at the beginning of the video, frame at the end of the video]
        self.Cropped_sp=[False,[0,0,self.or_shape[0],self.or_shape[1]]]#0 whether the video has been spacialy cropped or not, 1 x0, y0, x1 and y1 coordinates of the cropping rectangle
        self.Stab = [False,None,[30,3,0.05,200]] #0: False if no stabilisation, true if stabilisation. 1: array with the coordinates for the stabilisation.
        self.Back = [0,[]] #0: 0=Adaptive background, 1=subtract back, 2= Dynamical back. 1 Background used with this video.
        self.Mask = [False,[]] #0: False if no mask defined,True if so. 1 List of shapes used to draw the mask.
        self.Entrance=[]#It is a list of contours used to draw then entrance areas in case of unknown number of targets
        self.Scale=[1,"px"] # The scale and its unit
        self.liste_of_colors=[] # The list of colors used to draw the targets and their trajectories
        self.Tracked=False #Whether the video has already been tracked or not
        self.Events=[]

        self.Track=[False,[50,0,0,[0.0001,5000],[0,1],500,[1], False, False, False, [0,0,0]]]
        #0 Tresh , 1 Erosion ,2 Dilation ,3 Area ,4 Compact ,5 Distance (px), 6 number of targets, 7 Apply light correction, 8 Is fixed number of targets, 9 flickering correction, 10 kind of background subtraction [0 = greyscaled, 1=colored)][0=mean, 1=darker, 2=lighter][0=absoltue, 1=relative].
        self.Smoothed=[0,0]
        self.Analyses=[0,[[] for n in self.Track[1][6]],[0,1,2],0,[[],[],[]]]#0 = seuil de mouvement, 1=list of elements of interest (one [] per arena at the implementation), 2=style d'exploration(2.0 = type, 2.1=surface, 2.2=parametres pour cercles, 3=dist_nei, 4=Correction of deformation: 4.0= deformation matrix, 4.1=points in ref image, 4.2=points position after correction)

        self.Color_profiles="default.CPR"

    def check_coos(self):
        if self.User_Name == self.Name:
            file_name = self.Name
            point_pos = file_name.rfind(".")
            if file_name[point_pos:].lower() != ".avi":  # Old versions of AnimalTA did not allow to rename or duplicate the videos, the name of the video was the file name without the ".avi" extension
                file_name = self.User_Name
            else:
                file_name = file_name[:point_pos]
        else:
            file_name = self.User_Name

        file_tracked_not_corr = os.path.join(self.Folder, "coordinates", file_name + "_Coordinates.csv")
        file_tracked_corr = os.path.join(self.Folder, "corrected_coordinates", file_name + "_Corrected.csv")

        prev_track=self.Tracked


        if os.path.isfile(file_tracked_not_corr) or os.path.isfile(file_tracked_corr):
            self.Tracked = True
        else:
            self.Tracked = False


        return([prev_track and not self.Tracked, file_tracked_not_corr,file_tracked_corr])


    def clear_files(self):
        '''If we need to remove the tracking that were done (i.e. if the user want to change tracking parameters while the tracking has already be done)'''

        if self.User_Name == self.Name:
            file_name = self.Name
            point_pos = file_name.rfind(".")
            if file_name[point_pos:].lower() != ".avi":
                file_name = self.User_Name
            else:
                file_name = file_name[:point_pos]
        else:
            file_name = self.User_Name

        # Suppress coordinates from tracking
        files_tracked = [
            os.path.join(self.Folder, "coordinates", file_name + "_Coordinates.csv"),
            os.path.join(self.Folder, "corrected_coordinates", file_name + "_Corrected.csv")
        ]


        while True:
            try:
                for file in files_tracked:
                    if os.path.isfile(file):
                        os.rename(file,file)
                    if os.path.isfile(file):
                        os.remove(file)

                self.Tracked=False
                self.Smoothed=[0,0]
                self.Analyses=[0,[[] for n in self.Track[1][6]],[0,1,2],0,[[],[],[]]]#0 = movement threshold, 1=list of elements of interest, 2=exploration kind of measurement(2.0 = type, 2.1=area, 2.2=parameter for circular mesh), 3=inter-individual threshold

                try:
                    if not self.Track[1][8]:#If the number of targets was unknown, we remove put it back to 0
                        self.Track[1][6]=[0]*len(self.Track[1][6])
                except:
                    pass

                return True

            except PermissionError as e:
                question = MsgBox.Messagebox(parent=self, title=Messages["TError"],
                                             message=Messages["Error_Permission"].format(e.filename), Possibilities=[Messages["Retry"], Messages["Cancel"]])
                self.wait_window(question)
                answer = question.result
                if answer!=0:
                    return False



    def make_back(self,  Nb_Back=10):

        '''This function is used to create a background in which the moving targets are erased.
        It works by calculating the median value of all the pixels for N=Nb_Back images taken at regular intervals.
        '''

        Liste_Images=[]
        i = 0
        #intervals=how much space between two frame we will use
        if self.Cropped[0]:
            if round((self.Cropped[1][1]-self.Cropped[1][0]) / Nb_Back)>0:
                intervals=round((self.Cropped[1][1]-self.Cropped[1][0]) / Nb_Back)
            else:
                intervals=1
            Rank=range(self.Cropped[1][0], self.Cropped[1][1], intervals)
        else:
            if int(self.Frame_nb[0]/ Nb_Back)>0:
                intervals=round((self.Cropped[1][1]-self.Cropped[1][0]) / Nb_Back)
            else:
                intervals=1
            Rank=range(0, self.Frame_nb[0], intervals)

        Capture = cv2.VideoCapture(self.Fusion[0][1])

        for image_ID in Rank:
            Which_part=0
            if len(self.Fusion) > 1:  # If the video results from concatenation
                Which_part = [index for index, Fu_inf in enumerate(self.Fusion) if Fu_inf[0] <= image_ID][-1]
                Capture.release()
                Capture = cv2.VideoCapture(self.Fusion[Which_part][1])

            Capture.set(cv2.CAP_PROP_POS_FRAMES, int(image_ID-self.Fusion[Which_part][0]))
            _, frame=Capture.read()

            if self.Rotation == 1:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif self.Rotation == 2:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            if self.Rotation == 3:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

            if self.Cropped_sp[0]:
                frame=frame[self.Cropped_sp[1][0]:self.Cropped_sp[1][2], self.Cropped_sp[1][1]:self.Cropped_sp[1][3]]

            if i==0:
                Prem_img=np.copy(frame)

            if self.Stab[0] and i>0:#If the user choose the stabilization tool
                frame = Class_stabilise.find_best_position(Vid=self, Prem_Im=Prem_img, frame=frame, show=False)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            Liste_Images.append(np.copy(frame))
            i += 1
        Capture.release()

        Liste_Images[0] = np.median(Liste_Images, axis=0)#We calculate the median value for all pixels
        Liste_Images[0]=Liste_Images[0].astype("uint8")

        self.Back[0]=1
        self.Back[1] = Liste_Images[0]#Save the background

    def draw_entrance(self, distance_max=20):#If no entrance, we propose the external borders of the arena as entrance area.
        self.Entrance=[]
        mask = Dr.draw_mask(self)
        Arenas, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        Arenas = Dr.Organise_Ars(Arenas)

        for Ar in Arenas:
            empty=np.zeros([self.shape[0],self.shape[1],1], np.uint8)
            empty=cv2.drawContours(empty,[Ar],-1,255,min(1,int(round(distance_max*float(self.Scale[0])))*4))
            empty = cv2.drawContours(empty, [Ar], -1, 0,-1)
            cnts,_=cv2.findContours(empty, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            self.Entrance.append(cnts)


    def effacer_back(self):
        #Remove the background associated with the video
        self.Back[0]=0
        self.Back[1]=[]

    def effacer_mask(self):
        # Remove the arenas associated with the video
        self.Mask[0]=False
        self.Mask[1]=[]
        self.Track[1][6] = [1]
        self.Entrance = []


