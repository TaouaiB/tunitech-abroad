# LLM Job Enrichment Contract

## Goal

Extract structured job intelligence from messy France Travail job text.

The LLM extracts facts. It does not score candidates.

## Required JSON shape

```json
{
  "is_it_role": true,
  "role_family": "software_development",
  "normalized_role_title": "Développeur Fullstack Java",
  "seniority": "mid",
  "required_skills": [
    {
      "name": "Java",
      "evidence": "Conception et développement en langage Java"
    }
  ],
  "optional_skills": [
    {
      "name": "C",
      "evidence": "Des connaissances en langage C sont un plus"
    }
  ],
  "years_experience_min": 3,
  "languages": [
    {
      "language": "French",
      "level": "required",
      "evidence": "Français exigé"
    }
  ],
  "remote_policy": "hybrid",
  "confidence": "high"
}
```

## Allowed values

`role_family`:

- software_development
- web_mobile
- data_ai_bi
- devops_cloud_sre
- cybersecurity
- qa_testing
- systems_network
- database
- erp_crm
- it_support
- it_project_product_analysis
- it_training_apprenticeship
- other

`seniority`:

- intern
- junior
- mid
- senior
- unknown

`remote_policy`:

- remote
- hybrid
- onsite
- unknown

`confidence`:

- high
- medium
- low

## Evidence rules

Every skill must include evidence.

Evidence must be a short exact quote or near-exact substring from the original job text. Validation must reject skills with empty or fake evidence.

Do not extract soft skills as technical skills:

- rigueur
- autonomie
- bon relationnel
- esprit d'équipe
- communication
- curiosité

Do extract technical/professional IT skills:

- Java
- Quarkus
- PostgreSQL
- Oracle
- React
- Node.js
- TypeScript
- Docker
- Kubernetes
- Salesforce
- Apex
- Sage X3
- PeopleSoft
- SQL
- Power BI
- Cypress
- Selenium

## Required vs optional distinction

`required_skills` only if the text clearly indicates the skill is required/expected/main.

Examples:

- `Vos compétences : Java, PostgreSQL, Quarkus`
- `Compétences techniques indispensables : Flutter, React.js, Node.js`
- `Maîtrise de Salesforce`

`optional_skills` if text says:

- un plus
- serait apprécié
- connaissances en X
- nice to have
- bonus
- idéalement

## Validation result

The validation service must produce:

- `validated_output_json`
- `validation_errors_json`
- final status: `success` or `validation_error`

The raw LLM response must always be stored separately for debugging.
