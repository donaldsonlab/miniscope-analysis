% Script to compile and concatenate behavioral video clips from within a
% recording and/or across multiple recordings on same day (i.e., multiple
% videos within a single trial and multiple trials within a single session)
% 
% Also will convert behavioral video into new playback speed if needed -
% this part is a slight modification to a script from Samara Miller (UCLA).
% This is to roughly approximate the minicam and miniscope alignment as a
% first pass without matching up the timestamps (an early attempt to import
% into Bento without understanding the timestamp functionality). These
% lines are commented out for now. If you need to do this, uncomment those
% lines.
%
% 220720 note: minicams seem to always be recorded at 50 FPS for WMS recordings -> playback
% speed = 60 FPS in .avi video
%
% miniscope is recorded at 30 FPS -> playback speed = 60 FPS
%
% Note: this script assumes your behavioral videos directory is organized
% in the following format:
% ...animal/session_date/trials_times/devices/videos. This organization can
% be set up in the miniscope software userConfig files
%

%% 
clc;clear;

%you need the natsort package to naturally sort the trial times - download
%and add path below:
addpath('//penc8.rc.int.colorado.edu/DonaldsonLab/Sheeran/code/matlab/natsort') %load natsort fxns


%% IF CONCATENATING ACROSS A SINGLE TRIAL ONLY: USE THIS BLOCK

%choose time folder (e.g., "11_34_19") corresponding to your trial and
%set as cd
cd(uigetdir);
folder = cd

%create new subfolder under date folder to compile all minicam trial
%videos into
%mkdir minicam1_compiled
mkdir minicam2_compiled

%get into the folder w the minicam videos
d = dir; %next four lines are just getting into your exp_id folder, no matter what the name is (so long as there is only one exp_id folder, which there should be)
real_dir = d(~ismember({d.name},{'.','..'}));
exp_id = real_dir.name;
trial = cd(exp_id);
exp = cd('MiniCam2'); %exp = cd('MiniCam1');
%compile folder's video files into a list 
files = dir('*.avi');
LIST = {};
clear indx

for k = 1:length(files)
    LIST {k} = files(k).name;
    indx(k) = k;
end

prefix = '0'; %first digit corresponds to loop iteration

%rename each file
for I = 1:length(indx)
    id = indx(I); 
    
    %determine what new file name will be and rewrite
   
    [~, f,ext] = fileparts(files(id).name);
    rename = strcat(prefix,'_',f,ext) ; %define new file name
    movefile(files(id).name, rename); %overwrite existing file name
end
    
%save copies of all the newly named videos in the new minicam_compiled folder
%copyfile *.avi ../../minicam1_compiled
copyfile *.avi ../../minicam2_compiled

%re-set directory back to the date folder to move forward with code
cd(trial);

%% IF CONCATENATING ACROSS MULTIPLE TRIALS: USE THIS BLOCK

%choose date folder (e.g., "2022_07_09") containing all trials from a single session/animal to
%be concatenated and set as current directory
cd(uigetdir);
folder = cd

%identify each time (=trial) folder
trials = dir; %ID trial folders (=times)
trials = trials(~ismember({trials.name},{'.','..'})); %get rid of '.' and '..' in list
datefrmts = regexp({trials.name},'\d\d.\d\d.\d\d');
datefrmts_indx = ~cellfun(@isempty,datefrmts)
trials = trials(datefrmts_indx);


%reorganize folders by temporal order (first->last, likely already the case)
A = datetime({trials.name}, 'InputFormat', 'HH_mm_ss', 'Format', 'preserveinput');
[B,I] = sort(A); %B=sorted times, I=corresponding indices in A

formatOut = 'HH_MM_SS';
for l = 1:length(B)
    ordered_trials {l} = datestr(B(l),formatOut);
end


%create new subfolder under date folder to compile all minicam videos into
mkdir minicam1_compiled
%mkdir minicam2_compiled

%loop to 1) identify the subdirectory containing the desired minicam videos for this trial, 
% 2) rename each video file in that subdirectory to be concatenated in correct order
for j = 1:length(ordered_trials)
    a = ordered_trials{j};
    date = cd(a);
    %get into the folder w the minicam videos
    d = dir; %next four lines are just getting into your exp_id folder, no matter what the name is (so long as there is only one exp_id folder, which there should be)
    real_dir = d(~ismember({d.name},{'.','..'}));
    exp_id = real_dir.name;
    trial = cd(exp_id);
    exp = cd('MiniCam1'); %exp = cd('MiniCam2');
    %compile folder's video files into a list 
    files = dir('*.avi');
    LIST = {};
    clear indx
    for k = 1:length(files)
        LIST {k} = files(k).name;
        indx(k) = k;
    end

    %rename each file
    for I = 1:length(indx)
    id = indx(I); 
    
    %determine what new file name will be and rewrite
    prefix = num2str(j-1); %first digit corresponds to loop iteration

    [~, f,ext] = fileparts(files(id).name);
    rename = strcat(prefix,'_',f,ext) ; %define new file name
    movefile(files(id).name, rename); %overwrite existing file name
    end
    
    %save copies of all the newly named videos in the new minicam_compiled folder
    copyfile *.avi ../../../minicam1_compiled
    %copyfile *.avi ../../../minicam2_compiled

    %re-set directory back to the date folder for next loop iteration
    cd(date);

end
%%
%change directory to the folder containing newly compiled minicam files
cd('minicam2_compiled'); 
%cd('minicam1_compiled');

%create list of all file names
myFiles = dir('*.avi'); %gets all avi files in struct
for j = 1:length(myFiles) %place avi file names into list
        file_list {j} = myFiles(j).name;
        indx(j) = j;
end

%reorder file names so they are concatenated in correct order
sortedFiles = natsortfiles(file_list);


%% Optional section if want to change playback speed to 100 FPS
% %make directory to compile sped-up copies of clips
%mkdir('100FPS'); 

% %make copies of all video clips at a new playback speed of 100 FPS
%for k = 1:length(sortedFiles)
%    baseFileName = sortedFiles(k);
%    fullFileName = fullfile(cd, baseFileName); %change folder to minicam1_compiled, i think
%    obj = VideoReader(fullFileName{1}); 
%    newFileName = fullfile(cd, '\100FPS\', baseFileName); 
%    obj2= VideoWriter(newFileName{1}); % Write in new variable 
%    obj2.FrameRate = 100; %speed up playback of new video copy to 100FPS
%    % % for reading frames one by one
%    open(obj2)
%    while hasFrame(obj)              
%     k = readFrame(obj); 
%   
%     % write the frames in obj2.         
%     obj2.writeVideo(k);          
%    end
%    close(obj2)

%end
%% CONCATENATE VIDEOS
videoList = []; 

for f = 1:length(sortedFiles)
    videoList{f} = fullfile(cd, sortedFiles(f));
end

%if converting playback speed to 100FPS, instead run:
%for f = 1:length(sortedFiles)
%    videoList{f} = fullfile(cd, '\100FPS\' , sortedFiles(f));
%end

% create output in seperate folder (to avoid accidentally using it as input)
mkdir('output');
outputVideo = VideoWriter(fullfile(cd,'output/mergedVideo.avi'));

% if all clips are from the same source/have the same specifications
% just initialize with the settings of the first video in videoList
inputVideo_init = VideoReader(videoList{1}{1}); % first video
outputVideo.FrameRate = inputVideo_init.FrameRate; %FrameRate = 100 if speeding up, will stay at 60 FPS playback speed if not

open(outputVideo) % >> open stream
% iterate over all videos you want to merge (e.g. in videoList)
for i = 1:length(videoList)
    % select i-th clip (assumes they are in order in this list!)
    inputVideo = VideoReader(videoList{i}{1});
    % -- stream your inputVideo into an outputVideo
    while hasFrame(inputVideo)
        writeVideo(outputVideo, readFrame(inputVideo));
    end
end
close(outputVideo) % << close after having iterated through all videos