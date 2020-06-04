#!/bin/python3

import os, sys
import imp
import shutil
import random
import subprocess
import glob
import gencsmith
dexter_commands = {'expect':'DexExpectWatchValue'}
dwarf_reader_py = "./dwarf-lines-reader.py"
dexter_py = "./dexter/dexter.py"
lldb_executable = "lldb"
clang_executable = "clang"

def generate_dex_file(cfile, newfile, actual_line, var_name, var_value):
    with open(cfile, "r") as inf:
        with open(newfile, "w") as outf:
            for ln in inf:
                outf.write(ln)
            dexter_str = '//' + dexter_commands['expect'] + '(\'' + var_name + "\', \'" + var_value + "\', on_line=" + str(actual_line) + ")\n"
            outf.write(dexter_str)

def load_lldb_interface():
    lldb_executable = "lldb"
    args = [lldb_executable, '-P']
    pythonpath = subprocess.check_output(args, stderr=subprocess.STDOUT).rstrip().decode('utf-8')
    module_info = imp.find_module('lldb', [pythonpath])
    return imp.load_module('lldb', *module_info)

def dynamicVerify(cfile):
    ccomp_cmd = "ccomp -interp -fall".split() 
    ccomp_cmd.extend([cfile])
    if run_and_get_returncode(ccomp_cmd) == 0:
        return True
    else:
        return False


def shadow_validation(origfile, shadowfile, linenum, var_name, var_type):
    rm_cmd = ["rm", shadowfile]
    run_and_get_returncode(rm_cmd)
    shadow_cmd = "python3 shadow_create.py".split()
    shadow_cmd.extend([origfile, shadowfile, var_type, var_name, str(linenum)])
    ret = run_and_get_returncode(shadow_cmd)
    if ret != 0:
        return False
    if dynamicVerify(shadowfile):
        return True
    else:
        return False


def instrument_code(cfile, linenum, orig_cfile) -> int:
    # part 1 get O0 value
    accept_types = {"int", "short", "unsigned short", "unsigned int"}
    tmpc = "tmp.c"
    shadowc = "shadow.c"
    lldb = load_lldb_interface()
    #print("loaded lldb interface")

    # compile in O0
    rm_cmd = "rm a.out".split()
    run_and_get_returncode(rm_cmd)
    compile_cmd = [
            clang_executable,
            cfile,
            "-g",
            "-O0"]
    if(orig_cfile != cfile):
        #b.o contains opt() definition
        compile_cmd.extend(["b.o"])
    ret = run_and_get_returncode(compile_cmd)
    if ret != 0:
        print("does not compile in O0")
        return 1
    #print("compiled")

    # setup debugger
    debugger = lldb.SBDebugger.Create()
    print("seeking appropriate variables")
    #print("create a debugger: ", debugger)
    debugger.SetAsync(False)
    binary_exe = "a.out"
    #print("creating a target for ", binary_exe)
    target = debugger.CreateTargetWithFileAndArch(binary_exe, "x86_64")
    #print("get a target, ", target)
    line = linenum
    bp = target.BreakpointCreateByLocation(cfile, line)
    if not bp:
        #print("fail to create breakpoint at ", cfile, ":", line)
        return 2
    #print("create a breakpoint: ", bp)
    process = target.LaunchSimple (None, None, os.getcwd())
    if process:
        state = process.GetState()
        if state != lldb.eStateStopped:
            #print("debugger can not stop.\n")
            return 3
        else:
            thread = process.GetThreadAtIndex(0)
            frame = thread.GetFrameAtIndex(0)
            actual_line = frame.GetLineEntry().GetLine()
            #print("actual line:", actual_line)
            for var in frame.get_locals():
                if "*" in var.__str__():
                    continue
                if "[" in var.__str__():
                    continue
                if "out of scope" in var.__str__():
                    continue
                var_name = var.__str__().split(")")[-1].split("=")[0].strip()
                var_value = var.__str__().split(")")[-1].split("=")[-1].strip()
                var_type = var.GetType().GetCanonicalType().__str__().strip()
                #print(var_name, "has value", var_value, " with type:", var_type)
                # shadow validation
                if var_type in accept_types:
                    shadowresult = shadow_validation(orig_cfile, shadowc, actual_line, var_name, var_type)
                    if shadowresult:
                        print("Shadow validation passed for variable", var_name, "at line", actual_line)
                    else:
                        print("Shadow validation failed for variable", var_name, "at line", actual_line)
                        continue

                    # check value consistency
                    generate_dex_file(cfile, tmpc, actual_line, var_name, var_value)
                    check_correctness(tmpc)

        process.Kill()
    return 0



def check_correctness(tmpc):
    rm_cmd = "rm out_O3.txt".split()
    run_and_get_returncode(rm_cmd)
    print("test correctness in O3")
    dex_output = "dex_output.txt"
    rmdex_cmd = ["rm", dex_output]
    run_and_get_returncode(rmdex_cmd)
    
    run_dex_cmd=[
            "python3", 
            dexter_py,
            "test", 
            "--builder=clang-c",
            "--debugger=lldb",
            "--cflags", "-g -O3",
            "-v",
            tmpc]
    with open(dex_output, "w") as dex_outputf:
        ret = run_and_get_returncode(run_dex_cmd, outf=dex_outputf, errf=dex_outputf)
        if ret != 0:
            print("dexter does not run properly, please check settings")
    with open(dex_output, "r") as dex_outputf:
        for line in dex_outputf:
            if line.find("unexpected result:") >= 0:
                print("===============================")
                print("Found a bug")
                bugid = random.randint(0, 1000000)
                bugfile = "bug_" + str(bugid) + ".c"
                bugpath = os.path.join("bugs", bugfile)
                shutil.copyfile(tmpc, bugpath)
    return


def debugger_test_main(cfile, line_to_stop, orig_cfile):
    instrument_code(cfile, line_to_stop, orig_cfile)
    return

def run_and_get_returncode(cmd, outf=subprocess.DEVNULL, errf=subprocess.DEVNULL):
    cplt = subprocess.run(cmd, stdout=outf, stderr=errf)
    return cplt.returncode
    

# prepare for gcovr
def prepare_gcc_coverage(cfile):
    rm_cmd = "rm a.out".split()
    rm_cmd.extend([f for f in glob.glob("*.gcda")]) 
    rm_cmd.extend([f for f in glob.glob("*.gcno")]) 
    run_and_get_returncode(rm_cmd)
    devnull = subprocess.DEVNULL
    gcc_compile_cmd="gcc -msse4.2 -fprofile-arcs -ftest-coverage -fPIC -O0".split()
    gcc_compile_cmd.append(cfile)
    if run_and_get_returncode(gcc_compile_cmd, subprocess.DEVNULL, subprocess.DEVNULL) != 0:
        print("gcc cannot compile!")
        return 1
    run_exe_cmd = "timeout -s 9 10 ./a.out".split()
    if run_and_get_returncode(run_exe_cmd, devnull, devnull) != 0:
        print("gcc exe cannot run or timeout")
        return 2
    return 0

def collect_reach_lines(gcovtxt):
    reach_lines = set()
    with open(gcovtxt, "r") as inf:
        for line in inf:
            if "%" in line and "TOTAL" not in line:
                line = line.split("%")[-1].strip()
                for l in line.split(","):
                    if l.find("-") >= 0:
                        # multiple lines
                        start = l.split("-")[0]
                        end = l.split("-")[-1]
                        for i in range(int(start.strip()), int(end.strip())+1):
                            reach_lines.add(i)
                    else:
                        # single line
                        reach_lines.add(int(l.strip()))
                    #print(l)
    #print(reach_lines)
    return reach_lines
                

def get_coverage(cfile):
    gcovtxt = "gcov.txt"
    rm_cmd=["rm", gcovtxt]
    run_and_get_returncode(rm_cmd)
    run_gcovr_cmd = "gcovr -r .".split()
    with open(gcovtxt, "w") as txtf:
        run_and_get_returncode(run_gcovr_cmd, outf=txtf)
    
    return collect_reach_lines(gcovtxt)

def collect_stoppable_lines(line_file):
    stoppable_lines = set()
    with open(line_file, "r") as inf:
        for line in inf:
            stoppable_lines.add(int(line.strip()))
    return stoppable_lines


def get_stoppable_lines(cfile):
    rm_cmd = "rm a.out dwarf_line".split()
    dwarf_line_file = "dwarf_line.txt"
    run_and_get_returncode(rm_cmd)
    gcc_compile = "gcc -msse4.2".split()
    gcc_compile.extend([cfile])
    gcc_compile.extend("-g -O3".split())
    if run_and_get_returncode(gcc_compile) != 0:
        print("gcc cannot compile")
        return 1
    run_dwarf_line_cmd = ["python3", dwarf_reader_py]
    run_dwarf_line_cmd.append(cfile)
    run_dwarf_line_cmd.append("a.out")
    #print(run_dwarf_line_cmd)
    with open(dwarf_line_file, "w") as dwarff:
        if run_and_get_returncode(run_dwarf_line_cmd, outf=dwarff) != 0:
            print("===========\ndwarf_reader may not run appropriately, please check setting.")
    return collect_stoppable_lines(dwarf_line_file)
    


 


def instrument_and_test(cfile, newfile, reach_lines, stop_lines):
    print("start instrument and test")
    #print("reach lines:", reach_lines)
    #print("stoppable lines:", stop_lines)
    for linenum in list(stop_lines):
        print("checking for line", linenum)
        debugger_test_main(cfile, linenum, cfile)
    rm_cmd=["rm", newfile]
    run_and_get_returncode(rm_cmd)
    candidate_reaches = set()
    reach_list = list(reach_lines)
    for i in range(0, 10):
        randidx = random.randint(0, len(reach_list)-1)
        candidate_reaches.add(reach_list[randidx])
    
    for linenum in candidate_reaches:
        print("generate cc_inst for line", linenum)
        with open(cfile, "r") as inf:
            with open(newfile, "w") as outf:
                line_count = 1
                for line in inf:
                    if line_count != linenum:
                        outf.write(line)
                    else:
                        if "return" in line:
                            outf.write("opt();" + line)
                        elif "int main" in line:
                            outf.write(line)
                        elif "}" in line:
                            outf.write("opt();" + line )
                        else:
                            outf.write("opt();\n" + line)

                    line_count += 1
        debugger_test_main(newfile, linenum, cfile)
        print("tested for line", linenum)
    return




def test_gdb():
    cfile = "cc.c"
    inst_file = "cc_inst.c"
    while True:
        gencsmith.gencsmith(cfile) 
        print("Working on a new valid C file")
        if prepare_gcc_coverage(cfile) != 0:
            continue
        print("gcc sanity check finish")
        reach_lines = get_coverage(cfile)
        stoppable_lines = get_stoppable_lines(cfile)
        #print("collect reachable lines")
        #print(stoppable_lines)
        instrument_and_test(cfile, inst_file, reach_lines, stoppable_lines)


if __name__ == "__main__":
    test_gdb()
