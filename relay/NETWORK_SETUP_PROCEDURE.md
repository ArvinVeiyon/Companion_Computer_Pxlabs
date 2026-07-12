# Relay Network Bring-up — Manual Procedure (Runbook)

> **Status:** Manual runbook. These exact steps were **run live on `RELAY-STN` (Pi4) on
> 2026-07-12 and verified** — they are tested *as commands*, but are **NOT yet folded into
> `relay_bootstrap.sh`**. Do that only after testing on a spare board / fresh SD card
> (see §7). Until then, follow this by hand on new relay setups.
>
> Covers: USB **internet uplink**, onboard **P2P GS link**, and **IP forwarding** — the
> networking that `relay_bootstrap.sh` deliberately does *not* apply live. Companion to
> `RELAY_STATION_SETUP.md` (which documents the resulting end-state).
> **No secrets in this file** — passphrases shown as placeholders; put real values only in
> the on-box config.

---

## 0. Safety — read before touching the network

You are almost always SSH'd into the relay **over its onboard `wlan0`**. This procedure
repurposes `wlan0` for P2P, which **kills that SSH path**. Rules:

1. **Bring up the new USB uplink FIRST** and confirm you can SSH the relay on the uplink's
   new IP — *before* touching `wlan0`.
2. Apply the `wlan0`/netplan cutover **detached** (survives the link dropping) with a
   **dead-man auto-revert**: if you don't confirm reachability within ~5 min, it rolls the
   network back to the working state automatically.
3. Two interfaces on one subnet (old `wlan0` + new uplink, both on `192.168.1.0/24`) causes
   **ARP flux** — IPs become intermittently unreachable. This clears the moment `wlan0`
   leaves the subnet (i.e. after the P2P cutover).

---

## 1. Prerequisites

- USB Wi-Fi **client** adapter for internet (e.g. RTL8821CU / `rtw_8821cu`) — plugged in.
- Internet AP SSID + PSK (use the 64-hex PSK hash, not the plaintext).
- Chosen P2P network name (e.g. `RELAY-STN01`), P2P **passphrase**, and WPS **PIN** (`1987`).
- `sudo` on the relay.

Identify the new adapter's interface name and driver:
```bash
for d in /sys/class/net/wl*; do i=$(basename "$d"); \
  echo "$i $(cat $d/address) $(basename $(readlink -f $d/device/driver))"; done
```

---

## 2. Step 1 — Internet uplink on the USB adapter (additive, safe)

Write a dedicated netplan file (keeps it isolated/reversible). `route-metric: 100` makes it
the preferred default route.

```yaml
# /etc/netplan/60-relay-uplink.yaml   (chmod 600)
network:
  version: 2
  wifis:
    wlxXXXXXXXXXXXX:                 # <-- the USB adapter iface
      optional: true
      dhcp4: true
      dhcp4-overrides: { route-metric: 100 }
      regulatory-domain: "IN"
      access-points:
        "Nilan":                     # <-- internet SSID
          auth:
            key-management: "psk"
            password: "<64-HEX-PSK-HASH>"
```
```bash
sudo chmod 600 /etc/netplan/60-relay-uplink.yaml
sudo netplan generate            # validate first — abort on error
sudo netplan apply
```
**Verify (must pass before Step 2):** the adapter gets an IP, has internet, and you can SSH
the relay on that **new IP**:
```bash
ip -br addr show wlxXXXX          # expect 192.168.1.NNN
ping -I wlxXXXX -c2 8.8.8.8
# from your workstation:
ssh vind-admin@<new-uplink-IP> 'echo reachable'
```

---

## 3. Step 2 — Cut `wlan0` over to P2P (detached + dead-man)

Run this whole block as a **detached** root script (`setsid … </dev/null &`) so it survives
`wlan0` dropping. It schedules a revert that fires in 5 min unless you create
`/tmp/CUTOVER_CONFIRMED`.

```bash
# (a) backup + dead-man revert
cp -a /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml.premove
cat >/tmp/revert.sh <<'REV'
sleep 300; [ -f /tmp/CUTOVER_CONFIRMED ] && exit 0
pkill -f 'wpa_supplicant -B -i wlan0'; wpa_cli -i wlan0 p2p_group_remove p2p-wlan0-0
rm -f /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
cp -a /etc/netplan/50-cloud-init.yaml.premove /etc/netplan/50-cloud-init.yaml; netplan apply
REV
setsid bash /tmp/revert.sh </dev/null >/tmp/revert.log 2>&1 &

# (b) stop cloud-init from regenerating netplan on boot
echo 'network: {config: disabled}' >/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg

# (c) remove wlan0 from netplan (frees it; kills ARP flux)
printf 'network:\n  version: 2\n  renderer: networkd\n' >/etc/netplan/50-cloud-init.yaml
chmod 600 /etc/netplan/50-cloud-init.yaml
systemctl stop netplan-wpa-wlan0.service 2>/dev/null
netplan apply; sleep 4; ip link set wlan0 up

# (d) P2P credentials  (matches vind-rly / Pi5 structure)
cat >/etc/wpa_supplicant/wpa_supplicant.conf <<WPA
ctrl_interface=/var/run/wpa_supplicant
update_config=1
device_name=RELAY-STN01
network={
	ssid="RELAY-STN01"
	bssid=$(cat /sys/class/net/p2p-wlan0-0/address 2>/dev/null)   # own p2p MAC (optional)
	psk="<P2P-PASSPHRASE>"
	proto=RSN
	key_mgmt=WPA-PSK
	pairwise=CCMP
	auth_alg=OPEN
	mode=3
	mesh_fwding=1
	disabled=2
}
WPA
chmod 600 /etc/wpa_supplicant/wpa_supplicant.conf

# (e) ~/rely_p2p.sh — the Pi5-verbatim minimal P2P bring-up
cat >/home/vind-admin/rely_p2p.sh <<'RP2P'
#!/bin/bash
sudo wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf -C /var/run/wpa_supplicant
sudo wpa_cli -i wlan0 p2p_group_add persistent=0
sleep 5
sudo ifconfig p2p-wlan0-0 10.5.6.101 netmask 255.255.255.0 up
sudo wpa_cli -i p2p-wlan0-0 wps_pin any 1987
sleep 5
RP2P
chmod +x /home/vind-admin/rely_p2p.sh; chown vind-admin:vind-admin /home/vind-admin/rely_p2p.sh

# (f) persist P2P at boot + bring it up now
( crontab -l 2>/dev/null | grep -v rely_p2p.sh; echo '@reboot /home/vind-admin/rely_p2p.sh' ) | crontab -
bash /home/vind-admin/rely_p2p.sh
```
**Confirm & cancel the revert** — from your workstation, once the uplink IP is solid:
```bash
ssh vind-admin@<uplink-IP> 'touch /tmp/CUTOVER_CONFIRMED; ip -br addr show p2p-wlan0-0'
```
Expect `p2p-wlan0-0  UP  10.5.6.101/24`, and `iw dev` showing `ssid RELAY-STN01` (P2P-GO).

---

## 4. Step 3 — IP forwarding

```bash
echo 'net.ipv4.ip_forward=1' | sudo tee /etc/sysctl.d/99-relay-forward.conf
sudo sysctl -w net.ipv4.ip_forward=1
```
**No iptables NAT/FORWARD rules** — this matches `vind-rly` (default-ACCEPT). Only if you
want to share the uplink's internet to GS clients (the Pi5 does **not**):
```bash
sudo iptables -t nat -A POSTROUTING -o wlxXXXX -j MASQUERADE   # optional internet-share
```

---

## 5. Verify (end state)

```bash
ip -br addr                          # wlxXXXX=192.168.1.NNN (default route), p2p-wlan0-0=10.5.6.101
iw dev | grep -A2 p2p-wlan0-0        # P2P-GO, ssid RELAY-STN01
sysctl net.ipv4.ip_forward           # = 1
crontab -l | grep rely_p2p           # @reboot present
```

---

## 6. Credentials recap (the two P2P join methods)

- **WPS PIN `1987`** — for Wi-Fi-Direct/WPS clients; relay hands over creds automatically.
- **WPA2 passphrase** — for ordinary Wi-Fi clients (e.g. Windows GCS); typed like any Wi-Fi
  password. Lives only in `/etc/wpa_supplicant/wpa_supplicant.conf` on the box (**not in git**).

See `RELAY_STATION_SETUP.md` §5.2 for the full explanation.

---

## 7. To automate later (into `relay_bootstrap.sh`) — UNTESTED until then

When a spare board / fresh SD card is available to test a clean run, fold these in behind
flags (default off), then **verify on the fresh box before trusting**:

- `INTERNET_UPLINK=<wlxMAC|SSID>` → generate `60-relay-uplink.yaml` (§2)
- a guarded **cutover step** using the detached + dead-man-revert pattern (§3)
- `ip_forward` persist + `@reboot rely_p2p.sh` + cloud-init disable
- optional `INSTALL_CLAUDE=1`

⚠️ Do not mark these "automated" until a **fresh-box run** has been tested end-to-end.
The commands above are proven; the *integrated bootstrap path* is not.
