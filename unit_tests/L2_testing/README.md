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
* If appmetadata was not given by user, it extracts appmetadata.json from oci image, storing into unit_tests/L2_testing/metadatas folder.
* After running L2 test script file it removes all extracted ones and only oci image tar file in unit_tests/L2_testing/oci_images will be remaining.


## How to run L2 test
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py
```

## For specified app
* Required Parameters to run L2 test is appname.
* appname should be given like this dac-image-```<appname>```
* If platformname is not specified it will take default platformname has ''rpi3_reference_vc4_dunfell''
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -a appname
    Ex:  python run_L2_test.py -a dac-image-wayland-egl-test
```
## For specified platform
* Required Parameters to run L2 test is platformname.
* It will run all oci images present in oci_images folder.
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -t platformname
    Ex:  python run_L2_test.py -t rpi3_reference
```
## For specified appmetadata
* Required Parameters to run L2 test is appmetadata.
* Appmetadata should be given like this dac-image-```<appname>```-appmetadata.
* If platformname is not specified it will take default platformname has ''rpi3_reference_vc4_dunfell''
* It will run for specified app, i.e., mentioned in Appmetadata.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -m appmetadata
    Ex:  python run_L2_test.py -m dac-image-wayland-egl-test-appmetadata
```
## For particular app and platform
* Required Parameters to run L2 test are appname and platformname.
* appname should be given like this dac-image-```<appname>```
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -a appname -t platformname
    Ex:  python run_L2_test.py -a dac-image-wayland-egl-test -t rpi3_reference
```
## For particular app and appmetadata
* Required Parameters to run L2 test are appname and appmetadata.
* appname should be given like this dac-image-```<appname>```
* Appmetadata should be given like this dac-image-```<appname>```-appmetadata.
* If platformname is not specified it will take default platformname has ''rpi3_reference_vc4_dunfell''
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -a appname -m appmetadata
    Ex:  python run_L2_test.py -a dac-image-wayland-egl-test -m dac-image-wayland-egl-test-appmetadata
```
## For particular appmetadata and platform
* Required Parameters to run L2 test are appmetadata and platformname.
* Appmetadata should be given like this dac-image-```<appname>```-appmetadata.
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -m appmetadata -t platformname
    Ex:  python run_L2_test.py -m dac-image-wayland-egl-test-appmetadata -t rpi3_reference
```
## For particular app, appmetadata and platform
* Required Parameters to run L2 test are appname, appmetadata and platformname.
* appname should be given like this dac-image-```<appname>```
* appmetadata should be given like this dac-image-```<appname>```-appmetadata.
* Run the L2 test using the run_L2_test.py file.
```console
    $ cd unit_tests/L2_testing
    $ python run_L2_test.py -a appname -m appmetadata -t platformname
    Ex:  python run_L2_test.py -a dac-image-wayland-egl-test -m dac-image-wayland-egl-test-appmetadata -t rpi3_reference
```