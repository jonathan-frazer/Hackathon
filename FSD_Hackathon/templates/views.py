from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from .models import login_details,employee_details
from django.conf import settings
from datetime import datetime
import os
import random

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

def dashboard_page(request):
    username = request.session.get('logged_user', False) 
    if username:
        return render(request,'dashboard_page.html',{'username':username})
    
    return redirect("Login Page")

def employee_list_page(request):
    username = request.session.get('logged_user', False) 
    if username:
        return render(request,'employee_list.html',{'username':username,
                                                    'employee_details':employee_details.find({})})
    
    return redirect("Login Page")

def employee_create_page(request):
    username = request.session.get('logged_user', False) 
    if username:
        if request.method == 'POST':
            # Get Id
            newId = -1
            employeeIds = [entry['f_Id'] for entry in list(employee_details.find({}))]
            maxEmployeeId = max(employeeIds)+1
            for id,r_id in zip(employeeIds, range(1,maxEmployeeId)):
                if id != r_id:
                    newId = r_id
                    break
            else:
                newId = maxEmployeeId

            # Get the current date
            current_date = datetime.now()
            formatted_date = f"{current_date.day}-{current_date.strftime('%b')}-{current_date.strftime('%y')}"

            # Create a dictionary to store the form data
            employee_data = {
                'f_Id': newId,
                'f_Createdate': formatted_date,
                'f_Name': request.POST.get('name'),
                'f_Image' : "dummypath/",
                'f_Email': request.POST.get('email'),
                'f_Mobile': request.POST.get('mobile'),
                'f_Designation': request.POST.get('designation'),
                'f_gender': request.POST.get('gender'),
                'f_Course': request.POST.getlist('course'),  # Get list of selected courses
            }

            # Handle the image upload
            image = request.FILES.get('image')
            if image:
                # Define the directory to save the uploaded images
                upload_dir = os.path.join(settings.STATICFILES_DIRS[0], 'employee_images')
                os.makedirs(upload_dir, exist_ok=True)  # Create the directory if it doesn't exist

                # Create a unique filename for the uploaded image
                f_Id = employee_data['f_Id']
                f_Name = employee_data['f_Name'].replace(' ', '_')  # Replace spaces with underscores
                unique_filename = f"{f_Id}-{f_Name}{os.path.splitext(image.name)[1]}"  # Preserve the original file extension

                image_path = os.path.join(upload_dir, unique_filename)
                with open(image_path, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)

                # Store the file path in the employee_data dictionary
                employee_data['f_Image'] = str(os.path.join('employee_images',unique_filename))

                employee_details.insert_one(employee_data)

            return redirect("Employee List Page")

        # If the request method is not POST, render the form page again
        return render(request,'create_employee_page.html',{'username':username})

    return redirect("Login Page")

def edit_employee(request, employee_id):
    username = request.session.get('logged_user', False)
    if username:
        if request.method == 'POST':
            # Fetch the existing employee data
            employee = employee_details.find_one({'f_Id': int(employee_id)})
            if not employee:
                return HttpResponse("Employee not found", status=404)

            # Create a dictionary to store the form data, only updating fields that are provided
            update_data = {}
            if request.POST.get('name'):
                update_data['f_Name'] = request.POST.get('name')
            if request.POST.get('email'):
                update_data['f_Email'] = request.POST.get('email')
            if request.POST.get('mobile'):
                update_data['f_Mobile'] = request.POST.get('mobile')
            if request.POST.get('designation'):
                update_data['f_Designation'] = request.POST.get('designation')
            if request.POST.get('gender'):
                update_data['f_gender'] = request.POST.get('gender')
            if request.POST.getlist('course'):
                update_data['f_Course'] = request.POST.getlist('course')

            # Handle the image upload
            image = request.FILES.get('image')
            if image:
                # Define the directory to save the uploaded images
                upload_dir = os.path.join(settings.STATICFILES_DIRS[0], 'employee_images')
                os.makedirs(upload_dir, exist_ok=True)  # Create the directory if it doesn't exist

                # Create a unique filename for the uploaded image
                f_Name = update_data.get('f_Name', employee['f_Name']).replace(' ', '_')  # Use new name if provided
                unique_filename = f"{employee_id}-{f_Name}{os.path.splitext(image.name)[1]}"  # Preserve the original file extension

                image_path = os.path.join(upload_dir, unique_filename)
                with open(image_path, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)

                # Store the file path in the update_data dictionary
                update_data['f_Image'] = str(os.path.join('employee_images', unique_filename))

                # Delete the old image if it exists
                old_image_path = os.path.join(settings.STATICFILES_DIRS[0], employee.get('f_Image'))
                if os.path.exists(old_image_path):
                    os.unlink(old_image_path)

            # If only the name and ID are changed, rename the old image
            elif 'f_Name' in update_data and 'f_Id' in employee:
                new_image_path = os.path.join(upload_dir, f"{employee_id}-{update_data['f_Name'].replace(' ', '_')}{os.path.splitext(employee['f_Image'])[1]}")
                old_image_path = os.path.join(settings.STATICFILES_DIRS[0], employee['f_Image'])
                if os.path.exists(old_image_path):
                    os.rename(old_image_path, new_image_path)
                update_data['f_Image'] = str(os.path.join('employee_images', f"{employee_id}-{update_data['f_Name'].replace(' ', '_')}{os.path.splitext(employee['f_Image'])[1]}"))

            # Update the employee data in the database
            if update_data:
                employee_details.update_one({'f_Id': int(employee_id)}, {'$set': update_data})

            return redirect("Employee List Page")

        # If the request method is not POST, render the edit form page with existing data
        employee = employee_details.find_one({'f_Id': int(employee_id)})
        if not employee:
            return HttpResponse("Employee not found", status=404)
        
        return render(request, 'edit_employee_page.html', {'username': username})

    return redirect("Login Page")


def delete_employee(request, employee_id):
    #Perform the Image Deletion
    result = employee_details.find_one({'f_Id':employee_id})
    image_path = os.path.join(settings.STATICFILES_DIRS[0],result.get('f_Image'))
    os.unlink(image_path)

    #Delete Employee Data
    employee_details.delete_one({'f_Id':employee_id})
    return redirect("Employee List Page")