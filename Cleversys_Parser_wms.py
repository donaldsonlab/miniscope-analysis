import numpy as np
import pandas as pd
import io as io
import re
import math
import seaborn as sns
import os

version = '1.0'

def parse(file):
    '''takes a filepath and returns
    
    return df, animal_ID, frame_rate, date
    
    df         = pandas dataframe of parsed data
    animal_ID  = whatever animal ID is in the header
    frame_rate = scraped from header
    date       = date of the test
    
    '''
    with open(file) as f:

        #find the format string
        found = False
        frame_rate = None
        skip = 1

        #edit these if you want to change what rules are recoreded
        event_rules = {'Social Contact [ 1 with 2 ] in Area left':'huddle_left',
                        'Social Contact [ 1 with 3 ] in Area right ':'huddle_right',
                        'Distance between [ 1 and 2 ] Less Than 100.00 mm': 'proximity_left',
                        'Distance between [ 1 and 3 ] Less Than 100.00 mm':'proximity_right',
                        '1 Stay/Hide In left chamber':'left_chamber',
                        '1 Stay/Hide In right chamber':'right_chamber',
                        '1 Stay/Hide In center':'center_chamber'}


        #a dictionary where we can put our found event rule names for later
        #we are transposing here, so that, for example, we get:
        #event_rules ={'1 Stay/Hide In left chamber':'left_chamber', .... }
        #found_rules ={'left_chamber':None, ... }
        found_rules = {event_rules[key]:None for key in event_rules.keys()}

        while not found:
            skip +=1

            line = f.readline()

            if 'Frame Rate' in line:
                frame_rate = float(line.split(':')[1])
            #format line begins with 'Format:'
            if 'Format:' in line:
                found = True

                #raw column names. we'll get back to these, and rename them to make them more informative
                #also need to cleanup some of the cleversys output, because of course
                col_names_r = line.strip().replace('Motion\tOrientation(-pi/2 to pi/2)', 'Motion Orientation(-pi/2 to pi.2)\tUnknown').split('\t')
                col_names_r[0] = 'FrameNum'

            #find which side the partner is on. Animal 2 is always on the left
            if 'animal id' in line.lower():
                newline = f.readline()
                animal_ID = newline.split("\t")[line.lower().split('\t').index('animal id')]
                partner_pos = newline.split("\t")[line.lower().split('\t').index('side of partner')]

                treatment_idx = [i for i, s in enumerate(line.lower().split('\t')) if 'treatment' in s]
                if len(treatment_idx)>1:
                    print('too many matches for treatment in metadata')
                else:
                    treatment_group = newline.split("\t")[treatment_idx[0]]

                raw_date = newline.split("\t")[line.lower().split('\t').index('last modified date')]

                #replace '/' with '_', then split date from the time and use that
                date = raw_date.replace('/','_').split(' ')[0]

                #figure out who is where
                if partner_pos.lower() == 'l' or partner_pos.lower() == 'left':
                    'Partner on left, animal_2 = partner'
                    animal_2 = 'partner'
                    animal_3 = 'novel'
                else:
                    'Partner on right, animal_3 = partner'
                    animal_2 = 'novel'
                    animal_3 = 'partner'

            #get the event rule number corresponding to huddling with partner or novel
            #the line looks like:
            # EventRule17: Social Contact [ 1 with 2 ] in Area left while Joint Motion < 0.040
            # so splitting on ':' and taking the first element will give the eventrule name
            #corrseponding to the metric

            #also grab the event rule name for some other key metrics,
            #like vole location, and vole within 100 mm.

            #acheive by iterating over dict

            #note, could speed this up by making event_rules.keys a list and using a single "in" boolean
            for key in event_rules.keys():
                if key.lower() in line.lower():
                    found_rules[event_rules[key]] = line.split(':')[0]
                    break


    for k in found_rules.keys():
        if not found_rules[k]:
            print(f'couldnt find a line containing "{k}" in the file head. double check the file.')
    #READ IN WITH PANDAS
    df = pd.read_table(file, skiprows = skip, header = None)

    #get rid of weird empty columns
    df.dropna(how = 'all', axis =  'columns', inplace = True)

    #rename columns with informative names, like "CenterX(mm)_partner". start
    #with an empty array that we will add col names to
    new_col = []

    #when we iterate over the column names we're essentially going "left to right",
    #so test animal --> animal_2 --> animal_3. We've already assigned the identity
    # (novel or partner) to animal_2 and animal_3, so we can use those variables
    #when redefining our column names
    for n in col_names_r:

        #if the column not yet in the col name list, add it.
        #first pass is for the test animal
        if not n in new_col:
            new_col.append(n)

        #if the col name plus animal_2 is there, add name plus animal_3
        elif n+'_'+animal_2 in new_col:
            new_col.append(n+'_'+animal_3)

        #otherwise, we're currently iterating over animal_2's columns.
        else:
            new_col.append(n+'_'+animal_2)

    #re-assign column names to the new column names.
    df.columns = new_col



    #we will replace uncertain rows with np.nan, but leave the frame number information.
    #these list comprehensions assemble lists of columns specific to test, novel,
    #and partner animals to set to np.nan, while leaving event rules alone.
    #We will leave the event rules UNCHANGED so that if cleversys thinks the animals are huddling
    #that will still be captured.
    take_me = [col for col in df.columns if 'Frame' not in col if 'Event' not in col if 'partner' not in col if 'novel' not in col]
    take_me_n =[col for col in df.columns if 'novel' in col]
    take_me_p = [col for col in df.columns if 'partner' in col]

    #use np.nan to remove data from times when animal pos is uncertain.
    #Cleversys sets CenterX(mm) and CenterY(mm) to -1 in these cases. We can
    #look at each animal seperately, so even if one animal is uncertain, the
    # others are available.
    df.loc[df['CenterX(mm)'] == -1, take_me] = np.nan
    df.loc[df['CenterX(mm)_novel'] == -1, take_me_n] = np.nan
    df.loc[df['CenterX(mm)_partner'] == -1, take_me_p] = np.nan


    #the following renames key Event Rule columns. Note that this must occur after
    #the above removal of bad values, or else columns without "Event" will also
    #be overriden.

    if partner_pos.lower() == 'l' or partner_pos.lower() == 'left':

        df.rename(columns={found_rules['huddle_left']:'huddle_partner',
        found_rules['huddle_right']:'huddle_novel', found_rules['proximity_left']:'partner_dist_less_10cm',
        found_rules['proximity_right']:'novel_dist_less_10cm',found_rules['left_chamber']:'chamber_partner',
        found_rules['right_chamber']:'chamber_novel',found_rules['center_chamber']:'chamber_center'}, inplace = True)

    else:

        df.rename(columns={found_rules['huddle_right']:'huddle_partner',
        found_rules['huddle_left']:'huddle_novel', found_rules['proximity_right']:'partner_dist_less_10cm',
        found_rules['proximity_left']:'novel_dist_less_10cm', found_rules['right_chamber']:'chamber_partner',
        found_rules['left_chamber']:'chamber_novel',found_rules['center_chamber']:'chamber_center'}, inplace = True)

    #reset frames so they start at 1
    df['original_frames'] = df['FrameNum']
    df['FrameNum'] = df['FrameNum'] - df['FrameNum'].min() + 1
    
    #calculate time from frame num ( frame * 1 / (frame / sec)  --> sec )
    df['Time'] = df.FrameNum/frame_rate
    df['original_time'] = df.original_frames / frame_rate

    #add column of treatment group (IE Naive, Drug, etc)
    df['Treatment Group'] = treatment_group

    #reset the useless AnimalID column (cleversys sets it always to 1) to the number for the test vole
    df['[AnimalID]'] = animal_ID


    # np.linalg.norm can be used to calculate the distance between points
    # https://stackoverflow.com/questions/1401712/how-can-the-euclidean-distance-be-calculated-with-numpy/21986532
    # basically just a really fast way to take advantage of np to do:

    # sqrt((xt - xo)^2 + (yt - yo)^2)

    # where t is test and o is other animal

    df['distance_to_partner'] = np.linalg.norm((df['CenterY(mm)'] - df['CenterY(mm)_partner'],
                                df['CenterX(mm)'] - df['CenterX(mm)_partner']), axis = 0)

    df['distance_to_novel'] = np.linalg.norm((df['CenterY(mm)'] - df['CenterY(mm)_novel'],
                                df['CenterX(mm)'] - df['CenterX(mm)_novel']), axis = 0)

    # calculate distance traveled since last frame. First frame distance is
    #set to zero

    #make two offset arrays so we can simply subtract the finishX array
    #from the startX array, rather than going elementwise
    startX = df['CenterX(mm)'][:-1].values
    finishX = df['CenterX(mm)'][1:].values

    startY = df['CenterY(mm)'][:-1].values
    finishY = df['CenterY(mm)'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    dist_traveled = np.linalg.norm((startX-finishX, startY-finishY), axis = 0)
    #add on a zero to the start of the array for frame 1
    dist_traveled = np.append(np.asarray([0]), dist_traveled)

    startX_partner = df['CenterX(mm)_partner'][:-1].values
    finishX_partner = df['CenterX(mm)_partner'][1:].values

    startY_partner = df['CenterY(mm)_partner'][:-1].values
    finishY_partner = df['CenterY(mm)_partner'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    dist_traveled_partner = np.linalg.norm((startX_partner-finishX_partner, startY_partner-finishY_partner), axis = 0)
    #add on a zero to the start of the array for frame 1
    dist_traveled_partner = np.append(np.asarray([0]), dist_traveled_partner)

    startX_novel = df['CenterX(mm)_novel'][:-1].values
    finishX_novel= df['CenterX(mm)_novel'][1:].values

    startY_novel = df['CenterY(mm)_novel'][:-1].values
    finishY_novel = df['CenterY(mm)_novel'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    dist_traveled_novel = np.linalg.norm((startX_novel-finishX_novel, startY_novel-finishY_novel), axis = 0)
    #add on a zero to the start of the array for frame 1
    dist_traveled_novel = np.append(np.asarray([0]), dist_traveled_novel)

    df['distance_traveled'] = dist_traveled
    df['distance_traveled_partner'] = dist_traveled_partner
    df['distance_traveled_novel'] = dist_traveled_novel
    
    return df, animal_ID, frame_rate, date

def solo_parse(file):
    '''WMS added fxn - for parsing files with only one animal (for position tracking)
    takes a filepath and returns
    
    return df, animal_ID, frame_rate, date
    
    df         = pandas dataframe of parsed data
    animal_ID  = whatever animal ID is in the header
    frame_rate = scraped from header
    date       = date of the test
    
    '''
    with open(file) as f:

        #find the format string
        found = False
        frame_rate = None
        skip = 1

        #edit these if you want to change what rules are recoreded
        event_rules = {'vole 1 Center In left':'left_chamber',
                        'vole 1 Center In right':'right_chamber',
                        'vole 1 Center In center':'center_chamber'}


        #a dictionary where we can put our found event rule names for later
        #we are transposing here, so that, for example, we get:
        #event_rules ={'1 Stay/Hide In left chamber':'left_chamber', .... }
        #found_rules ={'left_chamber':None, ... }
        found_rules = {event_rules[key]:None for key in event_rules.keys()}

        while not found:
            skip +=1

            line = f.readline()

            if 'Frame Rate' in line:
                frame_rate = float(line.split(':')[1])
            #format line begins with 'Format:'
            if 'Format:' in line:
                found = True

                #raw column names. we'll get back to these, and rename them to make them more informative
                #also need to cleanup some of the cleversys output, because of course
                col_names_r = line.strip().replace('Motion\tOrientation(-pi/2 to pi/2)', 'Motion Orientation(-pi/2 to pi.2)\tUnknown').split('\t')
                col_names_r[0] = 'FrameNum'

            #get the event rule number corresponding to huddling with partner or novel
            #the line looks like:
            # EventRule17: Social Contact [ 1 with 2 ] in Area left while Joint Motion < 0.040
            # so splitting on ':' and taking the first element will give the eventrule name
            #corrseponding to the metric

            #also grab the event rule name for some other key metrics,
            #like vole location, and vole within 100 mm.

            #acheive by iterating over dict

            #note, could speed this up by making event_rules.keys a list and using a single "in" boolean
            for key in event_rules.keys():
                if key.lower() in line.lower():
                    found_rules[event_rules[key]] = line.split(':')[0]
                    break


    for k in found_rules.keys():
        if not found_rules[k]:
            print(f'couldnt find a line containing "{k}" in the file head. double check the file.')
    #READ IN WITH PANDAS
    df = pd.read_table(file, skiprows = skip, header = None)

    #get rid of weird empty columns
    df.dropna(how = 'all', axis =  'columns', inplace = True)

    #rename columns with informative names, like "CenterX(mm)_partner". start
    #with an empty array that we will add col names to
    new_col = []

    #when we iterate over the column names we're essentially going "left to right",
    #so test animal --> animal_2 --> animal_3. We've already assigned the identity
    # (novel or partner) to animal_2 and animal_3, so we can use those variables
    #when redefining our column names
    for n in col_names_r:

        #if the column not yet in the col name list, add it.
        #first pass is for the test animal
        if not n in new_col:
            new_col.append(n)

        #if the col name plus animal_2 is there, add name plus animal_3
        #elif n+'_'+animal_2 in new_col:
        #    new_col.append(n+'_'+animal_3)

        #otherwise, we're currently iterating over animal_2's columns.
        #else:
        #    new_col.append(n+'_'+animal_2)

    #re-assign column names to the new column names.
    df.columns = new_col



    #we will replace uncertain rows with np.nan, but leave the frame number information.
    #these list comprehensions assemble lists of columns specific to test, novel,
    #and partner animals to set to np.nan, while leaving event rules alone.
    #We will leave the event rules UNCHANGED so that if cleversys thinks the animals are huddling
    #that will still be captured.
    take_me = [col for col in df.columns if 'Frame' not in col if 'Event' not in col] #if 'partner' not in col if 'novel' not in col]
    #take_me_n =[col for col in df.columns if 'novel' in col]
    #take_me_p = [col for col in df.columns if 'partner' in col]

    #use np.nan to remove data from times when animal pos is uncertain.
    #Cleversys sets CenterX(mm) and CenterY(mm) to -1 in these cases. We can
    #look at each animal seperately, so even if one animal is uncertain, the
    # others are available.
    df.loc[df['CenterX(mm)'] == -1, take_me] = np.nan
    #df.loc[df['CenterX(mm)_novel'] == -1, take_me_n] = np.nan
    #df.loc[df['CenterX(mm)_partner'] == -1, take_me_p] = np.nan


    #the following renames key Event Rule columns. Note that this must occur after
    #the above removal of bad values, or else columns without "Event" will also
    #be overriden.

    #if partner_pos.lower() == 'l' or partner_pos.lower() == 'left':

        #df.rename(columns={found_rules['huddle_left']:'huddle_partner',
        #found_rules['huddle_right']:'huddle_novel', found_rules['proximity_left']:'partner_dist_less_10cm',
        #found_rules['proximity_right']:'novel_dist_less_10cm',found_rules['left_chamber']:'chamber_partner',
        #found_rules['right_chamber']:'chamber_novel',found_rules['center_chamber']:'chamber_center'}, inplace = True)

    #else:

        #df.rename(columns={found_rules['huddle_right']:'huddle_partner',
        #found_rules['huddle_left']:'huddle_novel', found_rules['proximity_right']:'partner_dist_less_10cm',
        #found_rules['proximity_left']:'novel_dist_less_10cm', found_rules['right_chamber']:'chamber_partner',
        #found_rules['left_chamber']:'chamber_novel',found_rules['center_chamber']:'chamber_center'}, inplace = True)

    #reset frames so they start at 1
    df['original_frames'] = df['FrameNum']
    df['FrameNum'] = df['FrameNum'] - df['FrameNum'].min() + 1
    
    #calculate time from frame num ( frame * 1 / (frame / sec)  --> sec )
    df['Time'] = df.FrameNum/frame_rate
    df['original_time'] = df.original_frames / frame_rate

    #add column of treatment group (IE Naive, Drug, etc)
    #df['Treatment Group'] = treatment_group

    #reset the useless AnimalID column (cleversys sets it always to 1) to the number for the test vole
    #df['[AnimalID]'] = animal_ID


    # np.linalg.norm can be used to calculate the distance between points
    # https://stackoverflow.com/questions/1401712/how-can-the-euclidean-distance-be-calculated-with-numpy/21986532
    # basically just a really fast way to take advantage of np to do:

    # sqrt((xt - xo)^2 + (yt - yo)^2)

    # where t is test and o is other animal

    #df['distance_to_partner'] = np.linalg.norm((df['CenterY(mm)'] - df['CenterY(mm)_partner'],
    #                            df['CenterX(mm)'] - df['CenterX(mm)_partner']), axis = 0)

    #df['distance_to_novel'] = np.linalg.norm((df['CenterY(mm)'] - df['CenterY(mm)_novel'],
    #                            df['CenterX(mm)'] - df['CenterX(mm)_novel']), axis = 0)

    # calculate distance traveled since last frame. First frame distance is
    #set to zero

    #make two offset arrays so we can simply subtract the finishX array
    #from the startX array, rather than going elementwise
    startX = df['CenterX(mm)'][:-1].values
    finishX = df['CenterX(mm)'][1:].values

    startY = df['CenterY(mm)'][:-1].values
    finishY = df['CenterY(mm)'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    dist_traveled = np.linalg.norm((startX-finishX, startY-finishY), axis = 0)
    #add on a zero to the start of the array for frame 1
    dist_traveled = np.append(np.asarray([0]), dist_traveled)

    #startX_partner = df['CenterX(mm)_partner'][:-1].values
    #finishX_partner = df['CenterX(mm)_partner'][1:].values

    #startY_partner = df['CenterY(mm)_partner'][:-1].values
    #finishY_partner = df['CenterY(mm)_partner'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    #dist_traveled_partner = np.linalg.norm((startX_partner-finishX_partner, startY_partner-finishY_partner), axis = 0)
    #add on a zero to the start of the array for frame 1
    #dist_traveled_partner = np.append(np.asarray([0]), dist_traveled_partner)

    #startX_novel = df['CenterX(mm)_novel'][:-1].values
    #finishX_novel= df['CenterX(mm)_novel'][1:].values

    #startY_novel = df['CenterY(mm)_novel'][:-1].values
    #finishY_novel = df['CenterY(mm)_novel'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    #dist_traveled_novel = np.linalg.norm((startX_novel-finishX_novel, startY_novel-finishY_novel), axis = 0)
    #add on a zero to the start of the array for frame 1
    #dist_traveled_novel = np.append(np.
    # asarray([0]), dist_traveled_novel)

    df['distance_traveled'] = dist_traveled
    #df['distance_traveled_partner'] = dist_traveled_partner
    #df['distance_traveled_novel'] = dist_traveled_novel
    
    return df, frame_rate



def assemble_names(directory):
    '''return a list of paths to files to parse'''
    os.chdir(directory)

    #create an empty 2d list
    out_names = []

    #this will assemble a list of ALL filenames for images, sorted by timestamp of acquisition


    for root, dirs, files in os.walk(directory):
        out = [os.path.join(root, f) for f in sorted(files) if
            f.endswith('TCR.TXT') if not f.startswith('.')]
        out_names += out
    return out_names

def parse_and_convert_csv(file, out_file):
    '''parse a file aaaannnnndd output a csv file'''
    df, ani, frame_rate, date = parse(file)
    df.to_csv(out_file)
    return df, ani, frame_rate, date



'''----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------'''




def parse_dev(file):
    '''
    dev parse function so we have a place to play around with stuff.
    
    
    takes a filepath and returns
    
    return df, animal_ID, frame_rate, date
    
    df         = pandas dataframe of parsed data
    animal_ID  = whatever animal ID is in the header
    frame_rate = scraped from header
    date       = date of the test
    
    '''
    with open(file) as f:

        #find the format string
        found = False
        frame_rate = None
        skip = 1

        #edit these if you want to change what rules are recoreded
        event_rules = {'Social Contact [ 1 with 2 ] in Area left':'huddle_left',
                        'Social Contact [ 1 with 3 ] in Area right ':'huddle_right',
                        'Distance between [ 1 and 2 ] Less Than 100.00 mm': 'proximity_left',
                        'Distance between [ 1 and 3 ] Less Than 100.00 mm':'proximity_right',
                        '1 Stay/Hide In left chamber':'left_chamber',
                        '1 Stay/Hide In right chamber':'right_chamber',
                        '1 Stay/Hide In center':'center_chamber'}


        #a dictionary where we can put our found event rule names for later
        found_rules = {event_rules[key]:None for key in event_rules.keys()}

        while not found:
            skip +=1

            line = f.readline()

            if 'Frame Rate' in line:
                frame_rate = float(line.split(':')[1])
            #format line begins with 'Format:'
            if 'Format:' in line:
                found = True

                #raw column names. we'll get back to these, and rename them to make them more informative
                #also need to cleanup some of the cleversys output, because of course
                col_names_r = line.strip().replace('Motion\tOrientation(-pi/2 to pi/2)', 'Motion Orientation(-pi/2 to pi.2)\tUnknown').split('\t')
                col_names_r[0] = 'FrameNum'

            #find which side the partner is on. Animal 2 is always on the left
            if 'animal id' in line.lower():
                newline = f.readline()
                animal_ID = newline.split("\t")[line.lower().split('\t').index('animal id')]
                partner_pos = newline.split("\t")[line.lower().split('\t').index('side of partner')]

                treatment_idx = [i for i, s in enumerate(line.lower().split('\t')) if 'treatment' in s]
                if len(treatment_idx)>1:
                    print('too many matches for treatment in metadata')
                else:
                    treatment_group = newline.split("\t")[treatment_idx[0]]

                raw_date = newline.split("\t")[line.lower().split('\t').index('last modified date')]

                #replace '/' with '_', then split date from the time and use that
                date = raw_date.replace('/','_').split(' ')[0]

                #figure out who is where
                if partner_pos.lower() == 'l' or partner_pos.lower() == 'left':
                    'Partner on left, animal_2 = partner'
                    animal_2 = 'partner'
                    animal_3 = 'novel'
                else:
                    'Partner on right, animal_3 = partner'
                    animal_2 = 'novel'
                    animal_3 = 'partner'

            #get the event rule number corresponding to huddling with partner or novel
            #the line looks like:
            # EventRule17: Social Contact [ 1 with 2 ] in Area left while Joint Motion < 0.040
            # so splitting on ':' and taking the first element will give the eventrule name
            #corrseponding to the metric

            #also grab the event rule name for some other key metrics,
            #like vole location, and vole within 100 mm.

            #acheive by iterating over dict


            for key in event_rules.keys():
                if key.lower() in line.lower():
                    found_rules[event_rules[key]] = line.split(':')[0]
                    break


    for k in found_rules.keys():
        if not found_rules[k]:
            print(f'couldnt find a line containing "{k}" in the file head. double check the file.')
    #READ IN WITH PANDAS
    df = pd.read_table(file, skiprows = skip, header = None)

    #get rid of weird empty columns
    df.dropna(how = 'all', axis =  'columns', inplace = True)

    #rename columns with informative names, like "CenterX(mm)_partner". start
    #with an empty array that we will add col names to
    new_col = []

    #when we iterate over the column names we're essentially going "left to right",
    #so test animal --> animal_2 --> animal_3. We've already assigned the identity
    # (novel or partner) to animal_2 and animal_3, so we can use those variables
    #when redefining our column names
    for n in col_names_r:

        #if the column not yet in the col name list, add it.
        #first pass is for the test animal
        if not n in new_col:
            new_col.append(n)

        #if the col name plus animal_2 is there, add name plus animal_3
        elif n+'_'+animal_2 in new_col:
            new_col.append(n+'_'+animal_3)

        #otherwise, we're currently iterating over animal_2's columns.
        else:
            new_col.append(n+'_'+animal_2)

    #re-assign column names to the new column names.
    df.columns = new_col



    #we will replace uncertain rows with np.nan, but leave the frame number information.
    #these list comprehensions assemble lists of columns specific to test, novel,
    #and partner animals to set to np.nan, while leaving event rules alone.
    #We will leave the event rules UNCHANGED so that if cleversys thinks the animals are huddling
    #that will still be captured.
    take_me = [col for col in df.columns if 'Frame' not in col if 'Event' not in col if 'partner' not in col if 'novel' not in col]
    take_me_n =[col for col in df.columns if 'novel' in col]
    take_me_p = [col for col in df.columns if 'partner' in col]

    #use np.nan to remove data from times when animal pos is uncertain.
    #Cleversys sets CenterX(mm) and CenterY(mm) to -1 in these cases. We can
    #look at each animal seperately, so even if one animal is uncertain, the
    # others are available.
    df.loc[df['CenterX(mm)'] == -1, take_me] = np.nan
    df.loc[df['CenterX(mm)_novel'] == -1, take_me_n] = np.nan
    df.loc[df['CenterX(mm)_partner'] == -1, take_me_p] = np.nan


    #the following renames key Event Rule columns. Note that this must occur after
    #the above removal of bad values, or else columns without "Event" will also
    #be overriden.

    if partner_pos.lower() == 'l' or partner_pos.lower() == 'left':

        df.rename(columns={found_rules['huddle_left']:'huddle_partner',
        found_rules['huddle_right']:'huddle_novel', found_rules['proximity_left']:'partner_dist_less_10cm',
        found_rules['proximity_right']:'novel_dist_less_10cm',found_rules['left_chamber']:'chamber_partner',
        found_rules['right_chamber']:'chamber_novel',found_rules['center_chamber']:'chamber_center'}, inplace = True)

    else:

        df.rename(columns={found_rules['huddle_right']:'huddle_partner',
        found_rules['huddle_left']:'huddle_novel', found_rules['proximity_right']:'partner_dist_less_10cm',
        found_rules['proximity_left']:'novel_dist_less_10cm', found_rules['right_chamber']:'chamber_partner',
        found_rules['left_chamber']:'chamber_novel',found_rules['center_chamber']:'chamber_center'}, inplace = True)

    #reset frames so they start at 1
    df['original_frames'] = df['FrameNum']
    df['FrameNum'] = df['FrameNum'] - df['FrameNum'].min() + 1
    

    #calculate time from frame num ( frame * 1 / (frame / sec)  --> sec )
    #frames start at 1, but we want time to start at 0s, so subtract off 1
    df['Time'] = (df.FrameNum - 1)/frame_rate
    df['original_time'] = df.original_frames / frame_rate

    #add column of treatment group (IE Naive, Drug, etc)
    df['Treatment Group'] = treatment_group

    #reset the useless AnimalID column (cleversys sets it always to 1) to the number for the test vole
    df['[AnimalID]'] = animal_ID


    # np.linalg.norm can be used to calculate the distance between points
    # https://stackoverflow.com/questions/1401712/how-can-the-euclidean-distance-be-calculated-with-numpy/21986532
    # basically just a really fast way to take advantage of np to do:

    # sqrt((xt - xo)^2 + (yt - yo)^2)

    # where t is test and o is other animal

    df['distance_to_partner'] = np.linalg.norm((df['CenterY(mm)'] - df['CenterY(mm)_partner'],
                                df['CenterX(mm)'] - df['CenterX(mm)_partner']), axis = 0)

    df['distance_to_novel'] = np.linalg.norm((df['CenterY(mm)'] - df['CenterY(mm)_novel'],
                                df['CenterX(mm)'] - df['CenterX(mm)_novel']), axis = 0)

    # calculate distance traveled since last frame. First frame distance is
    #set to zero

    #make two offset arrays so we can simply subtract the finishX array
    #from the startX array, rather than going elementwise
    startX = df['CenterX(mm)'][:-1].values
    finishX = df['CenterX(mm)'][1:].values

    startY = df['CenterY(mm)'][:-1].values
    finishY = df['CenterY(mm)'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    dist_traveled = np.linalg.norm((startX-finishX, startY-finishY), axis = 0)
    #add on a zero to the start of the array for frame 1
    dist_traveled = np.append(np.asarray([0]), dist_traveled)

    startX_partner = df['CenterX(mm)_partner'][:-1].values
    finishX_partner = df['CenterX(mm)_partner'][1:].values

    startY_partner = df['CenterY(mm)_partner'][:-1].values
    finishY_partner = df['CenterY(mm)_partner'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    dist_traveled_partner = np.linalg.norm((startX_partner-finishX_partner, startY_partner-finishY_partner), axis = 0)
    #add on a zero to the start of the array for frame 1
    dist_traveled_partner = np.append(np.asarray([0]), dist_traveled_partner)

    startX_novel = df['CenterX(mm)_novel'][:-1].values
    finishX_novel= df['CenterX(mm)_novel'][1:].values

    startY_novel = df['CenterY(mm)_novel'][:-1].values
    finishY_novel = df['CenterY(mm)_novel'][1:].values

    #use same strategy as distance_to_partner to calculate euclidean distance
    dist_traveled_novel = np.linalg.norm((startX_novel-finishX_novel, startY_novel-finishY_novel), axis = 0)
    #add on a zero to the start of the array for frame 1
    dist_traveled_novel = np.append(np.asarray([0]), dist_traveled_novel)

    df['distance_traveled'] = dist_traveled
    df['distance_traveled_partner'] = dist_traveled_partner
    df['distance_traveled_novel'] = dist_traveled_novel

    print(found_rules)
    #df_out, mod_log = correct_chamber_assignments(df)
    
    return df, animal_ID, frame_rate, date

def get_previous_location(df, search_start_index, current_loc = None, window = 3,max_distance = 10):
    '''iterate backwards over a dataframe from a starting index to find the last time an animal's position was known 
    with "certainty", using the columns 'chamber_partner' or 'chamber_novel'. Must be used after these
    columns have been renamed from their original EventRules. Ignores the center chamber, as we currently think that
    crossing events could lead to real double-labeling.
    
    df                 = pandas dataframe to search
    search_start_index = the df index to start at. 
    current_loc        = used for recursion. the first call should keep this set to None, but it will be updated as the search progresses
    window             = the number of consecutive rows on which the chamber position must match. 
    max_distance       = the maximum number of rows the algorithm will move backwards before giving up
    
    returns current_loc, col_name
    
    current loc = the last index of the window used for overwriting position
    col_name    = the column selected to overwrite the data ()
    '''
       


    start = search_start_index-1 if not current_loc else current_loc
    current_loc = current_loc if current_loc else start
    
    sli = df.iloc[start-window:start]
    sli = sli.loc[:,['chamber_partner','chamber_novel']]
    
    #check if the sum of all the 1's is greater than the window length, which would mean 
    #that there is at least once place where the animal is listed in both chambers
    if np.sum(sli.values) > window:
        #we've encountered a place where there was a multi-assignment
        if np.abs(current_loc-search_start_index) < max_distance:
            #if we havent gone to far, try taking another step back in time
            return get_previous_location(df,            
                                    search_start_index, current_loc = current_loc - 1, 
                                    window = window, 
                                    max_distance = max_distance)
        else:
            return -1, 'failed'
    
    else:
        #return the index the reassignment is taken from, and the column to 
        #set to 1 (True)
        if len(sli.sum()) == 0:
            print(sli)
            print('df:\n')
            print(df.head())
        return current_loc, sli.sum().idxmax()
    
    
def get_index_pairs(index_list):

    #offset the index list by 1 and take the difference
    diff = index_list[1:] - index_list[:-1]

    #where the difference is 1 the indices are sequential. Label nonsequential True
    new = np.asarray([False if val == 1 else True for val in diff])

        
    #get the location of the transition indices
    transition_indices = np.where(new)[0]

    sets = []
    pairs = []

    prev = 0
    
    for val in transition_indices:
        
        try:
            
                    
            #list s of sequential indeces, starting at location 0 (first index in 
            # index_list )
            s = index_list[prev:val+1]
            
            #add the list s to sets. not using this at the moment, but could be
            #useful down the line
            sets += [s]
            
            #update prev for the next loop
            prev = val+1

            if len(s) > 1:
                #if the list s has more than one value take the first and last
                pairs += [[s[0], s[-1]]]
            elif len(s) == 1:
                #if the s has just one value, it is both the 'start' and 'stop' of 
                # a sequence

                pairs += [[s[0], s[0]]]
            else:
                #we shouldnt ever get here. an empty list.
                print('oops')
                print(s)
        except:
            print(f'prev:{prev}, val:{val}')
    if len(new)>0 and new[-1]:
        sets += [[index_list[-1]]]
        pairs += [[index_list[-1], index_list[-1]]]
    else:
        if len(new)>0:
            sets += [[index_list[prev:]]]
            pairs += [[index_list[prev], index_list[-1]]]
    return np.asarray(pairs)

def correct_chamber_assignments(df_in, verbose = False):
    indices = df_in.loc[(df_in.chamber_partner >0)&(df_in.chamber_novel >0) & (df_in.chamber_center > 0)].index
    pairs = get_index_pairs(indices)
    
    new_df = df_in.copy()
    new_df['modified_due_to_uncertainty'] = 0
    new_df['reassigned_to'] = 'none'
    
    mod_log = [['time_start', 'time_end', 'reassigned_to', 'index_start', 'index_finish', 'index_distance']]
    all_cols = ['chamber_partner', 'chamber_novel', 'chamber_center']
    
    for start, finish in pairs:
        loc, col = get_previous_location(df_in, search_start_index=start, window = 3)
        st = df_in.iloc[start]["original_time"]
        ft = df_in.iloc[finish]["original_time"]
        if verbose:
            print(f'time_start: {st:.2f} time_end: {ft:.2f} reassigned_to: {col}       index_start: {start} index_finish: {finish} distance: {start-loc}')
        mod_log += [[st, ft, col, start, finish, start-loc]]
    
        new_df.loc[(new_df.index >= start) & (new_df.index <= finish), 'reassigned_to'] = col 
        for ac in all_cols:
            if ac != col:
                
                new_df.loc[(new_df.index >= start) & (new_df.index <= finish), ac] = 0
                new_df.loc[(new_df.index >= start) & (new_df.index <= finish), 'modified_due_to_uncertainty'] = 1
    return new_df, mod_log
