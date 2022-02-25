#!/bin/bash

# Copyright 2022 Liberty Global Services B.V.
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

function action_help {
    echo ""
    echo "Action can be one of:"
    echo ""
    echo " (requires valid APP_ID)"
    echo "  kill      - terminates the application"
    echo "  uninstall - uninstall the application"
    echo "  install   - install copied application"
    echo "  run       - launch the application"
    echo "  focus     - executes moveToFront and setFocus"
    echo ""
    echo " (ignores APP_ID - but the argument has to be given)"
    echo "  list      - list of installed applications"
    echo "  apps      - list of running applications"
    echo "  probe     - check if LISA service running"
    echo ""
    echo 'or unique abbreviation e.g. "ru", "r" for run action.'
    echo ""
    echo "If list of actions is empty then the default list of actions is as follows:"
    echo "  kill uninstall install run focus"
    echo ""
}

if [ "$#" -lt 2 ]; then
    echo "Usage:"
    echo "./testapp.sh <IP_ADDRESS> <APP_ID> [[actions1] action2] ..."
    echo ""
    echo " IP_ADDRESS - hostname or IP address of the target device"
    echo ""
    echo " APP_ID     - application ID or DAC bundle (path to bundle.tar.gz file)"
    echo '              Note: value of the APP_ID is ignored for the "list" and "apps" action.'
    action_help
    exit
fi

BOXIP=$1
PKG=$2
PKGNAME=`basename "${PKG}"`
PKGID="${PKG}"
PKGID="${PKGID%.bz2}"
PKGID="${PKGID%.xz}"
PKGID="${PKGID%.gz}"
PKGID="${PKGID%.tar}"
PKGID="${PKGID%.tgz}"
PKGID=`basename "${PKGID}"`
echo "--> Using Application ID: ${PKGID}"

function kill_app {
  echo "--> Killing app"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n --arg client "$PKGID" '{jsonrpc: "2.0", id: 1, method: "org.rdk.RDKShell.1.kill",  params: {client: $client}}'`
  echo
}

function uninstall_app {
  echo "--> Uninstall app"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n --arg pkgId "$PKGID" '{jsonrpc: "2.0", id: 1, method: "LISA.1.uninstall",  params: {id: $pkgId, version: "1.0", type: "dac", uninstallType: "full" }}'`
  echo

  # loop until app removed
  STATUS="....."
  while [ "$STATUS" != '""' ];
  do
    echo "--> Waiting until app removed..."
    sleep 2
    STATUS=`curl -s -X POST http://$BOXIP:9998/jsonrpc -d $(jq -c -n --arg pkgId "$PKGID" '{jsonrpc: "2.0", id: 1, method: "LISA.1.getStorageDetails",  params: {id: $pkgId, type: "dac", version: "1.0"}}') | jq '.result.apps.path' `
  done
  echo "--> App is removed!"
}

function install_app {
  echo "--> Copying bundle to box on lighttpd server location"
  echo "root@$BOXIP:/opt/www/${PKGNAME}"
  scp -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -C "${PKG}" "root@$BOXIP:/opt/www/${PKGNAME}"

  echo "--> Start (re-)installation of app"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n --arg pkgId "$PKGID" --arg url "http://127.0.0.1:50050/${PKGNAME}" '{jsonrpc: "2.0", id: 1, method: "LISA.1.install",  params: {id: $pkgId, url: $url, version: "1.0", appName: "testapp", type: "dac", category: "category"}}'`
  echo

  ## loop until app installed
  INSTALLED='""'
  while [ "$INSTALLED" == '""' ];
  do
    echo "--> Waiting until app installed..."
    sleep 2
    INSTALLED=`curl -s -X POST http://$BOXIP:9998/jsonrpc -d $(jq -c -n --arg pkgId "$PKGID" '{jsonrpc: "2.0", id: 1, method: "LISA.1.getStorageDetails",  params: {id: $pkgId, type: "dac", version: "1.0"}}') | jq '.result.apps.path' `
  done

  echo "--> App is installed!"
  ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no root@$BOXIP rm -f "/opt/www/${PKGNAME}"
}

function run_app {
  ## run app
  echo "--> Starting app!"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d \
    `jq -c -n --arg client "$PKGID" --arg client "$PKGID" --arg uri "$PKGID;1.0" '{jsonrpc: "2.0", id: 1, method: "org.rdk.RDKShell.1.launchApplication",  params: {client: $client, mimeType: "application/dac.native", uri: $uri}}'`
  echo
}

function focus_app {
  ## move to front and focus the app
  echo "--> Focus app!"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n --arg client "$PKGID" '{jsonrpc: "2.0", id: 1, method: "org.rdk.RDKShell.1.moveToFront",  params: {client: $client}}'`
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n --arg client "$PKGID" '{jsonrpc: "2.0", id: 1, method: "org.rdk.RDKShell.1.setFocus",  params: {client: $client}}'`
}

function list_installed_app {
  ## list installed applications
  echo "--> List installed applications"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n '{jsonrpc: "2.0", id: 1, method: "LISA.1.getList"}'` | jq '.result.apps'
}

function list_running_app {
  ## list running applications
  echo "--> List running applications"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n '{jsonrpc: "2.0", id: 1, method: "org.rdk.RDKShell.1.getClients"}'` | jq .
}

function probe {
  echo "--> Probe LISA"
  CMD=`jq -c -n '{jsonrpc: "2.0", id: 1, method: "LISA.1.getList"}'`
  RESULT=`curl -s -X POST http://$BOXIP:9998/jsonrpc -d $CMD | grep -v "error" -c`
  if [ "$RESULT" == "1" ]; then
    echo "LISA RUNNING"
  else
    echo "LISA NOT RUNNING"
  fi
}

function default_action {
  kill_app
  uninstall_app
  install_app
  run_app
  focus_app
}

if [ "$#" -eq 2 ]; then
    default_action
fi

shift
shift

for action in "$@"; do
  case "${action}" in
    k*)
      kill_app
    ;;
    u*)
      uninstall_app
    ;;
    i*)
      install_app
    ;;
    r*)
      run_app
    ;;
    f*)
      focus_app
    ;;
    l*)
      list_installed_app
    ;;
    a*)
      list_running_app
    ;;
    p*)
      probe
    ;;
    *)
      echo "Error: Unknown action (${action})"
      action_help
      exit 2
    ;;
  esac
done
