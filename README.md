# GeoAI for Cities

**A research website and article series on GeoAI and urban decision-making** · Johan (Jhoven) Fernandez · Ongoing

GeoAI is a popular term with a vague meaning. This series defines it carefully, shows how cities used spatial technology long before the term existed, and keeps returning to one question: **when cities use these tools to rank and decide, who benefits?**

## The series

| Part | What it is |
|---|---|
| **Part 1: What Is GeoAI?** | An academic-style primer: definitions, tables, a timeline of GIS and spatial technology, and paths for practitioners and academics |
| **Manhattan, Measured** | An exploratory case study of how researchers measured the city before and after machine learning |
| **Part 2: Who Gets the Shade?** | An original spatial study of tree planting and heat in New York, with an interactive map ([code and data](https://github.com/JohanArisato/who-gets-the-shade)) |

The site also profiles my projects, including [CurbCall](https://github.com/JohanArisato/curbcall) and [Will It Get Built?](https://github.com/JohanArisato/housing-site-realization).

## The research stack behind it

| Repository | Role |
|---|---|
| [geoai-cities-db](https://github.com/JohanArisato/geoai-cities-db) | Shared spatial database (GeoPackage + PostGIS) that every project reads from |
| [who-gets-the-shade](https://github.com/JohanArisato/who-gets-the-shade) | Study code; reproduces every number in Part 2 from public data |
| [curbcall](https://github.com/JohanArisato/curbcall) | Resident-ranked infrastructure repairs, San Diego |
| [housing-site-realization](https://github.com/JohanArisato/housing-site-realization) | Predicting which Housing Element sites get built |

## Viewing the site

`index.html` is the whole site in one self-contained file (D3 and three.js load from cdnjs). Open it locally, or enable **GitHub Pages** (Settings → Pages → deploy from `main`, root) to publish it at `https://johanarisato.github.io/geoai-for-cities/`.

## How this was made

Writing, figures and the website were drafted with an AI assistant (Claude, Anthropic) under my editorial direction. I chose the topics, rejected drafts that felt generic, and set the framing. Background articles are being fact-checked against sources before formal citation.

## Next steps

- Fact-check and cite all background articles.
- Add a research statement page and a disclosure note in the footer.
- Publish Part 3.
