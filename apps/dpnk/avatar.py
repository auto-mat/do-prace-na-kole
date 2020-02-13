def get_facebook_id(user):
    auth = user.social_auth.filter(provider='facebook').first()
    if auth:
        return auth.uid
    return None
