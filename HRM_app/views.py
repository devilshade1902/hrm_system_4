from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from .models import Department , Roles , User
from .forms import DepartmentForm , RoleForm , EmployeeForm
from django.contrib.auth import authenticate, login , logout

def is_admin(user):
    return user.is_superuser  


@login_required
def view_departments(request):
    departments = Department.objects.all()
    return render(request, 'view_departments.html', {'departments': departments})


@user_passes_test(is_admin)
def add_department(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('view_departments')
    else:
        form = DepartmentForm()
    return render(request, 'add_department.html', {'form': form})


@user_passes_test(is_admin)
def update_department(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('view_departments')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'update_department.html', {'form': form})



@user_passes_test(is_admin)
def toggle_department_status(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    department.status = not department.status  # Toggle status
    department.save()
    return redirect('view_departments')


def custom_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect based on user type
            if user.is_superuser or (hasattr(user, 'role') and user.role and user.role.role_name.lower() == 'hr'):
                return redirect('dashboard')
            return redirect('view_departments')  # Default for non-admin/non-HR users
        else:
            return render(request, "login.html", {"error": "Invalid username or password"})
    return render(request, "login.html")

def custom_logout(request):
    logout(request)
    return redirect('login') 


@login_required
def view_roles(request):
    roles = Roles.objects.all()
    return render(request, 'view_roles.html', {'roles': roles})


@user_passes_test(is_admin)
def add_role(request):
    if request.method == "POST":
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('view_roles')
    else:
        form = RoleForm()
    return render(request, 'add_role.html', {'form': form})


@user_passes_test(is_admin)
def update_role(request, role_id):
    role = get_object_or_404(Roles, id=role_id)
    if request.method == "POST":
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            return redirect('view_roles')
    else:
        form = RoleForm(instance=role)
    return render(request, 'update_role.html', {'form': form})



@user_passes_test(is_admin)
def toggle_roles_status(request, role_id):
    role = get_object_or_404(Roles, id=role_id)
    role.status = not role.status  # Toggle status
    role.save()
    return redirect('view_roles')



def is_hr_or_admin(user):
    if user.is_superuser:  # Allow admin without a role
        return True
    return hasattr(user, 'role') and user.role and user.role.role_name.lower() == 'hr'

def permission_denied(request):
    return render(request, 'permission_denied.html', {
        'message': "Only admin or HR can access this page."})

@login_required
@user_passes_test(is_hr_or_admin , login_url='permission_denied')
def dashboard(request):
    employees = User.objects.filter(is_superuser=False)
    return render(request, 'dashboard.html', {'employees': employees})

@login_required
@user_passes_test(is_hr_or_admin)
def add_employee(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data.get("password"):  # Check if password is provided
                form.add_error('password', "Password is required for new employees.")
                return render(request, 'add_employee.html', {'form': form})
            form.save()
            return redirect('dashboard')
    else:
        form = EmployeeForm()
    return render(request, 'add_employee.html', {'form': form})

@login_required
@user_passes_test(is_hr_or_admin)
def update_employee(request, emp_id):
    employee = get_object_or_404(User, employee_id=emp_id)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'update_employee.html', {'form': form})

@login_required
@user_passes_test(is_hr_or_admin)
def delete_employee(request, emp_id):
    employee = get_object_or_404(User, employee_id=emp_id)
    if employee == request.user:
        # Prevent deleting the current user
        return render(request, 'delete_employee.html', {
            'employee': employee,
            'error': "You cannot delete yourself while logged in."
        })
    if request.method == "POST":
        employee.delete()  # Hard delete: removes the employee from the database
        return redirect('dashboard')
    return render(request, 'delete_employee.html', {'employee': employee})