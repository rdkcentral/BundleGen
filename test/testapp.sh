#!/bin/bash

##############################################################################
# Copyright © 2021 Liberty Global B.V. and its Licensors.
# All rights reserved.
# Licensed by RDK Management, LLC under the terms of the RDK license.
# ============================================================================
# Liberty Global B.V. CONFIDENTIAL AND PROPRIETARY
# ============================================================================
# This file (and its contents) are the intellectual property of Liberty Global B.V.
# It may not be used, copied, distributed or otherwise disclosed in whole or in
# part without the express written permission of Liberty Global B.V.
# The RDK License agreement constitutes express written consent by Liberty Global.
# ============================================================================
# This software is the confidential and proprietary information of Liberty Global B.V.
# ("Confidential Information"). You shall not disclose this source code or
# such Confidential Information and shall use it only in accordance with the
# terms of the license agreement you entered into.
#
# LIBERTY GLOBAL B.V. MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE
# SUITABILITY OF THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. LIBERTY GLOBAL B.V. SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE NOR SHALL THEY BE RESPONSIBLE AS A RESULT
# OF USING, MODIFYING OR DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
##############################################################################

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
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n --arg pkgId "$PKGID" '{jsonrpc: "2.0", id: 1, method: "Packager.1.remove",  params: {pkgId: $pkgId}}'`
  echo

  # loop until app removed
  STATUS=""
  while [ "$STATUS" != "false" ];
  do
    echo "--> Waiting until app removed..."
    sleep 2
    STATUS=`curl -s -X POST http://$BOXIP:9998/jsonrpc -d $(jq -c -n --arg pkgId "$PKGID" '{jsonrpc: "2.0", id: 1, method: "Packager.1.getPackageInfo",  params: {pkgId: $pkgId}}') | jq .result.success`
  done
  echo "--> App is removed!"
}

function install_app {
  echo "--> Copying bundle to box on lighttpd server location"
  scp -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no -C "${PKG}" "root@$BOXIP:/opt/www/${PKGNAME}"

  echo "--> Start (re-)installation of app"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n --arg pkgId "$PKGID" --arg url "http://127.0.0.1:50050/${PKGNAME}" '{jsonrpc: "2.0", id: 1, method: "Packager.1.install",  params: {pkgId: $pkgId, type: "DAC", url: $url}}'`
  echo

  ## loop until app installed
 INSTALLED=""
  while [ "$INSTALLED" != "true" ];
  do
    echo "--> Waiting until app installed..."
    sleep 2
    INSTALLED=`curl -s -X POST http://$BOXIP:9998/jsonrpc -d $(jq -c -n --arg pkgId "$PKGID" '{jsonrpc: "2.0", id: 1, method: "Packager.1.getPackageInfo",  params: {pkgId: $pkgId}}') | jq .result.success`
  done

  echo "--> App is installed!"
  ssh -oUserKnownHostsFile=/dev/null -oStrictHostKeyChecking=no root@$BOXIP rm -f "/opt/www/${PKGNAME}"
}

function run_app {
  ## run app
  echo "--> Starting app!"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d \
    `jq -c -n --arg client "$PKGID" --arg client "$PKGID" --arg uri "$PKGID" '{jsonrpc: "2.0", id: 1, method: "org.rdk.RDKShell.1.launchApplication",  params: {client: $client, mimeType: "application/dac.native", uri: $uri}}'`
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
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n '{jsonrpc: "2.0", id: 1, method: "Packager.1.getInstalled"}'` | jq .
}

function list_running_app {
  ## list running applications
  echo "--> List running applications"
  curl -s -X POST http://$BOXIP:9998/jsonrpc -d `jq -c -n '{jsonrpc: "2.0", id: 1, method: "org.rdk.RDKShell.1.getClients"}'` | jq .
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
    *)
      echo "Error: Unknown action (${action})"
      action_help
      exit 2
    ;;
  esac
done
