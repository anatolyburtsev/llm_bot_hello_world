# llm_bot_hello_world


### Development

1. Create virtual env, install dependencies
2. Setup local secrets
```shell
cat ~/.streamlit/secrets.toml
OPENAI_API_KEY = "FILL ME"
GOOGLE_CSE_ID = "FILL ME"
GOOGLE_API_KEY = "FILL ME"
```
3. Run the app:
```shell
streamlit run streamlit_app.py
```


# Note
If app started failing to search on google, and google returns error code 429, it means you are out of free quota for custom search.

https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas

Enable billing and that quota will increase to 10k per day, (1k costs $5)