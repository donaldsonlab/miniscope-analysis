import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io as io
import re
import math
import seaborn as sns
import os
import Cleversys_Parser as cp

#modified version of Dave's cleversys parser for miniscope alignment/bento import
def ms_parse(cs_txt, cam_num):
    ''' input: 
    cs_txt = .txt output from cleversys
    cam_num = minicam # that you ran thru cleversys (likely the top view)

    return parse_df = df containing frame-by-frame parsed output with the columns you care about'''
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
    parse_df = cs_df.rename(columns={"original_frames":"Frame Number_"+cam_num})

    return parse_df




##aligning the minicam and miniscope feeds, using miniscope frames as reference
#WMS note 220804 - need to make these arguments all optional so people can plug in whatever feeds they recorded in their session
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
def align_cleversys(parse_df, align_df):
    ''' input: 
    parse_df = parsed output from cleversys, produced by ms_parse fxn above
    align_df = output df from align_feeds function above
    cam_num = minicam # that you ran thru cleversys (likely the top view)

    return align_cs = df where each row is the closest minicam frame to every miniscope frame and the corresponding cleversys tracking data for that frame'''
    
    #add the corresponding miniscope frames from align_df (need to confirm that no frames are being dropped besides those before the start time in cleversys)
    align_cs = parse_df.merge(align_df)

    return align_cs

#def align_dlc():
#
#   return align_pe


#code to take same cleversys .csv and binarize when animal is in different subregions of the chamber for place cells
#adapted from Will Mau (Cai Lab @ Sinai)'s spatial_bin function (https://github.com/wmau/CaImaging/blob/daa054cb00c9ed89ba65f6a53fa49fa24126585a/CaImaging/Behavior.py#L114
#and https://github.com/wmau/CaImaging/blob/master/CaImaging/PlaceFields.py)
#a good bin size is likely 5 cm x 5 cm for the PPT chamber (see Donegan et al., 2020 Nat Neuro for spatial binning in a similarly-sized three-chamber social interaction apparatus)
#(Murugan et al., 2017 Cell use 3 cm bins)

#incomplete -- need to better understand what is going on with numpy histogram to figure out how to get the boolean for bins https://numpy.org/devdocs/reference/generated/numpy.histogram2d.html
def space_bin(align_cs,bin_size,show_plot=False):
    '''input:
    align_cs = aligned frames and cleversys tracking from align_cleversys() above
    bin_size = bin length desired, in mm (per cleversys output)
    show_plot = if you want to show a plot of your bins (not sure what colors are corresponding to)
    '''
    y = align_cs['NoseY(mm)'].tolist()
    maxY = max(y)
    minY = min(y)
    Ylim = [minY, maxY]
    nbinsY = int(np.round(np.diff(Ylim)[0] / bin_size)) #may need to make this nbinsy + 1 to actually get the correct # of bins?

    x = align_cs['NoseX(mm)'].tolist()
    maxX = max(x)
    minX = min(x)
    Xlim = [minX, maxX]
    nbinsX = int(np.round(np.diff(Xlim)[0] / bin_size)) #may need to make this nbinsx + 1 to actually get the correct # of bins?

    xbins = np.linspace(minX,maxX,(nbinsX+1))
    ybins = np.linspace(minY,maxY,(nbinsY+1))
    bins = [ybins, xbins]

    H, xedges, yedges = np.histogram2d(y, x, bins)

    if show_plot:
        fig, ax = plt.subplots()
        ax.imshow(H)
    
    return H, xedges, yedges, bins

#code to use spatial bins produced in space_bin() to create a frame-by-frame boolean of animal occupancy in each bin
#can probably lump this with the space_bin()
#def bin_occ(align_cs, show_plot = True):


