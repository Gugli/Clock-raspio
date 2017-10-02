I - Installation

1 - Platform
 
Get a Raspberry-Pi with an audio out.
Get any kind of pluggable audio system that suits your needs. Usually, a pair of PC speakers do just fine.
Install Raspbian Lite on the Micro SD 
    - Raspbian is here : https://www.raspberrypi.org/downloads/raspbian/
    - Use Etcher to copy Raspbian on the USB stick : https://etcher.io/
    - Follow instructions here : https://www.raspberrypi.org/documentation/installation/installing-images/README.md
    - You will need to setup the wifi connection. It can be done before booting by creating a wpa-supplican file like described here : https://www.raspberrypi.org/forums/viewtopic.php?t=191252
    

2 - System

You will need to plug a screen and a keyboard to your Raspberry Pi
Switch on your Raspberry Pi
Login using the default account "pi" and the password "raspberry"
Run the following commands:
    sudo apt-get update
    sudo apt-get install git
    git clone https://github.com/Gugli/clock-raspio.git ./clock-raspio
    sudo ./clock-raspio/install-or-update.sh
    

II - Update

You will need to plug a screen and a keyboard to your Raspberry Pi
Switch on your Raspberry Pi
Login using the default account "pi" and the password "raspberry"
Run the following command:
    sudo ./clock-raspio/install-or-update.sh
    
III - Credits

WindChimes-a by InspectorJ from freesound https://www.jshaw.co.uk/sfx
If you feel like changing the tune, do not hesitate to pay the 10 pounds he charges for his whole sound collection. It's worth every penny. If you're broke, you can use them for free !

If you feel like donating for this project:
 - select the amount you'd like to donate, 
 - send it to a charity of your choice, possibly something like Unicef, or Adainitiative, or BlackGirlsCode. It's the best way to reward me.