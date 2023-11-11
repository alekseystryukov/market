from django import forms


class OrderSubmitForm(forms.Form):
    store_id = forms.CharField()
    phone = forms.CharField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    note = forms.CharField(widget=forms.Textarea, required=False)
