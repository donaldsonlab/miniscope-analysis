import numpy as np
import pandas as pd
import io as io
import re
import math
import seaborn as sns
import os
import Cleversys_Parser as cp


##aligning the minicam and miniscope feeds, using miniscope frames as reference
#need to make these arguments all optional so people can plug in whatever they recorded
def align_feeds(miniscope_ts, minicam1_ts, minicam2_ts):
    ''' takes the timestamp .csv files for your minicam and miniscope feeds and lines up each minicam feeds' frames to the closest miniscope timestamp
    input timeStamp.csv files from all feeds from trial
    return align_df = a dataframe with columns for miniscope timestamps and their corresponding miniscope frames and closest minicam frames'''
    scopets = pd.read_csv(miniscope_ts)
    cam1ts = pd.read_csv(minicam1_ts)
    cam2ts = pd.read_csv(minicam2_ts)

    scopecam1 = pd.merge_asof(scopets, cam1ts, on = "Time Stamp (ms)", direction = "nearest", suffixes = ['','_cam1'])
    
    align_df = pd.merge_asof(scopecam1, cam2ts, on = "Time Stamp (ms)", direction = "nearest", suffixes = ['','_cam2'])
    align_df = align_df[align_df.columns.drop(list(align_df.filter(regex='Buffer Index')))]

    return align_df

##aligning behavioral analysis output to both minicam and miniscope frames (just cleversys for now, next work on DLC +/- MARS output)
#take the cleversys output (whose original frames should be equivalent to those from one of your minicams, as that camera was the source for cleversys)
def align_cleversys(cs_txt, align_df, cam_num):
    ''' input: 
    cs_txt = .txt output from cleversys
    align_df = output df from align_feeds function above
    cam_num = minicam # that you ran thru cleversys (top view)

    return align_cs = df where each row is the closest minicam frame to every miniscope frame and the corresponding cleversys tracking data for that frame'''
    #run dave's parser on your cleversys txt, only return df
    cs_df, _, _, _ = cp.parse(cs_txt)
    
    #edit this depending on which values you care about
    #WMS note 220804 - i think 'original frames' in the cleversys .txt output is the frames of the original video, which is what we'd want
    useful = ['CenterX(mm)','CenterY(mm)','NoseX(mm)','NoseY(mm)','DistanceSum(mm)_novel','[Center_Areas]_novel', '[Nose_Areas]_novel','CenterX(mm)_partner', 'CenterY(mm)_partner','EventRule1',
       'EventRule2', 'EventRule3', 'chamber_novel', 'chamber_partner',
       'chamber_center', 'EventRule7', 'EventRule8', 'EventRule9',
       'EventRule10', 'EventRule11', 'EventRule12', 'EventRule13',
       'EventRule14', 'EventRule15', 'EventRule16', 'huddle_novel',
       'EventRule18', 'EventRule19', 'EventRule20', 'EventRule21',
       'huddle_partner', 'EventRule23', 'EventRule24', 'EventRule25',
       'EventRule26', 'EventRule27', 'EventRule28', 'EventRule29',
       'EventRule30', 'novel_dist_less_10cm', 'partner_dist_less_10cm',
       'EventRule33', 'EventRule34', 'EventRule35', 'EventRule36',
       'EventRule37', 'EventRule38', 'EventRule39', 'EventRule40',
       'EventRule41', 'EventRule42', 'original_frames', 'Time',
       'original_time''original_time','distance_to_partner',
       'distance_to_novel', 'distance_traveled', 'distance_traveled_partner',
       'distance_traveled_novel']

    #change the df column names to the variables you want to look at
    cs_df = cs_df[cs_df.columns.intersection(useful)]

    #i believe original frames = the frame number from the minicam (starting at the cutoff start time you set in cleversys)
    cs_df = cs_df.rename(columns={"original_frames":"Frame Number_"+cam_num})

    #add the corresponding miniscope frames from align_df (need to confirm that no frames are being dropped besides those before the start time in cleversys)
    align_cs = cs_df.merge(align_df)

    return align_cs

#def align_dlc():
#
#   return align_pe


#code to take same cleversys .csv and binarize when animal is in different subregions of the chamber for place cells