import os
import re
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Set your OpenAI API key as an environment variable

# Dummy hospital data you can use to simulate a hospital assistant also provide database integration or vectorization.
hospital_info = {
    "name": "City Care Hospital",
    "departments": ["Cardiology", "Neurology", "Orthopedics", "Pediatrics"],
    "doctors": [
        {"name": "Dr. John Smith", "specialty": "Cardiology", "fee": "$200", "consultation_hours": "9am-5pm"},
        {"name": "Dr. Emily Davis", "specialty": "Neurology", "fee": "$250", "consultation_hours": "10am-4pm"},
        {"name": "Dr. Michael Lee", "specialty": "Orthopedics", "fee": "$180", "consultation_hours": "11am-3pm"}
    ],
    "appointments": [],
    "medical_records": {
        "12345": {"name": "John Doe", "age": 30, "last_visit": "2023-12-01", "notes": "Routine checkup, all normal."}
    }
}

def schedule_appointment(message):
    """
    Schedule an appointment by extracting the department and date.
    Expects the message to contain a department (e.g., Cardiology) and a date in YYYY-MM-DD format.
    """
    department = None
    date = None
    for dept in hospital_info["departments"]:
        if dept.lower() in message.lower():
            department = dept
            break

    date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", message)
    if date_match:
        date = date_match.group(1)

    if not department:
        return "Could not determine the department for the appointment. Please specify the department (e.g., Cardiology, Neurology)."
    if not date:
        return "Please specify a valid date for the appointment in YYYY-MM-DD format."

    appointment = {"department": department, "date": date, "status": "Scheduled"}
    hospital_info["appointments"].append(appointment)
    return f"Your appointment with the {department} department has been scheduled for {date}."

def find_doctor(message):
    """
    Find doctors matching the provided specialty or name.
    """
    results = []
    for doctor in hospital_info["doctors"]:
        if doctor["specialty"].lower() in message.lower() or doctor["name"].lower() in message.lower():
            results.append(doctor)
    if not results:
        return "No doctor found matching your query. Please try specifying the specialty or doctor's name."
    response = "Found the following doctor(s):\n"
    for doc in results:
        response += f"{doc['name']} - Specialty: {doc['specialty']}, Fee: {doc['fee']}, Consultation Hours: {doc['consultation_hours']}\n"
    return response

def manage_records(message):
    """
    Retrieve a dummy medical record using a 5-digit patient ID.
    """
    id_match = re.search(r"\b(\d{5})\b", message)
    if id_match:
        patient_id = id_match.group(1)
        record = hospital_info["medical_records"].get(patient_id)
        if record:
            return (f"Medical Record for {record['name']} (ID: {patient_id}): "
                    f"Age: {record['age']}, Last Visit: {record['last_visit']}, Notes: {record['notes']}")
        else:
            return "No medical record found for the provided ID."
    else:
        return "Please provide a valid 5-digit patient ID to retrieve medical records."

def answer_health_query(message):
    """
    Use OpenAI's API to answer general health-related queries.
    """
    prompt = f"""You are Hospibot, an AI-powered hospital assistant for {hospital_info['name']}.
Answer the following health-related query with clear and concise information:

Query: {message}

Answer:"""
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
            n=1
        )
        answer = response.choices[0].text.strip()
    except Exception as e:
        answer = "Error in generating response: " + str(e)
    return answer

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    lower_message = user_message.lower()

    # Determine functionality based on keywords in the user message
    if "appointment" in lower_message or "schedule" in lower_message:
        response_text = schedule_appointment(user_message)
    elif "doctor" in lower_message:
        response_text = find_doctor(user_message)
    elif "record" in lower_message or "medical record" in lower_message:
        response_text = manage_records(user_message)
    elif "health" in lower_message or "symptom" in lower_message or "illness" in lower_message:
        response_text = answer_health_query(user_message)
    else:
        # Default to answering a health query
        response_text = answer_health_query(user_message)

    return jsonify({"response": response_text})

if __name__ == "__main__":
    app.run(debug=True)
