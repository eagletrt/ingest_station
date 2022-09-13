from audioop import avg
from genericpath import isfile
import pdb
import threading
import os
import argparse
import time
import subprocess
import shlex
import multiprocessing

IN_FOLDER_PATH=""
OUT_FOLDER_PATH=""
RAW_FILE_EXTENSION=".CR3"
Nproc=1

print("Seri, ma con brio")

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('folder', metavar='folder', type=str,
                    help='event folder to process')
parser.add_argument('-p', '--processes', type=int, default=1, help='number of processes to use')
parser.add_argument('-a', '--append', action='store_true', help='enable append to output event folder')

args = parser.parse_args()

if args.folder != None:
    IN_FOLDER_PATH = args.folder
    print(IN_FOLDER_PATH)

if args.processes != None:
    Nproc = args.processes

OUT_FOLDER_PATH = 'output/'+os.path.basename(os.path.normpath(IN_FOLDER_PATH))+'/'
COMMAND_TEMPLATE = 'ART/ART-cli -o "{output}" -d -c "{input}"'
print(IN_FOLDER_PATH,'->',OUT_FOLDER_PATH)

def find_pics(dir_path):
    res = []
    for path in os.listdir(dir_path):
        name=os.path.join(dir_path,path)
        # check if current path is a file
        if os.path.isfile(name) and path.endswith(RAW_FILE_EXTENSION) and not path.startswith('.'):
            res.append(name)
        elif os.path.isdir(name):
            res.extend(find_pics(name))
    return res

def convert(pic_path,queue):
    name = os.path.splitext(os.path.basename(os.path.normpath(pic_path)))[0]+'.jpg'
    name=name.replace(' ','_')
    print(pic_path,'->',OUT_FOLDER_PATH + name)

    if os.path.exists(OUT_FOLDER_PATH + name):
        print('file exists, skidpad')
        return

    ret = subprocess.run(
        shlex.split(COMMAND_TEMPLATE.format(output=OUT_FOLDER_PATH + name, input=pic_path)),
        check=True,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT
        )
    #print(ret)
    if ret.returncode != 0:
        print("Error converting: " + pic_path)
        print(ret.stdout)
    queue.put(time.time())

# make output directory
os.makedirs(OUT_FOLDER_PATH, exist_ok=args.append)
found_pics = find_pics(IN_FOLDER_PATH)
found_pics.sort()
#print(found_pics)

# pool=multiprocessing.Pool(Nproc)
queue=multiprocessing.Queue()
Npics=len(found_pics)
act=0
c = 0
last_time=0
avg_time = 0
while c < Npics or act!=0:
    if act < Nproc:
        act += 1
        t = multiprocessing.Process(target=convert, args=(found_pics[c], queue, ))
        t.start()
        c+=1
    else:
        queue.get()
        delta_time = time.time() - last_time
        print(f'P {c/Npics*100:.2f}% {c}/{Npics} ETA: {avg_time*(Npics-c):.0f}s AVG: {avg_time:.0f}s Last: {delta_time:.0f}s')
        last_time=time.time()
        avg_time = ((avg_time * (c-1)) + delta_time*(Npics-c))/c
        act -= 1

