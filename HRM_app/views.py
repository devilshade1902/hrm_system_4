from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from .models import Department , Roles , User,Task,TaskAssignment
from .forms import DepartmentForm , RoleForm , EmployeeForm,TaskForm
from django.contrib.auth import authenticate, login , logout
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from django.core.paginator import Paginator
from django.db.models import Q, Count
from datetime import datetime

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
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if is_hr_or_admin(user):
                return redirect('dashboard')
            return redirect('view_departments')
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




def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            # Generate a 6-digit OTP
            otp = ''.join(random.choices(string.digits, k=6))
            # Store OTP in session
            request.session['reset_otp'] = otp
            request.session['reset_email'] = email
            # Send OTP email
            send_mail(
                subject='HRM System Password Reset OTP',
                message=f'Your OTP for password reset is: {otp}. It is valid for 10 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return redirect('verify_otp')
        except User.DoesNotExist:
            return render(request, "forgot_password.html", {"error": "Email not registered."})
    return render(request, "forgot_password.html")

def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_otp = request.session.get('reset_otp')
        if entered_otp == stored_otp:
            return redirect('reset_password')
        else:
            return render(request, "verify_otp.html", {"error": "Invalid OTP. Please try again."})
    return render(request, "verify_otp.html")

def reset_password(request):
    if 'reset_email' not in request.session:
        return redirect('forgot_password')  # Prevent direct access
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if new_password == confirm_password:
            email = request.session.get('reset_email')
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            # Clear session data
            del request.session['reset_otp']
            del request.session['reset_email']
            return redirect('login')
        else:
            return render(request, "reset_password.html", {"error": "Passwords do not match."})
    return render(request, "reset_password.html")



@login_required
def tasks_dashboard(request):
    # Base queryset based on user role
    if is_hr_or_admin(request.user):
        task_assignments = TaskAssignment.objects.filter(assigned_by=request.user).select_related('task', 'employee')
        employees = User.objects.filter(reporting_manager=request.user)  # For employee filter dropdown
    else:
        task_assignments = TaskAssignment.objects.filter(employee=request.user).select_related('task', 'assigned_by')
        employees = User.objects.none()  # Employees don’t filter by others

    # Filtering logic
    employee_filter = request.GET.get('employee', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if employee_filter:
        task_assignments = task_assignments.filter(employee__employee_id=employee_filter)
    if status_filter:
        task_assignments = task_assignments.filter(status=status_filter)
    if date_from:
        task_assignments = task_assignments.filter(task__start_date__gte=date_from)
    if date_to:
        task_assignments = task_assignments.filter(task__start_date__lte=date_to)

    # Handle status update (Mark Completed)
    if request.method == "POST" and 'status' in request.POST:
        assignment_id = request.POST.get('assignment_id')
        new_status = request.POST.get('status')
        assignment = get_object_or_404(TaskAssignment, assignment_id=assignment_id)
        if assignment.employee == request.user or is_hr_or_admin(request.user):
            if new_status in ['Pending', 'In Progress', 'Completed']:
                assignment.status = new_status
                if new_status == 'Completed':
                    assignment.completed_at = datetime.now()
                elif new_status != 'Completed':
                    assignment.completed_at = None
                assignment.save()
        return redirect(request.get_full_path())  # Preserve filters

    # Statistics (Fixed: Use 'assignment_id' instead of 'id')
    stats = task_assignments.aggregate(
        completed=Count('assignment_id', filter=Q(status='Completed')),
        pending=Count('assignment_id', filter=Q(status='Pending')),
        in_progress=Count('assignment_id', filter=Q(status='In Progress'))
    )

    # Pagination
    paginator = Paginator(task_assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'is_hr_or_admin': is_hr_or_admin(request.user),
        'employees': employees,
        'employee_filter': employee_filter,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'stats': stats,
    }
    return render(request, 'tasks_dashboard.html', context)

@login_required
@user_passes_test(is_hr_or_admin, login_url='permission_denied')
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save()
            assigned_to = form.cleaned_data['assigned_to']
            for employee in assigned_to:
                TaskAssignment.objects.create(
                    task=task,
                    employee=employee,
                    assigned_by=request.user
                )
            return redirect('tasks_dashboard')
    else:
        form = TaskForm(user=request.user)
    return render(request, 'create_task.html', {'form': form})

@login_required
@user_passes_test(is_hr_or_admin, login_url='permission_denied')
def update_task(request, task_id):
    task = get_object_or_404(Task, task_id=task_id)
    assignments = TaskAssignment.objects.filter(task=task)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            new_assigned_to = form.cleaned_data['assigned_to']
            current_assignees = set(assignments.values_list('employee__employee_id', flat=True))
            new_assignees = set(new_assigned_to.values_list('employee_id', flat=True))
            assignments.exclude(employee__employee_id__in=new_assignees).delete()
            for employee in new_assigned_to:
                if employee.employee_id not in current_assignees:
                    TaskAssignment.objects.create(task=task, employee=employee, assigned_by=request.user)
            return redirect('tasks_dashboard')
    else:
        form = TaskForm(instance=task, user=request.user, initial={
            'assigned_to': [assignment.employee for assignment in assignments]
        })
    return render(request, 'update_task.html', {'form': form, 'task': task})

@login_required
@user_passes_test(is_hr_or_admin, login_url='permission_denied')
def delete_task(request, task_id):
    task = get_object_or_404(Task, task_id=task_id)
    if request.method == "POST":
        task.delete()
        return redirect('tasks_dashboard')
    return render(request, 'delete_task.html', {'task': task})

@login_required
def task_detail(request, assignment_id):
    assignment = get_object_or_404(TaskAssignment, assignment_id=assignment_id)
    if assignment.employee != request.user and not is_hr_or_admin(request.user):
        return render(request, 'permission_denied.html', {'message': "You can only view your own tasks."})
    return render(request, 'task_detail.html', {'assignment': assignment})