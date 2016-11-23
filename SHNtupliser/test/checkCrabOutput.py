import tarfile
from CRABAPI.RawCommand import crabCommand
import datetime
import glob

import contextlib
import sys
import os

class DummyFile(object):
    def write(self, x): pass

@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout

def find_missing_jobs(output_dir,nrjobs):
    file_extension = ".root"
    root_files = glob.glob(output_dir+"/0000/*"+file_extension)
    
    jobs_found=[]
    for root_file in root_files:
        file_name = root_file.split("/")[-1]
        jobnr = file_name.split("_")[-1].split(file_extension)[0]
        jobs_found.append(int(jobnr))
    
    jobs_notfound=[]
    for nr in range(1,nrjobs+1):
        if nr not in jobs_found:
            jobs_notfound.append(nr)
    return jobs_notfound
            

#there may be a small timestamp descripancy of a second or two
#so we need to figure it out
#we know its the format YYMMDD_HHMMSS
#so we compare YYMMDD_HHMM 
def get_grid_output_dir(base_dir,timestamp):
    subdirs = [p.split("/")[-2] for p in glob.glob(base_dir+"/*/")]
#    print timestamp
    for subdir in subdirs:
#        help(datetime.datetime.strptime(subdir,"%y%m%d_%H%M%S"))
#        print datetime.datetime.strptime(subdir,"%y%m%d_%H%M%S").time().time()
        if timestamp[:-2]==subdir[:-2] and abs(int(timestamp[-2:])-int(subdir[-2:])<=2):
            return base_dir+"/"+subdir
    return base_dir+"/"+timestamp

def check_crab_output(crab_dir):
    
    #first get the config file to figure out where the data was written too
    job_data =tarfile.open(crab_dir+"/inputs/debugFiles.tgz")    
    config_file = job_data.extractfile(job_data.getmember("debug/crabConfig.py"))
    exec(''.join(config_file.readlines()))

   # for line in config_file.readlines():
   #     print line,
    with nostdout():
        status = crabCommand('status',dir = crab_dir)

    #jobsPerStatus
    nrjobs = len(status['jobList'])
    
    #right time to build the output dir
    timestamp = datetime.datetime.fromtimestamp(int(status['submissionTime'])).strftime('%y%m%d_%H%M%S')
    grid_output_dir = get_grid_output_dir("/pnfs/pp.rl.ac.uk/data/cms"+config.Data.outLFNDirBase+"/"+config.Data.inputDataset.split("/")[1]+"/"+config.Data.outputDatasetTag+"/",timestamp)
    print grid_output_dir
    missing_jobs = find_missing_jobs(grid_output_dir,nrjobs)

    if not missing_jobs:
        print crab_dir," : all jobs completed"
    else:
        print crab_dir," : jobs missing"
        for jobnr in missing_jobs:
            print "   ",jobnr,status['jobs'][str(jobnr)]['State']
            


if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser(description='checks if the crab output is ')
    parser.add_argument('crab_dirs',nargs='+',help='list of crab directories to check')
    args = parser.parse_args()

    for crab_dir in args.crab_dirs:
        check_crab_output(crab_dir)
