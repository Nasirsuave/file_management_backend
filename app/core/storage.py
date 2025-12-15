

def save_upload_file(upload_file, destination):
    with open(destination, "wb") as f:
        f.write(upload_file)

