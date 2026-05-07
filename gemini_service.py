import os
import google.generativeai as genai
from flask import current_app

# Global variable to cache the first working model name
_cached_model = None

def get_gemini_response(prompt):
    global _cached_model
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return "Gemini API key not found. Please set GEMINI_API_KEY in .env"
    
    genai.configure(api_key=api_key)

    # 1. Use cached model if we already found one that works
    if _cached_model:
        try:
            model = genai.GenerativeModel(_cached_model)
            response = model.generate_content(prompt)
            return response.text
        except Exception:
            _cached_model = None # Reset if it stopped working

    # 2. Dynamically discover available models
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # Prioritize 1.5-flash and 1.5-pro
        priority_models = [m for m in available_models if '1.5' in m]
        other_models = [m for m in available_models if '1.5' not in m]
        
        for model_name in (priority_models + other_models):
            try:
                model = genai.GenerativeModel(model_name)
                # Quick test
                test_resp = model.generate_content("Hi", generation_config={"max_output_tokens": 5})
                if test_resp:
                    _cached_model = model_name
                    # Now do the real work
                    response = model.generate_content(prompt)
                    return response.text
            except Exception:
                continue
                
    except Exception as e:
        return f"Error discovering models: {str(e)}"
    
    return "Err: Could not find any supported Gemini models for this API key. Please check your Google AI Studio dashboard."

def generate_health_summary(patient_data):
    prompt = f"""
    As an AI medical assistant, summarize the following patient medical history for a doctor.
    Focus on key diagnoses, recurring issues, and recent treatments.
    Patient History: {patient_data}
    
    Provide a concise summary in bullet points.
    """
    return get_gemini_response(prompt)

def predict_waiting_time(queue_data):
    prompt = f"""
    Based on the following hospital queue data, predict the average waiting time for the next patient.
    Queue Data: {queue_data}
    Provide a numerical estimate in minutes and a brief explanation.
    """
    return get_gemini_response(prompt)

def suggest_appointment(symptoms, doctor_list):
    prompt = f"""
    A patient has the following symptoms: {symptoms}.
    Available doctors and their specializations: {doctor_list}.
    Suggest the most suitable doctor and explain why.
    """
    return get_gemini_response(prompt)

def check_medical_error(prescription_details, patient_history):
    prompt = f"""
    Check for potential medical errors or dangerous drug interactions.
    Prescription: {prescription_details}
    Patient History: {patient_history}
    If there is a risk, explain why. If safe, say "No immediate risks detected".
    """
    return get_gemini_response(prompt)

def predict_resource_demand(historical_usage):
    prompt = f"""
    Based on historical hospital resource usage: {historical_usage},
    predict the medicine demand and staff requirements for the next month.
    """
    return get_gemini_response(prompt)
