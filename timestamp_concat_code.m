%script to:
% 1) concatenate multiple timestamp .csv files produced by UCLA miniscope
% acquisition software over a single session (e.g., multiple trials within a session)
% and 
% 2) align the timestamps between files

%collect all timestamp files of each type and rename based on temporal
%order
%try doing a uigetdir loop or something where each pointed directory is
%assigned an index based on order - let the user define the order
%miniscope
%minicam1
%minicam2

%import the csvs into data structures

%reformat structure (if needed for Bento import)

%produce new empty structure for concatenation

%loop to add each csv in correct order 