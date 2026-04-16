# TODO List
> Tasks to perform AFTER full OS backup of both drone and relay station.

---

## [WFB-NG FIXES] — do after OS backup

### 1. Fix GS clock / NTP (Relay station vind-rly)
Root cause: relay clock is 14 days behind, NTP broken.
```bash
sudo systemctl restart systemd-timesyncd
sudo timedatectl set-ntp true
timedatectl status
```

### 2. Disable drone wlan0 during WFB-NG operation (Drone)
`wlan0` connected to "Nilan" 5GHz AP — possible interference with WFB-NG on ch 157.
First verify channel:
```bash
iw dev wlan0 link | grep freq
```
If 5GHz, disable:
```bash
sudo ip link set wlan0 down
```
Consider making this persistent (disable wlan0 in netplan or add pre-start to wifibroadcast service).

### 3. Increase WFB ring buffer on GS OR reduce drone video bitrate (Relay station)
Root cause: GS wfb-server crashes with BlockingIOError EAGAIN (socket buffer overflow).
19 service restarts observed → each causes "New session detected" + decrypt errors + uplink loss spikes.
Option A — increase rx_ring_size in /etc/wifibroadcast.cfg on relay (currently 2MB, try 4-8MB).
Option B — reduce drone video bitrate in /etc/vision_streaming.conf.

### 4. Check GS adapter TX power (Relay station)
Uplink (GS→Drone) has severe packet loss (1-7 pkt/s constant) vs downlink which is fine.
Asymmetry may indicate GS TX power too low.
```bash
iw dev wlx00c0cab6db3b info
```
