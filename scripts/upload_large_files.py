import requests
import os
import uuid

def chunked_upload(file_path, url, token, chunk_size=5 * 1024 * 1024):
    """
    Handles chunked file upload.

    :param file_path: Path to the file to upload.
    :param url: Chunked upload endpoint.
    :param chunk_size: Size of each chunk in bytes (default: 5MB).
    """
    file_id = str(uuid.uuid4())
    file_name = os.path.basename(file_path)
    total_chunks = (os.path.getsize(file_path) + chunk_size - 1) // chunk_size
    headers = {
            'Authorization': f'Token {token}'
        }
    with open(file_path, "rb") as file:
        for chunk_number in range(1, total_chunks + 1):
            chunk = file.read(chunk_size)
            files = {'chunk': ('chunk', chunk)}
            data = {
                'chunk_number': chunk_number,
                'total_chunks': total_chunks,
                'file_id': file_id,
                'file_name': file_name
            }
            response = requests.post(url, data=data, files=files, headers=headers)
            if response.status_code == 200:
                print(f"Chunk {chunk_number}/{total_chunks} uploaded successfully.")
            elif response.status_code == 201 and chunk_number == total_chunks:
                print("File uploaded successfully!")
                print(f"Response: {response.json()}")  # Debugging final response
            else:
                print(f"Error uploading chunk {chunk_number}: {response.text}")
                return

    print("File uploaded successfully!")

# Example Usage
file_path = "/Users/himanshu/Documents/repos/videoverse/merged_video.mp4"  # Path to your large file
upload_url = "http://localhost:8000/api/videos/chunked_upload/"  # Your chunked upload endpoint
token = ''
chunked_upload(file_path, upload_url, token)
