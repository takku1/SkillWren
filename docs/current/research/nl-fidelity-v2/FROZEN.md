# NL fidelity corpus v2: frozen for evaluation

Frozen 2026-11-17. Derived from v1 (`../nl-fidelity/`, still frozen) by
`scripts/make_corpus_v2.py`, which applies the fixes recorded in
`../nl-fidelity/independent-review/README.md`:

- pairs16 f17: the window verify is now unconditional and aborts when the
  window is shut; `verify#window before write#slot` added.
- pairs21 f22: restart and reload are each followed by a health re-check;
  only a still-unhealthy service aborts.
- 05: the flow now summarizes (`generate summary from request`).
- Unrequested `require <input> exists` gates removed from 03, f08, f14,
  f16, f17, f18, f21ingest and f24 (03 declares `inputs: design` instead,
  because the gate also served as its input declaration).

Same reviewer packet and protocol as v1 (`../nl-fidelity/FROZEN.md`).
Every flow checks clean; every fact is present in the explanation
(pinned by `tests/test_explain_workflow.py`).

## Manifest (sha256)

d176963ae8ff5a9c0e9f6fd56e5236518c92b3d601217cad98a4c2601291b831  01-facts.json
a667a7ff763e41c0b815b9a510d7d457056656d70f09905e4672264abf4103dd  01-flow.md
cf3269390d12c415229d56e6ea511727ed6dd09a269816666aa4d1e1b1992eb8  01-intent.md
d7859aa9e2dc7ae092e5f82d18d7efd0018f0d4bf95fa43cafa81f2fa0e6355c  02-facts.json
40f4b193065562dd6b4cb9821f09d66dc7f05dae84d6c467aec6938c7182f03f  02-flow.md
9f371f20cbeeb5dffaa9911f0a3f42cc0ae74ca56e44c5dc4093f1aa703c2f94  02-intent.md
01cc096606526b05569525cce293b6f9a472e58dd323b5f55226b32542aa1130  03-facts.json
eec57a13330ab20ee3e5ab4c6a863357e1618c4a358993ba0786be3eb1d95616  03-flow.md
7e3769eca800c4c117c8b3214f56baab0f3eb8193efe703f364b44fa599aaa0b  03-intent.md
5e443173ad6deeb3a6910b63f6e305aae8bc9bff48b574a89cdcad3357d2a199  04-facts.json
a9e1e70de48c6534a9d0cbeabeba91ea7b5e6b6698449e548e1ff272ebb78338  04-flow.md
26bcb6dca51fc80ea30fb429d3418a2473cfda15a96eea34e1e2eec6c7a08c55  04-intent.md
e32a68600f6eee2166439a795368fe2101b311a2528b3f3f641e41caf73c840f  05-facts.json
95245d2164da10838296ddbdfecba304467549832d15ca0d21980dfed26267e2  05-flow.md
2d1a9413970a7f1c9933c73a9ccd22b84c363d9bbca3209bc4ade6a06dc146d7  05-intent.md
16b1fadbb4360872537840d4add7daea80369dcfb3588dbf8074dad93f017e80  pairs06-facts.json
1361bd104ecdb196944f131121ff17c5abeb3402988e7031785554da0b93a94c  pairs06-flow.md
4a4e7ef56f5347924dbb546bb494569439d80265891f0da11833c9793acdfae2  pairs06-intent.md
723bb247ceed1a9d9ef378d7f4769e3bfd2271a816ca322c746ff188f5a83372  pairs11-facts.json
f980fe53d3c6f6cc2e41119865f050c1a5c2c655fae7f9e61fe33e448075d052  pairs11-flow.md
7cca15403f0f8d463807245d423105ede420d2c880c994c4e8df49f7591861af  pairs11-intent.md
15dfcfa19a1d7b117236e9451b7aa0b3613cd98a616462b785f03716f4c4dadc  pairs16-facts.json
cad215ee1ef2376f5b1d506f49231535eb01fd1fbbc408c6c712195fbb5a3ecd  pairs16-flow.md
e698e9d23d6a8b6325d7c6e27f22c1de47af0f845330dc836c02bbf4d3d56018  pairs16-intent.md
3feaa2e96cb37db1565b310bb4ea54490090feeb0c161c9c3a64bf1efc9d72e7  pairs21-facts.json
4fcf7f0c5d5fc44ccd21a73ee48e74fc82a5c09a0539b69621102b5444fc6c43  pairs21-flow.md
2ff395fd356396173dbe2da37e6eec60435d5752e69745500cd16d48bcd37261  pairs21-intent.md
