# data-io-app

```bash
rg_name=azstoragetestrg
resource_location=eastus
storage_account_name=ghstoragepltc
storage_sku=Standard_ZRS
container_name=databackup
```

```bash
az login
subscription_id=$(az account show --query id --output tsv)
az account set --subscription $subscription_id
az group create --name $rg_name --location $resource_location
az storage account create \
    --name $storage_account_name \
    --resource-group $rg_name \
    --location $resource_location \
    --sku $storage_sku \
    --encryption-services blob

az ad signed-in-user show --query objectId -o tsv | az role assignment create \
    --role "Storage Blob Data Contributor" \
    --assignee @- \
    --scope "/subscriptions/$subscription_id/resourceGroups/$rg_name/providers/Microsoft.Storage/storageAccounts/$storage_account_name"

az storage container create \
    --account-name $storage_account_name \
    --name $container_name \
    --auth-mode login
```

```bash
# data/.env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=ghstoragepltc;AccountKey=745546c1-218e-4260-80d7-208267004092745546c1-218e-4260-80d7-208267004092==;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER=databackup
```

## Directory structure

```bash
.
├── .gitkeep                   # Ensures folder structure in git
├── .env                       # All the env variables will be stored here.
├── data_io_app.py            # Data IO with Typer App
└── __init__.py                # All the module level meta data
```

## Installation

```bash
pip install azure-storage-blob loguru typer typer-cli
```
## Functionality:

* Download data from Blob
* Upload data from Blob
* Compress all folders in directory
* Unzip all folders in directory

Lets imaging this scenario you have some data in blob and you need the data from blob to you local system for development or you need the data in CI pipeline to run some tests or build some artifacts. Lets imaging there are a few images in a blob container and you need them for generating the wiki here are a few helpers which can be useful in that context,

#### 1. Check folder location

```bash
cd data
typer data_io_app.py run show_path
```

If you are getting an error like this, `ImportError: cannot import name 'BlobServiceClient' from 'azure.storage.blob'`, [this](https://github.com/Azure/azure-storage-python/issues/649) may resolve the issue.

```bash
pip uninstall -y azure-common azure-storage azure-nspkg azure-storage-blob
pip install azure-storage-blob --upgrade
pip install azure-common --upgrade
```

#### 2. Download files from blob container to a folder

```bash
typer data_io_app.py run download_all
```
### 3. Compress all local folders in current directory


```bash
typer data_io_app.py run compress_all
```

### 4. Upload all compressed folders in blob

```bash
typer data_io_app.py run upload_all
```

### 5. Download compressed files

```bash
typer data_io_app.py run download_all
```

### 6. Unzip compressed files

```bash
typer data_io_app.py run uncompress_all
```

## 7. data_io_app in github actions

```yml
name: CI
on:
  push:
    branches: [ develop ]
  pull_request:
    branches: [ develop ]
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
          architecture: 'x64'
      - name: Run a multi-line script
        run: |
          pip install -r requirements.txt
          cd data
          typer data_io_app.py run download_all
          typer data_io_app.py run uncompress_all
          rm pngs_files.zip
          typer data_io_app.py run compress_all
          mv pngs_files.zip pngs_files_gh_actions.zip
          typer data_io_app.py run upload_all
```


### Data folder

* Azure Container Name: `backenddsdata`

After creating a `.env` file run the following command to download and unzip the required folders in the `data` directory,


```bash
typer data_io_app.py run download_all
typer data_io_app.py run uncompress_all
```

Anytime we need some datasets in the `data` folder we need to create a zip file containing all the data. Upload data to the `mbabackenddsdata` container. Next time when we run the above commands we will get these datasets in local.

### Wiki folder

* Azure Container Name: `backendwikidata`

After creating a `.env` file run the following command to download the required files in the `wiki` directory,

```bash
typer data_io_app.py run download_all
```

### DB Backup folder

* Azure Container Name: `backenddbdata`

After creating a `.env` file run the following command to download the required files in the `backup` directory,

```bash
typer data_io_app.py run download_all
```
move `database.db` from backup folder to the project root directory.

When all the datasets are synced. Run `make clean` to clean all `__pycache__` folder generated due to the process.

### Details regarding blob

__Notes:__ If you want to have multiple version of the same file then in that case use the container name. you can use data in the container name to store multiple version of the same files. When getting the data take the latest container to fetch the latest version of the same data. Using these two  `Azure Container Name` & `Connection string link for the blob`  values mentioned above create a `.env` file in `data` directory and use the script and app for usual functionality.

#### Reference:

* https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python
* https://stackoverflow.com/questions/5137497/find-the-current-directory-and-files-directory
* https://stackoverflow.com/questions/3451111/unzipping-files-in-python
* https://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory/25650295#25650295
* https://stackoverflow.com/questions/26124281/convert-a-str-to-path-type
* https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
* https://github.com/Azure/azure-storage-python/issues/649