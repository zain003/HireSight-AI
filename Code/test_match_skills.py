import requests

url = "http://localhost:8000/resume/match-skills"
file_path = "backend/uploads/user_69b2ea4ba5fedef335c2960d/resume_69b2ea4ba5fedef335c2960d.pdf"
job_post_id = "example_job_post_id"
headers = {"Authorization": "Bearer <your_token_here>"}  # Replace <your_token_here> with a valid token

with open(file_path, "rb") as file:
    files = {"file": file}
    data = {"job_post_id": job_post_id}
    response = requests.post(url, headers=headers, files=files, data=data)

print("Status Code:", response.status_code)
print("Response:", response.json())