% MATLAB program to convert behavioral video into new speed (SM had to 30 FPS) and
% concatenate it - WMS slight modifications to SM code

%220720 note: minicams seem to always be recorded at 50 FPS -> playback
%speed = 60 FPS in .avi video
%
%miniscope is recorded at 30 FPS -> playback speed = 60 FPS
%
%should change minicam speed to playback at 100 FPS instead of 60 to match
%miniscope rate


%% THEN TRY PLUGGING INTO BENTO TO SEE WHETHER IT APPROPRIATELY ALIGNS
%% WITH THE MINIAN OUTPUT -- 220722 no, bento is importing 

clc;clear;

addpath('//penc2.rc.int.colorado.edu/DonaldsonLab/Sheeran/code/matlab/natsort') %load natsort fxns

%choose date folder (e.g., 2022_07_09) containing all trials from a single session/animal to
%be concatenated and set as current directory
cd(uigetdir);
folder = cd

%identify each time (=trial) folder
trials = dir; %ID trial folders (=times)
trials = trials(~ismember({trials.name},{'.','..'})); %get rid of '.' and '..' in list

%reorganize folders by temporal order (first->last, likely already the case)
A = datetime({trials.name}, 'InputFormat', 'HH_mm_ss', 'Format', 'preserveinput');
[B,I] = sort(A); %B=sorted times, I=corresponding indices in A

formatOut = 'HH_MM_SS';
for l = 1:length(B)
    ordered_trials {l} = datestr(B(l),formatOut);
end

%create new subfolder under date folder to compile all minicam trial
%videos into
mkdir minicam1_compiled
%mkdir minicam2_compiled

%loop to 1) identify each subdirectory containing the desired minicam videos for that trial
% (this part may need to be rewritten depending on structure variations), 
% 2) rename each video file in that subdirectory according to order of
% trial to be concatenated in correct order
for j = 1:length(ordered_trials)
    a = ordered_trials{j};
    date = cd(a);
    %get into the folder w the minicam videos
    trial = cd('MiniCam1'); %trial = cd('MiniCam2');
    %compile folder's video files into a list 
    files = dir('*.avi');
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
    
    %save copies of all the newly named videos in the new miniscope_compiled folder
    copyfile *.avi ../../minicam1_compiled
    %copyfile *.avi ../../minicam2_compiled

    %re-set directory back to the date folder for next loop iteration
    cd(date);

end
%%
%change directory to the folder containing newly compiled minicam files
cd('minicam1_compiled'); %cd('minicam2_compiled')

%create list of all file names
myFiles = dir('*.avi'); %gets all avi files in struct
for j = 1:length(myFiles) %place avi file names into list
        file_list {j} = myFiles(j).name;
        indx(j) = j;
end

%reorder file names so they are concatenated in correct order
sortedFiles = natsortfiles(file_list);


%% decide what to do with this section; from SM original code
mkdir('100FPS'); 
%% idk what's happening here; from SM original code

ID = split(folder, "\");
ID = ID(end);
filetype = string('.avi');
animalID = cell2mat(ID);
animalID = animalID + filetype; %likely need to change this section, not sure what going on here

%% make copies of all video clips at a new playback speed of 100 FPS
for k = 1:length(sortedFiles)
    baseFileName = sortedFiles(k);
    fullFileName = fullfile(cd, baseFileName); %change folder to minicam1_compiled, i think
    obj = VideoReader(fullFileName{1}); 
    newFileName = fullfile(cd, '\100FPS\', baseFileName); 
    obj2= VideoWriter(newFileName{1}); % Write in new variable 
    obj2.FrameRate = 100; %speed up playback of new video copy to 100FPS
    % % for reading frames one by one
    open(obj2)
    while hasFrame(obj)              
     k = readFrame(obj); 
%   
%     % write the frames in obj2.         
     obj2.writeVideo(k);          
    end
    close(obj2)

end
%% CONCATENATE VIDEOS
videoList = []; 
%for f = 1:length(sortedFiles)
%    videoList{f} = fullfile(cd, '\100FPS\' , sortedFiles(f));
%end

%just for testing first trial (15 miniCAM videos)
for f = 1:15
    videoList{f} = fullfile(cd, '\100FPS\' , sortedFiles(f));
end

% create output in seperate folder (to avoid accidentally using it as input)
mkdir('output');
outputVideo = VideoWriter(fullfile(cd,'output/mergedVideo.avi'));

% if all clips are from the same source/have the same specifications
% just initialize with the settings of the first video in videoList
inputVideo_init = VideoReader(videoList{1}{1}); % first video
outputVideo.FrameRate = inputVideo_init.FrameRate; %FrameRate = 100 for concatenated video

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