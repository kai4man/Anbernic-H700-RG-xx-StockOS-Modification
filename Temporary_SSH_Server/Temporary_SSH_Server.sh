#!/bin/bash
#make by G.R.H
#inspired by Skeeve

if [ ! -f /usr/bin/mpv ]; then
    echo "Error: The necessary playback files are missing and the program cannot run."
    exit 1
fi
. /mnt/mod/ctrl/configs/functions &>/dev/null 2>&1
progdir=$(cd $(dirname $0); pwd)

cat<<EOF > "${progdir}/res/ip.srt"
1
00:00:00,000 --> 02:00:00,000
IP address: $(ip -4 addr show wlan0 | awk '/inet / {print $2}' | cut -d/ -f1) Port: 22, User: root Pass: root
EOF

 case "$HW_MODEL" in
    "RG28xx")
        rm "$0"
        exit 2
    ;;
esac

function enable_ssh() {
systemctl enable ssh.service
systemctl start ssh.service
}

function disable_ssh() {
systemctl stop ssh.service
systemctl disable ssh.service
}

pkill -f mpv
pkill -f evtest
if [ "$(systemctl is-active ssh)" = "inactive" ]; then
    enable_ssh
fi
mpv $rotate_28 --really-quiet --fs --image-display-duration=6000 "${progdir}/res/sshtmp-${LANG_CUR}.png" --sub-file="${progdir}/res/ip.srt" &

get_devices

(
     for INPUT_DEVICE in ${INPUT_DEVICES[@]}
     do
     evtest "${INPUT_DEVICE}" 2>&1 &
     done
     wait
) | while read line; do
    case $line in
        (${CONTROLLER_DISCONNECTED})
        echo "Reloading due to ${CONTROLLER_DEVICE} reattach..." 2>&1
        get_devices
        ;;
        (${DEVICE_DISCONNECTED})
        echo "Reloading due to ${DEVICE} reattach..." 2>&1
        get_devices
        ;;
        (${FUNC_KEY_EVENT})
            if [[ "${line}" =~ ${PRESS} ]]; then
                continue
            elif [[ "${line}" =~ ${RELEASE} ]]; then
                pkill -f mpv
                if grep -q "global.ssh=0" "/mnt/mod/ctrl/configs/system.cfg"; then
                    disable_ssh
                fi
                user_quit
            fi
        ;;
    esac
done
