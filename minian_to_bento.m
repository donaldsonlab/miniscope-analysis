%script to save minian output files (converted to netCDF format) as .mat file for bento import
%bento will take in C variable as a simple neuron x time matrix (neurons =
%rows, frames = columns, calcium intensity = values)
%adapted from Federico Sangiuliano code (UCLA; miniscope google groups)
%
%220727 WMS - still figuring out 1) what the best way to upload the C data
%matrix is for Bento to interpret the UCLA software-produced timestamps for
%alignment with behavioral videos, and 2) whether A data (spatial
%footprints) can be uploaded into Bento (both 1 and 2 seem possible, at
%least in matlab distribution of Bento)

clc;clear

%point to directory with the minian-outputted netcdf file
cd \\penc8.rc.int.colorado.edu\donaldsonlab\Sheeran\miniscope_files\analyzed\5001\2022_09_02\11_40_34\miniscope_compiled\

%%read in variables from that file

Adata = ncread('minian_dataset.nc','A'); %spatial footprints, likely need to transpose
Cdata = ncread('minian_dataset.nc','C_curate'); %temporal values
Sdata = ncread('minian_dataset.nc','S'); 

%transpose matrix so that each neuron is its own row vs column (as needed
%by bento)
Cdata_trans = transpose(Cdata);

%drop NaN rows (apparently not dropped in the cell in minian pipeline)
C_final = Cdata_trans(sum(isnan(Cdata_trans),2)==0,:);


%WMS thought this structure would work w bento for a data and timestamp
%compatability but it didnt :(
%(create structure array with fieldnames = variable names and embedded
%arrays called "data" for each)
%minian_mat.A.data = Adata;
%minian_mat.C.data = Cdata_trans;
%minian_mat.S.data = Sdata;

%pick directory to save transposed matrix into
%cd(uigetdir);

%save matrix into new .mat file (accepted input format from bento)
save('minianCouput_mat', "C_final") 
%save('minianoutput_mat', 'minian_mat') this was a format that WMS thought would work for bento but didn't 