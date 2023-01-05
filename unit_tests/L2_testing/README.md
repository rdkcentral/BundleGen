# L2 Testing
Main objective of L2 testing is verifying the bundle image for an individual app which was taken from oci image.

## Pre-requisites
Copy oci image tar file and place it in unit_tests/L2_testing/oci_images folder.

## Environment Setup
-> Python version should be greater than or equal to 3.7 to run L2_testing.
-> Once the python is installed, install and setup pip
```console
    $ cd BundleGen
    $ pip install -r requirements.txt
    $ pip install --editable .
```

## run_L2_test.py workflow
-> Extracting oci image and storing in unit_tests/L2_testing/oci_images folder.
-> Generating a bundle with extracted oci_image and stores it in unit_tests/L2_testing/bundlegen_images folder.
-> Extracting bundle image in unit_tests/L2_testing/bundlegen_images folder.
-> Extracting appmetadata.json from oci image, storing into unit_tests/L2_testing/metadatas folder.
-> After running L2 test script file it removes all extracted ones and only oci image tar file in unit_tests/L2_testing/oci_images will be remaining.

## How to run L2 test
-> Required Parameters to run L2 test are Appname and Platformname.
-> Appname should named as dac-image-<Appname>
-> Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -a appname -p platformname
    Ex:  python run_L2_test.py -a dac-image-wayland-egl-test -p rpi3_reference
```