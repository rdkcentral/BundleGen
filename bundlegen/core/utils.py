# If not stated otherwise in this file or this component's license file the
# following copyright and licenses apply:
#
# Copyright 2020 Consult Red
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import shlex
import uuid
import tarfile
import os

from loguru import logger


class Utils:

    # ==========================================================================
    @staticmethod
    def run_process(command):
        """Runs the process with the specified command

        Will stream the stdout of the process to the console

        Args:
            command (string): Command with args to run

        Returns:
            int: Return code from the process
        """
        # Run the process
        process = subprocess.Popen(shlex.split(
            command), shell=False, stdout=subprocess.PIPE)

        # Monitor the stdout and print to the screen
        for line in iter(process.stdout.readline, b''):
            logger.debug(line.strip().decode())

        # Process has finished, clean up and get the return code
        process.stdout.close()
        return_code = process.wait()
        return return_code

    # ==========================================================================
    @staticmethod
    def run_process_and_return_output(command):
        """Runs the process with the specified command
        Will return the stdout of the process
        Args:
            command (string): Command with args to run
        Returns:
            int: Return code from the process
            string: stdout from the process
        """
        # Run the process
        process = subprocess.Popen(shlex.split(
            command), shell=False, stdout=subprocess.PIPE)

        out, err = process.communicate()

        # Process has finished, clean up and get the return code
        process.stdout.close()
        return_code = process.wait()
        return return_code, out.decode()

    # ==========================================================================
    @staticmethod
    def get_random_string(length=32):
        """Creates a string of random characters

        Args:
            length (int, optional): Length of the string to generate. Defaults to 32.

        Returns:
            string: Random string
        """
        string = uuid.uuid4().hex.lower()

        if length >= len(string):
            return string

        return string[:length]

    # ==========================================================================
    @staticmethod
    def create_tgz(source, dest):
        """Create a .tar.gz file of the source directory. Contents of source directory
        is at the root of the tar.gz file.

        Args:
            source (string): Path to directory to compress
            dest (string): Where to save the tarball

        Returns:
            bool: True for success
        """

        if not dest.endswith(".tar.gz"):
            output_filename = f'{dest}.tar.gz'
        else:
            output_filename = dest

        logger.info(f"Creating tgz of {source} as {output_filename}")
        source = os.path.abspath(source)

        # Make sure the bundle is at the root of the tarball
        source = source + '/'

        if not os.path.exists(source):
            logger.error("Cannot create tar - source directory does not exist")
            return False

        if os.path.exists(output_filename):
            os.remove(output_filename)

        with tarfile.open(f'{output_filename}', "w:gz") as tar:
            tar.add(source, arcname=os.path.basename(source))

        return True
