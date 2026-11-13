# NL fidelity corpus: frozen for evaluation

Frozen 2026-11-12 at commit `b31d602` (authoring pipeline release).
Any evaluation must use these bytes; the manifest below pins them.

Reviewer packet: for each pair, read ONLY the `-intent.md` and the
output of `skillwren explain-workflow --fragment <flow file>` (never
the flow file itself), write down the requirements, branches,
permissions, and limitations you recover, then check each fact in the
matching `-facts.json`. Record invented requirements (you found it, no
fact covers it), missed requirements (fact you could not recover), and
missed limitations separately. Structural validity (does it parse, do
rules hold) is already established by `check`; judge only semantic
fidelity: does the explanation carry the intent's meaning?

Independent review is pending: no reviewer outside this session has
assessed the corpus yet. Do not cite corpus scores until that happens.

## Manifest (sha256)

d176963ae8ff5a9c0e9f6fd56e5236518c92b3d601217cad98a4c2601291b831  01-facts.json
a667a7ff763e41c0b815b9a510d7d457056656d70f09905e4672264abf4103dd  01-flow.md
cf3269390d12c415229d56e6ea511727ed6dd09a269816666aa4d1e1b1992eb8  01-intent.md
d7859aa9e2dc7ae092e5f82d18d7efd0018f0d4bf95fa43cafa81f2fa0e6355c  02-facts.json
40f4b193065562dd6b4cb9821f09d66dc7f05dae84d6c467aec6938c7182f03f  02-flow.md
9f371f20cbeeb5dffaa9911f0a3f42cc0ae74ca56e44c5dc4093f1aa703c2f94  02-intent.md
01cc096606526b05569525cce293b6f9a472e58dd323b5f55226b32542aa1130  03-facts.json
3ad331206fcb9baeca9cc55cec365549e038d1feac6a4cbd64b32b2dc79f5d03  03-flow.md
7e3769eca800c4c117c8b3214f56baab0f3eb8193efe703f364b44fa599aaa0b  03-intent.md
5e443173ad6deeb3a6910b63f6e305aae8bc9bff48b574a89cdcad3357d2a199  04-facts.json
a9e1e70de48c6534a9d0cbeabeba91ea7b5e6b6698449e548e1ff272ebb78338  04-flow.md
26bcb6dca51fc80ea30fb429d3418a2473cfda15a96eea34e1e2eec6c7a08c55  04-intent.md
f04c2c14b25790777ca6577efcff363054c4b9662af64626c5f28b1e392830d2  05-facts.json
14c385bde55b9db900b8c2a51e23d80e99658a5779fcee4ff0a61c976567d0d1  05-flow.md
2d1a9413970a7f1c9933c73a9ccd22b84c363d9bbca3209bc4ade6a06dc146d7  05-intent.md
16b1fadbb4360872537840d4add7daea80369dcfb3588dbf8074dad93f017e80  pairs06-facts.json
5006c781d89c76496983219368e1db0ece5f85f5889610725fa4d17131694fa6  pairs06-flow.md
4a4e7ef56f5347924dbb546bb494569439d80265891f0da11833c9793acdfae2  pairs06-intent.md
723bb247ceed1a9d9ef378d7f4769e3bfd2271a816ca322c746ff188f5a83372  pairs11-facts.json
bfeb470b0cc038fa1b4dc6390f5453733b62de4802d7587610d65562e8fd82ef  pairs11-flow.md
7cca15403f0f8d463807245d423105ede420d2c880c994c4e8df49f7591861af  pairs11-intent.md
8d92b75abb64bf1935f0726d25c96a983c9125064b1e2edcb782bb7101d49b2b  pairs16-facts.json
ac8a3f3597ba58cfe5266aebeb74246c86b8978e2287b6ae53711f75fb5d7402  pairs16-flow.md
e698e9d23d6a8b6325d7c6e27f22c1de47af0f845330dc836c02bbf4d3d56018  pairs16-intent.md
a427c390f0c65b4ca0d9d0765bcfbbf3e9f3ec883c1ad85b6515a6abaa30d789  pairs21-facts.json
924d3fe91e05d86a81c566d89983f4a3c137ca6de766e7cff2e7b473e18ad0a4  pairs21-flow.md
2ff395fd356396173dbe2da37e6eec60435d5752e69745500cd16d48bcd37261  pairs21-intent.md
e4572248c5e8f1e8e6649b082cbe8acc69696746938a6d33d08dd1a119fbbc03  README.md
