# Search User Guide Documents Using Natural Language

The code is in the _src_ folder.

Sample documents are in the _docs-to-search_ folder.

You will need to:

- In Azure:
    - Create an Azure Storage account and add the sample documents into a blob container "pdfs" of this storage account
    - Create an Azure AI Search Service 
        - Add data source. Connec to the Azure Storage Account and the "pdfs" container
        - Add an index "azureblog-index"
        - Add Indexer "azureblob-indexer"
            - Index: Select index just created
            - Data Source: Select data storage just created
    - Create an Azure OpenAI service. In Azure AI Foundry, deploy the gpt-4o model.
- In the code:
    - Rename config-sample.py to config.py
    - update values in config.py corresponding to the assets created in Azure
- Run app.py
