from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from .models import login_details
from django.conf import settings
from datetime import datetime
import json
import yaml
import re

# Create your views here.
def login_page(request):
    if request.method == 'POST':
        #Get Data from the fields
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Find Directory
        response = login_details.find_one({'f_userName':username})
        if response and response['f_Pwd'] == password:
            request.session['logged_user'] = username
            return redirect("Dashboard Page")
        
        return render(request,'login_page.html', {'error_message': "Please Enter Correct Details"})
    
    return render(request,'login_page.html')

def logout_page(request):
    user = request.session['logged_user'] 
    del request.session['logged_user']

    return render(request,'logout_page.html',{'username':user})

import google.generativeai as genai

def setup_model():
    genai.configure(api_key='AIzaSyCEBGmIK2xD38NevJV4WDF7rVUEYPk5z7I')

    # Create the model
    # See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
    generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
    }
    safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    ]

    model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    safety_settings=safety_settings,
    generation_config=generation_config,
    system_instruction="""
    You are an assistive ai model for Natural Language. 
    Your task is to take 
    1. A user query, 2. A JSON File depicting schema. 
    And return a new modified JSON file that consists of the JSON Schema modified according to the user's query 

    Eg: 
    USER
    Query: I want the author's first and last names only
    JSON File:
    {
    "database": "LibraryDB",
    "tables": [
      {
        "name": "authors",
        "columns": [
          {
            "name": "id",
            "type": "INTEGER",
            "constraints": ["PRIMARY KEY", "AUTOINCREMENT"]
          },
          {
            "name": "first_name",
            "type": "VARCHAR(50)",
            "constraints": ["NOT NULL"]
          },
          {
            "name": "last_name",
            "type": "VARCHAR(50)",
            "constraints": ["NOT NULL"]
          },
          {
            "name": "birth_date",
            "type": "DATE",
            "constraints": []
          }
        ]
      },
      {
        "name": "books",
        "columns": [
          {
            "name": "id",
            "type": "INTEGER",
            "constraints": ["PRIMARY KEY", "AUTOINCREMENT"]
          },
          {
            "name": "title",
            "type": "VARCHAR(100)",
            "constraints": ["NOT NULL"]
          },
          {
            "name": "author_id",
            "type": "INTEGER",
            "constraints": ["NOT NULL", "FOREIGN KEY REFERENCES authors(id)"]
          },
          {
            "name": "published_date",
            "type": "DATE",
            "constraints": []
          },
          {
            "name": "isbn",
            "type": "VARCHAR(20)",
            "constraints": ["UNIQUE"]
          }
        ]
      }
    ]
  }

  RESPONSE:
  {
    "database": "LibraryDB",
    "tables": [
      {
        "name": "authors",
        "columns": [
          {
            "name": "first_name",
            "type": "VARCHAR(50)",
            "constraints": ["NOT NULL"]
          },
          {
            "name": "last_name",
            "type": "VARCHAR(50)",
            "constraints": ["NOT NULL"]
          }
        ]
      }
    ]
  }

  Ensure that it ONLY returns the modified JSON file and nothing else
    """,
    )
    return model

def setup_session():
    chat_session = setup_model().start_chat(
        history=[]
    )
    return chat_session

def get_response(user_input):
    chat_session = setup_session()
    return chat_session.send_message(user_input).text

def extract_json_string(input_string):
    # Use regex to find the first opening and last closing curly braces
    match = re.search(r'({.*})', input_string, re.DOTALL)
    if match:
        return match.group(1).strip()  # Return the matched JSON string
    return None  # Return None if no match is found

def dashboard_page(request):
    username = request.session.get('logged_user', False) 
    if not username:
        return redirect("Login Page")
    
    if request.method == 'POST':
        #Get Data from the fields
        userQuery = request.POST.get('userQuery')
        jsonFile = request.FILES.get('jsonFile')

        # Process the JSON file
        if jsonFile.name.endswith('.json'):
            # Read JSON file
            schema_data = json.load(jsonFile)
        elif jsonFile.name.endswith('.yaml') or jsonFile.name.endswith('.yml'):
            schema_data = json.load(jsonFile.read().decode('utf-8'))
        
        ai_input = f"Query: {userQuery}\nColumns: {json.dumps(schema_data, indent=4)}"

        response_string = get_response(ai_input)
        json_string = extract_json_string(response_string)

        return render(request,'dashboard_page.html',{'username':username,'jsonResponse':json_string})

    return render(request,'dashboard_page.html',{'username':username})