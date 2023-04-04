# For L1_testing
* Main objective for L1_testing is checking the api’s functionality in *.py script.

## Environment Setup
* Python version should be greater than or equal to 3.7 to run L1_testing.
* Once installed the python version, setup the pip install
```console
    $ cd BundleGen
    $ pip install -r requirements.txt
    $ pip install --editable .
```

## How to run L1 test without coverage report
* Run the L1 test using the run_L1_test.py file.
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

## How to run L1 test with coverage report
* Run the L1 test using the run_L1_test.py file.
## For all L1 test:
```bash
    $cd unit_tests/L1_testing
    $python run_L1_test.py -c coverage_report
```
## For individual test:
```bash
    $cd unit_tests/L1_testing
    $python run_L1_test.py -s classname
    Ex: $python run_L1_test.py -s Bundleprocessor -c coverage_report
```

## Adding additional testfiles
* In L1_testing folder, add another test file(inside L1_testing/test_files/).
* Filename should be named as follow '''test_classname_ut.py'''.
* In test_data_files to test ReadElf.retrieve_apiversions method libBrokenLocale-2.31.so file is renamed to libBrokenLocale-2.31.1
