#!/bin/bash
kill $(pgrep kdevtmp)
kill $(pgrep kinsing)
find / -iname kdevtmpfsi -exec rm -fv {} \;
find / -iname kinsing -exec rm -fv {} \;
rm /tmp/kdevtmp*
rm /tmp/kinsing*
