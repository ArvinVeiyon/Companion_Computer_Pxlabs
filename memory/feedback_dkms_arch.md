---
name: rtl88x2eu DKMS ARCH fix
description: DKMS build for rtl88x2eu fails on raspi kernel with arch/aarch64 error — must use ARCH=arm64
type: feedback
---

DKMS passes `ARCH=aarch64` (from `uname -m`) but raspi kernel headers expect `ARCH=arm64`. This causes build failure:
`arch/aarch64/Makefile: No such file or directory`

**Fix applied:** `/var/lib/dkms/rtl88x2eu/5.15.0.1/source/dkms.conf` MAKE line has `ARCH=arm64` explicitly:
```
MAKE="'make' -j$PROCS_NUM ARCH=arm64 KVER=${kernelver} KSRC=/lib/modules/${kernelver}/build"
```

**Why:** Linux kernel uses `arm64` arch name, not `aarch64` (the userspace/uname name). DKMS defaults to `uname -m` which is wrong for kernel builds on aarch64.

**How to apply:** Any time rtl88x2eu DKMS fails to build on a new raspi kernel, check the dkms.conf first. Also ensure `linux-headers-<kernel>-raspi` is installed before running `dkms install`.
