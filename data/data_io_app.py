import glob
import os
import shutil
from typing import Optional, Tuple

import typer
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from loguru import logger


def zip_local_directory(base_path: str, dir_name: str) -> Tuple[str, str]:
    """
    Zip the local directory
    """
    zip_file_name = dir_name
    dir_name = os.path.join(base_path, dir_name)
    logger.info(
        "\nZipping directory: \n\t"
        + dir_name
        + "\n\t to file: \n\t"
        + zip_file_name
    )
    shutil.make_archive(zip_file_name, "zip", dir_name)
    return str(dir_name) + ".zip", zip_file_name + ".zip"


def unzip_file(filename, extract_dir):
    """Unzip the file"""
    logger.info(
        "\nUnzipping file: \n\t"
        + filename
        + "\n\t to directory: \n\t"
        + extract_dir
    )
    shutil.unpack_archive(filename, extract_dir)


app = typer.Typer()


@app.command("show_path")
def know_script_path() -> Tuple[str, str, str]:
    """
    Get the path of the file
    """
    logger.info("Path at terminal when executing this file")
    logger.info(os.getcwd() + "\n")
    logger.info("This file path, relative to os.getcwd()")
    logger.info(__file__ + "\n")
    logger.info("This file full path (following symlinks)")
    full_path = os.path.realpath(__file__)
    logger.info(full_path + "\n")
    logger.info("This file directory and name")
    path, filename = os.path.split(full_path)
    logger.info(path + " --> " + filename + "\n")
    logger.info("This file directory only")
    logger.info(os.path.dirname(full_path))
    return path, filename, full_path


@app.command("compress_all")
def zip_all_dirs():
    """
    Zip all the directories
    """
    path, filename, full_path = know_script_path()
    all_dirs_curr_dir = next(os.walk(path))[1]
    all_dirs_curr_dir.remove("__pycache__")
    list_of_dirs_to_compress = all_dirs_curr_dir
    all_zipped_file_paths = []
    all_zipped_file_names = []
    for dir_name in list_of_dirs_to_compress:
        zipped_file_path, zip_file_name = zip_local_directory(path, dir_name)
        all_zipped_file_paths.append(zipped_file_path)
        all_zipped_file_names.append(zip_file_name)
    return all_zipped_file_paths, all_zipped_file_names


@app.command("uncompress_all")
def unzip_all_files_in_dir():
    """Unzip all the files"""
    path, filename, full_path = know_script_path()
    all_zipped_file_paths = glob.glob(f"{path}/*.zip")
    all_zipped_file_names = [
        str(os.path.basename(file)) for file in all_zipped_file_paths
    ]
    for file_name, folder_name in zip(
        all_zipped_file_paths, all_zipped_file_names
    ):
        unzip_file(file_name, str(folder_name).replace(".zip", ""))


@app.command("download_all")
def download_all_files_from_container_to_local(
    path: Optional[str] = None,
) -> None:
    """
    Download all the files from a container to local

    typer data_io_app.py run download_all --path

    """
    load_dotenv()
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = str(os.getenv("AZURE_STORAGE_CONTAINER"))
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)
    if path:
        if not os.path.exists(str(path)):
            raise ValueError("\nThe provided path does not exist\n")
    else:
        path, filename, full_path = know_script_path()
    logger.info("\nListing blobs...")
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        logger.info("\t" + blob.name)
        download_file_path = os.path.join(path, blob.name)
        logger.info("\nDownloading blob to \n\t" + download_file_path)
        with open(download_file_path, "wb") as download_file:
            blob_client = blob_service_client.get_blob_client(
                container=container_name, blob=blob.name
            )
            download_file.write(blob_client.download_blob().readall())


@app.command("upload_all")
def upload_all_from_local(path: Optional[str] = None) -> None:
    """
    Upload all the files from local to blob
    """
    load_dotenv()
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = str(os.getenv("AZURE_STORAGE_CONTAINER"))
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    logger.info("\nUploading files to blob...")
    logger.info("\n\tConnecting to blob storage...")
    logger.info("\n\t\tUploading to container: " + container_name)
    if path:
        if not os.path.exists(str(path)):
            raise ValueError("\nThe provided path does not exist\n")
        dir_name = str(path).split("\\")[-1]
        base_path = os.path.abspath(os.path.join(os.path.dirname(path)))
        zipped_file_path, zipped_file_name = zip_local_directory(
            base_path, dir_name
        )
        with open(os.path.normpath(zipped_file_path), "rb") as data:
            blob_client = blob_service_client.get_blob_client(
                container=container_name, blob=zipped_file_name
            )
            blob_client.upload_blob(data)
            logger.info("\tUploaded blob: " + zipped_file_name)
    else:
        path, filename, full_path = know_script_path()
        all_zipped_file_paths = glob.glob(f"{path}/*.zip")
        all_zipped_file_names = [
            str(os.path.basename(file)) for file in all_zipped_file_paths
        ]

        for zipped_file_path, zipped_file_name in zip(
            all_zipped_file_paths, all_zipped_file_names
        ):
            with open(os.path.normpath(zipped_file_path), "rb") as data:
                blob_client = blob_service_client.get_blob_client(
                    container=container_name, blob=zipped_file_name
                )
                blob_client.upload_blob(data)
                logger.info("\tUploaded blob: " + zipped_file_name)


if __name__ == "__main__":
    app()
