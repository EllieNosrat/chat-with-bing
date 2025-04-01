# Search Alerts Documents Using Natural Language

The code is in the _src_ folder.

Sample documents are in the _docs-to-search_ folder.

You will need to:

- In Azure:
    - Create an Azure Storage account and add the sample documents into a blob container "alerts" of this storage account
    - Create an Azure AI Search Service 
        - Add data source. Connect to the Azure Storage Account and the "alerts" container
        - Add an index "azurealerts-index"
        - Add Indexer "azurealerts-indexer"
            - Index: Select index just created
            - Data Source: Select data storage just created
            - Data to extrac: Content and metadata
    - Create an Azure AI Service
    - Create an Azure OpenAI service. 
    - Create an Azure AI Foundry Hub
        - Create a Project
            - Deploy Model gpt-4o
    Create Document Intelligence project
        http://documentintelligence.ai.azure.com/ (switch directory, if necessary)
            - Custom extraction model
                - Create AI Service / Doc Intelligence
                - Select resource group, storage account, "alerts" container
                - Label Data
                    - Drop sample document
                    - Run Layout
        This adds indexed data to storage account's 'alerts' container
- In the code:
    - Rename config-sample.py to config.py
    - update values in config.py corresponding to the assets created in Azure
- Run app.py
