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
In Document Intelligence studio (http://documentintelligence.ai.azure.com/)
    - Layout model
        - Add Alert_Param_Descriptions_241219_204304.pdf
        - [Analyze]
        - Download result
        - Copy result (Alert_Param_Descriptions_241219_204304.pdf.json) into _data\pdf_docintel_ folder
- In the code:
    - Rename config-sample.py to config.py
    - update values in config.py corresponding to the assets created in Azure
- Run transcript-aisearch.py
- Run app.py
