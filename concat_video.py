import json
import os
import ffmpeg

def get_video_list(path):
    
    #create a file list of files that dont start with a .
    file_set = [f for f in glob.glob(os.path.join(path,'*.avi')) if not f.startswith('.')]
    
    #return this list sorted by the digits (regex match \D to replace all non-digit characters with ''), 
    #os.path.split(path)[-1] gives us just the filename, leaving out the dates
    
    return sorted(file_set, key=lambda x: int(re.sub('\D', '',os.path.split(x)[-1])))

def get_framerate(json_file):
    with open(json_file) as f:
        metadata = json.load(f)
    return metadata['frameRate']

def concat_vid_list(vid_list, output_loc, output_name):
    temp_f = os.path.join(output_loc,'temp_vid_list.txt')
    with open(temp_f, 'w') as f:
        for vid in vid_list:
            f.write(f"file '{vid}'\n")
    
    ffmpeg_cmd = f"ffmpeg -f concat -safe 0 -i {temp_f} -c copy {os.path.join(output_loc,output_name)}"
    os.system(ffmpeg_cmd)
    
"""loc = '/mnt/working_storage/minian/5015/2022_07_29/13_54_34/baseplate/test_concat'
out_loc = '/mnt/working_storage/minian/5015/2022_07_29/13_54_34/baseplate/test_concat'
out_name = 'test_merge.avi'"""
def run_merge(loc, out_location, merged_name):
    vl = get_video_list(loc)
    concat_vid_list(vl, out_location, merged_name)