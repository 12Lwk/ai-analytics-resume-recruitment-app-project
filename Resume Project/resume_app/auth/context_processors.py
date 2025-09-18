def mongodb_user_data(request):
    """
    Add MongoDB user data to template context
    """
    if request.user.is_authenticated and hasattr(request, 'session'):
        mongodb_data = request.session.get('mongodb_user_data', {})
        return {
            'user_company': mongodb_data.get('company', ''),
            'user_role': mongodb_data.get('role', ''),
            'user_permissions': mongodb_data.get('permissions', {}),
            'user_profile': mongodb_data.get('profile', {})
        }
    return {}