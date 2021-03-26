#!/bin/sh

if [ "$#" -ne 2 ]; then
    echo "Usage:"
    echo "./testapp.sh BOX_OR_RPI_IPADDRESS bundle.tar.gz"
    exit
fi

BOXIP=$1
PKG=$2

echo "--> Copying bundle to box on lighttpd server location"
scp -C $PKG root@$BOXIP:/opt/www/

echo "--> Killing app"
curl -X POST http://$BOXIP:9998/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"org.rdk.RDKShell.1.kill", "params":{ "client": "testclient" } }'
echo

echo "--> Remove app"
curl -X POST http://$BOXIP:9998/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"Packager.1.remove", "params":{ "pkgId": "testpkg" } }'
echo

# loop until app removed
INSTALLED="2"
while [ "$INSTALLED" = "2" ];
do
  echo "--> Waiting until app removed..."
  sleep 2

  INSTALLED=`curl -s -X POST http://$BOXIP:9998/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"Packager.1.getPackageInfo", "params":{ "pkgId": "testpkg" } }' | jq '.' | grep testpkg -c`
done
echo "--> App is removed!"

echo "--> Start (re-)installation of app"
curl -X POST http://$BOXIP:9998/jsonrpc -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"Packager.1.install\", \"params\":{ \"pkgId\": \"testpkg\", \"type\": \"DAC\", \"url\": \"http://127.0.0.1:50050/$PKG\" } }"
echo

## loop until app installed
INSTALLED="0"
while [ "$INSTALLED" = "0" ];
do
  echo "--> Waiting until app installed..."
  sleep 2

  INSTALLED=`curl -s -X POST http://$BOXIP:9998/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"Packager.1.getPackageInfo", "params":{ "pkgId": "testpkg" } }' | jq '.' | grep testpkg -c`
done

echo "--> App is installed!"

## run app
echo "--> Starting app!"
curl -X POST http://$BOXIP:9998/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"org.rdk.RDKShell.1.launchApplication", "params":{ "client": "testclient", "mimeType": "application/dac.native", "uri": "testpkg" } }'
echo

## move to front and focus the app
echo "--> Focus app!"
curl -X POST http://$BOXIP:9998/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"org.rdk.RDKShell.1.moveToFront", "params":{ "client": "testclient" } }'
curl -X POST http://$BOXIP:9998/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"org.rdk.RDKShell.1.setFocus", "params":{ "client": "testclient" } }'
echo
