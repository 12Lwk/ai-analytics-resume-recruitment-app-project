from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
import pymongo
import hashlib
from datetime import datetime, timedelta
import random
import string

class MongoDBConnection:
    def __init__(self):
        # Use connection string for Atlas
        if hasattr(settings, 'MONGODB_SETTINGS') and 'connection_string' in settings.MONGODB_SETTINGS:
            self.client = pymongo.MongoClient(settings.MONGODB_SETTINGS['connection_string'])
        else:
            # Fallback to local connection
            self.client = pymongo.MongoClient('localhost', 27017)
        
        self._db = self.client['resume_admin']
        print(f"✅ Connected to MongoDB database: resume_admin")
    
    def get_collection(self, collection_name='resume_login'):
        return self._db[collection_name]
    
    def insert_user(self, user_data):
        collection = self.get_collection()
        return collection.insert_one(user_data)
    
    def find_user(self, query):
        collection = self.get_collection()
        return collection.find_one(query)
    
    def get_all_users(self):
        collection = self.get_collection()
        return list(collection.find({}))

class CustomLoginView(LoginView):
    template_name = 'resume_app/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return '/'
    
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        # Authenticate using our custom backend
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            login(self.request, user)
            # Get user's display name from MongoDB or fallback to username
            display_name = user.first_name or user.username
            messages.success(self.request, f'Welcome back, {display_name}!')
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.form_invalid(form)

class CustomUserCreationForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )
    company = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    role = forms.ChoiceField(
        choices=[
            ('', 'Select your role'),
            ('hr_manager', 'HR Manager'),
            ('recruiter', 'Recruiter'),
            ('hiring_manager', 'Hiring Manager'),
            ('team_lead', 'Team Lead'),
            ('admin', 'Administrator'),
            ('analyst', 'HR Analyst'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        
        # Check MongoDB only
        try:
            mongo = MongoDBConnection()
            if mongo.find_user({'username': username}):
                raise forms.ValidationError("Username already exists.")
        except Exception as e:
            print(f"Error checking username: {e}")
        
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Check MongoDB only
        try:
            mongo = MongoDBConnection()
            if mongo.find_user({'email': email}):
                raise forms.ValidationError("Email already registered.")
        except Exception as e:
            print(f"Error checking email: {e}")
        
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")
        
        if password1 and len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

        return cleaned_data

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                # Save ONLY to MongoDB (matching exact schema)
                mongo = MongoDBConnection()
                password_hash = hashlib.sha256(form.cleaned_data['password1'].encode()).hexdigest()
                
                # Split full name into first and last name
                full_name_parts = form.cleaned_data['full_name'].split()
                first_name = full_name_parts[0] if full_name_parts else ''
                last_name = ' '.join(full_name_parts[1:]) if len(full_name_parts) > 1 else ''
                
                user_data = {
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'password_hash': password_hash,
                    'full_name': form.cleaned_data['full_name'],
                    'first_name': first_name,
                    'last_name': last_name,
                    'company': form.cleaned_data.get('company', ''),
                    'role': form.cleaned_data.get('role', ''),
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False,
                    'date_joined': datetime.utcnow(),
                    'last_login': None,
                    'profile': {
                        'employee_id': f'EMP{datetime.now().strftime("%Y%m%d%H%M%S")}',
                        'department': form.cleaned_data.get('company', ''),
                        'phone': '',
                        'location': '',
                        'bio': '',
                        'skills': []
                    },
                    'permissions': {
                        'can_view_candidates': True,
                        'can_edit_candidates': form.cleaned_data.get('role') in ['hr_manager', 'admin'],
                        'can_delete_candidates': form.cleaned_data.get('role') == 'admin',
                        'can_manage_users': form.cleaned_data.get('role') == 'admin'
                    },
                    'preferences': {
                        'email_alerts': True,
                        'application_updates': True,
                        'theme': 'light',
                        'language': 'en'
                    }
                }
                
                # Insert into MongoDB
                result = mongo.insert_user(user_data)
                print(f"✅ User saved to MongoDB with ID: {result.inserted_id}")
                
                messages.success(request, 'Account created successfully! Please log in.')
                return redirect('login')
                
            except Exception as e:
                print(f"❌ Error saving to MongoDB: {e}")
                messages.error(request, f'Registration failed: {e}')
                
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'resume_app/register.html', {'form': form})

@login_required
def dashboard(request):
    # Mock data for dashboard
    context = {
        'total_candidates': 128,
        'time_to_hire': '32 days',
        'offer_acceptance_rate': '78%',
        'source_data': [40, 30, 20, 38],
        'pipeline': {'applied': 60, 'interviewed': 25, 'hired': 15},
    }
    return render(request, 'resume_app/dashboard.html', context)

@login_required
def candidates(request):
    return render(request, 'resume_app/candidates.html')

@login_required
def interviews(request):
    return render(request, 'resume_app/interviews.html')

@login_required
def offers(request):
    return render(request, 'resume_app/offers.html')

def handle_resume_upload(request):
    """Handle resume file uploads and AI processing"""
    try:
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile

        uploaded_files = request.FILES.getlist('resume_files')
        job_title = request.POST.get('job_title', '').strip()
        department = request.POST.get('department', '').strip()
        tags = request.POST.get('tags', '').strip()

        if not uploaded_files:
            messages.error(request, 'Please select at least one resume file to upload.')
            return redirect('resume_upload')

        mongo = MongoDBConnection()
        upload_collection = mongo.get_collection('resume_uploads')
        candidate_collection = mongo.get_collection('candidates')

        successful_uploads = 0
        failed_uploads = 0
        duplicate_count = 0

        for uploaded_file in uploaded_files:
            try:
                # Validate file type
                allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()

                if file_extension not in allowed_extensions:
                    messages.warning(request, f'File {uploaded_file.name} has unsupported format. Skipped.')
                    failed_uploads += 1
                    continue

                # Validate file size (5MB limit)
                if uploaded_file.size > 5 * 1024 * 1024:
                    messages.warning(request, f'File {uploaded_file.name} is too large (max 5MB). Skipped.')
                    failed_uploads += 1
                    continue

                # Save file
                file_path = default_storage.save(
                    f'resumes/{datetime.now().strftime("%Y/%m/%d")}/{uploaded_file.name}',
                    ContentFile(uploaded_file.read())
                )

                # Simulate AI parsing (in real implementation, you'd use actual AI/ML libraries)
                parsed_data = simulate_ai_parsing(uploaded_file.name, file_extension)

                # Check for duplicates
                existing_candidate = candidate_collection.find_one({
                    '$or': [
                        {'email': parsed_data.get('email')},
                        {'phone': parsed_data.get('phone')},
                        {'$and': [
                            {'first_name': parsed_data.get('first_name')},
                            {'last_name': parsed_data.get('last_name')}
                        ]}
                    ]
                })

                if existing_candidate:
                    duplicate_count += 1
                    # Update existing candidate with new resume
                    candidate_collection.update_one(
                        {'_id': existing_candidate['_id']},
                        {
                            '$set': {
                                'last_updated': datetime.now(),
                                'resume_file_path': file_path,
                                'updated_by': request.user.username
                            },
                            '$push': {
                                'resume_history': {
                                    'file_path': file_path,
                                    'upload_date': datetime.now(),
                                    'uploaded_by': request.user.username
                                }
                            }
                        }
                    )
                    candidate_id = existing_candidate['_id']
                else:
                    # Create new candidate profile
                    candidate_data = {
                        'first_name': parsed_data.get('first_name', ''),
                        'last_name': parsed_data.get('last_name', ''),
                        'email': parsed_data.get('email', ''),
                        'phone': parsed_data.get('phone', ''),
                        'location': parsed_data.get('location', ''),
                        'linkedin_url': parsed_data.get('linkedin_url', ''),
                        'experience': parsed_data.get('experience', []),
                        'education': parsed_data.get('education', []),
                        'skills': parsed_data.get('skills', []),
                        'certifications': parsed_data.get('certifications', []),
                        'summary': parsed_data.get('summary', ''),
                        'resume_file_path': file_path,
                        'job_title_applied': job_title,
                        'department': department,
                        'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
                        'ai_score': parsed_data.get('ai_score', 0),
                        'quality_score': parsed_data.get('quality_score', 0),
                        'status': 'new',
                        'source': 'resume_upload',
                        'created_date': datetime.now(),
                        'created_by': request.user.username,
                        'last_updated': datetime.now(),
                        'resume_history': [{
                            'file_path': file_path,
                            'upload_date': datetime.now(),
                            'uploaded_by': request.user.username
                        }]
                    }

                    result = candidate_collection.insert_one(candidate_data)
                    candidate_id = result.inserted_id

                # Record upload activity
                upload_record = {
                    'filename': uploaded_file.name,
                    'file_path': file_path,
                    'file_size': uploaded_file.size,
                    'file_type': file_extension,
                    'candidate_id': candidate_id,
                    'parsed_data': parsed_data,
                    'job_title': job_title,
                    'department': department,
                    'tags': [tag.strip() for tag in tags.split(',') if tag.strip()],
                    'status': 'completed',
                    'upload_date': datetime.now(),
                    'uploaded_by': request.user.username,
                    'processing_time': random.uniform(0.5, 3.0),  # Simulated processing time
                    'is_duplicate': existing_candidate is not None
                }

                upload_collection.insert_one(upload_record)
                successful_uploads += 1

            except Exception as e:
                print(f"Error processing file {uploaded_file.name}: {e}")
                failed_uploads += 1
                continue

        # Provide feedback to user
        if successful_uploads > 0:
            messages.success(request, f'Successfully processed {successful_uploads} resume(s).')

        if duplicate_count > 0:
            messages.info(request, f'{duplicate_count} duplicate candidate(s) found and updated.')

        if failed_uploads > 0:
            messages.warning(request, f'{failed_uploads} file(s) failed to process.')

    except Exception as e:
        print(f"Error in resume upload handler: {e}")
        messages.error(request, 'An error occurred while processing the uploads.')

    return redirect('resume_upload')

def simulate_ai_parsing(filename, file_extension):
    """Simulate AI parsing of resume content"""
    # In a real implementation, this would use actual AI/ML libraries
    # like spaCy, transformers, or custom trained models

    # Generate realistic mock data based on filename
    import hashlib
    seed = int(hashlib.md5(filename.encode()).hexdigest()[:8], 16)
    random.seed(seed)

    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'James', 'Maria']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

    skills_pool = [
        'Python', 'JavaScript', 'Java', 'React', 'Node.js', 'SQL', 'MongoDB', 'AWS', 'Docker', 'Kubernetes',
        'Machine Learning', 'Data Analysis', 'Project Management', 'Agile', 'Scrum', 'Git', 'Linux', 'Azure',
        'Angular', 'Vue.js', 'Django', 'Flask', 'Spring Boot', 'Microservices', 'REST APIs', 'GraphQL'
    ]

    companies = ['Google', 'Microsoft', 'Amazon', 'Apple', 'Meta', 'Netflix', 'Spotify', 'Uber', 'Airbnb', 'Tesla']
    universities = ['MIT', 'Stanford', 'Harvard', 'Berkeley', 'CMU', 'Caltech', 'Princeton', 'Yale', 'Columbia', 'Cornell']

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)

    return {
        'first_name': first_name,
        'last_name': last_name,
        'email': f"{first_name.lower()}.{last_name.lower()}@email.com",
        'phone': f"+1-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
        'location': random.choice(['New York, NY', 'San Francisco, CA', 'Seattle, WA', 'Austin, TX', 'Boston, MA']),
        'linkedin_url': f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}",
        'experience': [
            {
                'title': random.choice(['Software Engineer', 'Senior Developer', 'Tech Lead', 'Product Manager']),
                'company': random.choice(companies),
                'duration': f"{random.randint(1,5)} years",
                'description': 'Led development of scalable web applications and managed cross-functional teams.'
            }
        ],
        'education': [
            {
                'degree': random.choice(['Bachelor of Science', 'Master of Science', 'Bachelor of Engineering']),
                'field': random.choice(['Computer Science', 'Software Engineering', 'Information Technology']),
                'university': random.choice(universities),
                'year': random.randint(2015, 2023)
            }
        ],
        'skills': random.sample(skills_pool, random.randint(5, 12)),
        'certifications': random.sample(['AWS Certified', 'Google Cloud Certified', 'Microsoft Azure Certified'], random.randint(0, 2)),
        'summary': f"Experienced {random.choice(['software engineer', 'developer', 'technical lead'])} with expertise in modern technologies and agile methodologies.",
        'ai_score': random.randint(75, 95),
        'quality_score': random.randint(70, 90)
    }

@login_required
def resume_upload(request):
    """Resume Upload page for recruiters with AI-powered parsing"""
    if request.method == 'POST':
        return handle_resume_upload(request)

    try:
        # Get recent uploads and statistics
        mongo = MongoDBConnection()

        # Get recent uploads for this user
        recent_uploads = list(mongo.get_collection('resume_uploads').find(
            {'uploaded_by': request.user.username}
        ).sort('upload_date', -1).limit(10))

        # Get upload statistics
        total_uploads = mongo.get_collection('resume_uploads').count_documents(
            {'uploaded_by': request.user.username}
        )

        # Get processing statistics
        processing_count = mongo.get_collection('resume_uploads').count_documents(
            {'uploaded_by': request.user.username, 'status': 'processing'}
        )

        completed_count = mongo.get_collection('resume_uploads').count_documents(
            {'uploaded_by': request.user.username, 'status': 'completed'}
        )

        context = {
            'recent_uploads': recent_uploads,
            'total_uploads': total_uploads,
            'processing_count': processing_count,
            'completed_count': completed_count,
            'success_rate': round((completed_count / total_uploads * 100) if total_uploads > 0 else 0, 1)
        }

        return render(request, 'resume_app/resume_upload.html', context)

    except Exception as e:
        print(f"Error in resume upload page: {e}")
        messages.error(request, 'An error occurred while loading the upload page.')
        return redirect('dashboard')

def handle_password_change(request):
    """Handle password change form submission"""
    try:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validation
        if not all([current_password, new_password, confirm_password]):
            messages.error(request, 'All password fields are required.')
            return redirect('settings')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('settings')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('settings')

        # Verify current password
        mongo = MongoDBConnection()
        current_password_hash = hashlib.sha256(current_password.encode()).hexdigest()
        user_data = mongo.find_user({
            'username': request.user.username,
            'password_hash': current_password_hash
        })

        if not user_data:
            messages.error(request, 'Current password is incorrect.')
            return redirect('settings')

        # Update password in MongoDB
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        result = mongo.get_collection().update_one(
            {'username': request.user.username},
            {
                '$set': {
                    'password_hash': new_password_hash,
                    'last_login': datetime.now()
                }
            }
        )

        if result.modified_count > 0:
            messages.success(request, 'Password changed successfully!')
        else:
            messages.error(request, 'Failed to update password.')

    except Exception as e:
        print(f"Error changing password: {e}")
        messages.error(request, 'An error occurred while changing password.')

    return redirect('settings')

def handle_profile_update(request):
    """Handle profile update form submission"""
    try:
        mongo = MongoDBConnection()

        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        address = request.POST.get('address', '').strip()
        device_info = request.POST.get('device_info', '').strip()
        browser_info = request.POST.get('browser_info', '').strip()

        # Update user data in MongoDB
        update_data = {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}".strip(),
            'profile.location': address,
            'profile.device_info': device_info,
            'profile.browser_info': browser_info,
            'last_login': datetime.now()
        }

        result = mongo.get_collection().update_one(
            {'username': request.user.username},
            {'$set': update_data}
        )

        if result.modified_count > 0:
            messages.success(request, 'Profile updated successfully!')
        else:
            messages.info(request, 'No changes were made to your profile.')

    except Exception as e:
        print(f"Error updating profile: {e}")
        messages.error(request, 'An error occurred while updating profile.')

    return redirect('settings')

def handle_notifications_update(request):
    """Handle notification preferences update"""
    try:
        mongo = MongoDBConnection()

        # Get notification preferences from form
        email_alerts = request.POST.get('email_alerts') == 'on'
        application_updates = request.POST.get('application_updates') == 'on'
        interview_reminders = request.POST.get('interview_reminders') == 'on'
        offer_notifications = request.POST.get('offer_notifications') == 'on'
        system_updates = request.POST.get('system_updates') == 'on'
        marketing_emails = request.POST.get('marketing_emails') == 'on'

        # Get communication preferences
        email_frequency = request.POST.get('email_frequency', 'daily')
        notification_time = request.POST.get('notification_time', '09:00')
        timezone_pref = request.POST.get('timezone_pref', 'UTC')

        # Get mobile preferences
        push_notifications = request.POST.get('push_notifications') == 'on'
        sms_notifications = request.POST.get('sms_notifications') == 'on'
        phone_number = request.POST.get('phone_number', '').strip()

        # Update notification preferences in MongoDB
        notification_data = {
            'preferences.email_alerts': email_alerts,
            'preferences.application_updates': application_updates,
            'preferences.interview_reminders': interview_reminders,
            'preferences.offer_notifications': offer_notifications,
            'preferences.system_updates': system_updates,
            'preferences.marketing_emails': marketing_emails,
            'preferences.email_frequency': email_frequency,
            'preferences.notification_time': notification_time,
            'preferences.timezone_pref': timezone_pref,
            'preferences.push_notifications': push_notifications,
            'preferences.sms_notifications': sms_notifications,
            'profile.phone': phone_number,
            'last_login': datetime.now()
        }

        result = mongo.get_collection().update_one(
            {'username': request.user.username},
            {'$set': notification_data}
        )

        if result.modified_count > 0:
            messages.success(request, 'Notification preferences updated successfully!')
        else:
            messages.info(request, 'No changes were made to your notification preferences.')

    except Exception as e:
        print(f"Error updating notifications: {e}")
        messages.error(request, 'An error occurred while updating notification preferences.')

    return redirect('settings')

def handle_verification_request(request):
    """Handle verification requests and updates"""
    try:
        mongo = MongoDBConnection()
        verification_type = request.POST.get('verification_type')

        if verification_type == 'email':
            return handle_email_verification(request, mongo)
        elif verification_type == 'phone':
            return handle_phone_verification(request, mongo)
        elif verification_type == 'identity':
            return handle_identity_verification(request, mongo)
        elif verification_type == 'two_factor':
            return handle_two_factor_setup(request, mongo)
        else:
            messages.error(request, 'Invalid verification type.')

    except Exception as e:
        print(f"Error handling verification: {e}")
        messages.error(request, 'An error occurred during verification process.')

    return redirect('settings')

def handle_email_verification(request, mongo):
    """Handle email verification process"""
    import random
    import string

    try:
        # Generate verification code
        verification_code = ''.join(random.choices(string.digits, k=6))

        # Store verification code in MongoDB
        verification_data = {
            'verification.email_code': verification_code,
            'verification.email_code_expires': datetime.now() + timedelta(minutes=15),
            'verification.email_attempts': 0,
            'last_login': datetime.now()
        }

        mongo.get_collection().update_one(
            {'username': request.user.username},
            {'$set': verification_data}
        )

        # In a real application, you would send this code via email
        # For demo purposes, we'll show it in the message
        messages.success(request, f'Email verification code sent! (Demo code: {verification_code})')

    except Exception as e:
        print(f"Error in email verification: {e}")
        messages.error(request, 'Failed to send email verification code.')

    return redirect('settings')

def handle_phone_verification(request, mongo):
    """Handle phone verification process"""
    import random

    try:
        phone_number = request.POST.get('phone_number', '').strip()

        if not phone_number:
            messages.error(request, 'Phone number is required for verification.')
            return redirect('settings')

        # Generate SMS verification code
        sms_code = ''.join(random.choices(string.digits, k=6))

        # Store verification code in MongoDB
        verification_data = {
            'verification.phone_code': sms_code,
            'verification.phone_code_expires': datetime.now() + timedelta(minutes=10),
            'verification.phone_attempts': 0,
            'profile.phone': phone_number,
            'last_login': datetime.now()
        }

        mongo.get_collection().update_one(
            {'username': request.user.username},
            {'$set': verification_data}
        )

        # In a real application, you would send this code via SMS
        messages.success(request, f'SMS verification code sent to {phone_number}! (Demo code: {sms_code})')

    except Exception as e:
        print(f"Error in phone verification: {e}")
        messages.error(request, 'Failed to send SMS verification code.')

    return redirect('settings')

def handle_identity_verification(request, mongo):
    """Handle identity document verification"""
    try:
        document_type = request.POST.get('document_type')
        document_number = request.POST.get('document_number', '').strip()

        if not document_type or not document_number:
            messages.error(request, 'Document type and number are required.')
            return redirect('settings')

        # Store identity verification request
        verification_data = {
            'verification.identity_document_type': document_type,
            'verification.identity_document_number': document_number,
            'verification.identity_status': 'pending',
            'verification.identity_submitted_at': datetime.now(),
            'last_login': datetime.now()
        }

        mongo.get_collection().update_one(
            {'username': request.user.username},
            {'$set': verification_data}
        )

        messages.success(request, 'Identity verification request submitted successfully! Review may take 1-3 business days.')

    except Exception as e:
        print(f"Error in identity verification: {e}")
        messages.error(request, 'Failed to submit identity verification.')

    return redirect('settings')

def handle_two_factor_setup(request, mongo):
    """Handle two-factor authentication setup"""
    try:
        action = request.POST.get('two_factor_action')

        if action == 'enable':
            # Generate backup codes
            backup_codes = [''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) for _ in range(10)]

            verification_data = {
                'verification.two_factor_enabled': True,
                'verification.two_factor_backup_codes': backup_codes,
                'verification.two_factor_setup_date': datetime.now(),
                'last_login': datetime.now()
            }

            mongo.get_collection().update_one(
                {'username': request.user.username},
                {'$set': verification_data}
            )

            messages.success(request, 'Two-factor authentication enabled successfully! Please save your backup codes.')

        elif action == 'disable':
            verification_data = {
                'verification.two_factor_enabled': False,
                'verification.two_factor_backup_codes': [],
                'verification.two_factor_disabled_date': datetime.now(),
                'last_login': datetime.now()
            }

            mongo.get_collection().update_one(
                {'username': request.user.username},
                {'$set': verification_data}
            )

            messages.success(request, 'Two-factor authentication disabled successfully.')

    except Exception as e:
        print(f"Error in two-factor setup: {e}")
        messages.error(request, 'Failed to update two-factor authentication settings.')

    return redirect('settings')

@login_required
def settings_page(request):
    """Settings page view with MongoDB integration"""
    if not request.user.is_authenticated:
        return redirect('login')

    # Handle form submissions
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'password':
            return handle_password_change(request)
        elif form_type == 'profile':
            return handle_profile_update(request)
        elif form_type == 'notifications':
            return handle_notifications_update(request)
        elif form_type == 'verification':
            return handle_verification_request(request)

    try:
        # Get user data from MongoDB
        mongo = MongoDBConnection()
        user_data = mongo.find_user({'username': request.user.username})
        
        if not user_data:
            # If user not found in MongoDB, create basic data matching schema
            user_data = {
                'username': request.user.username,
                'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                'first_name': request.user.first_name or '',
                'last_name': request.user.last_name or '',
                'email': request.user.email or '',
                'company': '',
                'role': '',
                'is_active': True,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'date_joined': timezone.now(),
                'last_login': None,
                'profile': {
                    'employee_id': f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'department': '',
                    'phone': '',
                    'location': '',
                    'bio': '',
                    'skills': []
                },
                'permissions': {
                    'can_view_candidates': True,
                    'can_edit_candidates': False,
                    'can_delete_candidates': False,
                    'can_manage_users': False
                },
                'preferences': {
                    'email_alerts': True,
                    'application_updates': True,
                    'theme': 'light',
                    'language': 'en'
                }
            }
            
            # Save this default data to MongoDB
            mongo.insert_user(user_data)
        
        # Ensure profile exists and has employee_id
        if 'profile' not in user_data or not user_data['profile'].get('employee_id'):
            if 'profile' not in user_data:
                user_data['profile'] = {}
            user_data['profile']['employee_id'] = f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Update MongoDB with employee_id
            mongo.get_collection().update_one(
                {'username': request.user.username},
                {'$set': {'profile.employee_id': user_data['profile']['employee_id']}},
                upsert=True
            )
        
        context = {
            'user_data': user_data,
        }
        
        return render(request, 'resume_app/settings.html', context)
        
    except Exception as e:
        print(f"Error in settings page: {e}")
        messages.error(request, 'An error occurred while loading settings.')
        return redirect('dashboard')

def debug_mongodb(request):
    """Debug view to check MongoDB data"""
    try:
        mongo = MongoDBConnection()
        collection = mongo.get_collection('resume_login')
        users = list(collection.find({}))
        
        return JsonResponse({
            'status': 'success',
            'total_users': len(users),
            'users': [
                {
                    'username': user.get('username'),
                    'email': user.get('email'),
                    'full_name': user.get('full_name'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'company': user.get('company'),
                    'role': user.get('role'),
                    'is_active': user.get('is_active'),
                    'date_joined': str(user.get('date_joined')),
                    'employee_id': user.get('profile', {}).get('employee_id'),
                    'phone': user.get('profile', {}).get('phone'),
                    'location': user.get('profile', {}).get('location')
                } for user in users
            ]
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

def test_auth_flow(request):
    """Test function to verify authentication flow works correctly"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Test MongoDB connection
            mongo = MongoDBConnection()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Check if user exists in MongoDB
            user_data = mongo.find_user({
                'username': username,
                'password_hash': password_hash,
                'is_active': True
            })
            
            if user_data:
                return JsonResponse({
                    'status': 'success',
                    'message': 'User found in MongoDB',
                    'user_data': {
                        'username': user_data.get('username'),
                        'email': user_data.get('email'),
                        'full_name': user_data.get('full_name'),
                        'first_name': user_data.get('first_name'),
                        'last_name': user_data.get('last_name'),
                        'company': user_data.get('company'),
                        'role': user_data.get('role'),
                        'is_active': user_data.get('is_active'),
                        'last_login': str(user_data.get('last_login')) if user_data.get('last_login') else None
                    }
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User not found or invalid credentials'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Database error: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'POST method required'})





