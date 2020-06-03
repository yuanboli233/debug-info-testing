# debug-info-testing
Debugging Information Validation

This is a python implementation for the debug-information testing framework for the paper "Debug Information Validation for Optimized Code"

Dependency:
    
This project depends on the following tools, please make sure you have the following tools available:
        
csmith 

gcovr

gcc

clang

To test a clang compiler, please set "clang" as a softlink to the clang compiler with the desired version you wish to test.

Usage:
    ./config.sh
    python3 test-debug-info.py
