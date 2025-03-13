from django import forms
from .models import Department,Roles , User

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['dept_name', 'description']
        
class RoleForm(forms.ModelForm):
    class Meta:
        model = Roles
        fields = ['role_name', 'description']
        

class EmployeeForm(forms.ModelForm):
    dept = forms.ModelChoiceField(queryset=Department.objects.all(), label="Select Department")
    role = forms.ModelChoiceField(queryset=Roles.objects.all(), label="Select Role")
    reporting_manager = forms.ModelChoiceField(queryset=User.objects.all(), required=False, label="Reporting Manager")
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        label="Set Password (leave blank to keep unchanged)"
    )
    date_of_joining = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date of Joining",
        required=False  # Match the model's null=True, blank=True
    )

    class Meta:
        model = User
        # Exclude password from the fields list to prevent it from being updated automatically
        fields = ['first_name', 'last_name', 'username', 'email', 'mobile', 'dept', 'role', 'reporting_manager', 'date_of_joining']

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:  # Only update password if a new value is provided
            user.set_password(password)
        if commit:
            user.save()
        return user