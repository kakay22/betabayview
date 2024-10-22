from ADMIN.models import Secretary

def profile_picture(request):
	user_name = request.session.get('user_name')

	if user_name is not None:
		try:
			secretary = Secretary.objects.get(user_name=user_name)
			return {'profile_picture_url': secretary.profile_picture.url}
		except Secretary.DoesNotExist:
			return {'profile_picture_url': None}
	return {}
