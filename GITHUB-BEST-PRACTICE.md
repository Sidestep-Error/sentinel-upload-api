Snabb översikt

Ja: alla jobbar i egna branches och allt går in via Pull Requests. Best practice i DevSecOps är att göra main “helig”: ingen direct push, bara PR + CI-gates.

2–4 frågor (för att välja rätt workflow)

Vill ni jobba som ett “produktteam” med en main och kortlivade branches?

Ska ni ha en staging-miljö (t.ex. namespace staging) eller bara dev/prod i demo?

Vill ni kräva 1 eller 2 approvals per PR?

Kör ni GitHub Projects/Jira eller bara Issues?

(Svara kort, men jag ger redan ett bra default-upplägg nedan.)

Rekommenderad best practice (enkel, proffsig)
Branching-modell: Trunk-based development (rekommenderas)

main = alltid deploybar

Alla features i kortlivade branches (1–3 dagar)

Merge via PR efter:

✅ CI passerar

✅ minst 1 review

✅ inga sårbarheter över er policy (senare Trivy/SBOM)

Varför: snabb feedback, mindre merge-conflicts, passar 6 veckor.

Praktisk rutin (hur ni jobbar dag för dag)
1) Skapa en branch per uppgift (inte per person)

Exempel:

feat/health-and-tests

ci/basic-workflow

docker/non-root

sec/trivy-gate

k8s/base-manifests

policy/gatekeeper-no-latest

Varför: ni kan parallellisera och ändå ha ren historik.

Om ni vill kan varje person “äga” ett område, men branchen ska representera en tydlig förändring.

PR-regler (minimum som räcker långt)

Sätt upp detta i GitHub:

Branch protection på main

✅ Require a pull request before merging

✅ Require status checks to pass (CI)

✅ Require at least 1 approval

✅ Dismiss stale approvals when new commits are pushed

✅ Block force pushes

✅ (valfritt) Require signed commits

Merge-strategi

Rekommenderat: Squash and merge

1 PR = 1 tydlig commit i main

lättare att backa (revert)

Hur ni undviker krockar (viktigast i team)
Ägarskap + CODEOWNERS (enkelt men effektivt)

Skapa .github/CODEOWNERS för att styra reviewers:

Exempel:

/.github/workflows/ → CI-personen

/policy/ och /k8s/ → K8s/Policy-personen

/runbooks/ och /sre/ → SRE/IR-personen

/app/ → App-owner

Det gör att GitHub automatiskt pingar rätt reviewer.

Issue → Branch → PR (en standard-loop)

Skapa en Issue (eller GitHub Project-kort)

Skapa branch: feat/<issue>-kort-beskrivning

Jobba, committa smått

Öppna PR tidigt som “Draft” om ni vill få feedback snabbt

CI + review → merge

Mini-exempel (kommandon ni följer)
git checkout main
git pull
git checkout -b feat/k8s-base-manifests
# gör ändringar
git add .
git commit -m "Add base Kubernetes manifests (Deployment/Service)"
git push -u origin feat/k8s-base-manifests


Sen PR i GitHub.

Vanliga misstag (som ni bör undvika)

En branch per person i 6 veckor → gigantiska PR:ar, konflikter, svårt att reviewa.

Mergar utan CI → ni tappar DevSecOps-poängen direkt.

För långa branches → trunk-based funkar bara om ni håller dem korta.

Min rekommenderade “teamkontrakt” (1 minut att enas om)

Main är skyddad, endast PR.

PR måste ha CI green + 1 approval.

Branchar ska vara små och kortlivade.

Namnge PR med prefix: feat:, fix:, sec:, k8s:, docs:.

En person är merge captain per vecka (roterar), som ser till att inget fastnar.

---

Kort cheat-sheet (teamet)

- Starta alltid från remote main:
  - git fetch origin
  - git checkout -b feat/<kort-namn> origin/main
- Jobba och committa smått:
  - git status -sb
  - git add <filer>
  - git commit -m "feat: kort beskrivning"
- Pusha och skapa PR:
  - git push -u origin feat/<kort-namn>
- Om "entirely different commit histories" uppstår:
  - Skapa ny branch från origin/main
  - Kopiera in filer från din gamla branch
  - Commit + push → PR
