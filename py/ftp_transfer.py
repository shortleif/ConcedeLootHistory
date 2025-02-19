import ftplib
from dotenv import load_dotenv
import os

load_dotenv()

def upload_file_to_ftp(filename, ftp_host, ftp_user, ftp_pass):
    """Uploads a file to an FTP server.

    Args:
        filename: The name of the file to upload.
        ftp_host: The hostname or IP address of the FTP server.
        ftp_user: The username for the FTP account.
        ftp_pass: The password for the FTP account.
    """
    try:
        # Connect to the FTP server
        with ftplib.FTP(ftp_host) as ftp:
            ftp.login(user=ftp_user, passwd=ftp_pass)

            # Open the file in binary mode
            with open(filename, 'rb') as file:
                # Upload the file
                ftp.storbinary(f'STOR loothistory/{filename}', file)

            print(f"File '{filename}' uploaded successfully to {ftp_host}")

    except ftplib.all_errors as e:
        print(f"FTP error: {e}")


upload_file_to_ftp(filename, ftp_host, ftp_user, ftp_pass)