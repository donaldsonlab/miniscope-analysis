# miniscope-analysis
Code forming various parts of the lab's pipeline for UCLA miniscope data analysis

# Current outline of pipeline (as of 8/19/22):
1) Pre-process miniscope videos (i.e., rename all clips for proper import into/concatenation by minian and, if need be, collect all videos from all trials within a single recording session)
    - changefilenames_WMS.m

2) Import pre-processed miniscope videos into minian and run pipeline

3) Export minian output (specifically the C variable = calcium traces) as NetCDF file
    - 

4) Import NetCDF file into matlab, transpose matrix, save as .mat file for import into Bento
    - minian_to_bento.m

5) Concatenate all behavioral video files (and, if need be, collect all videos from all trials within a single recording session in order)
    -miniCAM_concat_code.m

6) Import concatenated video file(s) and C data matrix into Bento, along with corresponding timestamp files produced by miniscope DAQ software (pending support for timestamp file-based feed alignment in Bento - coming soon?)
    - for now, for alignment outside of Bento, use timestamp_align.py (once also have a Cleversys .txt output for the behavioral videos; WMS needs to write a pipeline to incorporate these functions)

7) Run behavioral video(s) through Cleversys (or, eventually DLC->SiMBA or MARS)

8) Run Cleversys .txt output through modified version of DWP parser for import into Bento

9) Run parsed Cleversys output (or eventually DLC output) through spatial_bin_occupancy script for place cell analysis (WMS needs to write this script)

10) Import parsed Cleversys output and spatial_bin_occupancy script output into Bento (WMS needs to modify Bento-MAT loadAnyAnnot.m script to enable this)

11) Visually confirm aligned inputs and run any desired/supported analysis in Bento

12) Produce .annot file structure containing all aligned data for future custom analysis scripts
