#! /bin/bash

set -e

function run {
  echo "=== $@"
  "$@"
}

function install_once {
  run git submodule update --init
  run sudo apt-get install \
    python-smbus python-pip i2c-tools \
    libxml2 python-dev python-pycurl python-pyquery \
    imagemagick cmake \
    gcc-avr binutils-avr gdb-avr avr-libc avrdude
  run sudo -H pip install --upgrade pip
  # TODO: This only works on the Pi.
  run sudo -H pip install --upgrade \
    RPi.GPIO \
    enum34 WebOb Paste webapp2 python-gflags
  install_polymer
  curl https://d3js.org/d3.v3.min.js > static/d3.v3.min.js
  mkdir -p monitor/data
}

function initialize {
  # Switch to performance governor.
  echo performance |
      sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
  echo 'Reloading i2c module (might be needed per boot/user)'
  sudo rmmod i2c-bcm2708 || echo 'failed to unload -- ignoring'
  sudo rmmod i2c-dev || echo 'failed to unload -- ignoring'
  run sudo modprobe i2c-bcm2708
  run sudo modprobe i2c-dev
  echo 'Making sure i2c module is loaded...'
  lsmod | grep i2c
  I2C_GROUP=$(stat -c "%G" /dev/i2c* | head -n1)
  echo "Adding $USER to $I2C_GROUP -- needs login/logout to take effect."
  sudo usermod -a -G "${I2C_GROUP}" $USER
}

function test_config {
  echo "Testing for i2c access. Login/logout if this fails."
  run i2cdetect -y 1
}

function install_polymer {
  # Install nodejs-legacy for the symlink from node to nodejs, required by
  # bower.
  # Warning: the node package is an amateur radio program!
  run sudo apt-get install nodejs nodejs-legacy npm
  run sudo -H npm install -g bower
  run sudo -H npm install -g vulcanize # Used to minify app
  mkdir -p bower_components
  run bower update
}

function reformat {
  find . -type d \( -path ./adafruit -o -path ./arduinoio \) -prune -o -type f -name '*.py' -print0 |
  xargs -0 -n1 yapf -i -r --style ~/.style.yapf
}

function all {
  install_once
  initialize
  test_config
}

function main {
  if [ "$#" -eq 0 ]; then
    all
    return $?
  fi
  while [ "$#" -gt 0 ]; do
    $1
    shift
  done
}

main "$@"
