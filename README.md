# Debugging Information Testing

This is a python implementation for the debug-information testing framework for the paper 
    - Debug Information Validation for Optimized Code in *PLDI* 2020 by Yuanbo Li, Shuo Ding, Qirun Zhang, Davide Italiano

## Dependency:
    
This project depends on the following tools, please make sure you have the following tools available:
        
- csmith 
- gcovr
- gcc
- clang
- dexter (code included in the repo)

To test a clang compiler, please set "clang" as a softlink to the clang compiler with the desired version you wish to test.

## Usage:
```
    ./config.sh
    python3 test-debug-info.py
```
Bugs found by the framework will be put under "bugs" directory.
