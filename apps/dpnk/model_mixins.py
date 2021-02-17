import photologue


class WithGalleryMixin:
    def get_gallery(self):
        if self.gallery:
            return self.gallery
        title_slug = "%s-%s-photos" % (self._meta.object_name.lower(), self.pk)
        self.gallery, _ = photologue.models.Gallery.objects.get_or_create(
            title=title_slug,
            slug=title_slug,
            is_public=False,
        )
        self.save()
        return self.gallery

    def gallery_slug(self):
        return self.get_gallery().slug

    def icon_url(self):
        if self.icon is not None:
            return self.icon.image.url
        else:
            return None
