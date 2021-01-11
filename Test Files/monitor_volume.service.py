[Unit]
Description=Volume knob monitor

[Service]
User=volumio
Group=volumio
ExecStart=/home/pi/bin/monitor_volume

[Install]
WantedBy=multi-user.target