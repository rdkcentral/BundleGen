# For L1_testing
Main objective for L1_testing is checking the api’s functionality in *.py script.

## Environment Setup
Python version should be greater than or equal to 3.7 to run L1_testing.
Once installed the python version, setup the pip install
```console
    $ cd BundleGen
    $ pip install -r requirements.txt
    $ pip install --editable .
```

## How to run L1 test
Run the L1 test using the run_L1_test.py file.
## For all L1 test:
```bash
    $cd unit_tests/L1_testing
    $python run_L1_test.py
```
## For individual test:
```bash
    $cd unit_tests/L1_testing
    $python run_L1_test.py -s classname
    Ex: $python run_L1_test.py -s Bundleprocessor
```

## Adding additional testfiles
In L1_testing folder, add another test file(inside L1_testing/test_files/).
Filename should be named as follow '''test_classname_ut.py'''.
