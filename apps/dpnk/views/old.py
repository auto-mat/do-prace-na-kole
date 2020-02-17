"""
class BikeRepairView(CampaignParameterMixin, TitleViewMixin, GroupRequiredResponseMixin, LoginRequiredMixin, CreateView):
    group_required = 'cykloservis'
    template_name = 'base_generic_form.html'
    form_class = forms.BikeRepairForm
    success_url = 'bike_repair'
    success_message = _("%(user_attendance)s je nováček a právě si zažádal o opravu kola")
    model = models.CommonTransaction
    title = _("Cykloservis")

    def get_initial(self):
        return {'campaign': self.campaign}

    def form_valid(self, form):
        super().form_valid(form)
        return redirect(reverse(self.success_url))
"""
