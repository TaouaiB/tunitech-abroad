# CV Name Extraction Policy

Reject candidate names that:

```text
contain je/me/moi/suis/j'ai/i am/my
look like sentences
contain section headers
contain profile summary phrases
contain job titles only
contain emails/URLs/phones/dates
have too many words
are all-lowercase prose
```

Must never return `je me suis` as a name. Return `None` with `low_confidence_name` warning instead.
