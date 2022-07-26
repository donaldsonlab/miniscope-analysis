%script to save minian output files as .mat file for bento import
%adapted from FS code (miniscope google groups)
clc;clear

%point to directory with the minian-outputted netcdf file
cd C:\Users\sheer\minian

%%read in variables from that file

Adata = ncread('minian_dataset.nc','A'); %spatial footprints, likely need to transpose
Cdata = ncread('minian_dataset.nc','C'); %temporal values
Sdata = ncread('minian_dataset.nc','S'); 

%transpose matrix so that each neuron is its own row vs column (as needed
%by bento)
Cdata_trans = transpose(Cdata);

%create structure array with fieldnames = variable names and embedded
%arrays called "data" for each
minian_mat.A.data = Adata;
minian_mat.C.data = Cdata_trans;
minian_mat.S.data = Sdata;

%pick directory to save transposed matrix into
cd(uigetdir);

%save matrix into new .mat file (accepted input format from bento)
save('minianoutput_mat', 'minian_mat')