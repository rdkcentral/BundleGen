# L2 Testing
Main objective of L2 testing is verifying the bundle image for an individual app which was taken from oci image.

## Pre-requisites
* Copy oci image tar file and place it in unit_tests/L2_testing/oci_images folder.
* Oci Image should be named in the form of appname and platformname.
```
<appname>-<platform>-oci.tar
Ex: dac-image-wayland-egl-test-raspberrypi3-oci.tar
```
Filename should not be saved as mentioned above, it will throw below error
```
File name should consists of platform name
```

## Environment Setup
* Python version should be greater than or equal to 3.7 to run L2_testing.
* Once the python is installed, install and setup pip
```console
    $ cd BundleGen
    $ pip install -r requirements.txt
    $ pip install --editable .
```

## run_L2_test.py workflow
* Extracting oci image and storing in unit_tests/L2_testing/oci_images folder.
* Generating a bundle with extracted oci_image and stores it in unit_tests/L2_testing/bundlegen_images folder.
* Extracting bundle image in unit_tests/L2_testing/bundlegen_images folder.
* Extracting appmetadata.json from oci image, storing into unit_tests/L2_testing/metadatas folder.
* After running L2 test script file it removes all extracted ones and only oci image tar file in unit_tests/L2_testing/oci_images will be remaining.


## How to run L2 test
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py
```

## For specified app
* Required Parameters to run L2 test is Appname.
* Appname should named as dac-image-<Appname>
* If platformname is not specified it will take default platformname has ''rpi3_reference_vc4_dunfell''
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -a appname
    Ex:  python run_L2_test.py -a dac-image-wayland-egl-test
```
## For specified platform
* Required Parameters to run L2 test is Platformname.
* Appname should named as dac-image-<Appname>, it will run all oci images present in oci_images folder.
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -t platformname
    Ex:  python run_L2_test.py -t rpi3_reference
```
## For particular app and platform
* Required Parameters to run L2 test are Appname and Platformname.
* Appname should named as dac-image-<Appname>
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -a appname -t platformname
    Ex:  python run_L2_test.py -a dac-image-wayland-egl-test -t rpi3_reference
```
## For user specified app metadata
* Required Parameters to run L2 test are Appname and App Metadata
* App metadata should be named as dac-image-<Appname>-appmetadata
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -m appmetadata -a appname
    Ex:  python run_L2_test.py -m "dac-image-wayland-egl-test-appmetadata" -a "dac-image-wayland-egl-test"
```