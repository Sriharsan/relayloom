# Tested fully disconnected

Started 2026-11-03 21:51 +0530, finished 2026-11-03 21:56 +0530. Machine: SRIHARSAN, Windows 11. Demo run.

| Step | Result | Detail |
| --- | --- | --- |
| the network is really off | PASS | 1.1.1.1:443: OSError: [WinError 10065] A socket operation was attempted to an unreachable host; 8.8.8.8:53: OSError: [WinError 10065] A socket operation was attempted to an unreachable host; dns example.com: gaierror: [Errno 11001] getaddrinfo failed |
| live Muse Glimmer bill reading | PASS | ARD-5101 read in 194.0 s, valid schema, total 11611.2 |
| live SAM 3.1 count | PASS | counted 24 of 24 cans in 39.2 s |
| seven cases with signed receipts verified offline | PASS | match: PASS in 0.2 s, short: PASS in 2.1 s, price: PASS in 0.0 s, injection: PASS in 0.0 s, netcut: PASS in 0.1 s, duplicate: PASS in 0.0 s, split: PASS in 0.0 s |

Overall: all steps passed.
When this was written the network had been switched off, and the three tests above show no route to the internet.
