from django import forms
from .models import Department,Roles , User, Task 

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
    

class TaskForm(forms.ModelForm):
    TASK_PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    TASK_TYPE_CHOICES = [
        ('Individual', 'Individual'),
        ('Team', 'Team'),
    ]

    task_priority = forms.ChoiceField(choices=TASK_PRIORITY_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    task_type = forms.ChoiceField(choices=TASK_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control', 'id': 'task_type'}))
    assigned_to = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'id': 'assigned_to'}),
        label="Assigned To"
    )

    class Meta:
        model = Task
        fields = ['task_title', 'task_description', 'task_priority', 'start_date', 'end_date', 'task_type', 'assigned_to']
        widgets = {
            'task_title': forms.TextInput(attrs={'class': 'form-control'}),
            'task_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['assigned_to'].queryset = User.objects.filter(reporting_manager=user)

    def clean(self):
        cleaned_data = super().clean()
        task_type = cleaned_data.get('task_type')
        assigned_to = cleaned_data.get('assigned_to')
        if task_type == 'Individual' and assigned_to and len(assigned_to) > 1:
            raise forms.ValidationError("For an Individual task, only one employee can be assigned.")
        return cleaned_data