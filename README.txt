I - Installation

1 - Platform
 
Get a Raspberry-Pi with an audio out.
Get any kind of pluggable audio system that suits your needs. Usually, a pair of PC speakers do just fine.
Install Raspbian Lite on the Micro SD 
    - Raspbian is here : https://www.raspberrypi.org/downloads/raspbian/
    - Use Etcher to copy Raspbian on the USB stick : https://etcher.io/
    - Follow instructions here : https://www.raspberrypi.org/documentation/installation/installing-images/README.md
    
Switch on your Raspberry Pi

2 - System

You will need to plug a screen and a keyboard to your Raspberry Pi
Login using the default account "pi" and the password "raspberry"
Run the following commands:
    apt-get update
    apt-get install git
    git clone https://github.com/Gugli/clock-raspio.git ./clock-raspio
    ./clock-raspio/install-or-update.sh
    

II - Update

You will need to plug a screen and a keyboard to your Raspberry Pi
Login using the default account "pi" and the password "raspberry"
Run the following command:
    ./clock-raspio/install-or-update.sh