#! /bin/bash

set -e

function install_once {
  git submodule update --init
  sudo apt-get install \
    python-smbus python-pip i2c-tools \
    libxml2 python-dev python-pycurl python-pyquery
  sudo pip install --upgrade pip
  sudo pip install --upgrade \
    RPi.GPIO \
    enum34 WebOb Paste webapp2
  install_polymer
}

function initialize {
  # Switch to performance governor.
  echo performance |
      sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
  echo 'Reloading i2c module (might be needed per boot/user)'
  sudo rmmod i2c-bcm2708 || echo 'failed to unload -- ignoring'
  sudo rmmod i2c-dev || echo 'failed to unload -- ignoring'
  sudo modprobe i2c-bcm2708
  sudo modprobe i2c-dev
  echo 'Making sure i2c module is loaded...'
  lsmod | grep i2c
  I2C_GROUP=$(stat -c "%G" /dev/i2c* | head -n1)
  echo "Adding $USER to $I2C_GROUP -- needs login/logout to take effect."
  sudo usermod -a -G "${I2C_GROUP}" $USER
}

function test_config {
  echo "Testing for i2c access. Login/logout if this fails."
  i2cdetect -y 1
}

function install_polymer {
  sudo apt-get install nodejs
  sudo npm install -g bower
  bower update
}

function all {
  install_once
  install_polymer
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