import subprocess
import random
import os

csmith="csmith"

#filename should be under the working directory
def checkUB(cfilename):
    clangfc="clang -msse4.2 -m64 -O0  -fsanitize=undefined"
    timeout="timeout"
    filename=cfilename.split(".")[0]
    exe = "exe." + filename + "-clang"
    out = "out." + filename + "-clang"
    rm_cmd = ["rm", "-f", "-o", exe, cfilename]
    subprocess.call(rm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    compile_cmd = "timeout -s 9 5".split()
    compile_cmd.extend(clangfc.split())
    compile_cmd.extend([ "-o", exe, cfilename])
    cplt = subprocess.run(compile_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if(cplt.returncode != 0):
        print("Seed Program Generation: cannot compile")
        return 2

    run_cmd =  "timeout -s 9 10".split()
    run_cmd.append("./" + exe)
    with open(out, "w") as outf:
        cplt = subprocess.run(run_cmd, stdout=outf, stderr=subprocess.DEVNULL)
        if cplt.returncode != 0:
            print("Seed Program Generation: exe timeout")
            subprocess.call(rm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return 3
    
    rterrorflag=False
    with open(out, "r") as outf:
        for line in outf:
            if line.find("runtime error") >= 0:
                print("Seed Program Generation: runtime error in exe")
                rterrorflag=True
                break
    subprocess.call(rm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rterrorflag:
        return 1
    else:
        return 0

            





def gencsmith(cfilename):
    while True:
        all_swarm_opts= [
            #    "argc",
                "arrays",
            #    "bitfields",
                "checksum",
                "comma-operators",
                "compound-assignment",
                "consts",
                "divs",
                "embedded-assigns",
                "jumps",
                "longlong",
                "force-non-uniform-arrays",
                "math64",
                "builtins",
                "muls",
                "packed-struct",
                "paranoid",
                "pointers",
                "structs",
            #    "unions",
                "volatiles",
                "volatile-pointers",
            #    "inline-function",
            #    "return-structs",
                "arg-structs",
                #"return-unions",
                #"arg-unions",
                "dangling-global-pointers",
                #"return-dead-pointer",
                #"union-read-type-sensitive",
                ]
        extra = "--no-unions --safe-math --no-argc --no-inline-function --no-bitfields --no-return-structs --quiet --concise";
        swarm_opt = ""
        for opt in all_swarm_opts:
            p = random.randint(0, 99) / 100
            if p < 0.5:
                swarm_opt = swarm_opt + " --" + opt + " "
            else:
                swarm_opt = swarm_opt + " --no-" + opt + " " 
        #print(swarm_opt)
        csmith_cmd = [csmith]
        csmith_cmd.extend(swarm_opt.split())
        csmith_cmd.extend(extra.split())
        #print(csmith_cmd)
        with open(cfilename, "w") as cfile:
            subprocess.call(csmith_cmd, stdout=cfile)

        #check ub
        ret = checkUB(cfilename)
        if ret != 0:
            continue

        #check size
        minsize = 4000
        filesize = os.path.getsize(cfilename)
        if filesize < minsize:
            print("Seed Program Generation: generated C file too small")
            continue

        #check ccomp
        ccomp_cmd = "timeout -s 9 30 ccomp -interp -fall".split()
        ccomp_cmd.append(cfilename)
        cplt = subprocess.run(ccomp_cmd,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if cplt.returncode != 0:
            print("Seed Program Generation: generated C file cannot pass ccomp")
            continue

        print("Seed Program Generation: have a good seed file")
        return 0
        
