#flask api which extracts data from image and returns these keys 


from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# Set your OpenAI API key
api_key = ""

def send_prompt_for_ocr(system_prompt, base64_image):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please extract the text from the following image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "low"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 400,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    base64_image = data.pop('Base64Image')
    system_prompt = f"""
    You are an OCR tool. Extract the text from the provided base64 image and keep your response exactly in the JSON structure below without any deviation for functional use. strictly ZERO leading or following characters.
    Expected format = {{
        "question_id": "{data['question_id']}",
        "student_id": "{data['student_id']}",
        "answer_sheet_path_masked": "{data['answer_sheet_path_masked']}",
        "extracted_answer": "string"
    }}
    """
    response = send_prompt_for_ocr(system_prompt, base64_image)
    return jsonify(response)







# the local script to send data to this api 


import pandas as pd
import requests
import json

# Function to send expected_format data to Flask API
def send_data_to_flask_api(data):
    url = "http://pratikreddy1.pythonanywhere.com/process"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# File path to your CSV
csv_file_path = 'output_with_base64_test50.csv'

# Read the CSV file
data = pd.read_csv(csv_file_path)

# Process each row in the CSV
for index, row in data.iterrows():
    question_id = row['QuestionId']
    student_id = row['StudentId']
    answer_sheet_path_masked = row['AnswerSheetPathMasked']
    student_answer_base64 = row['Base64Image']

    # Prepare the data in expected format without the Base64Image
    expected_format = {
        "question_id": question_id,
        "student_id": student_id,
        "answer_sheet_path_masked": answer_sheet_path_masked
    }

    # Combine expected_format and Base64Image for the API call
    payload = expected_format.copy()
    payload["Base64Image"] = student_answer_base64

    # Send the data to Flask API
    print(f"Sending OCR request for student {student_id} with QuestionId {question_id}")
    response = send_data_to_flask_api(payload)

    # Log the response
    print("Received response from Flask API:")
    print(json.dumps(response, indent=4))

    # Extract the student answer from the response
    try:
        extracted_answer = json.loads(response['choices'][0]['message']['content'])['extracted_answer']
        print(f"Extracted answer for student {student_id}: {extracted_answer}")
        # Update the DataFrame with the extracted answer
        data.at[index, 'StudentAnswer'] = extracted_answer
    except Exception as e:
        print(f"Error extracting answer for student {student_id}: {e}")

# Save the updated DataFrame back to a CSV file
updated_csv_file_path = 'output_with_base64_test50_updated.csv'
data.to_csv(updated_csv_file_path, index=False)

print(f"Updated CSV saved to {updated_csv_file_path}")



# the csv used is in the structure of the one hem sir has sent for student answers   "UM22MB654A_Data.csv"  with an added base64 coloumn mantainde locally.
