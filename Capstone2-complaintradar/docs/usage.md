# Usage

ComplaintRadar answers questions from **public CFPB consumer complaint narratives**.

## Good questions

- "What are Wells Fargo customers saying about overdraft fees?"
- "What identity-theft issues show up against Equifax?"
- "How many mortgage complaints mention forbearance?" (uses the theme tool)
- "What went wrong with Apple Card / Goldman Sachs account closures?"

## Not this product

- SEC 10-K / earnings analysis (that was Capstone 1 / FinDocs)
- Legal advice or a claim that a company is guilty
- Invented nationwide statistics

## Retrieval modes

The Streamlit sidebar default is the **evaluation winner** written to
`evaluation_results/selected_retriever.json`. You can still switch to BM25,
vector, hybrid, or hybrid+rerank to compare.

## Agent tools

When enabled, the app can:

- `lookup_complaint` — open one CFPB id
- `theme_breakdown` — count issues by company/product
- `similar_cases` — hybrid retrieval of related narratives
