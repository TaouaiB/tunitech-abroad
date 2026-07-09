# Broad IT Preset

The `broad_it` preset must cover broad France IT roles, not only developers.

Default keyword set should include at least:

```text
développeur
ingénieur logiciel
fullstack
backend
frontend
java
python
javascript
typescript
react
angular
node.js
php
django
mobile developer
flutter
kotlin
swift
data analyst
data scientist
data engineer
business intelligence
power bi
devops
sre
cloud
azure
aws
kubernetes
docker
cybersécurité
sécurité informatique
soc
pentest
qa
testeur
test automation
support informatique
technicien informatique
helpdesk
administrateur systèmes
administrateur réseau
réseau informatique
dba
base de données
salesforce
sage x3
erp
crm
business analyst informatique
chef de projet informatique
product owner informatique
amoa informatique
alternance informatique
stage informatique
stage développeur
pfe informatique
```

Implementation may store these in a constant/service such as:

```python
BROAD_IT_KEYWORDS = [...]
```

or in a JSON/preset service.

## Filtering

The preset will still fetch false positives. This is normal.

After fetch:

- Deduplicate by France Travail job ID.
- Normalize.
- Apply IT relevance / enrichment eligibility.
- LLM enrichment can mark non-IT as `is_it_role=False`.
- Recommendations must exclude non-technical/irrelevant jobs.

Do not rely on one keyword such as `développeur`. France Travail has many IT categories and wording variations.
