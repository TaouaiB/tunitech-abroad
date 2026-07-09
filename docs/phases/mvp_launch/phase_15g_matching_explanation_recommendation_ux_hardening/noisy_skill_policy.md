# Phase 15G Noisy / Foundational Skill Policy

## Goal

Avoid low-quality missing-skill recommendations like `JSON` when stronger skills imply it.

This is a presentation/recommendation filter, not a taxonomy deletion.

## Keep extraction, suppress display

Skills like JSON can still exist in:

- Skill taxonomy
- Skill aliases
- Job materialized skills
- Internal scoring evidence

But they should not appear prominently in:

- `Compétences requises manquantes`
- `Compétences optionnelles à renforcer`
- Learning-plan actions

when they are foundational or implied by stronger skills.

## Baseline noisy list

Suppress or downgrade in display when not explicitly advanced:

```text
JSON
XML
YAML
CSV
Markdown
HTTP
HTTPS
Agile
Scrum
Documentation
Office tools
Microsoft Office
Pack Office
```

## JSON implied coverage rule

If candidate has any of:

```text
JavaScript
TypeScript
Node.js
REST API
API REST
RESTful API
Frontend development
Backend development
Full-stack development
Django
Flask
Express
Spring
ASP.NET
```

then hide `JSON` from missing/optional/recommendation lists.

## Do not suppress specific advanced skills

Do not hide:

```text
JSON Schema
JSON-LD
jq
OpenAPI
Swagger
XML Schema
XSD
XPath
XSLT
```

## Required example

Input optional gaps:

```text
JSON, Kubernetes, Jenkins, Nexus Repository, Ionic, Cypress, GitLab, Jira, Confluence
```

Candidate has:

```text
JavaScript, TypeScript, REST API, Node.js
```

Displayed optional gaps:

```text
Kubernetes, Jenkins, Nexus Repository, Ionic, Cypress, GitLab, Jira, Confluence
```
