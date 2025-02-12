# Bing-powered custom chat

## tl;dr
In this repo, we create an agent that can use Bing to provide citations for its answers. The Bing Search API is also narrowed down to a list of domains (not entire web).

## Getting Started
- `python3.12 -m venv .venv`
- `./.venv/Scripts/activate` or `source ./.venv/bin/activate`
- `pip install -r requirements.txt`
- `pip install jupyter notebook` (if you need to run it in notebook)
- Create a file `.env` and copy contents of `sample.env`
    - Create the Azure resources and fill in the `*****` values.
- Run the notebook or code.