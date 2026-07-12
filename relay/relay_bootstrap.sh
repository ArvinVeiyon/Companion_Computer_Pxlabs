#!/usr/bin/env bash
###############################################################################
# relay_bootstrap.sh — one-shot Vind-Roz RELAY STATION installer
#
#   Target : fresh Ubuntu 24.04 LTS on Raspberry Pi 4 OR Pi 5 (aarch64).
#            The board is auto-detected (/proc/device-tree/model) and any
#            board-specific handling (e.g. USB power for the RF adapter) is
#            applied automatically — one script, both platforms.
#   Result : a working WFB-NG ground-station relay (gs profile) with:
#              - RTL8812AU DKMS driver
#              - WFB-NG (built from source, installed as .deb)
#              - mavlink-router (built from source)
#              - all relay configs + control tools (wfb-rlyctl, wfb-cfg-apply)
#              - systemd services enabled (wifibroadcast@gs, mavlink.router,
#                ssh-tunnel-to-companion)
#
#   Usage  : sudo ./relay_bootstrap.sh              # interactive-safe defaults
#            sudo WFB_NIC=wlxAABBCCDDEEFF ./relay_bootstrap.sh
#            sudo DRONE_IP=10.5.5.87 GCS_IP=10.5.6.50 ./relay_bootstrap.sh
#
#   Needs  : internet during install (apt + git clone + build).
#
#   NOTE   : This is ONE executable. Non-secret configs are embedded as a
#            base64 payload at the bottom. Secrets (WFB keys, SSH keys) are
#            NOT embedded — they are generated, or supplied via ./keys/.
###############################################################################
set -euo pipefail

# ======================= EDITABLE PARAMETERS =================================
# Override any of these on the command line, e.g.  sudo GCS_IP=10.0.0.5 ./relay_bootstrap.sh
ROLE="gs"                                             # this installer targets the relay/GS
WFB_TAG="${WFB_TAG:-wfb-ng-25.01}"                    # svpcom/wfb-ng tag to build
MAVROUTER_COMMIT="${MAVROUTER_COMMIT:-51983a4}"       # mavlink-router pin (relay's build)
RTL_REPO="${RTL_REPO:-https://github.com/aircrack-ng/rtl8812au}"

SET_USB_POWER="${SET_USB_POWER:-1}"                   # 1 = apply board-specific USB power headroom for the RF adapter (Pi5 config.txt)

WFB_NIC="${WFB_NIC:-auto}"                            # WFB RF adapter; 'auto' = detect an 88XXau/eu NIC
WFB_CHANNEL="${WFB_CHANNEL:-161}"                     # must match the drone
WFB_REGION="${WFB_REGION:-BO}"
WFB_TXPOWER="${WFB_TXPOWER:-3000}"

DRONE_IP="${DRONE_IP:-10.5.5.87}"                     # drone companion (WFB tunnel far end)
DRONE_USER="${DRONE_USER:-roz}"                       # ssh user on the drone (for the 2222 tunnel)
GCS_IP="${GCS_IP:-10.5.6.50}"                         # QGroundControl PC
RELAY_TUNNEL_IP="${RELAY_TUNNEL_IP:-10.5.5.77}"       # relay's gs-wfb tunnel IP

ADMIN_USER="${ADMIN_USER:-vind-admin}"               # admin login (owns tunnel + configs)
GS_USER="${GS_USER:-vind-gs}"                         # ground-station user
CREATE_USERS="${CREATE_USERS:-1}"                    # 1 = create the two users if missing
ENABLE_SERVICES="${ENABLE_SERVICES:-1}"              # 1 = enable services for boot
START_SERVICES="${START_SERVICES:-1}"                # 1 = also start them now; 0 = enable-only (no radio yet)
SETUP_TUNNEL="${SETUP_TUNNEL:-1}"                    # 1 = install the autossh drone tunnel

# --- GS P2P uplink (wpa_supplicant) ---
SETUP_P2P="${SETUP_P2P:-1}"                           # 1 = deploy wpa_supplicant P2P config
START_P2P="${START_P2P:-0}"                           # 1 = bring P2P up NOW (DANGER if managing over wlan0!)
P2P_SSID="${P2P_SSID:-vind_rely}"
P2P_PSK="${P2P_PSK:-}"                                # P2P pre-shared key (SECRET — supply via env)
P2P_DEVNAME="${P2P_DEVNAME:-VIND_RLY_P2P}"
P2P_IP="${P2P_IP:-10.5.6.101}"                        # relay side of the P2P GS LAN
P2P_PIN="${P2P_PIN:-1987}"
# =============================================================================

log()  { echo -e "\033[1;36m[relay-bootstrap]\033[0m $*"; }
warn() { echo -e "\033[1;33m[warn]\033[0m $*" >&2; }
die()  { echo -e "\033[1;31m[error]\033[0m $*" >&2; exit 1; }

SELF="$(readlink -f "$0")"
SELF_DIR="$(dirname "$SELF")"
WORK="$(mktemp -d /tmp/relay-bootstrap.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
BUILD_USER="${SUDO_USER:-$ADMIN_USER}"                # unprivileged user for git/build
chown "$BUILD_USER" "$WORK" 2>/dev/null || true      # so sudo -u builds can write here

########################## 0. platform detection + sanity ####################
[[ $EUID -eq 0 ]] || die "run with sudo: sudo $0"

# Identify the Raspberry Pi board so board-specific steps can adapt.
# Sets: PI_MODEL (full string), PI_GEN (4/5/3/0=unknown), CONFIG_TXT (boot cfg path)
detect_platform() {
  PI_MODEL="unknown"; PI_GEN=0
  local m="" f
  for f in /proc/device-tree/model /sys/firmware/devicetree/base/model; do
    [[ -r "$f" ]] && m="$(tr -d '\000' < "$f" 2>/dev/null)" && [[ -n "$m" ]] && break
  done
  [[ -n "$m" ]] && PI_MODEL="$m"
  case "$m" in
    *"Raspberry Pi 5"*) PI_GEN=5 ;;
    *"Raspberry Pi 4"*) PI_GEN=4 ;;
    *"Raspberry Pi 3"*) PI_GEN=3 ;;
  esac
  # boot firmware config path varies by OS image, not by board model
  if   [[ -f /boot/firmware/config.txt ]]; then CONFIG_TXT=/boot/firmware/config.txt
  elif [[ -f /boot/config.txt ]];         then CONFIG_TXT=/boot/config.txt
  else CONFIG_TXT=""; fi
}

# Board-specific USB power headroom for the (power-hungry) RTL8812AU adapter.
apply_usb_power_tuning() {
  [[ "$SET_USB_POWER" == "1" ]] || { log "USB power tuning disabled (SET_USB_POWER=0)"; return 0; }
  case "$PI_GEN" in
    5)
      [[ -n "$CONFIG_TXT" ]] || { warn "no config.txt found — skipping Pi5 USB power tuning"; return 0; }
      if grep -qE '^[[:space:]]*usb_max_current_enable[[:space:]]*=' "$CONFIG_TXT"; then
        log "Pi5: usb_max_current_enable already set in $CONFIG_TXT"
      else
        cp -n "$CONFIG_TXT" "${CONFIG_TXT}.vind-relay.bak" 2>/dev/null || true
        printf '\n# Vind-Roz relay: full USB current for the RTL8812AU RF adapter (needs a proper 5V/5A PSU)\nusb_max_current_enable=1\n' >> "$CONFIG_TXT"
        log "Pi5: enabled usb_max_current_enable=1 in $CONFIG_TXT (takes effect after reboot)"
      fi
      ;;
    4)
      # Pi4 USB ports already share ~1.2 A and have no equivalent config knob.
      log "Pi4: no config.txt USB knob needed (use a powered USB hub if the RF adapter resets under TX load)"
      ;;
    *)
      log "USB power tuning: nothing board-specific to do (gen ${PI_GEN})"
      ;;
  esac
}

detect_platform
log "hardware platform: ${PI_MODEL} | gen=${PI_GEN} | $(uname -m) | kernel $(uname -r)"

. /etc/os-release 2>/dev/null || true
[[ "${VERSION_ID:-}" == "24.04" ]] || warn "expected Ubuntu 24.04 (found ${VERSION_ID:-unknown}) — continuing anyway"
case "$(uname -m)" in aarch64|arm64) : ;; *) warn "expected aarch64 (found $(uname -m)) — relay targets 64-bit Pi OS";; esac
case "$PI_GEN" in
  4|5) : ;;
  0)   warn "could not identify a Raspberry Pi model ('${PI_MODEL}') — continuing with generic aarch64 setup" ;;
  *)   warn "Raspberry Pi gen ${PI_GEN} is untested for this relay (supported: Pi4, Pi5) — continuing" ;;
esac
log "checking internet..."
ping -c1 -W3 github.com >/dev/null 2>&1 || die "no internet — this installer needs to apt/clone/build"

########################## 1. extract embedded payload #######################
log "extracting embedded config payload..."
PAYLOAD_START="$(awk '/^__PAYLOAD_BELOW__$/{print NR+1; exit}' "$SELF")"
[[ -n "$PAYLOAD_START" ]] || die "payload marker not found (corrupt installer?)"
tail -n +"$PAYLOAD_START" "$SELF" | base64 -d | tar -xzf - -C "$WORK" \
    || die "failed to extract payload"
PL="$WORK/payload"
[[ -d "$PL" ]] || die "payload directory missing after extract"

########################## 2. apt dependencies ###############################
log "installing apt dependencies..."
export DEBIAN_FRONTEND=noninteractive
# survive first-boot unattended-upgrades holding the dpkg lock
echo 'DPkg::Lock::Timeout "900";' > /etc/apt/apt.conf.d/99lock-timeout
for i in $(seq 1 90); do
  if pgrep -x unattended-upgr >/dev/null 2>&1 || fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
    [[ $i -eq 1 ]] && log "waiting for unattended-upgrades / dpkg lock to clear..."
    sleep 5
  else
    break
  fi
done
apt-get update -y
# critical build toolchain (must succeed)
apt-get install -y git build-essential pkg-config bc dkms
# kernel headers for DKMS — running kernel first, else the raspi meta (newer ABI is fine,
# it just means the driver builds once you're rebooted onto that kernel)
apt-get install -y "linux-headers-$(uname -r)" \
  || apt-get install -y linux-headers-raspi \
  || warn "no matching kernel headers available — RTL8812AU build will be deferred"
# WFB-NG build deps (incl. GStreamer for the wfb_rtsp component)
apt-get install -y \
  libpcap-dev libsodium-dev libevent-dev \
  debhelper devscripts dh-python fakeroot \
  python3-all-dev python3-pyroute2 python3-future \
  python3-msgpack python3-setuptools python3-virtualenv
apt-get install -y \
  libgstreamer1.0-dev libgstrtspserver-1.0-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
  gstreamer1.0-tools gstreamer1.0-libav || warn "gstreamer deps partial — wfb_rtsp may not build"
# mavlink-router build deps
apt-get install -y meson ninja-build
# runtime tools (best-effort — don't abort the whole install on one optional pkg)
apt-get install -y socat iw autossh wpasupplicant wireless-tools net-tools \
  rfkill iproute2 dnsmasq-base || warn "some runtime tools failed to install"

########################## 3. RTL8812AU DKMS driver ##########################
if dkms status 2>/dev/null | grep -qi '8812au'; then
  log "rtl8812au DKMS already installed — skipping"
elif [[ ! -e "/lib/modules/$(uname -r)/build" ]]; then
  warn "kernel headers for the RUNNING kernel ($(uname -r)) are not installed."
  warn "  -> RTL8812AU driver DEFERRED. After 'sudo apt full-upgrade && sudo reboot'"
  warn "     (lands on a kernel whose headers exist), re-run this installer to build it."
else
  log "building + installing rtl8812au DKMS driver..."
  if sudo -u "$BUILD_USER" -H git clone --depth=1 "$RTL_REPO" "$WORK/rtl8812au"; then
    make -C "$WORK/rtl8812au" dkms_install || warn "rtl8812au dkms_install failed (headers mismatch?) — driver deferred"
  else
    warn "rtl8812au clone failed — driver deferred"
  fi
fi

########################## 3b. board-specific USB power #######################
apply_usb_power_tuning

########################## 4. WFB-NG (from source -> .deb) ####################
if dpkg -l 2>/dev/null | grep -q '^ii  wfb-ng'; then
  log "wfb-ng already installed ($(dpkg-query -W -f '${Version}' wfb-ng)) — skipping build"
else
  log "building WFB-NG ($WFB_TAG) from source..."
  sudo -u "$BUILD_USER" -H git clone https://github.com/svpcom/wfb-ng.git "$WORK/wfb-ng"
  sudo -u "$BUILD_USER" -H git -C "$WORK/wfb-ng" fetch --all --tags --prune
  sudo -u "$BUILD_USER" -H git -C "$WORK/wfb-ng" checkout "$WFB_TAG"
  # NOTE: run make from *inside* the source dir. `sudo -H` resets PWD, and
  # wfb-ng's Makefile uses ENV ?= $(PWD)/env — with an empty PWD it becomes
  # /env and virtualenv fails ("destination . is not write-able at /"). A real
  # CWD makes $(PWD) resolve to the writable build dir.
  sudo -u "$BUILD_USER" -H bash -c "cd '$WORK/wfb-ng' && make clean" || true
  sudo -u "$BUILD_USER" -H bash -c "cd '$WORK/wfb-ng' && make deb" || die "wfb-ng 'make deb' failed"
  dpkg -i "$WORK"/wfb-ng/deb_dist/wfb-ng*.deb || apt-get install -f -y
fi

########################## 5. mavlink-router (from source) ###################
if command -v mavlink-routerd >/dev/null 2>&1; then
  log "mavlink-router already present — skipping build"
else
  log "building mavlink-router ($MAVROUTER_COMMIT)..."
  sudo -u "$BUILD_USER" -H git clone --recursive \
      https://github.com/mavlink-router/mavlink-router.git "$WORK/mavlink-router"
  sudo -u "$BUILD_USER" -H git -C "$WORK/mavlink-router" checkout "$MAVROUTER_COMMIT" || true
  sudo -u "$BUILD_USER" -H git -C "$WORK/mavlink-router" submodule update --init --recursive
  sudo -u "$BUILD_USER" -H meson setup --buildtype=release "$WORK/mavlink-router/build" "$WORK/mavlink-router"
  ninja -C "$WORK/mavlink-router/build"
  ninja -C "$WORK/mavlink-router/build" install
fi

########################## 6. users ##########################################
if [[ "$CREATE_USERS" == "1" ]]; then
  for u in "$GS_USER" "$ADMIN_USER"; do
    if ! id "$u" >/dev/null 2>&1; then
      log "creating user $u"
      useradd -m -s /bin/bash "$u"
      usermod -aG sudo,netdev,dialout "$u" || true
    fi
  done
fi
ADMIN_HOME="$(getent passwd "$ADMIN_USER" | cut -d: -f6)"; ADMIN_HOME="${ADMIN_HOME:-/home/$ADMIN_USER}"

########################## 7. detect WFB NIC #################################
if [[ "$WFB_NIC" == "auto" ]]; then
  log "auto-detecting WFB RF adapter (RTL88xxAU/EU, monitor-capable)..."
  WFB_NIC=""
  for dev in /sys/class/net/wl*; do
    [[ -e "$dev" ]] || continue
    ifn="$(basename "$dev")"
    drv="$(basename "$(readlink -f "$dev/device/driver" 2>/dev/null)" 2>/dev/null || true)"
    if echo "$drv" | grep -qiE '88|rtl8812'; then WFB_NIC="$ifn"; break; fi
  done
  [[ -n "$WFB_NIC" ]] || warn "could not auto-detect a WFB adapter; set WFB_NIC=<iface> and re-run the config step"
fi
log "WFB NIC = ${WFB_NIC:-<unset>}"

########################## 8. deploy configs from payload ####################
log "deploying relay configuration files..."
install -d /etc/mavlink-router /etc/systemd/system /usr/local/sbin /usr/local/bin \
           /etc/sudoers.d "$ADMIN_HOME"

# control tools (executable, root-owned)
install -m 0755 -o root -g root "$PL/usr/local/sbin/wfb-cfg-apply" /usr/local/sbin/wfb-cfg-apply
install -m 0755 -o root -g root "$PL/usr/local/sbin/wfb-rlyctl"    /usr/local/sbin/wfb-rlyctl
install -m 0755 -o root -g root "$PL/usr/local/bin/bg10_producer_rgb.py" /usr/local/bin/ 2>/dev/null || true

# WFB configs (relay gs). NIC is written to /etc/default/wifibroadcast below.
install -m 0644 -o root -g root "$PL/etc/wifibroadcast.cfg"         /etc/wifibroadcast.cfg
install -m 0644 -o root -g root "$PL/etc/wifibroadcast.cfg.default" /etc/wifibroadcast.cfg.default
printf 'WFB_NICS="%s"\n' "${WFB_NIC}" > /etc/default/wifibroadcast

# record the detected hardware platform for later reference / troubleshooting
printf 'PI_MODEL="%s"\nPI_GEN=%s\nARCH=%s\nKERNEL=%s\nPROVISIONED=%s\n' \
  "$PI_MODEL" "$PI_GEN" "$(uname -m)" "$(uname -r)" "$(date -Is 2>/dev/null || date)" \
  > /etc/vind-relay-platform

# mavlink-router
install -m 0644 -o root -g root "$PL/etc/mavlink-router/main.conf" /etc/mavlink-router/main.conf
sed -i "s/^Address=10\.5\.6\.50/Address=${GCS_IP}/" /etc/mavlink-router/main.conf || true
install -m 0644 -o root -g root "$PL/etc/sid.conf" /etc/sid.conf 2>/dev/null || true

# systemd units
install -m 0644 -o root -g root "$PL/etc/systemd/system/mavlink.router.service"         /etc/systemd/system/
install -m 0644 -o root -g root "$PL/etc/systemd/system/wifibroadcast-cluster@.service" /etc/systemd/system/
# tunnel unit — rewrite drone endpoint/user + key path for this host
sed -e "s#10\.5\.5\.87#${DRONE_IP}#g" \
    -e "s#roz@#${DRONE_USER}@#g" \
    -e "s#/home/vind-admin/#${ADMIN_HOME}/#g" \
    "$PL/etc/systemd/system/ssh-tunnel-to-companion.service" \
    > /etc/systemd/system/ssh-tunnel-to-companion.service

# P2P helper scripts (optional networking)
install -m 0755 -o "$ADMIN_USER" -g "$ADMIN_USER" "$PL/home/vind-admin/rely_p2p.sh" "$ADMIN_HOME/rely_p2p.sh" 2>/dev/null || true
install -m 0755 -o "$ADMIN_USER" -g "$ADMIN_USER" "$PL/home/vind-admin/start_p2p_on_wlan0.sh" "$ADMIN_HOME/start_p2p_on_wlan0.sh" 2>/dev/null || true

# sudoers for wfb-rlyctl (passwordless, scoped)
cat > /etc/sudoers.d/wfb-rlyctl <<SUDOERS
# Passwordless sudo scoped to the WFB relay control tools (GCS-driven)
${ADMIN_USER} ALL=(root) NOPASSWD: /usr/local/sbin/wfb-rlyctl, /usr/local/sbin/wfb-cfg-apply
SUDOERS
chmod 0440 /etc/sudoers.d/wfb-rlyctl
visudo -cf /etc/sudoers.d/wfb-rlyctl >/dev/null || { rm -f /etc/sudoers.d/wfb-rlyctl; warn "sudoers syntax check failed — removed"; }

# apply channel/region/txpower to the deployed config
sed -i -E "s/^(wifi_channel\s*=\s*).*/\1${WFB_CHANNEL}/;   s/^(wifi_region\s*=\s*).*/\1'${WFB_REGION}'/;   s/^(wifi_txpower\s*=\s*).*/\1${WFB_TXPOWER}/" /etc/wifibroadcast.cfg || true

########################## 8b. GS P2P uplink (wpa_supplicant) ################
if [[ "$SETUP_P2P" == "1" ]]; then
  log "deploying wpa_supplicant P2P config (SSID=$P2P_SSID, dev=$P2P_DEVNAME)..."
  install -d /etc/wpa_supplicant
  cat > /etc/wpa_supplicant/wpa_supplicant.conf <<WPA
ctrl_interface=/var/run/wpa_supplicant
update_config=1
device_name=${P2P_DEVNAME}

network={
	ssid="${P2P_SSID}"
	psk="${P2P_PSK:-CHANGE_ME}"
	proto=RSN
	key_mgmt=WPA-PSK
	pairwise=CCMP
	auth_alg=OPEN
	mode=3
	mesh_fwding=1
	disabled=2
}
WPA
  chmod 0600 /etc/wpa_supplicant/wpa_supplicant.conf
  # patch the P2P IP into the helper scripts to match this host
  sed -i "s/10\.5\.6\.101/${P2P_IP}/g; s/wps_pin any [0-9]*/wps_pin any ${P2P_PIN}/g" \
      "$ADMIN_HOME/rely_p2p.sh" "$ADMIN_HOME/start_p2p_on_wlan0.sh" 2>/dev/null || true
  [[ -z "$P2P_PSK" ]] && warn "P2P_PSK not set — wrote placeholder; edit /etc/wpa_supplicant/wpa_supplicant.conf"
  if [[ "$START_P2P" == "1" ]]; then
    warn "START_P2P=1 — bringing P2P up on wlan0 (WILL drop any wlan0-based session!)"
    su - "$ADMIN_USER" -c "bash '$ADMIN_HOME/rely_p2p.sh'" || warn "P2P start script failed"
  else
    log "P2P config deployed but NOT started. Start later with:  sudo ~/rely_p2p.sh"
  fi
fi

########################## 9. keys (SECRETS) #################################
# WFB link keys: MUST match the drone. Priority: ./keys/ next to installer > generate fresh.
if [[ -f "$SELF_DIR/keys/gs.key" && -f "$SELF_DIR/keys/drone.key" ]]; then
  log "using WFB keys supplied in $SELF_DIR/keys/"
  install -m 0644 -o root -g root "$SELF_DIR/keys/gs.key"    /etc/gs.key
  install -m 0644 -o root -g root "$SELF_DIR/keys/drone.key" /etc/drone.key
elif [[ -f /etc/gs.key && -f /etc/drone.key ]]; then
  log "existing /etc/gs.key + /etc/drone.key kept"
else
  warn "no WFB keys supplied — generating FRESH keys with wfb-keygen."
  warn ">> The drone MUST be given these SAME keys or the link will not connect. <<"
  ( cd /etc && wfb-keygen ) || warn "wfb-keygen failed; run 'cd /etc && sudo wfb-keygen' manually"
fi

# SSH key for the drone tunnel (autossh). Generated if missing; must be authorized on the drone.
if [[ "$SETUP_TUNNEL" == "1" ]]; then
  install -d -m 0700 -o "$ADMIN_USER" -g "$ADMIN_USER" "$ADMIN_HOME/.ssh"
  if [[ ! -f "$ADMIN_HOME/.ssh/id_rsa" ]]; then
    log "generating SSH key for the drone tunnel ($ADMIN_HOME/.ssh/id_rsa)"
    sudo -u "$ADMIN_USER" ssh-keygen -t rsa -b 4096 -N "" -f "$ADMIN_HOME/.ssh/id_rsa" -C "relay-tunnel"
    warn "authorize this key on the drone: copy $ADMIN_HOME/.ssh/id_rsa.pub into ${DRONE_USER}@${DRONE_IP}:~/.ssh/authorized_keys"
  fi
fi

########################## 10. enable services ###############################
systemctl daemon-reload
if [[ "$ENABLE_SERVICES" == "1" ]]; then
  NOW=""; [[ "$START_SERVICES" == "1" ]] && NOW="--now"
  [[ -n "$NOW" ]] && log "enabling + starting services..." || log "enabling services for boot (not starting now)..."
  systemctl enable $NOW "wifibroadcast@${ROLE}.service" || warn "wifibroadcast@${ROLE} enable/start issue (radio present?)"
  systemctl enable $NOW mavlink.router.service          || warn "mavlink.router enable/start issue"
  [[ "$SETUP_TUNNEL" == "1" ]] && { systemctl enable $NOW ssh-tunnel-to-companion.service || warn "tunnel enable/start issue (drone key authorized?)"; }
fi

########################## 11. summary #######################################
cat <<SUMMARY

===================== RELAY BOOTSTRAP COMPLETE =====================
 Platform       : ${PI_MODEL} (gen ${PI_GEN}, $(uname -m))
 Role           : ${ROLE}
 WFB NIC        : ${WFB_NIC:-<set WFB_NIC and re-run>}
 WFB channel    : ${WFB_CHANNEL} / region ${WFB_REGION} / txpower ${WFB_TXPOWER}
 Drone tunnel   : localhost:2222 -> ${DRONE_USER}@${DRONE_IP}:22
 GCS (QGC)      : ${GCS_IP}
 Control tools  : wfb-rlyctl, wfb-cfg-apply  (/usr/local/sbin)

 NEXT STEPS
  1. WFB keys: ensure /etc/gs.key + /etc/drone.key are IDENTICAL on drone & relay.
  2. Tunnel:  authorize ${ADMIN_HOME}/.ssh/id_rsa.pub on the drone (${DRONE_USER}@${DRONE_IP}).
  3. Verify:  wfb-cli gs ; systemctl status wifibroadcast@${ROLE} ; ip -br a | grep gs-wfb
  4. Mode:    sudo wfb-rlyctl status   (standalone <-> cluster)
  5. P2P GS:  sudo ~/rely_p2p.sh   (brings up ${P2P_IP} on wlan0 — do NOT run over a wlan0 SSH session)

 NOTE: cluster mode + netplan networking are host-specific — review
       /etc/wifibroadcast.cfg [cluster] and your netplan before enabling.
       P2P config: /etc/wpa_supplicant/wpa_supplicant.conf (SSID ${P2P_SSID}).
====================================================================
SUMMARY
log "done."
exit 0
__PAYLOAD_BELOW__
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
