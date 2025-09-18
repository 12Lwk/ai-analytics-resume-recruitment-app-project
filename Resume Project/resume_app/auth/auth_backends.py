import hashlib
from datetime import datetime
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from ..views import MongoDBConnection

class MongoDBAuthBackend(BaseBackend):
    """
    Custom authentication backend that authenticates against MongoDB
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
            
        try:
            # Connect to MongoDB and find user
            mongo = MongoDBConnection()
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            user_data = mongo.find_user({
                'username': username,
                'password_hash': password_hash,
                'is_active': True
            })
            
            if user_data:
                # Update last_login in MongoDB
                mongo.get_collection().update_one(
                    {'username': username},
                    {'$set': {'last_login': datetime.utcnow()}}
                )
                
                # Create or get Django User object for session management
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    # Create a Django user for session management
                    user = User.objects.create_user(
                        username=username,
                        email=user_data.get('email', ''),
                        first_name=user_data.get('first_name', ''),
                        last_name=user_data.get('last_name', ''),
                        password=None  # We don't store password in Django
                    )
                
                # Update user info from MongoDB
                user.email = user_data.get('email', '')
                user.first_name = user_data.get('first_name', '')
                user.last_name = user_data.get('last_name', '')
                user.is_active = user_data.get('is_active', True)
                user.is_staff = user_data.get('is_staff', False)
                user.is_superuser = user_data.get('is_superuser', False)
                user.save()
                
                # Store MongoDB user data in session for later use
                if hasattr(request, 'session'):
                    request.session['mongodb_user_data'] = {
                        'company': user_data.get('company', ''),
                        'role': user_data.get('role', ''),
                        'permissions': user_data.get('permissions', {}),
                        'profile': user_data.get('profile', {}),
                        'preferences': user_data.get('preferences', {})
                    }
                
                return user
                
        except Exception as e:
            print(f"Authentication error: {e}")
            
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


