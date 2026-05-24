# LLM Managed Wiki Pages
This project is aimed to use agent skills to leverage LLM to convert raw input documentations into wiki pages in order to serve as personal knowlege management system (PKM).

It is inspected by Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).  This implementation is aimed to build three sets of skills 

| Category | Skill | Purpose |
| ---- | ---- | ---- |
| Wiki Management | wiki-init | Initialize the wiki page folders and metadata files |
| Wiki Management | wiki-ingest-all | Reset wiki pages.  Load all raw materials and generate wiki pages from scratch |
| Wiki Management | wiki-ingest-delta | Load new raw materials and update existing wiki pages |
| Wiki Management | wiki-lint | Detect orphan page and contradicting information |
| Collector | collect-yt-transcript | Collect youtube transcript as raw material |
| Load to LLM | TBC | TBC |


## Reference

- Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
- [llm-wiki-vault](https://github.com/MirkoSon/llm-wiki-vault/)
- [lm-knowledge-base](https://github.com/gatelynch/llm-knowledge-base/)
