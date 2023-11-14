import os
import asyncio
import aiofiles
import asyncssh
from fnmatch import fnmatch
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import gnupg
import logging
import json
import time

logging.basicConfig(level=logging.INFO)

class SFTPHandler(FileSystemEventHandler):
    def __init__(self, local_folder, sftp_folder, sftp, filename_patterns=None, direction="upload", gpg_executable=None):
        super().__init__()
        self.local_folder = local_folder
        self.sftp_folder = sftp_folder
        self.sftp = sftp
        self.filename_patterns = filename_patterns
        self.direction = direction
        self.gpg_executable = gpg_executable
        self.gpg = gnupg.GPG(gpgbinary=gpg_executable) if gpg_executable else None

    async def on_created(self, event):
        if event.is_directory:
            return

        filename = os.path.basename(event.src_path)
        if self.should_transfer(filename):
            local_path = event.src_path
            remote_path = os.path.join(self.sftp_folder, filename)

            if self.direction == "upload":
                logging.info(f"File created: {filename}")
                await self.upload_file(local_path, remote_path)
            elif self.direction == "download":
                logging.info(f"File created: {filename}")
                await self.download_file(remote_path, local_path)

    async def on_deleted(self, event):
        if event.is_directory:
            return

        filename = os.path.basename(event.src_path)
        if self.should_transfer(filename):
            remote_path = os.path.join(self.sftp_folder, filename)

            if self.direction == "upload":
                logging.info(f"File deleted: {filename}")
                await self.delete_file(remote_path)
            elif self.direction == "download":
                logging.info(f"File deleted: {filename}")
                # Add download logic if needed

    async def on_modified(self, event):
        if event.is_directory:
            return

        filename = os.path.basename(event.src_path)
        if self.should_transfer(filename):
            local_path = event.src_path
            remote_path = os.path.join(self.sftp_folder, filename)

            if self.direction == "upload":
                logging.info(f"File modified: {filename}")
                await self.upload_file(local_path, remote_path)
            elif self.direction == "download":
                logging.info(f"File modified: {filename}")
                # Add download logic if needed

    async def upload_file(self, local_path, remote_path):
        try:
            async with aiofiles.open(local_path, 'rb') as local_file:
                async with self.sftp.start_sftp() as sftp:
                    async with sftp.file(remote_path, 'wb') as remote_file:
                        async for chunk in local_file.iter_any(1024):
                            await remote_file.write(chunk)
            logging.info(f"Uploaded {local_path} to {remote_path}")
        except Exception as e:
            logging.error(f"Error uploading file: {e}")

    async def download_file(self, remote_path, local_path):
        try:
            async with self.sftp.start_sftp() as sftp:
                async with sftp.file(remote_path, 'rb') as remote_file:
                    async with aiofiles.open(local_path, 'wb') as local_file:
                        async for chunk in remote_file.iter_any(1024):
                            await local_file.write(chunk)
            logging.info(f"Downloaded {remote_path} to {local_path}")

            # Check if the downloaded file is encrypted and decrypt if GPG is available
            if self.gpg:
                decrypted_path = f"{local_path}_decrypted"
                self.decrypt_file(local_path, decrypted_path)
                os.replace(decrypted_path, local_path)

        except Exception as e:
            logging.error(f"Error downloading file: {e}")

    def decrypt_file(self, input_path, output_path):
        with open(input_path, 'rb') as encrypted_file:
            decrypted_data = self.gpg.decrypt_file(encrypted_file)
            with open(output_path, 'wb') as decrypted_file:
                decrypted_file.write(decrypted_data.data)

    async def delete_file(self, remote_path):
        try:
            async with self.sftp.start_sftp() as sftp:
                await sftp.remove(remote_path)
            logging.info(f"Deleted {remote_path}")
        except Exception as e:
            logging.error(f"Error deleting file: {e}")

    def should_transfer(self, filename):
        if not self.filename_patterns:
            return True

        return any(fnmatch(filename, pattern) for pattern in self.filename_patterns)


async def monitor_folders(configurations, gpg_executable):
    observers = []

    def load_configurations():
        try:
            with open("configurations.json", "r") as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            return []

    while True:
        current_configurations = load_configurations()

        # Check for changes in configurations
        if current_configurations != configurations:
            # Stop and join existing observers
            for observer in observers:
                observer.stop()
                observer.join()

            # Update configurations
            configurations = current_configurations

            # Create new observers
            for config in configurations:
                local_folder = config["local_folder"]
                sftp_folder = config["sftp_folder"]
                sftp_host = config["sftp_host"]
                sftp_port = config["sftp_port"]
                sftp_username = config["sftp_username"]
                sftp_password = config["sftp_password"]
                filename_patterns = config.get("filename_patterns", None)
                direction = config.get("direction", "upload")

                async with asyncssh.connect(sftp_host, port=sftp_port, username=sftp_username, password=sftp_password) as sftp:
                    event_handler = SFTPHandler(local_folder, sftp_folder, sftp, filename_patterns, direction, gpg_executable)
                    observer = Observer()
                    observer.schedule(event_handler, local_folder, recursive=False)
                    observer.start()

                    logging.info(f"Monitoring local folder: {local_folder}")
                    logging.info(f"Monitoring SFTP folder: {sftp_folder}")
                    logging.info(f"Direction: {direction}")
                    observers.append(observer)

        await asyncio.sleep(5)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    gpg_executable = "/path/to/gpg"

    configurations = []

    loop.run_until_complete(monitor_folders(configurations, gpg_executable))
    loop.close()
