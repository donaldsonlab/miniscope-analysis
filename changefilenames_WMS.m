%script to compile all miniscope video files from multiple trials within a
%single session into a single directory while maintaining their temporal
%order and renaming the files names so they can be concatenated correctly
%by minian. 
%
%prerequisite: structure of miniscope software output =
%xyz->animalName->date->time->exp_id->devices, with date = session date and time = each
%individual trial
%
% WMS modification to Samara Miller (UCLA) code, last update 220710

%clear workspace and command window
clc;clear

%choose date folder (e.g., 2022_07_09) containing all trials from a single session/animal to
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

%create new subfolder under date folder to compile all miniscope trial
%videos into
mkdir miniscope_compiled

%loop to 1) identify each subdirectory containing the miniscope videos for that trial
% (this part may need to be rewritten depending on structure variations), 
% 2) rename each miniscope file in that subdirectory according to order of
% trial, changing the syntax so minian will read in correct order
for j = 1:length(ordered_trials)
    a = ordered_trials{j};
    date = cd(a);
    d = dir; %next four lines are just getting into your exp_id folder, no matter what the name is (so long as there is only one exp_id folder, which there should be)
    real_dir = d(~ismember({d.name},{'.','..'}));
    exp_id = real_dir.name;
    trial = cd(exp_id);
    exp = cd('My_V4_Miniscope'); %get into the folder w the miniscope videos
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

    %first: figure out how minian concatenates files (i.e., will it go
    %09->10 (and also 08->11, if there are fewer than 10 files in a folder), or 09->010)
    %
    %pretty sure it is the former based on how natsort.natsorted works (see
    %minian pipeline and avi for details)

    %if the former:
    prefix = num2str(j-1); %first digit corresponds to loop iteration

    [~, f,ext] = fileparts(files(id).name);
    rename = strcat(prefix,'_',f,ext) ; %define new file name
    movefile(files(id).name, rename); %overwrite existing file name
    end
    
    %save copies of all the newly named videos in the new miniscope_compiled folder
    copyfile *.avi ../../../miniscope_compiled

    %re-set directory back to the date folder for next loop iteration
    cd(date);

end
